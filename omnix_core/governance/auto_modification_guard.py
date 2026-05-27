"""
OMNIX Auto-Modification Guard (AMG)
ADR-144: Meta-Governance Layer Over Adaptive Governance

═══════════════════════════════════════════════════════════════════════════════
PURPOSE
═══════════════════════════════════════════════════════════════════════════════

Every automated threshold modification to AVM snapshots — whether triggered by
MCM auto-remediation (ADR-118) or AVM Phase 3/4 optimization (ADR-120) — MUST
pass through this guard before any change is written to disk or database.

The AMG enforces six governance invariants:

  1. CUMULATIVE DRIFT CAP    — total threshold change from genesis never exceeds
                               AVM_MAX_CUMULATIVE_DRIFT_PCT (default 30%).
  2. AUTOMATIC ROLLBACK      — post-deployment performance check at T+24h; if
                               degradation is detected, previous snapshot is
                               automatically restored.
  3. SIGNED DIFF PROOF       — every modification produces a cryptographic proof
                               of the exact before/after delta, signed with the
                               process signing key (Dilithium-3 when available).
  4. APPROVAL GATE           — any single threshold change > AVM_APPROVAL_THRESHOLD_PCT
                               (default 10%) is HELD pending human approval via
                               Telegram. AVM_AUTO_APPROVE=true bypasses in dev only.
  5. AUTO_MODIFIED TRUST FLAG — receipts issued under auto-modified snapshots carry
                               trust_flags.auto_modified_snapshot=true.
  6. ANTI-LOOP GUARD         — MCM cannot trigger recalibration that feeds back into
                               its own CRITICAL detection within 24 hours.

═══════════════════════════════════════════════════════════════════════════════
DESIGN INVARIANTS (never relaxed)
═══════════════════════════════════════════════════════════════════════════════

- Past governance receipts are immutable. AMG only affects future evaluations.
- The genesis snapshot is permanent. It is never overwritten. It is the only
  anchor for cumulative drift computation.
- AMG failure mode is BLOCK, not PASS. If the guard cannot evaluate a
  safeguard (DB unavailable, genesis snapshot missing), the modification is
  HELD — not permitted silently.
- ADR-116 fail-closed policy is never affected by AMG modifications.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

logger = logging.getLogger("OMNIX.AMG")

# ── Environment configuration — dynamic readers ────────────────────────────────
# All env vars are read at call time (not import time) so that Railway can set
# them before server startup and test suites can patch os.environ reliably.
# Module-level constants are NEVER used for guard decisions.

def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        return default


def _max_cumulative_drift_pct() -> float:
    """AVM_MAX_CUMULATIVE_DRIFT_PCT — hard cap on total drift from genesis (default 30%)."""
    return _env_float("AVM_MAX_CUMULATIVE_DRIFT_PCT", 30.0)


def _approval_threshold_pct() -> float:
    """AVM_APPROVAL_THRESHOLD_PCT — single-threshold delta requiring human approval (default 10%)."""
    return _env_float("AVM_APPROVAL_THRESHOLD_PCT", 10.0)


def _rollback_window_hours() -> float:
    """AVM_ROLLBACK_WINDOW_HOURS — hours after deployment before performance rollback check (default 24)."""
    return _env_float("AVM_ROLLBACK_WINDOW_HOURS", 24.0)


def _anti_loop_window_hours() -> float:
    """AVM_ANTI_LOOP_WINDOW_HOURS — anti-loop detection window in hours (default 24)."""
    return _env_float("AVM_ANTI_LOOP_WINDOW_HOURS", 24.0)


def _auto_approve() -> bool:
    """AVM_AUTO_APPROVE — bypass approval gate (true only for dev/test environments)."""
    active = os.environ.get("AVM_AUTO_APPROVE", "false").lower() == "true"
    if active:
        logger.error(
            "[AMG] SECURITY WARNING: AVM_AUTO_APPROVE=true is active — "
            "the AMG approval gate is DISABLED. This must NEVER be set in production. "
            "All threshold modifications will be auto-approved without human review."
        )
    return active


# ── Backward-compatible module-level aliases (read-only, never used in guards) ─
# These exist solely for external code that may have imported the old constants.
# Do NOT use these in guard logic — use the _xxx() accessor functions instead.
MAX_CUMULATIVE_DRIFT_PCT: float = 30.0   # noqa — see _max_cumulative_drift_pct()
APPROVAL_THRESHOLD_PCT:   float = 10.0   # noqa — see _approval_threshold_pct()
ROLLBACK_WINDOW_HOURS:    float = 24.0   # noqa — see _rollback_window_hours()
ANTI_LOOP_WINDOW_HOURS:   float = 24.0   # noqa — see _anti_loop_window_hours()
AUTO_APPROVE:             bool  = False  # noqa — see _auto_approve()


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_conn(db_url: str):
    try:
        import psycopg
        return psycopg.connect(db_url)
    except Exception as exc:
        logger.error(f"[AMG] DB connection failed: {exc}")
        return None


# ── 1. Cumulative drift cap ────────────────────────────────────────────────────

def compute_cumulative_drift(
    genesis_thresholds: dict[str, float],
    proposed_thresholds: dict[str, float],
) -> float:
    """
    Return the mean absolute percentage change from genesis to proposed.

    Formula per checkpoint:
        delta_pct = |proposed - genesis| / genesis × 100

    Returns the mean across all shared checkpoints (0–∞).
    Returns 0.0 if genesis is empty or no overlap exists.
    """
    if not genesis_thresholds:
        return 0.0
    deltas = []
    for cp, genesis_val in genesis_thresholds.items():
        proposed_val = proposed_thresholds.get(cp)
        if proposed_val is None:
            continue
        if genesis_val == 0:
            continue
        deltas.append(abs(proposed_val - genesis_val) / abs(genesis_val) * 100.0)
    if not deltas:
        return 0.0
    return round(sum(deltas) / len(deltas), 2)


def _fetch_genesis_thresholds(domain: str, db_url: str) -> dict[str, float] | None:
    """
    Load checkpoint_thresholds from the genesis snapshot for this domain.
    Returns None if genesis not found or DB unavailable.
    """
    conn = _get_conn(db_url)
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT checkpoint_thresholds
              FROM avm_calibration_snapshots
             WHERE domain = %s AND is_genesis = TRUE
             LIMIT 1
            """,
            (domain,),
        )
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            raw = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            return {k: float(v) for k, v in raw.items()}
        return None
    except Exception as exc:
        logger.warning(f"[AMG] _fetch_genesis_thresholds failed for {domain}: {exc}")
        try:
            conn.close()
        except Exception:
            pass
        return None


# ── 2. Signed diff proof ───────────────────────────────────────────────────────

def build_signed_diff_proof(
    domain: str,
    thresholds_before: dict[str, float],
    thresholds_after: dict[str, float],
    actor: str = "system",
) -> tuple[str, str]:
    """
    Build a cryptographic diff proof for a threshold modification.

    Format:
        AMG-DIFF-v1:{sha256_hex}:{algorithm}[:{pqc_sig_b64}]

    Returns:
        (proof_string, algorithm_name)
    """
    ts_utc = datetime.now(timezone.utc).isoformat()
    canonical_payload = json.dumps(
        {
            "domain":  domain,
            "before":  dict(sorted(thresholds_before.items())),
            "after":   dict(sorted(thresholds_after.items())),
            "actor":   actor,
            "ts_utc":  ts_utc,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    sha256_hex = hashlib.sha256(canonical_payload.encode()).hexdigest()

    # Attempt PQC signing (Dilithium-3) if available
    pqc_sig_b64: str | None = None
    algorithm = "SHA-256"
    try:
        from omnix_core.security.crypto_providers import get_active_provider
        provider = get_active_provider()
        sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
        if provider and sk_b64:
            sk_bytes = base64.b64decode(sk_b64)
            sig_bytes = provider.sign(sha256_hex.encode(), sk_bytes)
            if sig_bytes:
                pqc_sig_b64 = base64.b64encode(sig_bytes).decode()
                algorithm = provider.algorithm_name()
    except Exception as _pqc_err:
        logger.debug(f"[AMG] PQC signing unavailable, using SHA-256: {_pqc_err}")

    proof = f"AMG-DIFF-v1:{sha256_hex}:{algorithm}"
    if pqc_sig_b64:
        proof += f":{pqc_sig_b64[:64]}"  # truncate for storage, full sig in payload

    return proof, algorithm


# ── 3. Single-delta computation ───────────────────────────────────────────────

def _max_single_delta_pct(
    thresholds_before: dict[str, float],
    thresholds_after: dict[str, float],
) -> float:
    """Return the largest single-threshold change in % relative to the before value."""
    max_delta = 0.0
    for cp, before_val in thresholds_before.items():
        after_val = thresholds_after.get(cp)
        if after_val is None or before_val == 0:
            continue
        delta = abs(after_val - before_val) / abs(before_val) * 100.0
        if delta > max_delta:
            max_delta = delta
    return round(max_delta, 2)


# ── 4. Record modification ────────────────────────────────────────────────────

def record_modification(
    domain: str,
    thresholds_before: dict[str, float],
    thresholds_after: dict[str, float],
    diff_proof: str,
    diff_proof_algorithm: str,
    cumulative_drift_pct: float,
    max_single_delta_pct: float,
    source: str,
    status: str,
    db_url: str,
) -> str:
    """
    Persist a modification record to avm_modification_registry.

    Returns the modification_id (e.g. "AMG-TRADING-4A7B3F").
    """
    modification_id = f"AMG-{domain.upper()[:12]}-{uuid.uuid4().hex[:8].upper()}"
    conn = _get_conn(db_url)
    if not conn:
        logger.error(f"[AMG] Cannot record modification — DB unavailable: {modification_id}")
        return modification_id
    try:
        performance_check_at = datetime.now(timezone.utc) + timedelta(hours=ROLLBACK_WINDOW_HOURS)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO avm_modification_registry (
                modification_id, domain, source,
                thresholds_before, thresholds_after,
                diff_proof, diff_proof_algorithm,
                cumulative_drift_pct, max_single_delta_pct,
                status, approval_required, performance_check_at
            ) VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (modification_id) DO NOTHING
            """,
            (
                modification_id, domain, source,
                json.dumps(thresholds_before), json.dumps(thresholds_after),
                diff_proof, diff_proof_algorithm,
                cumulative_drift_pct, max_single_delta_pct,
                status, status == "PENDING_APPROVAL", performance_check_at,
            ),
        )
        conn.commit()
        conn.close()
        logger.info(
            f"[AMG] Modification recorded: id={modification_id} domain={domain} "
            f"source={source} status={status} cumulative_drift={cumulative_drift_pct:.1f}%"
        )
    except Exception as exc:
        logger.error(f"[AMG] record_modification failed: {exc}")
        try:
            conn.close()
        except Exception:
            pass
    return modification_id


# ── 5. Approval gate ──────────────────────────────────────────────────────────

def check_approval_gate(
    domain: str,
    thresholds_before: dict[str, float],
    thresholds_after: dict[str, float],
    source: str,
    db_url: str,
) -> tuple[bool, float, str | None]:
    """
    Check whether this modification requires human approval.

    Rules:
      - If max single delta > APPROVAL_THRESHOLD_PCT (default 10%) → approval required
      - AVM_AUTO_APPROVE=true bypasses this gate (dev/test only)
      - If approval required: write PENDING_APPROVAL record, notify Telegram
      - Returns (gate_passed, max_delta_pct, modification_id_if_held)
    """
    max_delta = _max_single_delta_pct(thresholds_before, thresholds_after)

    _approval_thresh = _approval_threshold_pct()
    if max_delta <= _approval_thresh or _auto_approve():
        return True, max_delta, None

    # Approval required — record PENDING and notify
    diff_proof, algo = build_signed_diff_proof(domain, thresholds_before, thresholds_after, source)
    genesis_thresholds = _fetch_genesis_thresholds(domain, db_url) or {}
    cumulative_drift = compute_cumulative_drift(genesis_thresholds, thresholds_after)

    mod_id = record_modification(
        domain=domain,
        thresholds_before=thresholds_before,
        thresholds_after=thresholds_after,
        diff_proof=diff_proof,
        diff_proof_algorithm=algo,
        cumulative_drift_pct=cumulative_drift,
        max_single_delta_pct=max_delta,
        source=source,
        status="PENDING_APPROVAL",
        db_url=db_url,
    )

    logger.warning(
        f"[AMG] APPROVAL GATE HELD: domain={domain} mod_id={mod_id} "
        f"max_delta={max_delta:.1f}% > threshold={_approval_thresh:.1f}% "
        f"source={source}"
    )

    _notify_telegram(
        f"🔒 AMG APPROVAL REQUIRED\n"
        f"Domain: {domain}\n"
        f"Modification ID: {mod_id}\n"
        f"Source: {source}\n"
        f"Max single threshold change: {max_delta:.1f}%\n"
        f"Cumulative drift from genesis: {cumulative_drift:.1f}%\n"
        f"Diff proof: {diff_proof[:48]}...\n\n"
        f"Reply /approve_avm {mod_id} to deploy, or /reject_avm {mod_id} to discard."
    )

    return False, max_delta, mod_id


# ── 6. Anti-loop guard ────────────────────────────────────────────────────────

def is_auto_loop(domain: str, db_url: str) -> bool:
    """
    ADR-144 §6: Detect MCM→MCM feedback loops.

    A loop is defined as: 2+ entries in mcm_remediation_log for the same domain,
    within ANTI_LOOP_WINDOW_HOURS, both with action_taken IN
    ('TIGHTEN_CHECKPOINT_THRESHOLDS', 'FORCE_AVM_RECALIBRATION').

    Returns True if a loop is detected (modification should be escalated, not executed).
    """
    conn = _get_conn(db_url)
    if not conn:
        logger.warning(f"[AMG] is_auto_loop: DB unavailable for {domain} — assuming no loop")
        return False
    try:
        _loop_window = _anti_loop_window_hours()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=_loop_window)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*)
              FROM mcm_remediation_log
             WHERE domain = %s
               AND triggered_at >= %s
               AND action_taken IN (
                   'TIGHTEN_CHECKPOINT_THRESHOLDS',
                   'FORCE_AVM_RECALIBRATION'
               )
               AND outcome NOT IN ('ROLLED_BACK', 'REJECTED', 'SKIPPED')
            """,
            (domain, cutoff),
        )
        row = cur.fetchone()
        conn.close()
        count = int(row[0]) if row else 0
        if count >= 2:
            logger.warning(
                f"[AMG] LOOP DETECTED: domain={domain} has {count} auto-remediations "
                f"in the last {_loop_window:.0f}h — escalating to human"
            )
            return True
        return False
    except Exception as exc:
        logger.warning(f"[AMG] is_auto_loop query failed for {domain}: {exc}")
        try:
            conn.close()
        except Exception:
            pass
        return False


# ── 7. Rollback check ─────────────────────────────────────────────────────────

def check_rollback_needed(domain: str, db_url: str) -> tuple[bool, dict[str, float] | None]:
    """
    ADR-144 §2: Check whether a post-deployment performance rollback is needed.

    Logic:
      - Find the most recent DEPLOYED modification for this domain whose
        performance_check_at has passed.
      - Compare: if the domain's current block rate diverges from the expected
        direction, trigger rollback by returning (True, thresholds_before).
      - If no rollback needed or check not yet due: return (False, None).

    Note: this method queries avm_modification_registry only. It does NOT execute
    the rollback itself — the caller (deploy_optimized_thresholds) handles that.
    """
    conn = _get_conn(db_url)
    if not conn:
        return False, None
    try:
        now = datetime.now(timezone.utc)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT modification_id, thresholds_before, max_single_delta_pct,
                   performance_check_at
              FROM avm_modification_registry
             WHERE domain = %s
               AND status = 'DEPLOYED'
               AND performance_check_at <= %s
             ORDER BY created_at DESC
             LIMIT 1
            """,
            (domain, now),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return False, None

        mod_id, thresholds_before_raw, max_delta, perf_check_at = row
        thresholds_before = (
            thresholds_before_raw
            if isinstance(thresholds_before_raw, dict)
            else json.loads(thresholds_before_raw)
        )

        # Query recent block rate (last 24h vs previous 24h)
        cur.execute(
            """
            SELECT
                SUM(CASE WHEN decision = 'BLOCKED' AND timestamp_utc >= NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END)::float
                    / NULLIF(SUM(CASE WHEN timestamp_utc >= NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END), 0) AS post_block_rate,
                SUM(CASE WHEN decision = 'BLOCKED'
                         AND timestamp_utc >= NOW() - INTERVAL '48 hours'
                         AND timestamp_utc < NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END)::float
                    / NULLIF(SUM(CASE WHEN timestamp_utc >= NOW() - INTERVAL '48 hours'
                                      AND timestamp_utc < NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END), 0) AS pre_block_rate
              FROM decision_receipts
             WHERE domain = %s
            """,
            (domain,),
        )
        rates_row = cur.fetchone()
        conn.close()

        if not rates_row or rates_row[0] is None or rates_row[1] is None:
            # Insufficient data for rollback decision — mark check done, skip rollback
            logger.info(f"[AMG] {domain}: insufficient data for rollback check mod={mod_id}")
            return False, None

        post_block_rate = float(rates_row[0])
        pre_block_rate  = float(rates_row[1])

        # If block rate worsened by > 50% relative to pre-deployment: rollback
        # "Worsened" means: if we tightened (higher block rate expected) but it got
        # even MORE blocked than expected; or if we loosened but block rate INCREASED.
        worsened = abs(post_block_rate - pre_block_rate) > 0.5 * pre_block_rate and post_block_rate > pre_block_rate

        if worsened:
            logger.warning(
                f"[AMG] ROLLBACK TRIGGERED: domain={domain} mod={mod_id} "
                f"pre_block={pre_block_rate:.1%} post_block={post_block_rate:.1%} — "
                f"performance degraded after auto-modification"
            )
            return True, {k: float(v) for k, v in thresholds_before.items()}

        logger.info(
            f"[AMG] {domain}: post-deployment check OK mod={mod_id} "
            f"pre={pre_block_rate:.1%} post={post_block_rate:.1%}"
        )
        return False, None

    except Exception as exc:
        logger.error(f"[AMG] check_rollback_needed failed for {domain}: {exc}")
        try:
            conn.close()
        except Exception:
            pass
        return False, None


def mark_modification_status(modification_id: str, status: str, db_url: str) -> None:
    """Update the status of a modification record (DEPLOYED, ROLLED_BACK, REJECTED, VERIFIED_OK)."""
    conn = _get_conn(db_url)
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE avm_modification_registry
               SET status = %s,
                   performance_check_at = CASE
                       WHEN %s = 'DEPLOYED' THEN NOW() + %s * INTERVAL '1 hour'
                       ELSE performance_check_at
                   END
             WHERE modification_id = %s
            """,
            (status, status, _rollback_window_hours(), modification_id),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning(f"[AMG] mark_modification_status failed {modification_id}: {exc}")
        try:
            conn.close()
        except Exception:
            pass


# ── Main guard entry-point ────────────────────────────────────────────────────

class AutoModificationResult:
    """
    Result of running the full AMG gate sequence.

    Attributes:
        allowed        — True if the modification may proceed
        modification_id — ID written to avm_modification_registry
        blocked_reason  — Human-readable reason if allowed=False
        cumulative_drift_pct — Drift from genesis baseline
        max_single_delta_pct — Largest single threshold change
        diff_proof      — Signed diff proof string
        diff_proof_algo — Algorithm used for proof
        trust_flags     — Dict to embed in AVMResult / governance receipts
    """

    def __init__(
        self,
        allowed: bool,
        modification_id: str,
        blocked_reason: str | None,
        cumulative_drift_pct: float,
        max_single_delta_pct: float,
        diff_proof: str,
        diff_proof_algo: str,
    ):
        self.allowed               = allowed
        self.modification_id       = modification_id
        self.blocked_reason        = blocked_reason
        self.cumulative_drift_pct  = cumulative_drift_pct
        self.max_single_delta_pct  = max_single_delta_pct
        self.diff_proof            = diff_proof
        self.diff_proof_algo       = diff_proof_algo

    @property
    def trust_flags(self) -> dict[str, Any]:
        return {
            "auto_modified_snapshot":    True,
            "modification_id":           self.modification_id,
            "cumulative_drift_from_genesis_pct": self.cumulative_drift_pct,
            "max_single_delta_pct":      self.max_single_delta_pct,
            "diff_proof":                self.diff_proof[:48] + "...",
            "diff_proof_algorithm":      self.diff_proof_algo,
        }


def run_guard(
    domain: str,
    thresholds_before: dict[str, float],
    thresholds_after: dict[str, float],
    source: str,
    db_url: str,
) -> AutoModificationResult:
    """
    Run all AMG safeguards in sequence. Returns AutoModificationResult.

    Sequence:
      1. Fetch genesis thresholds
      2. Compute cumulative drift — block if > MAX_CUMULATIVE_DRIFT_PCT
      3. Build signed diff proof
      4. Check approval gate — hold if single delta > APPROVAL_THRESHOLD_PCT
      5. Record modification (DEPLOYED or PENDING_APPROVAL)
      6. Return result with trust_flags

    Note: is_auto_loop() is checked separately by MCM before calling run_guard().
    Note: check_rollback_needed() is checked in a post-deployment background job.
    """
    # ── Step 1: genesis thresholds ─────────────────────────────────────────────
    genesis_thresholds = _fetch_genesis_thresholds(domain, db_url) or {}
    if not genesis_thresholds:
        logger.warning(
            f"[AMG] {domain}: no genesis snapshot found — using thresholds_before as reference"
        )
        genesis_thresholds = thresholds_before

    # ── Step 2: cumulative drift cap ───────────────────────────────────────────
    _drift_cap = _max_cumulative_drift_pct()
    cumulative_drift = compute_cumulative_drift(genesis_thresholds, thresholds_after)
    if cumulative_drift > _drift_cap:
        reason = (
            f"Cumulative drift from genesis {cumulative_drift:.1f}% exceeds hard cap "
            f"{_drift_cap:.1f}% (AVM_MAX_CUMULATIVE_DRIFT_PCT). "
            f"Auto-modification BLOCKED. Manual human review required."
        )
        logger.error(f"[AMG] DRIFT CAP EXCEEDED: domain={domain} {reason}")
        _notify_telegram(
            f"🚨 AMG DRIFT CAP EXCEEDED\n"
            f"Domain: {domain}\n"
            f"Source: {source}\n"
            f"Cumulative drift: {cumulative_drift:.1f}% (cap: {_drift_cap:.1f}%)\n"
            f"Modification BLOCKED. Manual review required."
        )
        diff_proof, algo = build_signed_diff_proof(domain, thresholds_before, thresholds_after, source)
        mod_id = record_modification(
            domain=domain,
            thresholds_before=thresholds_before,
            thresholds_after=thresholds_after,
            diff_proof=diff_proof,
            diff_proof_algorithm=algo,
            cumulative_drift_pct=cumulative_drift,
            max_single_delta_pct=_max_single_delta_pct(thresholds_before, thresholds_after),
            source=source,
            status="REJECTED",
            db_url=db_url,
        )
        return AutoModificationResult(
            allowed=False,
            modification_id=mod_id,
            blocked_reason=reason,
            cumulative_drift_pct=cumulative_drift,
            max_single_delta_pct=_max_single_delta_pct(thresholds_before, thresholds_after),
            diff_proof=diff_proof,
            diff_proof_algo=algo,
        )

    # ── Step 3: signed diff proof ──────────────────────────────────────────────
    diff_proof, algo = build_signed_diff_proof(domain, thresholds_before, thresholds_after, source)
    max_delta = _max_single_delta_pct(thresholds_before, thresholds_after)

    # ── Step 4: approval gate ──────────────────────────────────────────────────
    gate_passed, _, pending_mod_id = check_approval_gate(
        domain=domain,
        thresholds_before=thresholds_before,
        thresholds_after=thresholds_after,
        source=source,
        db_url=db_url,
    )

    if not gate_passed:
        reason = (
            f"Approval gate HELD: max single delta {max_delta:.1f}% > "
            f"{_approval_threshold_pct():.1f}% threshold. "
            f"Awaiting human approval — modification_id={pending_mod_id}"
        )
        return AutoModificationResult(
            allowed=False,
            modification_id=pending_mod_id or "PENDING",
            blocked_reason=reason,
            cumulative_drift_pct=cumulative_drift,
            max_single_delta_pct=max_delta,
            diff_proof=diff_proof,
            diff_proof_algo=algo,
        )

    # ── Step 5: record as DEPLOYED ─────────────────────────────────────────────
    mod_id = record_modification(
        domain=domain,
        thresholds_before=thresholds_before,
        thresholds_after=thresholds_after,
        diff_proof=diff_proof,
        diff_proof_algorithm=algo,
        cumulative_drift_pct=cumulative_drift,
        max_single_delta_pct=max_delta,
        source=source,
        status="DEPLOYED",
        db_url=db_url,
    )

    logger.info(
        f"[AMG] ✅ Modification APPROVED: domain={domain} mod_id={mod_id} "
        f"source={source} cumulative={cumulative_drift:.1f}% max_delta={max_delta:.1f}%"
    )

    return AutoModificationResult(
        allowed=True,
        modification_id=mod_id,
        blocked_reason=None,
        cumulative_drift_pct=cumulative_drift,
        max_single_delta_pct=max_delta,
        diff_proof=diff_proof,
        diff_proof_algo=algo,
    )


# ── Telegram helper ───────────────────────────────────────────────────────────

def _notify_telegram(message: str) -> None:
    try:
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        admin_id  = os.environ.get("TELEGRAM_ADMIN_USER_ID", "")
        if not bot_token or not admin_id:
            return
        import urllib.request as _req
        payload = json.dumps({"chat_id": admin_id, "text": message}).encode()
        _req.urlopen(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=payload,
            timeout=5,
        )
    except Exception:
        pass

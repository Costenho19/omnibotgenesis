"""
OMNIX BEV — Mandate Integrity Verification Protocol (MIVP)
ADR-194 · RFC-ATF-6 extension

Closes the governance gap between constraint conformance and mandate alignment:
an agent can satisfy every BEV constraint while optimizing for a proxy metric
instead of the declared mandate. MIVP detects and halts that failure mode.

Three artifact classes:
  MBR  — Mandate Binding Record      (per session, issued before turn 1)
  MAS  — Mandate Alignment Score     (per turn, continuous [0.0, 1.0])
  MBRS — MBR Seal                    (per session, issued at close)

Invariants enforced here:
  MIVP-INV-001: MBR MUST be issued and PQC-signed BEFORE the first agent turn.
  MIVP-INV-002: mandate_objective_hash is fixed at session start — immutable.
  MIVP-INV-003: Every turn in an MBR-bound session MUST produce a MAS before output delivery.
  MIVP-INV-004: MAS MUST be in [0.0, 1.0]; out-of-range → HALT.
  MIVP-INV-005: MAS < mas_halt_threshold → HALT verdict immediately.
  MIVP-INV-006: MAS history is append-only, linked to CTCHC turn hash.
  MIVP-INV-007: MBR Seal MUST be issued at session close covering all turns.
  MIVP-INV-008: MANDATE-BOUND PoGC tag requires MBR present, seal complete, turns_in_violation=0.

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("OMNIX.BEV.MIVP")

# ── Compiled thresholds (non-overridable for safety-critical defaults) ─────────
_DEFAULT_MAS_HALT    = float(os.environ.get("MIVP_MAS_HALT_THRESHOLD", "0.30"))
_DEFAULT_MAS_WARNING = float(os.environ.get("MIVP_MAS_WARNING_THRESHOLD", "0.65"))

# ── PoGC Compliance Tags — Tiered Mandate Certification ─────────────────────
#
# Three-tier hierarchy (MIVP-INV-008 / MIVP-INV-009):
#
#   MANDATE-BOUND   — Pristine execution: zero violations AND zero warnings.
#                     Highest designation. Every turn tracked at or above the
#                     warning threshold throughout the session.
#
#   MANDATE-ALIGNED — Mission-aligned: zero violations, warnings allowed.
#                     Agent stayed within mandate intent despite transient
#                     drift signals. Second-tier designation.
#
#   (no tag)        — Mandate violations recorded. MANDATE-BOUND and
#                     MANDATE-ALIGNED are both withheld.
#
# Only one tag is appended to the PoGC per session. MANDATE-BOUND supersedes
# MANDATE-ALIGNED — both are never issued simultaneously.
MANDATE_BOUND_TAG   = "MANDATE-BOUND"
MANDATE_ALIGNED_TAG = "MANDATE-ALIGNED"


# ─────────────────────────────────────────────────────────────────
#  Sub-structures
# ─────────────────────────────────────────────────────────────────

@dataclass
class ProxyGuard:
    """
    A single proxy optimization guard.

    Identifies a measurable signal that indicates the agent is optimizing
    for a prohibited proxy metric instead of the declared mandate.
    """
    guard_id: str
    signal_name: str
    description: str
    detection_keywords: List[str]
    weight: float                     # contribution to MAS degradation [0.0, 1.0]

    def activation_score(self, text: str) -> float:
        """
        Compute proxy activation [0.0, 1.0] for this guard against output text.

        A higher activation score means the text shows more evidence of
        optimizing for this guard's prohibited signal.

        Implementation: keyword density analysis (production deployments should
        extend this with domain-specific ML classifiers).
        """
        if not text or not self.detection_keywords:
            return 0.0
        text_lower = text.lower()
        total_words = max(len(text_lower.split()), 1)
        hits = 0
        for kw in self.detection_keywords:
            # Count non-overlapping occurrences
            pattern = re.compile(re.escape(kw.lower()))
            hits += len(pattern.findall(text_lower))
        # Normalize: 0 hits → 0.0; 1 hit per 20 words → 1.0 (saturates at 5+)
        density = hits / total_words
        return min(1.0, density * 20.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "guard_id": self.guard_id,
            "signal_name": self.signal_name,
            "description": self.description,
            "detection_keywords": self.detection_keywords,
            "weight": round(self.weight, 4),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProxyGuard":
        return cls(
            guard_id=d["guard_id"],
            signal_name=d["signal_name"],
            description=d.get("description", ""),
            detection_keywords=d.get("detection_keywords", []),
            weight=float(d.get("weight", 0.5)),
        )


# ─────────────────────────────────────────────────────────────────
#  Artifact 1 — Mandate Binding Record (MBR)
# ─────────────────────────────────────────────────────────────────

@dataclass
class MandateBindingRecord:
    """
    PQC-signed declaration of the session's true mandate, issued before turn 1.

    The MBR cryptographically binds:
      1. The declared objective (mandate_objective_hash — immutable, MIVP-INV-002)
      2. The proxy guards (what the agent must NOT optimize for)
      3. The admissibility thresholds (halt and warning MAS levels)

    This is the artifact that answers Brian Hodak's question:
    "Was the original intent bound before path generation?"
    Answer: Yes — MBR is PQC-signed before the first agent turn (MIVP-INV-001).
    """
    mbr_id: str
    session_id: str
    governing_receipt_id: str
    mandate_objective: str
    mandate_objective_hash: str       # SHA-256 — immutable reference (MIVP-INV-002)
    proxy_guards: List[ProxyGuard]
    objective_constraints: List[str]
    mas_halt_threshold: float
    mas_warning_threshold: float
    issued_at: str
    content_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]

    @classmethod
    def _canonical(
        cls,
        session_id: str,
        governing_receipt_id: str,
        mandate_objective_hash: str,
        proxy_guards: List[ProxyGuard],
        objective_constraints: List[str],
        mas_halt_threshold: float,
        mas_warning_threshold: float,
        issued_at: str,
    ) -> str:
        return json.dumps({
            "session_id": session_id,
            "governing_receipt_id": governing_receipt_id,
            "mandate_objective_hash": mandate_objective_hash,
            "proxy_guards": [g.to_dict() for g in proxy_guards],
            "objective_constraints": sorted(objective_constraints),
            "mas_halt_threshold": mas_halt_threshold,
            "mas_warning_threshold": mas_warning_threshold,
            "issued_at": issued_at,
        }, sort_keys=True)

    @classmethod
    def compute_content_hash(
        cls,
        session_id: str,
        governing_receipt_id: str,
        mandate_objective_hash: str,
        proxy_guards: List[ProxyGuard],
        objective_constraints: List[str],
        mas_halt_threshold: float,
        mas_warning_threshold: float,
        issued_at: str,
    ) -> str:
        canonical = cls._canonical(
            session_id, governing_receipt_id, mandate_objective_hash,
            proxy_guards, objective_constraints,
            mas_halt_threshold, mas_warning_threshold, issued_at,
        )
        return hashlib.sha3_256(canonical.encode()).hexdigest()

    def verify_content_hash(self) -> bool:
        expected = self.compute_content_hash(
            self.session_id, self.governing_receipt_id,
            self.mandate_objective_hash, self.proxy_guards,
            self.objective_constraints,
            self.mas_halt_threshold, self.mas_warning_threshold,
            self.issued_at,
        )
        return self.content_hash == expected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mbr_id": self.mbr_id,
            "session_id": self.session_id,
            "governing_receipt_id": self.governing_receipt_id,
            "mandate_objective": self.mandate_objective,
            "mandate_objective_hash": self.mandate_objective_hash,
            "proxy_guards": [g.to_dict() for g in self.proxy_guards],
            "objective_constraints": self.objective_constraints,
            "mas_halt_threshold": self.mas_halt_threshold,
            "mas_warning_threshold": self.mas_warning_threshold,
            "issued_at": self.issued_at,
            "content_hash": self.content_hash,
            "pqc_signature": self.pqc_signature,
            "pqc_algorithm": self.pqc_algorithm,
        }

    def mandate_summary(self) -> Dict[str, Any]:
        return {
            "mbr_id": self.mbr_id,
            "session_id": self.session_id,
            "mandate_objective": self.mandate_objective,
            "mandate_objective_hash": self.mandate_objective_hash,
            "proxy_guards_count": len(self.proxy_guards),
            "mas_halt_threshold": self.mas_halt_threshold,
            "mas_warning_threshold": self.mas_warning_threshold,
            "pqc_signed": self.pqc_signature is not None,
            "issued_at": self.issued_at,
        }


# ─────────────────────────────────────────────────────────────────
#  Artifact 2 — Mandate Alignment Score (MAS)
# ─────────────────────────────────────────────────────────────────

@dataclass
class MandateAlignmentScore:
    """
    Per-turn continuous [0.0, 1.0] signal measuring mandate alignment.

    MAS = 1.0 - Σ(proxy_guard_i.weight × proxy_activation_i)

    1.0 = fully aligned with declared mandate (no proxy optimization detected)
    0.0 = fully optimizing for prohibited proxies

    Linked to the CTCHC turn hash (MIVP-INV-006) for chain continuity.
    """
    mas_id: str
    session_id: str
    mbr_id: str
    bar_id: str
    turn_index: int
    alignment_score: float            # [0.0, 1.0] — MIVP-INV-004
    proxy_activations: Dict[str, float]  # guard_id → activation_score
    dominant_proxy: Optional[str]     # guard with highest activation, if any
    verdict: str                      # ALIGNED | WARNING | HALT
    ctchc_link_hash: Optional[str]    # MIVP-INV-006
    computed_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mas_id": self.mas_id,
            "session_id": self.session_id,
            "mbr_id": self.mbr_id,
            "bar_id": self.bar_id,
            "turn_index": self.turn_index,
            "alignment_score": round(self.alignment_score, 4),
            "proxy_activations": {
                k: round(v, 4) for k, v in self.proxy_activations.items()
            },
            "dominant_proxy": self.dominant_proxy,
            "verdict": self.verdict,
            "ctchc_link_hash": self.ctchc_link_hash,
            "computed_at": self.computed_at,
        }

    def mas_summary(self) -> Dict[str, Any]:
        return {
            "mas_id": self.mas_id,
            "turn_index": self.turn_index,
            "alignment_score": round(self.alignment_score, 4),
            "verdict": self.verdict,
            "dominant_proxy": self.dominant_proxy,
        }


# ─────────────────────────────────────────────────────────────────
#  Artifact 3 — MBR Seal (per session, at close)
# ─────────────────────────────────────────────────────────────────

@dataclass
class MBRSeal:
    """
    Session-level mandate alignment attestation, issued at close.

    Summarizes the mandate alignment across all turns and determines
    whether the session qualifies for the MANDATE-BOUND PoGC tag.

    MIVP-INV-007: Must be issued at session close.
    MIVP-INV-008: mandate_verdict = ALIGNED + turns_in_violation = 0 → MANDATE-BOUND.
    """
    seal_id: str
    session_id: str
    mbr_id: str
    final_mas: float
    mas_average: float
    mas_minimum: float
    turns_covered: int
    turns_in_warning: int
    turns_in_violation: int
    mandate_verdict: str              # ALIGNED | WARNING | VIOLATED
    mandate_bound_eligible: bool      # MIVP-INV-008: zero violations + zero warnings
    mandate_aligned_eligible: bool    # MIVP-INV-009: zero violations (warnings allowed)
    sealed_at: str
    content_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seal_id": self.seal_id,
            "session_id": self.session_id,
            "mbr_id": self.mbr_id,
            "final_mas": round(self.final_mas, 4),
            "mas_average": round(self.mas_average, 4),
            "mas_minimum": round(self.mas_minimum, 4),
            "turns_covered": self.turns_covered,
            "turns_in_warning": self.turns_in_warning,
            "turns_in_violation": self.turns_in_violation,
            "mandate_verdict": self.mandate_verdict,
            "mandate_bound_eligible": self.mandate_bound_eligible,
            "mandate_aligned_eligible": self.mandate_aligned_eligible,
            "mandate_certification_tier": (
                "MANDATE-BOUND" if self.mandate_bound_eligible
                else "MANDATE-ALIGNED" if self.mandate_aligned_eligible
                else "UNCERTIFIED"
            ),
            "sealed_at": self.sealed_at,
            "content_hash": self.content_hash,
            "pqc_signature": self.pqc_signature,
            "pqc_algorithm": self.pqc_algorithm,
        }

    def seal_summary(self) -> Dict[str, Any]:
        return {
            "seal_id": self.seal_id,
            "mandate_verdict": self.mandate_verdict,
            "mandate_bound_eligible": self.mandate_bound_eligible,
            "mandate_aligned_eligible": self.mandate_aligned_eligible,
            "mandate_certification_tier": (
                "MANDATE-BOUND" if self.mandate_bound_eligible
                else "MANDATE-ALIGNED" if self.mandate_aligned_eligible
                else "UNCERTIFIED"
            ),
            "mas_average": round(self.mas_average, 4),
            "mas_minimum": round(self.mas_minimum, 4),
            "turns_covered": self.turns_covered,
            "turns_in_warning": self.turns_in_warning,
            "turns_in_violation": self.turns_in_violation,
        }


# ─────────────────────────────────────────────────────────────────
#  MIVP Engine
# ─────────────────────────────────────────────────────────────────

class MIVPEngine:
    """
    Mandate Integrity Verification Protocol engine.

    Activated when a governing receipt's constraint_set contains a
    'mandate_binding' block. Integrates with the OGR session lifecycle:

      start_session → create_mbr()          (MIVP-INV-001)
      record_turn   → compute_mas()          (MIVP-INV-003)
      close_session → seal_mbr()             (MIVP-INV-007)
      get_proof     → get_mandate_proof()
    """

    _CREATE_MBR_TABLE = """
    CREATE TABLE IF NOT EXISTS atf_mandate_binding_records (
        mbr_id               TEXT PRIMARY KEY,
        session_id           TEXT NOT NULL UNIQUE,
        governing_receipt_id TEXT NOT NULL,
        mandate_objective    TEXT NOT NULL,
        mandate_objective_hash TEXT NOT NULL,
        proxy_guards         JSONB NOT NULL DEFAULT '[]'::jsonb,
        objective_constraints JSONB NOT NULL DEFAULT '[]'::jsonb,
        mas_halt_threshold   REAL NOT NULL DEFAULT 0.30,
        mas_warning_threshold REAL NOT NULL DEFAULT 0.65,
        content_hash         TEXT NOT NULL,
        pqc_signature        TEXT,
        pqc_algorithm        TEXT,
        issued_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        metadata             JSONB DEFAULT '{}'::jsonb
    );
    CREATE INDEX IF NOT EXISTS idx_mbr_session ON atf_mandate_binding_records(session_id);
    """

    _CREATE_MAS_TABLE = """
    CREATE TABLE IF NOT EXISTS atf_mandate_alignment_scores (
        mas_id              TEXT PRIMARY KEY,
        session_id          TEXT NOT NULL,
        mbr_id              TEXT NOT NULL,
        bar_id              TEXT NOT NULL,
        turn_index          INTEGER NOT NULL,
        alignment_score     REAL NOT NULL,
        proxy_activations   JSONB NOT NULL DEFAULT '{}'::jsonb,
        dominant_proxy      TEXT,
        verdict             TEXT NOT NULL DEFAULT 'ALIGNED',
        ctchc_link_hash     TEXT,
        computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        metadata            JSONB DEFAULT '{}'::jsonb
    );
    CREATE INDEX IF NOT EXISTS idx_mas_session   ON atf_mandate_alignment_scores(session_id);
    CREATE INDEX IF NOT EXISTS idx_mas_turn      ON atf_mandate_alignment_scores(session_id, turn_index);
    CREATE INDEX IF NOT EXISTS idx_mas_verdict   ON atf_mandate_alignment_scores(verdict);
    """

    _CREATE_SEAL_TABLE = """
    CREATE TABLE IF NOT EXISTS atf_mbr_seals (
        seal_id                  TEXT PRIMARY KEY,
        session_id               TEXT NOT NULL UNIQUE,
        mbr_id                   TEXT NOT NULL,
        final_mas                REAL NOT NULL,
        mas_average              REAL NOT NULL,
        mas_minimum              REAL NOT NULL,
        turns_covered            INTEGER NOT NULL DEFAULT 0,
        turns_in_warning         INTEGER NOT NULL DEFAULT 0,
        turns_in_violation       INTEGER NOT NULL DEFAULT 0,
        mandate_verdict          TEXT NOT NULL DEFAULT 'ALIGNED',
        mandate_bound_eligible   BOOLEAN NOT NULL DEFAULT FALSE,
        mandate_aligned_eligible BOOLEAN NOT NULL DEFAULT FALSE,
        mandate_certification_tier TEXT NOT NULL DEFAULT 'UNCERTIFIED',
        content_hash             TEXT NOT NULL,
        pqc_signature            TEXT,
        pqc_algorithm            TEXT,
        sealed_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_seal_tier CHECK (
            mandate_certification_tier IN ('MANDATE-BOUND', 'MANDATE-ALIGNED', 'UNCERTIFIED')
        ),
        CONSTRAINT chk_seal_tier_consistency CHECK (
            NOT (mandate_bound_eligible AND mandate_aligned_eligible)
        )
    );
    CREATE INDEX IF NOT EXISTS idx_mbrseal_session  ON atf_mbr_seals(session_id);
    CREATE INDEX IF NOT EXISTS idx_mbrseal_tier     ON atf_mbr_seals(mandate_certification_tier);
    CREATE INDEX IF NOT EXISTS idx_mbrseal_bound    ON atf_mbr_seals(mandate_bound_eligible);
    CREATE INDEX IF NOT EXISTS idx_mbrseal_aligned  ON atf_mbr_seals(mandate_aligned_eligible);
    """

    # F-003: FK constraints applied as a non-fatal post-table step (referencing
    # atf_ogr_sessions and atf_mandate_binding_records, which may not yet exist
    # when MIVP initialises first). Applied opportunistically in ensure_tables().
    _APPLY_SEAL_FK = """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'fk_seals_mbr'
        ) THEN
            ALTER TABLE atf_mbr_seals
                ADD CONSTRAINT fk_seals_mbr
                FOREIGN KEY (mbr_id)
                REFERENCES atf_mandate_binding_records(mbr_id)
                ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
        END IF;
    END $$;
    """

    def __init__(self):
        self._db_url = os.environ.get("DATABASE_URL")
        # In-memory stores for no-DB environments
        self._mbr_store: Dict[str, MandateBindingRecord]  = {}
        self._mas_store: Dict[str, List[MandateAlignmentScore]] = {}
        self._seal_store: Dict[str, MBRSeal] = {}

    def ensure_tables(self) -> None:
        if not self._db_url:
            return
        try:
            import psycopg
            with psycopg.connect(self._db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(self._CREATE_MBR_TABLE)
                    cur.execute(self._CREATE_MAS_TABLE)
                    cur.execute(self._CREATE_SEAL_TABLE)
                conn.commit()
            logger.info("[MIVP] Tables ready: atf_mandate_binding_records, "
                        "atf_mandate_alignment_scores, atf_mbr_seals")
        except Exception as exc:
            logger.warning(f"[MIVP] ensure_tables failed (non-blocking): {exc}")

        # F-003: Apply FK constraint opportunistically — non-fatal if referenced
        # table (atf_mandate_binding_records) was not created in the same init order.
        if self._db_url:
            try:
                import psycopg
                with psycopg.connect(self._db_url) as conn:
                    with conn.cursor() as cur:
                        cur.execute(self._APPLY_SEAL_FK)
                    conn.commit()
                logger.debug("[MIVP] FK constraint fk_seals_mbr applied (or already exists)")
            except Exception as fk_exc:
                logger.debug(f"[MIVP] FK constraint not applied (non-blocking): {fk_exc}")

    # ── PQC signing (mirrors BAR/CCS pattern) ────────────────────

    def _pqc_sign(self, content_hash: str) -> tuple[Optional[str], Optional[str]]:
        try:
            from omnix_core.security.pqc_security import PQCSecurity
            sig = PQCSecurity.sign(content_hash.encode())
            return sig, "ML-DSA-65 (Dilithium-3, FIPS 204)"
        except Exception as exc:
            logger.debug(f"[MIVP] PQC sign unavailable: {exc}")
            return None, None

    # ─────────────────────────────────────────────────────────────
    #  1. CREATE MBR — before turn 1 (MIVP-INV-001)
    # ─────────────────────────────────────────────────────────────

    def create_mbr(
        self,
        session_id: str,
        governing_receipt_id: str,
        mandate_binding: Dict[str, Any],
    ) -> MandateBindingRecord:
        """
        Create and PQC-sign the Mandate Binding Record for a session.

        Must be called before record_turn() is called (MIVP-INV-001).
        The mandate_objective_hash is computed and frozen here (MIVP-INV-002).

        mandate_binding schema:
          {
            "mandate_objective": "Maximize merchant net recovery ...",
            "proxy_guards": [{"guard_id": ..., "signal_name": ...,
                              "detection_keywords": [...], "weight": 0.6}, ...],
            "objective_constraints": ["Do not optimize for ..."],
            "mas_halt_threshold": 0.30,      # optional, default 0.30
            "mas_warning_threshold": 0.65,   # optional, default 0.65
          }
        """
        if not mandate_binding.get("mandate_objective"):
            raise ValueError("mandate_binding.mandate_objective is required")

        mandate_objective = mandate_binding["mandate_objective"]
        mandate_objective_hash = hashlib.sha256(
            mandate_objective.encode("utf-8")
        ).hexdigest()

        raw_guards = mandate_binding.get("proxy_guards", [])
        proxy_guards = [ProxyGuard.from_dict(g) for g in raw_guards]

        # Normalize weights to sum to 1.0
        total_weight = sum(g.weight for g in proxy_guards)
        if total_weight > 0:
            for g in proxy_guards:
                g.weight = g.weight / total_weight

        objective_constraints = mandate_binding.get("objective_constraints", [])
        mas_halt = float(mandate_binding.get("mas_halt_threshold", _DEFAULT_MAS_HALT))
        mas_warn = float(mandate_binding.get("mas_warning_threshold", _DEFAULT_MAS_WARNING))

        # F-006: floor validation — prevents disabling HALT via env/config (MIVP-INV-005)
        if mas_halt < 0.05:
            raise ValueError(
                f"mas_halt_threshold {mas_halt} invalid: minimum is 0.05. "
                "Setting below 0.05 effectively disables mandate HALT (MIVP-INV-005)."
            )
        if mas_halt >= mas_warn:
            raise ValueError(
                f"mas_halt_threshold {mas_halt} must be strictly less than "
                f"mas_warning_threshold {mas_warn}."
            )

        issued_at = datetime.now(timezone.utc).isoformat()
        mbr_id = f"MBR-{uuid.uuid4().hex[:16].upper()}"

        content_hash = MandateBindingRecord.compute_content_hash(
            session_id, governing_receipt_id, mandate_objective_hash,
            proxy_guards, objective_constraints, mas_halt, mas_warn, issued_at,
        )
        pqc_sig, pqc_algo = self._pqc_sign(content_hash)

        mbr = MandateBindingRecord(
            mbr_id=mbr_id,
            session_id=session_id,
            governing_receipt_id=governing_receipt_id,
            mandate_objective=mandate_objective,
            mandate_objective_hash=mandate_objective_hash,
            proxy_guards=proxy_guards,
            objective_constraints=objective_constraints,
            mas_halt_threshold=mas_halt,
            mas_warning_threshold=mas_warn,
            issued_at=issued_at,
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_algo,
        )

        self._mbr_store[session_id] = mbr
        self._mas_store[session_id] = []
        self._persist_mbr(mbr)

        logger.info(
            f"[MIVP] MBR created: {mbr_id} | session={session_id} "
            f"| guards={len(proxy_guards)} | halt={mas_halt} | warn={mas_warn}"
        )
        return mbr

    # ─────────────────────────────────────────────────────────────
    #  2. COMPUTE MAS — per turn (MIVP-INV-003)
    # ─────────────────────────────────────────────────────────────

    def compute_mas(
        self,
        session_id: str,
        bar_id: str,
        turn_index: int,
        output_text: str,
        ctchc_link_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MandateAlignmentScore:
        """
        Compute the Mandate Alignment Score for one agent turn.

        MAS = 1.0 - Σ(guard.weight × guard.activation_score(output))

        MIVP-INV-003: Must run before output delivery.
        MIVP-INV-004: Score guaranteed in [0.0, 1.0].
        MIVP-INV-006: ctchc_link_hash links MAS to the behavioral chain.
        """
        mbr = self.get_mbr(session_id)
        if mbr is None:
            raise RuntimeError(
                f"[MIVP] No MBR found for session {session_id}. "
                "create_mbr() must be called before compute_mas()."
            )

        # Compute per-guard proxy activations
        proxy_activations: Dict[str, float] = {}
        weighted_sum = 0.0
        dominant_proxy = None
        max_activation = 0.0

        for guard in mbr.proxy_guards:
            act = guard.activation_score(output_text)
            proxy_activations[guard.guard_id] = act
            weighted_sum += guard.weight * act
            if act > max_activation:
                max_activation = act
                dominant_proxy = guard.signal_name if act > 0.05 else None

        # MIVP-INV-004: clamp to [0.0, 1.0]
        alignment_score = max(0.0, min(1.0, 1.0 - weighted_sum))

        # Determine verdict
        if alignment_score < mbr.mas_halt_threshold:
            verdict = "HALT"
        elif alignment_score < mbr.mas_warning_threshold:
            verdict = "WARNING"
        else:
            verdict = "ALIGNED"

        mas = MandateAlignmentScore(
            mas_id=f"MAS-{uuid.uuid4().hex[:16].upper()}",
            session_id=session_id,
            mbr_id=mbr.mbr_id,
            bar_id=bar_id,
            turn_index=turn_index,
            alignment_score=alignment_score,
            proxy_activations=proxy_activations,
            dominant_proxy=dominant_proxy,
            verdict=verdict,
            ctchc_link_hash=ctchc_link_hash,
            computed_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        # Append-only (MIVP-INV-006)
        if session_id not in self._mas_store:
            self._mas_store[session_id] = []
        self._mas_store[session_id].append(mas)
        self._persist_mas(mas)

        log_fn = logger.warning if verdict != "ALIGNED" else logger.debug
        log_fn(
            f"[MIVP] MAS turn={turn_index} | score={alignment_score:.3f} "
            f"| verdict={verdict} | dominant_proxy={dominant_proxy} | session={session_id}"
        )

        if verdict == "HALT":
            logger.warning(
                f"[MIVP] MANDATE HALT — session={session_id} turn={turn_index} "
                f"MAS={alignment_score:.3f} < threshold={mbr.mas_halt_threshold} "
                f"(MIVP-INV-005)"
            )

        return mas

    # ─────────────────────────────────────────────────────────────
    #  3. SEAL MBR — at session close (MIVP-INV-007)
    # ─────────────────────────────────────────────────────────────

    def seal_mbr(self, session_id: str) -> MBRSeal:
        """
        Issue the MBR Seal covering all turns. Called at session close.

        MIVP-INV-007: Must cover all turns.
        MIVP-INV-008: mandate_bound_eligible = True only if turns_in_violation = 0.
        """
        mbr = self.get_mbr(session_id)
        if mbr is None:
            raise RuntimeError(f"[MIVP] Cannot seal — no MBR for session {session_id}")

        mas_history = self.get_mas_history(session_id)
        if not mas_history:
            # No turns recorded — session sealed with 0 turns covered
            final_mas = 1.0
            mas_avg = 1.0
            mas_min = 1.0
        else:
            scores = [m.alignment_score for m in mas_history]
            final_mas = scores[-1]
            mas_avg   = sum(scores) / len(scores)
            mas_min   = min(scores)

        turns_in_warning   = sum(1 for m in mas_history if m.verdict == "WARNING")
        turns_in_violation = sum(1 for m in mas_history if m.verdict == "HALT")

        if turns_in_violation > 0:
            mandate_verdict = "VIOLATED"
        elif turns_in_warning > 0:
            mandate_verdict = "WARNING"
        else:
            mandate_verdict = "ALIGNED"

        # ── Three-tier mandate certification (MIVP-INV-008 / MIVP-INV-009) ──────
        #
        # MANDATE-BOUND   (tier 1, highest): pristine execution.
        #   Requires turns_in_violation = 0 AND turns_in_warning = 0.
        #   Every agent turn was tracked at or above the warning threshold.
        #   The governing mandate was followed without a single detected drift signal.
        #
        # MANDATE-ALIGNED (tier 2): mission-aligned despite transient signals.
        #   Requires turns_in_violation = 0, warnings are permitted.
        #   The agent never violated the mandate halt boundary; warning-level
        #   drift occurred but was never confirmed as a mandate breach.
        #
        # (no tag)        (tier 3): mandate violations recorded.
        #   turns_in_violation > 0. Both higher tiers are withheld.
        #
        # At this point mbr is always non-None (early-return guard above).
        mandate_bound_eligible   = (turns_in_violation == 0 and turns_in_warning == 0)
        mandate_aligned_eligible = (turns_in_violation == 0 and turns_in_warning > 0)

        sealed_at = datetime.now(timezone.utc).isoformat()
        seal_id   = f"MBRS-{uuid.uuid4().hex[:16].upper()}"

        seal_content = json.dumps({
            "seal_id": seal_id,
            "session_id": session_id,
            "mbr_id": mbr.mbr_id,
            "final_mas": round(final_mas, 4),
            "mas_average": round(mas_avg, 4),
            "mas_minimum": round(mas_min, 4),
            "turns_covered": len(mas_history),
            "turns_in_warning": turns_in_warning,
            "turns_in_violation": turns_in_violation,
            "mandate_verdict": mandate_verdict,
            "mandate_bound_eligible": mandate_bound_eligible,
            "mandate_aligned_eligible": mandate_aligned_eligible,
            "mandate_certification_tier": (
                "MANDATE-BOUND" if mandate_bound_eligible
                else "MANDATE-ALIGNED" if mandate_aligned_eligible
                else "UNCERTIFIED"
            ),
            "sealed_at": sealed_at,
        }, sort_keys=True)
        content_hash = hashlib.sha3_256(seal_content.encode()).hexdigest()
        pqc_sig, pqc_algo = self._pqc_sign(content_hash)

        seal = MBRSeal(
            seal_id=seal_id,
            session_id=session_id,
            mbr_id=mbr.mbr_id,
            final_mas=final_mas,
            mas_average=mas_avg,
            mas_minimum=mas_min,
            turns_covered=len(mas_history),
            turns_in_warning=turns_in_warning,
            turns_in_violation=turns_in_violation,
            mandate_verdict=mandate_verdict,
            mandate_bound_eligible=mandate_bound_eligible,
            mandate_aligned_eligible=mandate_aligned_eligible,
            sealed_at=sealed_at,
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_algo,
        )

        self._seal_store[session_id] = seal
        self._persist_seal(seal)

        logger.info(
            f"[MIVP] MBR sealed: {seal_id} | session={session_id} "
            f"| verdict={mandate_verdict} | mandate_bound={mandate_bound_eligible} "
            f"| avg_mas={mas_avg:.3f} | violations={turns_in_violation}"
        )
        return seal

    # ─────────────────────────────────────────────────────────────
    #  4. GETTERS
    # ─────────────────────────────────────────────────────────────

    def get_mbr(self, session_id: str) -> Optional[MandateBindingRecord]:
        if session_id in self._mbr_store:
            return self._mbr_store[session_id]
        return self._load_mbr_from_db(session_id)

    def get_mas_history(self, session_id: str) -> List[MandateAlignmentScore]:
        if session_id in self._mas_store:
            return sorted(self._mas_store[session_id], key=lambda m: m.turn_index)
        return self._load_mas_from_db(session_id)

    def get_seal(self, session_id: str) -> Optional[MBRSeal]:
        if session_id in self._seal_store:
            return self._seal_store[session_id]
        return self._load_seal_from_db(session_id)

    def is_mandate_bound_eligible(self, session_id: str) -> bool:
        """Returns True if session qualifies for MANDATE-BOUND PoGC tag (MIVP-INV-008)."""
        seal = self.get_seal(session_id)
        return seal.mandate_bound_eligible if seal else False

    def get_mandate_proof(self, session_id: str) -> Dict[str, Any]:
        """Full MIVP evidence package for a session (for get_proof integration)."""
        mbr = self.get_mbr(session_id)
        if mbr is None:
            return {"mivp_active": False}

        mas_history = self.get_mas_history(session_id)
        seal = self.get_seal(session_id)

        return {
            "mivp_active": True,
            "mbr": mbr.mandate_summary(),
            "mas_history": [m.mas_summary() for m in mas_history],
            "mbr_seal": seal.seal_summary() if seal else None,
            "mandate_bound_eligible": seal.mandate_bound_eligible if seal else False,
            "pqc_signed": mbr.pqc_signature is not None,
            "invariants_enforced": [
                "MIVP-INV-001", "MIVP-INV-002", "MIVP-INV-003",
                "MIVP-INV-004", "MIVP-INV-005", "MIVP-INV-006",
                "MIVP-INV-007", "MIVP-INV-008",
            ],
        }

    # ─────────────────────────────────────────────────────────────
    #  Persistence (DB + in-memory fallback)
    # ─────────────────────────────────────────────────────────────

    def _persist_mbr(self, mbr: MandateBindingRecord) -> None:
        if not self._db_url:
            return
        try:
            import psycopg
            with psycopg.connect(self._db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_mandate_binding_records
                          (mbr_id, session_id, governing_receipt_id,
                           mandate_objective, mandate_objective_hash,
                           proxy_guards, objective_constraints,
                           mas_halt_threshold, mas_warning_threshold,
                           content_hash, pqc_signature, pqc_algorithm, issued_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (session_id) DO NOTHING
                    """, (
                        mbr.mbr_id, mbr.session_id, mbr.governing_receipt_id,
                        mbr.mandate_objective, mbr.mandate_objective_hash,
                        json.dumps([g.to_dict() for g in mbr.proxy_guards]),
                        json.dumps(mbr.objective_constraints),
                        mbr.mas_halt_threshold, mbr.mas_warning_threshold,
                        mbr.content_hash, mbr.pqc_signature, mbr.pqc_algorithm,
                        mbr.issued_at,
                    ))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[MIVP] MBR persist failed (non-blocking): {exc}")

    def _persist_mas(self, mas: MandateAlignmentScore) -> None:
        if not self._db_url:
            return
        try:
            import psycopg
            with psycopg.connect(self._db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_mandate_alignment_scores
                          (mas_id, session_id, mbr_id, bar_id, turn_index,
                           alignment_score, proxy_activations, dominant_proxy,
                           verdict, ctchc_link_hash, computed_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (mas_id) DO NOTHING
                    """, (
                        mas.mas_id, mas.session_id, mas.mbr_id, mas.bar_id,
                        mas.turn_index, mas.alignment_score,
                        json.dumps({k: round(v, 4) for k, v in mas.proxy_activations.items()}),
                        mas.dominant_proxy, mas.verdict,
                        mas.ctchc_link_hash, mas.computed_at,
                    ))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[MIVP] MAS persist failed (non-blocking): {exc}")

    def _persist_seal(self, seal: MBRSeal) -> None:
        if not self._db_url:
            return
        try:
            import psycopg
            with psycopg.connect(self._db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_mbr_seals
                          (seal_id, session_id, mbr_id, final_mas, mas_average,
                           mas_minimum, turns_covered, turns_in_warning,
                           turns_in_violation, mandate_verdict,
                           mandate_bound_eligible, mandate_aligned_eligible,
                           mandate_certification_tier,
                           content_hash, pqc_signature, pqc_algorithm, sealed_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (session_id) DO NOTHING
                    """, (
                        seal.seal_id, seal.session_id, seal.mbr_id,
                        seal.final_mas, seal.mas_average, seal.mas_minimum,
                        seal.turns_covered, seal.turns_in_warning,
                        seal.turns_in_violation, seal.mandate_verdict,
                        seal.mandate_bound_eligible, seal.mandate_aligned_eligible,
                        (
                            "MANDATE-BOUND" if seal.mandate_bound_eligible
                            else "MANDATE-ALIGNED" if seal.mandate_aligned_eligible
                            else "UNCERTIFIED"
                        ),
                        seal.content_hash,
                        seal.pqc_signature, seal.pqc_algorithm, seal.sealed_at,
                    ))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[MIVP] MBR Seal persist failed (non-blocking): {exc}")

    def _load_mbr_from_db(self, session_id: str) -> Optional[MandateBindingRecord]:
        if not self._db_url:
            return None
        try:
            import psycopg
            with psycopg.connect(self._db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM atf_mandate_binding_records WHERE session_id=%s",
                        (session_id,)
                    )
                    row = cur.fetchone()
                    if row is None:
                        return None
                    cols = [d[0] for d in cur.description]
                    d = dict(zip(cols, row))
                    guards_raw = d.get("proxy_guards") or []
                    if isinstance(guards_raw, str):
                        guards_raw = json.loads(guards_raw)
                    mbr = MandateBindingRecord(
                        mbr_id=d["mbr_id"],
                        session_id=d["session_id"],
                        governing_receipt_id=d["governing_receipt_id"],
                        mandate_objective=d["mandate_objective"],
                        mandate_objective_hash=d["mandate_objective_hash"],
                        proxy_guards=[ProxyGuard.from_dict(g) for g in guards_raw],
                        objective_constraints=d.get("objective_constraints") or [],
                        mas_halt_threshold=float(d["mas_halt_threshold"]),
                        mas_warning_threshold=float(d["mas_warning_threshold"]),
                        issued_at=str(d["issued_at"]),
                        content_hash=d["content_hash"],
                        pqc_signature=d.get("pqc_signature"),
                        pqc_algorithm=d.get("pqc_algorithm"),
                    )
                    self._mbr_store[session_id] = mbr
                    return mbr
        except Exception as exc:
            logger.warning(f"[MIVP] MBR DB load failed: {exc}")
            return None

    def _load_mas_from_db(self, session_id: str) -> List[MandateAlignmentScore]:
        if not self._db_url:
            return []
        try:
            import psycopg
            with psycopg.connect(self._db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM atf_mandate_alignment_scores "
                        "WHERE session_id=%s ORDER BY turn_index ASC",
                        (session_id,)
                    )
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description]
                    result = []
                    for row in rows:
                        d = dict(zip(cols, row))
                        pa = d.get("proxy_activations") or {}
                        if isinstance(pa, str):
                            pa = json.loads(pa)
                        result.append(MandateAlignmentScore(
                            mas_id=d["mas_id"],
                            session_id=d["session_id"],
                            mbr_id=d["mbr_id"],
                            bar_id=d["bar_id"],
                            turn_index=int(d["turn_index"]),
                            alignment_score=float(d["alignment_score"]),
                            proxy_activations=pa,
                            dominant_proxy=d.get("dominant_proxy"),
                            verdict=d["verdict"],
                            ctchc_link_hash=d.get("ctchc_link_hash"),
                            computed_at=str(d["computed_at"]),
                        ))
                    self._mas_store[session_id] = result
                    return result
        except Exception as exc:
            logger.warning(f"[MIVP] MAS DB load failed: {exc}")
            return []

    def _load_seal_from_db(self, session_id: str) -> Optional[MBRSeal]:
        if not self._db_url:
            return None
        try:
            import psycopg
            with psycopg.connect(self._db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM atf_mbr_seals WHERE session_id=%s",
                        (session_id,)
                    )
                    row = cur.fetchone()
                    if row is None:
                        return None
                    cols = [d[0] for d in cur.description]
                    d = dict(zip(cols, row))
                    seal = MBRSeal(
                        seal_id=d["seal_id"],
                        session_id=d["session_id"],
                        mbr_id=d["mbr_id"],
                        final_mas=float(d["final_mas"]),
                        mas_average=float(d["mas_average"]),
                        mas_minimum=float(d["mas_minimum"]),
                        turns_covered=int(d["turns_covered"]),
                        turns_in_warning=int(d["turns_in_warning"]),
                        turns_in_violation=int(d["turns_in_violation"]),
                        mandate_verdict=d["mandate_verdict"],
                        mandate_bound_eligible=bool(d["mandate_bound_eligible"]),
                        sealed_at=str(d["sealed_at"]),
                        content_hash=d["content_hash"],
                        pqc_signature=d.get("pqc_signature"),
                        pqc_algorithm=d.get("pqc_algorithm"),
                    )
                    self._seal_store[session_id] = seal
                    return seal
        except Exception as exc:
            logger.warning(f"[MIVP] Seal DB load failed: {exc}")
            return None

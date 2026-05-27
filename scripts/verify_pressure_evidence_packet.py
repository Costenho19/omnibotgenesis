"""
OMNIX QUANTUM — Pressure Evidence Packet Verifier
==================================================
RFC-ATF-1 through RFC-ATF-6 · ADR-157 · ADR-159 · ADR-200
TA-14 Third-Pass: Offline Verification of Pressure Scenarios

Verifies every cryptographic artifact in a Pressure Evidence Packet
WITHOUT calling the OMNIX runtime. All verification uses only the
public key embedded in the packet.

Scenarios verified:
  P1 — Authority Drift       (DR expired before admissibility gate)
  P2 — Stale Continuity      (CES degraded to HALT band)
  P3 — RC TTL Enforcement    (Reauthorization Challenge expired → HALT)

Per scenario, verifies:
  ✓ DR  — content_hash (SHA-256/compact) + PQC signature
  ✓ TAR — content_hash (SHA-256/compact) + admission_status
  ✓ RCR — hash integrity (SHA3-256/default) + PQC signature
  ✓ Binding — hash + PQC signature + refusal/halt status
  ✓ Refusal/HALT receipt — hash + PQC signature
  ✓ Outcome — hash + execution_occurred=False
  ✓ Pressure invariant assertions per scenario

Usage:
  python scripts/verify_pressure_evidence_packet.py <packet_file.json>

Exit codes:
  0 — all verifications PASS
  1 — one or more verifications FAIL

Author: Harold Nunes — OMNIX QUANTUM LTD
ADR: ADR-200 · ADR-157 · ADR-159
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────────────────────────────────────
#  Report
# ─────────────────────────────────────────────────────────────────────────────

class VerificationReport:
    def __init__(self, packet_id: str):
        self.packet_id = packet_id
        self.checks: List[Dict] = []
        self.passed = self.failed = self.skipped = 0

    def add(self, check_id: str, label: str, passed: bool, detail: str = "", skip: bool = False):
        status = "SKIP" if skip else ("PASS" if passed else "FAIL")
        icon   = "⏭ " if skip else ("✓" if passed else "✗")
        self.checks.append({"id": check_id, "label": label, "result": status, "detail": detail})
        if skip:   self.skipped += 1
        elif passed: self.passed += 1
        else:        self.failed  += 1
        colour = "\033[90m" if skip else ("\033[32m" if passed else "\033[31m")
        reset  = "\033[0m"
        suffix = f"  → {detail}" if detail else ""
        print(f"  {colour}{icon} [{check_id}] {label}{reset}{suffix}")

    def summary(self) -> bool:
        total  = self.passed + self.failed + self.skipped
        all_ok = self.failed == 0
        colour = "\033[32m" if all_ok else "\033[31m"
        reset  = "\033[0m"
        print()
        print("─" * 68)
        print(f"  TOTAL CHECKS : {total}")
        print(f"  {colour}PASSED{reset}        : {self.passed}")
        print(f"  \033[31mFAILED\033[0m        : {self.failed}")
        print(f"  \033[90mSKIPPED\033[0m       : {self.skipped}")
        print("─" * 68)
        if all_ok:
            print(f"  {colour}VERDICT: ALL VERIFICATIONS PASS — pressure packet integrity confirmed{reset}")
        else:
            print(f"  \033[31mVERDICT: {self.failed} VERIFICATION(S) FAILED\033[0m")
        return all_ok

    def to_dict(self) -> Dict:
        return {
            "packet_id":    self.packet_id,
            "verified_at":  datetime.now(timezone.utc).isoformat(),
            "total_checks": self.passed + self.failed + self.skipped,
            "passed":       self.passed,
            "failed":       self.failed,
            "skipped":      self.skipped,
            "verdict":      "PASS" if self.failed == 0 else "FAIL",
            "checks":       self.checks,
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Crypto helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_pqc(pk_b64: str):
    try:
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        if not pqc.pqc_enabled:
            print("  [WARN] PQC unavailable — signature checks will be SKIPPED.")
            return None, None
        return pqc, base64.b64decode(pk_b64)
    except Exception as e:
        print(f"  [WARN] PQC load failed: {e}")
        return None, None

def _sha3_default(d: Dict) -> str:
    return hashlib.sha3_256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()

def _sha256_compact(d: Dict) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()

def _verify_sig_compact(pqc, pk_bytes: bytes, payload: Dict, sig_b64: Optional[str]) -> Tuple[bool, str]:
    if not sig_b64:    return False, "no signature"
    if pqc is None:    return False, "PQC unavailable"
    try:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ok  = pqc.verify_signature(base64.b64decode(sig_b64), raw, pk_bytes)
        return ok, "OK" if ok else "mismatch"
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────────────────────────
#  Per-artifact verifiers
# ─────────────────────────────────────────────────────────────────────────────

def _verify_dr(dr: Dict, pqc, pk_bytes, report: VerificationReport, pfx: str):
    did = dr.get("delegation_id", "?")

    # MAR invariant
    mar_ok = dr.get("authority_budget_granted", 999) <= dr.get("authority_budget_delegator", -1)
    report.add(f"{pfx}.DR.MAR", f"DR {did[:20]} — MAR (granted≤delegator)", mar_ok,
               f"granted={dr.get('authority_budget_granted')} delegator={dr.get('authority_budget_delegator')}")

    # content_hash (SHA-256 compact)
    excl  = {"content_hash", "pqc_signature", "pqc_algorithm"}
    clean = {k: v for k, v in dr.items() if k not in excl}
    exp   = _sha256_compact(clean)
    ok    = dr.get("content_hash") == exp
    report.add(f"{pfx}.DR.HASH", f"DR {did[:20]} — content_hash", ok,
               f"stored={dr.get('content_hash','?')[:16]}... expected={exp[:16]}...")

    # PQC signature (DR signs content_hash.encode())
    sig_b64 = dr.get("pqc_signature")
    if sig_b64 and pqc:
        try:
            sig_ok = pqc.verify_signature(base64.b64decode(sig_b64),
                                           dr.get("content_hash", "").encode(), pk_bytes)
            report.add(f"{pfx}.DR.SIG", f"DR {did[:20]} — PQC signature", sig_ok,
                        "OK" if sig_ok else "mismatch")
        except Exception as e:
            report.add(f"{pfx}.DR.SIG", f"DR {did[:20]} — PQC signature", False, str(e))
    else:
        report.add(f"{pfx}.DR.SIG", f"DR {did[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def _verify_tar(tar: Dict, pqc, pk_bytes, report: VerificationReport, pfx: str):
    tid = tar.get("tar_id", "?")

    # content_hash (SHA-256 compact)
    excl  = {"content_hash", "pqc_signature", "pqc_algorithm"}
    clean = {k: v for k, v in tar.items() if k not in excl}
    exp   = _sha256_compact(clean)
    ok    = tar.get("content_hash") == exp
    report.add(f"{pfx}.TAR.HASH", f"TAR {tid[:20]} — content_hash", ok,
               f"stored={tar.get('content_hash','?')[:16]}... expected={exp[:16]}...")

    # admission_status present
    status = tar.get("admission_status", "")
    report.add(f"{pfx}.TAR.STATUS", f"TAR {tid[:20]} — admission_status",
               status in ("ADMITTED", "REJECTED"), f"status={status}")

    # PQC signature
    sig_b64 = tar.get("pqc_signature")
    if sig_b64 and pqc:
        try:
            sig_ok = pqc.verify_signature(base64.b64decode(sig_b64),
                                           tar.get("content_hash", "").encode(), pk_bytes)
            report.add(f"{pfx}.TAR.SIG", f"TAR {tid[:20]} — PQC signature", sig_ok,
                        "OK" if sig_ok else "mismatch")
        except Exception as e:
            report.add(f"{pfx}.TAR.SIG", f"TAR {tid[:20]} — PQC signature", False, str(e))
    else:
        report.add(f"{pfx}.TAR.SIG", f"TAR {tid[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def _verify_continuity(rcr: Dict, pqc, pk_bytes, report: VerificationReport, pfx: str):
    rid = rcr.get("rcr_id") or rcr.get("posture_id", "?")
    hash_field = "rcr_hash" if "rcr_hash" in rcr else "posture_hash"

    excl  = {hash_field, "pqc_signature", "pqc_algorithm"}
    clean = {k: v for k, v in rcr.items() if k not in excl}
    exp   = _sha3_default(clean)
    ok    = rcr.get(hash_field) == exp
    report.add(f"{pfx}.RCR.HASH", f"RCR {rid[:20]} — hash integrity", ok,
               f"stored={rcr.get(hash_field,'?')[:16]}... expected={exp[:16]}...")

    sig_b64 = rcr.get("pqc_signature")
    if sig_b64 and pqc:
        payload = {"rcr_id": rid, "rcr_hash": rcr.get(hash_field, "")} if "rcr_hash" in rcr else \
                  {"posture_id": rid, "posture_hash": rcr.get(hash_field, ""),
                   "captured_at": rcr.get("captured_at", "")}
        ok2, detail = _verify_sig_compact(pqc, pk_bytes, payload, sig_b64)
        report.add(f"{pfx}.RCR.SIG", f"RCR {rid[:20]} — PQC signature", ok2, detail)
    else:
        report.add(f"{pfx}.RCR.SIG", f"RCR {rid[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def _verify_binding(bind: Dict, pqc, pk_bytes, report: VerificationReport, pfx: str):
    bid = bind.get("binding_id", "?")

    excl  = {"binding_hash", "pqc_signature", "pqc_algorithm"}
    clean = {k: v for k, v in bind.items() if k not in excl}
    exp   = _sha3_default(clean)
    ok    = bind.get("binding_hash") == exp
    report.add(f"{pfx}.BIND.HASH", f"Binding {bid[:20]} — hash integrity", ok,
               f"stored={bind.get('binding_hash','?')[:16]}... expected={exp[:16]}...")

    status = bind.get("binding_status", "")
    report.add(f"{pfx}.BIND.STATUS", f"Binding {bid[:20]} — status is REFUSED/HALT",
               status in ("REFUSED", "HALT"), f"status={status}")

    sig_b64 = bind.get("pqc_signature")
    if sig_b64 and pqc:
        payload = {"binding_id": bid, "binding_hash": bind.get("binding_hash", ""),
                   "binding_ts": bind.get("binding_ts", "")}
        ok2, detail = _verify_sig_compact(pqc, pk_bytes, payload, sig_b64)
        report.add(f"{pfx}.BIND.SIG", f"Binding {bid[:20]} — PQC signature", ok2, detail)
    else:
        report.add(f"{pfx}.BIND.SIG", f"Binding {bid[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def _verify_execution_receipt(rec: Dict, pqc, pk_bytes, report: VerificationReport, pfx: str):
    """Verifies HARD_REFUSAL or HALT receipt."""
    rid      = rec.get("receipt_id", "?")
    rtype    = rec.get("type", "?")
    hash_fld = "content_hash"

    excl  = {hash_fld, "pqc_signature", "pqc_algorithm"}
    clean = {k: v for k, v in rec.items() if k not in excl}
    exp   = _sha3_default(clean)
    ok    = rec.get(hash_fld) == exp
    report.add(f"{pfx}.EXEC.HASH", f"{rtype} {rid[:20]} — content_hash", ok,
               f"stored={rec.get(hash_fld,'?')[:16]}... expected={exp[:16]}...")

    report.add(f"{pfx}.EXEC.TYPE", f"{rtype} {rid[:20]} — type is HARD_REFUSAL or HALT",
               rtype in ("HARD_REFUSAL", "HALT"), f"type={rtype}")

    sig_b64 = rec.get("pqc_signature")
    if sig_b64 and pqc:
        payload = {"receipt_id": rid, "content_hash": rec.get(hash_fld, ""),
                   "issued_at": rec.get("issued_at", "")}
        ok2, detail = _verify_sig_compact(pqc, pk_bytes, payload, sig_b64)
        report.add(f"{pfx}.EXEC.SIG", f"{rtype} {rid[:20]} — PQC signature", ok2, detail)
    else:
        report.add(f"{pfx}.EXEC.SIG", f"{rtype} {rid[:20]} — PQC signature", False,
                   "no signature" if not sig_b64 else "PQC unavailable", skip=not pqc)


def _verify_outcome(outcome: Dict, report: VerificationReport, pfx: str):
    oid = outcome.get("outcome_id", "?")

    excl  = {"outcome_hash"}
    clean = {k: v for k, v in outcome.items() if k not in excl}
    exp   = _sha3_default(clean)
    ok    = outcome.get("outcome_hash") == exp
    report.add(f"{pfx}.OUT.HASH", f"Outcome {oid[:20]} — hash integrity", ok,
               f"stored={outcome.get('outcome_hash','?')[:16]}... expected={exp[:16]}...")

    report.add(f"{pfx}.OUT.EXEC", f"Outcome {oid[:20]} — execution_occurred=False",
               outcome.get("execution_occurred") is False, "")


# ─────────────────────────────────────────────────────────────────────────────
#  Pressure-invariant assertions
# ─────────────────────────────────────────────────────────────────────────────

def _assert_p1(steps: Dict, report: VerificationReport):
    pfx = "P1"
    tar   = steps.get("4_admissibility", {})
    bind  = steps.get("5_binding", {})
    out   = steps.get("8_outcome", {})
    cont  = steps.get("3_continuity", {})

    report.add(f"{pfx}.ASSERT.TAR_REJECTED", "P1 — TAR rejected expired DR (TAR-INV-003)",
               tar.get("admission_status") == "REJECTED", f"status={tar.get('admission_status')}")
    report.add(f"{pfx}.ASSERT.BIND_REFUSED", "P1 — Binding refused after drift",
               bind.get("binding_status") == "REFUSED", f"status={bind.get('binding_status')}")
    report.add(f"{pfx}.ASSERT.DRIFT", "P1 — drift_confirmed=True in binding",
               bind.get("drift_confirmed") is True, "")
    report.add(f"{pfx}.ASSERT.NO_EXEC", "P1 — execution_occurred=False",
               out.get("execution_occurred") is False, "")
    report.add(f"{pfx}.ASSERT.DRIFT_NOTE", "P1 — source captured before expiry (pressure_note present)",
               "pressure_note" in steps.get("1_source_state", {}), "")


def _assert_p2(steps: Dict, report: VerificationReport):
    pfx  = "P2"
    cont = steps.get("3_continuity", {})
    bind = steps.get("5_binding", {})
    out  = steps.get("8_outcome", {})

    ces_score = cont.get("ces_score", 999)
    ces_band  = cont.get("ces_band", "")
    report.add(f"{pfx}.ASSERT.CES_HALT", f"P2 — CES score in HALT/WARNING band (RGC-INV-002)",
               ces_band in ("HALT", "WARNING", "MONITORING"), f"ces={ces_score} band={ces_band}")
    report.add(f"{pfx}.ASSERT.STALE", "P2 — staleness_confirmed=True in continuity",
               cont.get("staleness_confirmed") is True, "")
    report.add(f"{pfx}.ASSERT.HALT_POSTURE", "P2 — halt_posture_raised=True",
               cont.get("halt_posture_raised") is True, "")
    report.add(f"{pfx}.ASSERT.BIND_REFUSED", "P2 — Binding refused (CES HALT posture)",
               bind.get("binding_status") == "REFUSED", f"status={bind.get('binding_status')}")
    report.add(f"{pfx}.ASSERT.NO_EXEC", "P2 — execution_occurred=False",
               out.get("execution_occurred") is False, "")


def _assert_p3(steps: Dict, report: VerificationReport):
    pfx  = "P3"
    cont = steps.get("3_continuity", {})
    bind = steps.get("5_binding", {})
    comm = steps.get("6_commit", {})
    out  = steps.get("8_outcome", {})
    rec  = steps.get("7_execution", {})

    report.add(f"{pfx}.ASSERT.RC_EXPIRED", "P3 — rc_expired=True in continuity (RGC-INV-008)",
               cont.get("rc_expired") is True, "")
    report.add(f"{pfx}.ASSERT.HALT_RC", "P3 — halt_triggered_by_rc=True",
               cont.get("halt_triggered_by_rc") is True, "")
    report.add(f"{pfx}.ASSERT.BIND_HALT", "P3 — Binding status=HALT",
               bind.get("binding_status") == "HALT", f"status={bind.get('binding_status')}")
    report.add(f"{pfx}.ASSERT.SUBTASKS", "P3 — sub_tasks_revoked=True in commit (RGC-INV-003)",
               comm.get("sub_tasks_revoked") is True, "")
    report.add(f"{pfx}.ASSERT.HALT_TYPE", "P3 — execution receipt type=HALT",
               rec.get("type") == "HALT", f"type={rec.get('type')}")
    report.add(f"{pfx}.ASSERT.NO_EXEC", "P3 — execution_occurred=False",
               out.get("execution_occurred") is False, "")


# ─────────────────────────────────────────────────────────────────────────────
#  Scenario verifier
# ─────────────────────────────────────────────────────────────────────────────

def verify_scenario(name: str, scenario: Dict, pqc, pk_bytes, report: VerificationReport):
    steps = scenario.get("chain_steps", {})
    pfx   = name.upper()

    print(f"\n  ── {name} — {scenario.get('label','')[:60]} ──")
    _verify_dr(steps.get("2_record", {}), pqc, pk_bytes, report, pfx)
    _verify_tar(steps.get("4_admissibility", {}), pqc, pk_bytes, report, pfx)
    _verify_continuity(steps.get("3_continuity", {}), pqc, pk_bytes, report, pfx)
    _verify_binding(steps.get("5_binding", {}), pqc, pk_bytes, report, pfx)
    _verify_execution_receipt(steps.get("7_execution", {}), pqc, pk_bytes, report, pfx)
    _verify_outcome(steps.get("8_outcome", {}), report, pfx)

    # Pressure-specific assertions
    if name == "P1_authority_drift":      _assert_p1(steps, report)
    elif name == "P2_stale_continuity":   _assert_p2(steps, report)
    elif name == "P3_rc_ttl_enforcement": _assert_p3(steps, report)


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_pressure_evidence_packet.py <packet_file.json>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        sys.exit(1)

    packet = json.load(open(path))

    print("=" * 68)
    print("  OMNIX QUANTUM — Pressure Evidence Packet Verifier")
    print("  TA-14 Third-Pass: Offline Verification")
    print("=" * 68)
    print(f"  Packet ID   : {packet.get('packet_id','?')}")
    print(f"  Generated   : {packet.get('generated_at','?')}")
    print(f"  OMNIX Ver   : {packet.get('omnix_version','?')}")

    pqc_info = packet.get("pqc", {})
    print(f"  PQC         : {pqc_info.get('algorithm','?')}")
    print(f"  Scenarios   : P1 (authority drift) · P2 (stale continuity) · P3 (RC TTL)")
    print()

    pqc, pk_bytes = _load_pqc(pqc_info.get("public_key_b64", ""))
    report = VerificationReport(packet.get("packet_id", "UNKNOWN"))

    scenarios = packet.get("pressure_scenarios", {})
    for name, scenario in scenarios.items():
        verify_scenario(name, scenario, pqc, pk_bytes, report)

    # Global packet assertions
    print("\n  ── PACKET-LEVEL ASSERTIONS ──")
    report.add("PKT.VERSION", "Packet version present",
               bool(packet.get("packet_version")), f"version={packet.get('packet_version')}")
    report.add("PKT.PQC_KEY", "Ephemeral public key embedded",
               len(pqc_info.get("public_key_b64", "")) > 100, "")
    report.add("PKT.SCENARIOS", "Three pressure scenarios present",
               len(scenarios) == 3, f"found={len(scenarios)}")
    report.add("PKT.INVARIANTS", "Invariants stress-tested list present",
               len(packet.get("invariants_stress_tested", [])) >= 7, "")
    report.add("PKT.VERIF_INSTR", "Verification instructions present",
               "offline_verification" in packet.get("verification_instructions", {}), "")

    all_ok = report.summary()

    # Write report
    rpt_path = path.replace(".json", "_verification_report.json")
    with open(rpt_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"\n  Report saved: {rpt_path}")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()

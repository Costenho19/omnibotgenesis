#!/usr/bin/env python3
"""Demo check — 3 casos + verify firma."""
import json, subprocess, sys

KEY  = "OMNIX-DEMO-INVESTOR-TEST-2026042400001"
BASE = "http://localhost:8080"

SIGNALS_MED = {
    "probability_score": 72, "confidence_score": 68, "risk_exposure": 45,
    "signal_coherence": 65, "trend_persistence": 60, "stress_resilience": 55,
    "logic_consistency": 70,
}
SIGNALS_HI = {
    "probability_score": 85, "confidence_score": 80, "risk_exposure": 20,
    "signal_coherence": 82, "trend_persistence": 75, "stress_resilience": 72,
    "logic_consistency": 88,
}


def post(path, body):
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", BASE + path,
         "-H", "Content-Type: application/json",
         "-H", f"X-API-Key: {KEY}",
         "-d", json.dumps(body)],
        capture_output=True, text=True, timeout=20,
    )
    return json.loads(r.stdout)


def get(path):
    r = subprocess.run(
        ["curl", "-s", BASE + path, "-H", f"X-API-Key: {KEY}"],
        capture_output=True, text=True, timeout=20,
    )
    return json.loads(r.stdout)


def layer0_source(d):
    vc  = d.get("veto_chain") or []
    v   = vc[0] if vc else {}
    cid = v.get("constraint_id", "")
    cp  = v.get("checkpoint_name", "")
    # Real SAE constraint IDs use structured codes: ES-, JO-, JA-, SN-
    # Inline fallback produces: SHARIA_VIOLATION or JURISDICTION_BLOCK
    if any(cid.startswith(p) for p in ("ES-", "JO-", "JA-", "SN-")):
        return f"REAL SAE (omnix_core) — checkpoint_name='{cp}'"
    elif cid:
        return f"INLINE FALLBACK — cid={cid}"
    return "n/a (ADMITTED — Layer 0 passed)"


CASES = [
    {
        "label": "CASO 1 — SHARIA + LEVERAGED",
        "expected": "BLOCKED",
        "body": {
            "signals": SIGNALS_MED,
            "asset": "BTC/USD",
            "domain": "trading",
            "compliance_config": {
                "ethical_frameworks": ["SHARIA"],
                "action": "LEVERAGED",
            },
        },
    },
    {
        "label": "CASO 2 — UAE + LEVERAGED",
        "expected": "BLOCKED",
        "body": {
            "signals": SIGNALS_MED,
            "asset": "BTC/USD",
            "domain": "trading",
            "compliance_config": {
                "jurisdiction": "UAE",
                "action": "LEVERAGED",
                "jurisdiction_enabled": True,
            },
        },
    },
    {
        "label": "CASO 3 — BTC / GLOBAL / SPOT",
        "expected": "APPROVED",
        "body": {
            "signals": SIGNALS_HI,
            "asset": "BTC/USD",
            "domain": "trading",
            "compliance_config": {"jurisdiction": "GLOBAL"},
        },
    },
]

print()
all_ok     = True
receipt_id = None
algo       = None

for case in CASES:
    d   = post("/api/governance/evaluate", case["body"])
    dec = d.get("decision", "ERROR")
    ok  = dec == case["expected"]
    all_ok = all_ok and ok
    mark = "✅" if ok else "❌"

    vc  = d.get("veto_chain") or []
    v   = vc[0] if vc else {}

    print("━" * 56)
    print(f"  {mark}  {case['label']}")
    print("━" * 56)
    print(f"  decision        : {dec}  (expected: {case['expected']})")
    print(f"  Layer 0 source  : {layer0_source(d)}")
    print(f"  constraint_id   : {v.get('constraint_id', '-')}")
    print(f"  constraint_class: {v.get('constraint_class', '-')}")
    if dec == "APPROVED":
        receipt_id = d.get("receipt_id")
        algo       = d.get("signature_algorithm")
        print(f"  receipt_id      : {receipt_id}")
        print(f"  sig_algorithm   : {algo}")
        print(f"  pqc_sig_len     : {len(d.get('pqc_signature',''))} chars")
    err = d.get("error")
    if err:
        print(f"  ERROR           : {err}")
    print()

print("━" * 56)
print("  🔐  VERIFICACIÓN DE FIRMA")
print("━" * 56)
if receipt_id:
    vr = get(f"/api/verify/{receipt_id}")
    status     = vr.get("status", "?")
    hash_valid = vr.get("hash_valid")
    sig_valid  = vr.get("signature_valid")
    chain      = vr.get("chain_valid")
    src        = vr.get("source", "-")
    # status = "VALID" when hash_valid is not False, sig_valid is not False
    # null means "could not verify" — acceptable in ephemeral-key dev mode
    verify_ok  = (status == "VALID")
    print(f"  receipt_id    : {receipt_id}")
    print(f"  status        : {status}  {'✅' if verify_ok else '❌'}")
    print(f"  source        : {src}")
    print(f"  hash_valid    : {hash_valid}")
    print(f"  sig_valid     : {sig_valid}")
    print(f"  chain_valid   : {chain}")
    print(f"  algorithm     : {vr.get('decision_trace', {}).get('engine_version', algo)}")
    all_ok = all_ok and verify_ok
else:
    print("  No receipt_id — CASO 3 falló")
    all_ok = False

print()
print("━" * 56)
print(f"  RESULTADO FINAL : {'ALL PASS ✅' if all_ok else 'FALLO ❌'}")
print("━" * 56)
print()
sys.exit(0 if all_ok else 1)

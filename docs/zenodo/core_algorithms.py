"""
OMNIX Core Algorithm Reference Implementation
==============================================

Reference implementations of key OMNIX Decision Governance algorithms,
provided for academic reproducibility alongside the Zenodo publication:

    "OMNIX: Post-Quantum Decision Governance Infrastructure
     for Automated Financial Systems"
    Harold Nunes, OMNIX Quantum, March 2026
    DOI: 10.5281/zenodo.XXXXXXX

These implementations are simplified for clarity and readability.
They do not constitute the full production system.

License: Creative Commons Attribution 4.0 International (CC BY 4.0)
"""

import hashlib
import json
import math
import random
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# 1. Rolling SHA-256 Merkle Chain (ADR-044)
# ─────────────────────────────────────────────────────────────────────────────

class TransparencyChain:
    """
    Append-only cryptographic ledger for governance receipts.

    Construction:
        new_root = SHA256(prev_root || SHA256(receipt_payload))

    This ensures any modification to any historical receipt invalidates
    all subsequent chain roots — detectable by any party holding a
    known-good checkpoint.
    """

    def __init__(self):
        # Genesis root: SHA256 of a well-known constant
        self._root = hashlib.sha256(b"OMNIX-GENESIS-TRANSPARENCY-CHAIN-v1").hexdigest()
        self._sequence = 0

    @property
    def root(self) -> str:
        return self._root

    def append(self, receipt_payload: dict) -> dict:
        """
        Append a governance receipt to the chain.

        Args:
            receipt_payload: Dict with receipt fields (receipt_id, timestamp,
                             decision, asset, policy_version, ...)

        Returns:
            Updated chain metadata including content_hash and prev_hash.
        """
        prev_root = self._root
        self._sequence += 1

        # Canonical serialization (sorted keys, no whitespace)
        canonical = json.dumps(receipt_payload, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

        # Rolling Merkle root update
        combined = prev_root.encode('utf-8') + payload_hash.encode('utf-8')
        self._root = hashlib.sha256(combined).hexdigest()

        return {
            'content_hash': payload_hash,
            'prev_hash': prev_root,
            'chain_root': self._root,
            'sequence': self._sequence,
        }

    @staticmethod
    def verify_chain(receipts: list[dict]) -> dict:
        """
        Verify hash chain integrity for a list of receipts (ordered oldest→newest).

        Args:
            receipts: List of receipt dicts, each with 'content_hash' and 'prev_hash'.

        Returns:
            {'valid': bool, 'links_verified': int, 'breaks': list[int]}
        """
        links_verified = 0
        breaks = []

        for i in range(len(receipts) - 1):
            current = receipts[i]
            nxt = receipts[i + 1]
            if current['content_hash'] == nxt['prev_hash']:
                links_verified += 1
            else:
                breaks.append(i + 1)

        return {
            'valid': len(breaks) == 0,
            'links_verified': links_verified,
            'breaks': breaks,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Monte Carlo VETO Engine (CP-1)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MonteCarloResult:
    expected_return: float
    win_rate: float
    max_drawdown: float
    decision: str           # "PASS", "VETO", "SIZE_REDUCE"
    size_multiplier: float  # 1.0 = full size; 0.5 = half size
    iterations: int


def monte_carlo_veto(
    signal_vector: dict,
    n_iterations: int = 1000,
    min_win_rate: float = 0.50,
    max_drawdown_threshold: float = 0.15,
) -> MonteCarloResult:
    """
    Monte Carlo VETO Engine — Checkpoint CP-1.

    Simulates N outcome scenarios conditioned on the incoming signal vector
    and applies governance criteria:

    - VETO:         Expected return < 0, OR max drawdown > threshold
    - SIZE_REDUCE:  Win rate < min_win_rate (position size reduced proportionally)
    - PASS:         All criteria satisfied

    Args:
        signal_vector:   Normalized 8-signal governance vector (all in [0, 1]).
        n_iterations:    Number of Monte Carlo simulations.
        min_win_rate:    Minimum win rate for full position sizing.
        max_drawdown_threshold: Maximum acceptable simulated drawdown.

    Returns:
        MonteCarloResult with decision and size_multiplier.
    """
    momentum = signal_vector.get('market_momentum', 0.5)
    volatility = signal_vector.get('volatility_risk', 0.5)
    confidence = signal_vector.get('confidence_level', 0.5)

    # Simulate outcome distribution
    mu = (momentum - 0.5) * 2 * confidence        # centered expected return
    sigma = volatility * 0.3 + 0.05               # volatility-scaled std dev

    outcomes = [random.gauss(mu, sigma) for _ in range(n_iterations)]

    expected_return = sum(outcomes) / n_iterations
    wins = sum(1 for r in outcomes if r > 0)
    win_rate = wins / n_iterations

    # Max drawdown simulation (running equity curve)
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in outcomes[:200]:  # use first 200 for drawdown path
        equity *= (1 + r * 0.01)
        peak = max(peak, equity)
        dd = (peak - equity) / peak
        max_dd = max(max_dd, dd)

    # Governance decision logic
    if expected_return < 0 or max_dd > max_drawdown_threshold:
        return MonteCarloResult(
            expected_return=expected_return,
            win_rate=win_rate,
            max_drawdown=max_dd,
            decision="VETO",
            size_multiplier=0.0,
            iterations=n_iterations,
        )

    if win_rate < min_win_rate:
        # SIZE_REDUCE: multiplier proportional to win rate shortfall
        size_multiplier = max(0.25, win_rate / min_win_rate)
        return MonteCarloResult(
            expected_return=expected_return,
            win_rate=win_rate,
            max_drawdown=max_dd,
            decision="SIZE_REDUCE",
            size_multiplier=size_multiplier,
            iterations=n_iterations,
        )

    return MonteCarloResult(
        expected_return=expected_return,
        win_rate=win_rate,
        max_drawdown=max_dd,
        decision="PASS",
        size_multiplier=1.0,
        iterations=n_iterations,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Decision Contradiction Index — DCI (ADR-018)
# ─────────────────────────────────────────────────────────────────────────────

def compute_dci(signal_vector: dict) -> float:
    """
    Decision Contradiction Index (DCI) — ADR-018.

    Quantifies internal signal divergence. High DCI (≥ 70) mandates a HOLD
    regardless of individual signal strength, because contradictory signals
    indicate the system cannot form a confident directional commitment.

    DCI = standard deviation of directional signals × 100

    Args:
        signal_vector: Normalized 8-signal governance vector.

    Returns:
        DCI score in [0, 100]. DCI ≥ 70 → HOLD.
    """
    directional_signals = [
        signal_vector.get('market_momentum', 0.5),
        signal_vector.get('sentiment_score', 0.5),
        signal_vector.get('coherence_score', 0.5),
        signal_vector.get('confidence_level', 0.5),
        1.0 - signal_vector.get('volatility_risk', 0.5),  # inverted: high vol = bearish
    ]

    n = len(directional_signals)
    mean = sum(directional_signals) / n
    variance = sum((x - mean) ** 2 for x in directional_signals) / n
    std_dev = math.sqrt(variance)

    # Normalize to [0, 100]; max possible std_dev of [0,1] values is 0.5
    dci = min(100.0, std_dev * 200.0)
    return round(dci, 2)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Hybrid KEM Reference (ADR-042)
# ─────────────────────────────────────────────────────────────────────────────
#
# NOTE: The full hybrid KEM requires the `kyber-py` and `cryptography` packages.
# This is a structural reference showing the composition logic.
# Production implementation: omnix_core/security/hybrid_crypto.py
#
# from kyber_py.kyber import Kyber768
# from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
# from cryptography.hazmat.primitives.kdf.hkdf import HKDF
# from cryptography.hazmat.primitives import hashes

HYBRID_KEM_LABEL = b"OMNIX-ADR042-HybridKEM-v1"

def hybrid_kem_derive_key_reference(
    secret_kyber: bytes,   # shared secret from Kyber768.decapsulate()
    secret_x25519: bytes,  # shared secret from X25519 exchange
    length: int = 32,
) -> bytes:
    """
    Structural reference for OMNIX hybrid KEM key derivation (ADR-042).

    The composite input is the concatenation of both shared secrets.
    HKDF-SHA256 with a domain-separation label derives the final shared key.

    Full production implementation uses:
        cryptography.hazmat.primitives.kdf.hkdf.HKDF

    Args:
        secret_kyber:  32-byte shared secret from Kyber-768 encapsulation.
        secret_x25519: 32-byte shared secret from X25519 key exchange.
        length:        Output key length in bytes (default: 32).

    Returns:
        Derived shared secret of `length` bytes.
    """
    composite = secret_kyber + secret_x25519
    # HKDF-SHA256(ikm=composite, info=HYBRID_KEM_LABEL, length=length)
    # Reference: https://tools.ietf.org/html/rfc5869
    #
    # In production:
    #   hkdf = HKDF(algorithm=hashes.SHA256(), length=length,
    #               salt=None, info=HYBRID_KEM_LABEL)
    #   return hkdf.derive(composite)
    #
    # Structural simulation using HMAC-SHA256 as HKDF approximation:
    import hmac
    prk = hmac.new(b'\x00' * 32, composite, 'sha256').digest()
    okm = hmac.new(prk, HYBRID_KEM_LABEL + b'\x01', 'sha256').digest()
    return okm[:length]


# ─────────────────────────────────────────────────────────────────────────────
# 5. 8-Checkpoint Pipeline Orchestrator (simplified)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CheckpointResult:
    checkpoint: str
    passed: bool
    decision: str
    metrics: dict = field(default_factory=dict)


def governance_pipeline(signal_vector: dict) -> dict:
    """
    Simplified reference implementation of the OMNIX 8-checkpoint governance pipeline.

    In production, each checkpoint is a separate module with full exception handling,
    timeout enforcement, and PostgreSQL-persisted state. This reference implementation
    shows the pipeline logic and fail-closed behavior.

    Args:
        signal_vector: Normalized 8-signal dict (all values in [0, 1]).

    Returns:
        Pipeline result dict with decision, checkpoint trace, and DCI.
    """
    results = []

    # CP-0: Signal Integrity Validation
    violations = sum(1 for v in signal_vector.values() if not (0.0 <= v <= 1.0))
    siv_pass = violations == 0
    results.append(CheckpointResult("SIV(CP-0)", siv_pass, "PASS" if siv_pass else "BLOCKED",
                                    {"violations": violations}))
    if not siv_pass:
        return _build_result("BLOCKED", results, signal_vector)

    # CP-1: Monte Carlo VETO
    mc = monte_carlo_veto(signal_vector)
    mc_pass = mc.decision != "VETO"
    results.append(CheckpointResult("MC(CP-1)", mc_pass, mc.decision,
                                    {"expected_return": round(mc.expected_return, 4),
                                     "win_rate": round(mc.win_rate, 4),
                                     "max_drawdown": round(mc.max_drawdown, 4)}))
    if not mc_pass:
        return _build_result("BLOCKED", results, signal_vector)

    # CP-2: Risk Management System
    drawdown_limit = 0.20
    current_drawdown = signal_vector.get('volatility_risk', 0) * 0.3
    rms_pass = current_drawdown <= drawdown_limit
    results.append(CheckpointResult("RMS(CP-2)", rms_pass, "PASS" if rms_pass else "BLOCKED",
                                    {"drawdown": round(current_drawdown, 4)}))
    if not rms_pass:
        return _build_result("BLOCKED", results, signal_vector)

    # CP-3/4/5: Coherence Engine
    coherence = signal_vector.get('coherence_score', 0.5)
    coherence_pct = coherence * 100
    coherence_pass = coherence_pct >= 30.0   # ADR-007: 30% minimum
    dci = compute_dci(signal_vector)
    coherence_decision = "PASS" if coherence_pass and dci < 70 else "BLOCKED"
    results.append(CheckpointResult("COHERENCE(CP-3/4/5)", coherence_pass and dci < 70,
                                    coherence_decision,
                                    {"coherence_pct": round(coherence_pct, 1), "dci": dci}))
    if coherence_decision == "BLOCKED":
        return _build_result("HOLD" if dci >= 70 else "BLOCKED", results, signal_vector)

    # CP-6: Edge Confirmation Window
    risk_reward = signal_vector.get('risk_reward_ratio', 0.5)
    ecw_pass = risk_reward >= 0.6 and mc.win_rate >= 0.52
    results.append(CheckpointResult("ECW(CP-6)", ecw_pass, "PASS" if ecw_pass else "WAITING",
                                    {"risk_reward": round(risk_reward, 4)}))
    if not ecw_pass:
        return _build_result("HOLD", results, signal_vector)

    # CP-7: Temporal Coherence Validation
    time_horizon = signal_vector.get('time_horizon', 0.5)
    tcv_pass = time_horizon >= 0.4
    results.append(CheckpointResult("TCV(CP-7)", tcv_pass, "PASS" if tcv_pass else "BLOCKED",
                                    {"time_horizon": time_horizon}))
    if not tcv_pass:
        return _build_result("HOLD", results, signal_vector)

    # CP-7b: Forward Trajectory Implication
    liquidity = signal_vector.get('liquidity_score', 0.5)
    fti_pass = liquidity >= 0.5
    results.append(CheckpointResult("FTI(CP-7b)", fti_pass, "PASS" if fti_pass else "NONE",
                                    {"liquidity": liquidity}))
    if not fti_pass:
        return _build_result("HOLD", results, signal_vector)

    # All checkpoints passed
    return _build_result("APPROVED", results, signal_vector,
                         size_multiplier=mc.size_multiplier)


def _build_result(decision: str, results: list, signal_vector: dict,
                  size_multiplier: float = 1.0) -> dict:
    return {
        "decision": decision,
        "size_multiplier": size_multiplier,
        "dci": compute_dci(signal_vector),
        "checkpoints_run": len(results),
        "checkpoint_trace": [
            {"checkpoint": r.checkpoint, "passed": r.passed,
             "decision": r.decision, "metrics": r.metrics}
            for r in results
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Example usage
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    # Example signal vector
    test_signal = {
        "market_momentum":  0.62,
        "volatility_risk":  0.35,
        "liquidity_score":  0.78,
        "sentiment_score":  0.55,
        "coherence_score":  0.68,
        "risk_reward_ratio": 0.72,
        "time_horizon":     0.60,
        "confidence_level": 0.65,
    }

    print("=== OMNIX 8-Checkpoint Governance Pipeline ===\n")
    result = governance_pipeline(test_signal)
    print(json.dumps(result, indent=2))

    print("\n=== Hash Chain Verification ===")
    chain = TransparencyChain()
    receipts = []
    for i in range(5):
        payload = {"receipt_id": f"TEST-{i:04d}", "decision": "HOLD", "seq": i}
        meta = chain.append(payload)
        receipts.append(meta)
        print(f"Receipt {i}: {meta['content_hash'][:16]}... (root: {meta['chain_root'][:16]}...)")

    verify = TransparencyChain.verify_chain(receipts)
    print(f"\nChain integrity: {'VALID' if verify['valid'] else 'BROKEN'}")
    print(f"Links verified: {verify['links_verified']}")

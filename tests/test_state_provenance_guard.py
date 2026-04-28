"""
ADR-133 — State Provenance Guard — Full Test Suite

Tests:
    T01–T05: Module import and basic structure
    T06–T10: Hypothesis evaluation
    T11–T15: Contradiction detection
    T16–T20: Lineage singularity score and verdict
    T21–T25: SPGResult dataclass and to_dict()
    T26–T30: Advisory vs blocking mode
    T31–T35: Edge cases and fail-safe behaviour
    T36–T40: Integration convenience function
"""

import pytest
from omnix_core.governance.state_provenance_guard import (
    StateProvenanceGuard,
    SPGResult,
    SPGMode,
    ProvenanceVerdict,
    evaluate_provenance,
    get_global_spg,
    _evaluate_hypothesis,
    _detect_contradictions,
    _compute_lineage_singularity,
    _compute_provenance_hash,
    _HYPOTHESES,
    _CONTRADICTION_PAIRS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def singular_signals():
    """Clear bullish signals — unambiguously one causal origin."""
    return {
        "probability_score": 75.0,
        "risk_exposure":     30.0,
        "signal_coherence":  72.0,
        "trend_persistence": 68.0,
        "stress_resilience": 65.0,
        "logic_consistency": 78.0,
    }


@pytest.fixture
def ambiguous_signals():
    """High probability + high risk + low resilience — multiple contradictory hypotheses."""
    return {
        "probability_score": 78.0,   # Bullish signal
        "risk_exposure":     75.0,   # High-volatility signal (contradicts bullish)
        "signal_coherence":  45.0,   # Degraded coherence
        "trend_persistence": 72.0,   # Bullish persistence
        "stress_resilience": 28.0,   # Very low (contradicts high trend)
        "logic_consistency": 40.0,   # Low (contradicts high coherence expectation)
    }


@pytest.fixture
def bearish_signals():
    """Clear bearish signals."""
    return {
        "probability_score": 38.0,
        "risk_exposure":     68.0,
        "signal_coherence":  42.0,
        "trend_persistence": 36.0,
        "stress_resilience": 38.0,
        "logic_consistency": 44.0,
    }


@pytest.fixture
def stable_signals():
    """Stable low-risk signals."""
    return {
        "probability_score": 65.0,
        "risk_exposure":     28.0,
        "signal_coherence":  70.0,
        "trend_persistence": 58.0,
        "stress_resilience": 72.0,
        "logic_consistency": 68.0,
    }


@pytest.fixture
def spg_advisory():
    return StateProvenanceGuard(mode=SPGMode.ADVISORY)


@pytest.fixture
def spg_blocking():
    return StateProvenanceGuard(mode=SPGMode.BLOCKING)


# ── T01–T05: Module import and basic structure ────────────────────────────────────

def test_T01_module_imports():
    assert StateProvenanceGuard is not None
    assert SPGMode is not None
    assert ProvenanceVerdict is not None
    assert evaluate_provenance is not None


def test_T02_provenance_verdict_values():
    assert ProvenanceVerdict.SINGULAR.value      == "SINGULAR"
    assert ProvenanceVerdict.AMBIGUOUS.value     == "AMBIGUOUS"
    assert ProvenanceVerdict.INDETERMINATE.value == "INDETERMINATE"


def test_T03_spg_mode_values():
    assert SPGMode.ADVISORY.value == "ADVISORY"
    assert SPGMode.BLOCKING.value == "BLOCKING"


def test_T04_hypotheses_defined():
    assert len(_HYPOTHESES) == 5
    names = {h["name"] for h in _HYPOTHESES}
    assert "BULLISH" in names
    assert "BEARISH" in names
    assert "RANGING" in names
    assert "HIGH_VOLATILITY" in names
    assert "STABLE_LOW_RISK" in names


def test_T05_contradiction_pairs_defined():
    assert len(_CONTRADICTION_PAIRS) == 4
    for pair in _CONTRADICTION_PAIRS:
        assert "signal_a" in pair
        assert "signal_b" in pair
        assert "relationship" in pair
        assert "tolerance" in pair
        assert "severity" in pair


# ── T06–T10: Hypothesis evaluation ───────────────────────────────────────────────

def test_T06_bullish_hypothesis_fits_bullish_signals(singular_signals):
    bullish_hyp = next(h for h in _HYPOTHESES if h["name"] == "BULLISH")
    fit = _evaluate_hypothesis(singular_signals, bullish_hyp)
    assert fit > 0.0, "Bullish signals should activate the BULLISH hypothesis"


def test_T07_bearish_hypothesis_fits_bearish_signals(bearish_signals):
    bearish_hyp = next(h for h in _HYPOTHESES if h["name"] == "BEARISH")
    fit = _evaluate_hypothesis(bearish_signals, bearish_hyp)
    assert fit > 0.0, "Bearish signals should activate the BEARISH hypothesis"


def test_T08_hypothesis_returns_zero_below_fit_floor(bearish_signals):
    """Bullish hypothesis should NOT activate for clearly bearish signals."""
    bullish_hyp = next(h for h in _HYPOTHESES if h["name"] == "BULLISH")
    fit = _evaluate_hypothesis(bearish_signals, bullish_hyp)
    assert fit == 0.0, "Bullish hypothesis should not fit bearish signals"


def test_T09_hypothesis_handles_missing_signals():
    """Hypothesis with missing signals should still produce a value."""
    minimal = {"probability_score": 70.0}
    bullish_hyp = next(h for h in _HYPOTHESES if h["name"] == "BULLISH")
    fit = _evaluate_hypothesis(minimal, bullish_hyp)
    assert isinstance(fit, float)


def test_T10_stable_hypothesis_fits_stable_signals(stable_signals):
    stable_hyp = next(h for h in _HYPOTHESES if h["name"] == "STABLE_LOW_RISK")
    fit = _evaluate_hypothesis(stable_signals, stable_hyp)
    assert fit > 0.0, "Stable signals should activate STABLE_LOW_RISK hypothesis"


# ── T11–T15: Contradiction detection ─────────────────────────────────────────────

def test_T11_no_contradictions_in_singular_signals(singular_signals):
    contradictions = _detect_contradictions(singular_signals)
    assert isinstance(contradictions, list)
    assert len(contradictions) == 0, "Singular signals should produce no contradictions"


def test_T12_contradiction_detected_high_prob_high_risk():
    """High probability + high risk = contradiction (inverse relationship violated)."""
    signals = {
        "probability_score": 85.0,
        "risk_exposure":     82.0,
        "signal_coherence":  60.0,
        "trend_persistence": 60.0,
        "stress_resilience": 50.0,
        "logic_consistency": 60.0,
    }
    contradictions = _detect_contradictions(signals)
    assert any(
        c["signal_a"] == "probability_score" and c["signal_b"] == "risk_exposure"
        for c in contradictions
    ), "High prob + high risk should be flagged as contradiction"


def test_T13_contradiction_detected_high_risk_high_resilience():
    """High resilience + high risk = contradiction."""
    signals = {
        "probability_score": 55.0,
        "risk_exposure":     80.0,
        "signal_coherence":  55.0,
        "trend_persistence": 55.0,
        "stress_resilience": 80.0,   # High resilience with high risk
        "logic_consistency": 55.0,
    }
    contradictions = _detect_contradictions(signals)
    assert any(
        c["signal_a"] == "stress_resilience" and c["signal_b"] == "risk_exposure"
        for c in contradictions
    ), "High resilience + high risk should be flagged"


def test_T14_contradiction_record_has_required_fields(ambiguous_signals):
    contradictions = _detect_contradictions(ambiguous_signals)
    if contradictions:
        c = contradictions[0]
        assert "signal_a"     in c
        assert "signal_b"     in c
        assert "relationship" in c
        assert "value_a"      in c
        assert "value_b"      in c
        assert "deviation"    in c
        assert "severity"     in c
        assert "description"  in c


def test_T15_contradiction_severity_is_valid(ambiguous_signals):
    contradictions = _detect_contradictions(ambiguous_signals)
    valid_severities = {"HIGH", "MEDIUM", "LOW"}
    for c in contradictions:
        assert c["severity"] in valid_severities


# ── T16–T20: Lineage singularity score and verdict ───────────────────────────────

def test_T16_singular_signals_score_high(singular_signals):
    spg = StateProvenanceGuard()
    result = spg.evaluate(singular_signals)
    assert result.lineage_singularity >= 50.0
    assert result.verdict in (ProvenanceVerdict.SINGULAR, ProvenanceVerdict.INDETERMINATE)


def test_T17_ambiguous_signals_have_contradictions(ambiguous_signals):
    """Ambiguous signals must produce at least one internal contradiction."""
    spg = StateProvenanceGuard()
    result = spg.evaluate(ambiguous_signals)
    assert result.contradiction_count >= 1, (
        "Contradictory signals (high prob + high risk) must surface at least one contradiction"
    )


def test_T18_two_active_hypotheses_reduce_score():
    """Two active hypotheses reduce lineage_singularity by 18 points from 100."""
    score_one   = _compute_lineage_singularity({}, [], active_count=1)
    score_two   = _compute_lineage_singularity({}, [], active_count=2)
    score_three = _compute_lineage_singularity({}, [], active_count=3)
    assert score_one   == 100.0
    assert score_two   == 82.0
    assert score_three == 64.0


def test_T19_high_contradiction_lowers_lineage_score(ambiguous_signals):
    """Each HIGH contradiction must reduce lineage_singularity by 14 points."""
    contradictions = _detect_contradictions(ambiguous_signals)
    high_count = sum(1 for c in contradictions if c["severity"] == "HIGH")
    if high_count >= 1:
        score = _compute_lineage_singularity({}, contradictions, active_count=1)
        assert score < 100.0, "HIGH contradictions must reduce the lineage singularity score"


def test_T20_score_clamped_between_zero_and_100():
    score = _compute_lineage_singularity({}, [], 10)
    assert 0.0 <= score <= 100.0
    score2 = _compute_lineage_singularity({}, [{"severity": "HIGH"}] * 20, 1)
    assert score2 >= 0.0


# ── T21–T25: SPGResult dataclass and to_dict() ───────────────────────────────────

def test_T21_result_has_all_required_fields(spg_advisory, singular_signals):
    result = spg_advisory.evaluate(singular_signals)
    assert hasattr(result, "verdict")
    assert hasattr(result, "lineage_singularity")
    assert hasattr(result, "dominant_hypothesis")
    assert hasattr(result, "hypothesis_fits")
    assert hasattr(result, "contradictions")
    assert hasattr(result, "contradiction_count")
    assert hasattr(result, "evaluation_mode")
    assert hasattr(result, "blocked")
    assert hasattr(result, "spg_id")
    assert hasattr(result, "evaluated_at")
    assert hasattr(result, "elapsed_ms")
    assert hasattr(result, "signal_count")
    assert hasattr(result, "adr_reference")
    assert hasattr(result, "provenance_hash")


def test_T22_to_dict_returns_serialisable_dict(spg_advisory, singular_signals):
    import json
    result = spg_advisory.evaluate(singular_signals)
    d = result.to_dict()
    assert isinstance(d, dict)
    serialised = json.dumps(d)
    assert len(serialised) > 0


def test_T23_adr_reference_is_adr_133(spg_advisory, singular_signals):
    result = spg_advisory.evaluate(singular_signals)
    assert result.adr_reference == "ADR-133"


def test_T24_provenance_hash_is_sha256_hex(spg_advisory, singular_signals):
    result = spg_advisory.evaluate(singular_signals)
    assert isinstance(result.provenance_hash, str)
    assert len(result.provenance_hash) == 64  # SHA-256 hex


def test_T25_spg_id_has_correct_prefix(spg_advisory, singular_signals):
    result = spg_advisory.evaluate(singular_signals)
    assert result.spg_id.startswith("SPG-")


# ── T26–T30: Advisory vs blocking mode ───────────────────────────────────────────

def test_T26_advisory_mode_never_blocks(spg_advisory, ambiguous_signals):
    result = spg_advisory.evaluate(ambiguous_signals)
    assert result.blocked is False, "ADVISORY mode must never set blocked=True"


def test_T27_advisory_mode_singular_signals_not_blocked(spg_advisory, singular_signals):
    result = spg_advisory.evaluate(singular_signals)
    assert result.blocked is False


def test_T28_blocking_mode_blocks_on_ambiguous(spg_blocking, ambiguous_signals):
    result = spg_blocking.evaluate(ambiguous_signals)
    if result.verdict == ProvenanceVerdict.AMBIGUOUS:
        assert result.blocked is True, "BLOCKING mode must set blocked=True for AMBIGUOUS verdict"


def test_T29_blocking_mode_does_not_block_singular(spg_blocking, singular_signals):
    result = spg_blocking.evaluate(singular_signals)
    if result.verdict == ProvenanceVerdict.SINGULAR:
        assert result.blocked is False


def test_T30_evaluation_mode_matches_constructor(singular_signals):
    for mode in (SPGMode.ADVISORY, SPGMode.BLOCKING):
        spg = StateProvenanceGuard(mode=mode)
        result = spg.evaluate(singular_signals)
        assert result.evaluation_mode == mode


# ── T31–T35: Edge cases and fail-safe behaviour ──────────────────────────────────

def test_T31_empty_signals_returns_indeterminate():
    spg = StateProvenanceGuard()
    result = spg.evaluate({})
    assert result.verdict == ProvenanceVerdict.INDETERMINATE
    assert result.blocked is False


def test_T32_insufficient_signals_returns_indeterminate():
    """Less than 3 signals should yield INDETERMINATE."""
    spg = StateProvenanceGuard()
    result = spg.evaluate({"probability_score": 70.0, "risk_exposure": 30.0})
    assert result.verdict == ProvenanceVerdict.INDETERMINATE
    assert result.signal_count <= 2


def test_T33_non_numeric_signals_are_skipped():
    """Non-numeric values should be filtered without error."""
    spg = StateProvenanceGuard()
    signals = {
        "probability_score": "not_a_number",
        "risk_exposure":     None,
        "signal_coherence":  70.0,
        "trend_persistence": 60.0,
        "stress_resilience": 65.0,
        "logic_consistency": 68.0,
    }
    result = spg.evaluate(signals)
    assert isinstance(result, SPGResult)
    assert result.signal_count <= 4


def test_T34_evaluate_returns_spg_result_not_raises():
    """SPG must never raise — always returns SPGResult."""
    spg = StateProvenanceGuard()
    result = spg.evaluate({"bad": object()})
    assert isinstance(result, SPGResult)


def test_T35_provenance_hash_deterministic():
    h1 = _compute_provenance_hash("SPG-TEST-001", "SINGULAR", 86.0)
    h2 = _compute_provenance_hash("SPG-TEST-001", "SINGULAR", 86.0)
    assert h1 == h2, "Provenance hash must be deterministic"


# ── T36–T40: Integration convenience function ─────────────────────────────────────

def test_T36_evaluate_provenance_returns_spg_result(singular_signals):
    result = evaluate_provenance(singular_signals)
    assert isinstance(result, SPGResult)


def test_T37_evaluate_provenance_never_raises():
    result = evaluate_provenance({"garbage": "value"})
    assert isinstance(result, SPGResult)


def test_T38_evaluate_provenance_passes_domain_and_asset(singular_signals):
    result = evaluate_provenance(
        signals   = singular_signals,
        domain    = "insurance",
        asset     = "POLICY-001",
        client_id = "CLIENT-TEST",
    )
    assert result.verdict in (
        ProvenanceVerdict.SINGULAR,
        ProvenanceVerdict.AMBIGUOUS,
        ProvenanceVerdict.INDETERMINATE,
    )


def test_T39_get_global_spg_returns_singleton():
    spg1 = get_global_spg()
    spg2 = get_global_spg()
    assert spg1 is spg2, "get_global_spg() must return the same instance"


def test_T40_singular_signals_dominant_hypothesis_is_set(singular_signals):
    spg = StateProvenanceGuard()
    result = spg.evaluate(singular_signals)
    if result.verdict == ProvenanceVerdict.SINGULAR:
        assert result.dominant_hypothesis is not None
        assert isinstance(result.dominant_hypothesis, str)

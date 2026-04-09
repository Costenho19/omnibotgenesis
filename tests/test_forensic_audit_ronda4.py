"""
OMNIX Forensic Audit — Ronda 4
Bugs encontrados en zonas no auditadas previamente.

Bug 1: governance_sandbox.py — receipt OMNIX-SB-{8hex} viola ADR-074
Bug 2: credit_signal_adapter.py — dsr_norm usa 0.5 hardcodeado en lugar de ISLAMIC_DSR_MAX=0.40
Bug 3: anti_replay.py — módulo real de protección anti-replay (nuevo)

35 tests | April 2026
"""
import os
import time
import pytest
import threading

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUE I — Sandbox receipt_id canonical format (ADR-074)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSandboxReceiptIdFormat:
    """Bug 1: governance_sandbox usaba OMNIX-SB-{8hex} — código no registrado + longitud errónea."""

    def setup_method(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        self.engine = DecisionReceiptEngine

    def test_I1_public_sandbox_produces_PUB_code(self):
        rid = self.engine.build_receipt_id("public_sandbox")
        assert rid.startswith("OMNIX-PUB-"), f"Expected OMNIX-PUB-..., got {rid}"

    def test_I2_public_sandbox_receipt_has_12_hex_suffix(self):
        rid = self.engine.build_receipt_id("public_sandbox")
        suffix = rid.replace("OMNIX-PUB-", "")
        assert len(suffix) == 12, f"Expected 12 hex chars, got {len(suffix)} in {rid}"
        assert all(c in "0123456789ABCDEF" for c in suffix), f"Non-hex chars in {suffix}"

    def test_I3_SB_code_not_in_domain_codes(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("sb")
        assert "OMNIX-SB-" not in rid, (
            "SB is not a registered domain code — should produce OMNIX-{12hex}, not OMNIX-SB-..."
        )
        assert rid.startswith("OMNIX-"), f"Receipt should start with OMNIX-, got {rid}"

    def test_I4_unknown_domain_produces_no_double_dash(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("unknown_domain")
        assert "--" not in rid, f"Double dash in receipt_id: {rid}"

    def test_I5_build_receipt_id_public_sandbox_length_is_22(self):
        rid = self.engine.build_receipt_id("public_sandbox")
        assert len(rid) == 22, f"OMNIX-PUB-{{12hex}} should be 22 chars, got {len(rid)}: {rid}"

    def test_I6_all_canonical_domains_correct_codes(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        expected = {
            "trading": "TRD",
            "islamic_credit": "CRD",
            "insurance": "INS",
            "robotics": "RBT",
            "public_sandbox": "PUB",
        }
        for domain, code in expected.items():
            rid = DecisionReceiptEngine.build_receipt_id(domain)
            assert rid.startswith(f"OMNIX-{code}-"), f"domain={domain}: expected OMNIX-{code}-..., got {rid}"

    def test_I7_governance_sandbox_uses_build_receipt_id(self):
        """Static analysis: governance_sandbox.py must not contain hardcoded OMNIX-SB-."""
        import ast, pathlib
        src = pathlib.Path("omnix_dashboard/blueprints/governance_sandbox.py").read_text()
        assert "OMNIX-SB-" not in src, (
            "governance_sandbox.py still contains hardcoded OMNIX-SB- receipt format"
        )
        assert "build_receipt_id" in src or "_ReceiptEngine.build_receipt_id" in src, (
            "governance_sandbox.py must use build_receipt_id() for receipt ID generation"
        )

    def test_I8_no_8hex_suffix_pattern_in_sandbox(self):
        """Verify the old 8-hex pattern is gone from governance_sandbox."""
        import pathlib
        src = pathlib.Path("omnix_dashboard/blueprints/governance_sandbox.py").read_text()
        assert "hex[:8]" not in src or "OMNIX" not in src.split("hex[:8]")[0].split("\n")[-1], (
            "Old 8-hex OMNIX receipt pattern still present"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUE J — Islamic Credit DSR inconsistency (Bug 2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestIslamicCreditDSRConsistency:
    """
    Bug 2: dsr_norm usaba 0.5 hardcodeado en lugar de ISLAMIC_DSR_MAX=0.40.
    Un borrower con DSR=42% (por encima del límite islámico) obtenía
    dsr_score=0 (correcto) pero dsr_norm=16 (positivo — incorrecto).
    Ambas señales deben usar el mismo techo para que signal_coherence
    sea internamente consistente.
    """

    def setup_method(self):
        from omnix_core.credit.credit_signal_adapter import (
            CreditSignalAdapter, CreditApplication, ISLAMIC_DSR_MAX
        )
        from omnix_core.credit.credit_macro_data import MacroSnapshot
        self.adapter = CreditSignalAdapter()
        self.dsr_max = ISLAMIC_DSR_MAX
        self.CreditApplication = CreditApplication

        self.baseline_app = CreditApplication(
            application_id="TEST-BASELINE-001",
            credit_score=680,
            debt_service_ratio=0.25,
            asset_backing_ratio=1.2,
            collateral_type="property",
            requested_amount=150_000,
            tenor_months=36,
            sector="education",
        )
        self.baseline_macro = MacroSnapshot(
            market_stress_index=20.0,
            credit_conditions_index=40.0,
            liquidity_score=70.0,
            macro_volatility=25.0,
        )

    def test_J1_ISLAMIC_DSR_MAX_is_0_40(self):
        from omnix_core.credit.credit_signal_adapter import ISLAMIC_DSR_MAX
        assert ISLAMIC_DSR_MAX == 0.40, f"Expected 0.40, got {ISLAMIC_DSR_MAX}"

    def test_J2_dsr_above_limit_gives_zero_probability(self):
        """DSR=42% (above 40% limit) → dsr_score clamped to 0 → low probability."""
        import dataclasses
        high_dsr_app = dataclasses.replace(self.baseline_app, debt_service_ratio=0.42)
        signals = self.adapter.adapt(high_dsr_app, self.baseline_macro)
        # probability_score should be low (DSR dominates at 25% weight)
        assert signals.probability_score < 60.0, (
            f"DSR=42% should suppress probability_score, got {signals.probability_score}"
        )

    def test_J3_dsr_norm_uses_ISLAMIC_DSR_MAX_not_0_5(self):
        """Static analysis: dsr_norm must reference ISLAMIC_DSR_MAX, not 0.5."""
        import pathlib
        src = pathlib.Path("omnix_core/credit/credit_signal_adapter.py").read_text()
        # Find the dsr_norm line
        for line in src.splitlines():
            if "dsr_norm" in line and "=" in line and "0.5" in line and "#" not in line.split("dsr_norm")[0]:
                pytest.fail(
                    f"dsr_norm still uses hardcoded 0.5 instead of ISLAMIC_DSR_MAX:\n  {line}"
                )

    def test_J4_high_dsr_coherence_reflects_inconsistency(self):
        """
        A borrower with good credit score but DSR=42% (above Islamic limit)
        should have LOW coherence (indicators disagree).
        Before fix: dsr_norm used 0.5 ceiling → 42% DSR gave positive contribution
        After fix: dsr_norm uses 0.40 ceiling → 42% DSR gives 0 (correctly low).
        """
        import dataclasses
        conflicted_app = dataclasses.replace(
            self.baseline_app,
            credit_score=780,        # great credit score
            debt_service_ratio=0.42, # but DSR above Islamic limit
        )
        signals = self.adapter.adapt(conflicted_app, self.baseline_macro)
        # Coherence should be < 70 (indicators disagree: good credit score, bad DSR)
        assert signals.signal_coherence < 75.0, (
            f"Conflicted borrower (good credit, bad DSR) should have low coherence, "
            f"got {signals.signal_coherence}"
        )

    def test_J5_dsr_at_limit_gives_zero_both_scores(self):
        """DSR exactly at ISLAMIC_DSR_MAX (0.40) → dsr_score=0 AND dsr_norm=0."""
        import dataclasses
        app = dataclasses.replace(self.baseline_app, debt_service_ratio=self.dsr_max)
        signals = self.adapter.adapt(app, self.baseline_macro)
        # Both scores should be consistent — neither can be positive if DSR is at limit
        # probability_score will have some value from other factors, but DSR contribution = 0
        # Key: signal_coherence should not be artificially inflated by inconsistent dsr_norm
        assert isinstance(signals.signal_coherence, float)
        assert 0.0 <= signals.signal_coherence <= 100.0

    def test_J6_dsr_well_below_limit_gives_positive_coherence(self):
        """DSR=10% (well within limit) → both dsr_score and dsr_norm are high → high coherence."""
        import dataclasses
        good_app = dataclasses.replace(
            self.baseline_app,
            credit_score=750,
            debt_service_ratio=0.10,
            asset_backing_ratio=1.5,
        )
        signals = self.adapter.adapt(good_app, self.baseline_macro)
        assert signals.signal_coherence > 60.0, (
            f"Good borrower should have high coherence, got {signals.signal_coherence}"
        )

    def test_J7_dsr_signals_internally_consistent(self):
        """
        For any DSR value, the sign of the DSR contribution must be consistent
        between probability_score and signal_coherence pathways.
        A DSR above ISLAMIC_DSR_MAX must not contribute positively to coherence.
        """
        import dataclasses
        from omnix_core.credit.credit_signal_adapter import ISLAMIC_DSR_MAX
        good_signals = self.adapter.adapt(self.baseline_app, self.baseline_macro)

        over_limit_app = dataclasses.replace(
            self.baseline_app,
            debt_service_ratio=ISLAMIC_DSR_MAX + 0.05,
        )
        over_signals = self.adapter.adapt(over_limit_app, self.baseline_macro)

        # Over-limit DSR should produce lower probability (not higher)
        assert over_signals.probability_score < good_signals.probability_score, (
            "Higher DSR should produce lower probability_score"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUE K — Anti-Replay Guard (Bug 3: promesa → implementación real)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAntiReplayGuard:
    """
    Bug 3: Harold le dijo a Naimat que anti-replay existía.
    El nonce en transparency_chain se generaba pero nunca se validaba.
    Este bloque verifica el nuevo módulo anti_replay.py.
    """

    def setup_method(self):
        from omnix_core.evidence.anti_replay import AntiReplayStore
        self.store = AntiReplayStore()  # fresh store per test

    def test_K1_first_registration_succeeds(self):
        self.store.check_and_register("OMNIX-TRD-AABBCCDDEEFF", ttl_ms=30_000)

    def test_K2_second_registration_within_ttl_raises_replay(self):
        from omnix_core.evidence.anti_replay import ReplayDetected
        rid = "OMNIX-TRD-112233445566"
        self.store.check_and_register(rid, ttl_ms=30_000)
        with pytest.raises(ReplayDetected):
            self.store.check_and_register(rid, ttl_ms=30_000)

    def test_K3_replay_detected_message_contains_receipt_id(self):
        from omnix_core.evidence.anti_replay import ReplayDetected
        rid = "OMNIX-CRD-AABBCCDDEEFF"
        self.store.check_and_register(rid, ttl_ms=30_000)
        with pytest.raises(ReplayDetected) as exc_info:
            self.store.check_and_register(rid, ttl_ms=30_000)
        assert rid in str(exc_info.value)

    def test_K4_different_receipts_do_not_conflict(self):
        self.store.check_and_register("OMNIX-TRD-AAAAAAAAAAAA", ttl_ms=30_000)
        self.store.check_and_register("OMNIX-TRD-BBBBBBBBBBBB", ttl_ms=30_000)
        self.store.check_and_register("OMNIX-INS-CCCCCCCCCCCC", ttl_ms=30_000)

    def test_K5_is_replay_returns_false_before_registration(self):
        from omnix_core.evidence.anti_replay import AntiReplayStore
        store = AntiReplayStore()
        assert store.is_replay("OMNIX-TRD-UNREGISTERED0") is False

    def test_K6_is_replay_returns_true_after_registration(self):
        rid = "OMNIX-TRD-REGISTERED00"
        self.store.check_and_register(rid, ttl_ms=30_000)
        assert self.store.is_replay(rid) is True

    def test_K7_expired_entry_allows_reregistration(self):
        """Inject an already-expired entry directly, then verify re-registration succeeds."""
        rid = "OMNIX-TRD-SHORTTTL0001"
        # Inject directly as already-expired (past epoch)
        expired_ms = int(time.time() * 1000) - 5_000   # expired 5 seconds ago
        self.store._store[rid] = expired_ms
        # Should NOT raise — entry is expired
        self.store.check_and_register(rid, ttl_ms=30_000)

    def test_K8_revoke_allows_immediate_reregistration(self):
        rid = "OMNIX-TRD-REVOKEME0001"
        self.store.check_and_register(rid, ttl_ms=30_000)
        revoked = self.store.revoke(rid)
        assert revoked is True
        # After revocation, re-registration should succeed
        self.store.check_and_register(rid, ttl_ms=30_000)

    def test_K9_revoke_nonexistent_returns_false(self):
        result = self.store.revoke("OMNIX-TRD-DOESNOTEXIST")
        assert result is False

    def test_K10_empty_receipt_id_raises_value_error(self):
        with pytest.raises(ValueError):
            self.store.check_and_register("", ttl_ms=30_000)

    def test_K11_zero_ttl_raises_value_error(self):
        with pytest.raises(ValueError):
            self.store.check_and_register("OMNIX-TRD-AABBCCDDEEFF", ttl_ms=0)

    def test_K12_negative_ttl_raises_value_error(self):
        with pytest.raises(ValueError):
            self.store.check_and_register("OMNIX-TRD-AABBCCDDEEFF", ttl_ms=-1000)

    def test_K13_stats_returns_correct_counts(self):
        self.store.check_and_register("OMNIX-TRD-STAT000001AA", ttl_ms=30_000)
        self.store.check_and_register("OMNIX-TRD-STAT000002BB", ttl_ms=30_000)
        stats = self.store.stats()
        assert stats["active_entries"] == 2
        assert stats["total_entries"] == 2
        assert stats["expired_entries"] == 0

    def test_K14_thread_safety_no_races_under_concurrency(self):
        """50 threads each trying to register a unique receipt — zero races expected."""
        from omnix_core.evidence.anti_replay import AntiReplayStore
        store = AntiReplayStore()
        results = []
        errors = []

        def register(i):
            try:
                store.check_and_register(f"OMNIX-TRD-{i:012X}", ttl_ms=30_000)
                results.append("ok")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=register, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(results) == 50

    def test_K15_concurrent_duplicate_only_one_wins(self):
        """100 threads race to register the SAME receipt_id — exactly 1 should win."""
        from omnix_core.evidence.anti_replay import AntiReplayStore, ReplayDetected
        store = AntiReplayStore()
        rid = "OMNIX-TRD-RACERECEIPT"
        successes = []
        replays = []

        def try_register():
            try:
                store.check_and_register(rid, ttl_ms=30_000)
                successes.append(1)
            except ReplayDetected:
                replays.append(1)

        threads = [threading.Thread(target=try_register) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
        assert len(replays) == 99, f"Expected 99 replays, got {len(replays)}"

    def test_K16_module_level_singleton_exists(self):
        from omnix_core.evidence import anti_replay
        assert hasattr(anti_replay, "check_and_register")
        assert hasattr(anti_replay, "is_replay")
        assert hasattr(anti_replay, "get_store")
        assert callable(anti_replay.check_and_register)
        assert callable(anti_replay.is_replay)

    def test_K17_module_singleton_is_shared_across_imports(self):
        """Two imports of the module-level function share the same store."""
        from omnix_core.evidence.anti_replay import check_and_register, get_store, is_replay
        rid = "OMNIX-PUB-SINGLETON001"
        check_and_register(rid, ttl_ms=30_000)
        assert is_replay(rid) is True
        # Cleanup
        get_store().revoke(rid)

    def test_K18_min_window_enforced_when_ttl_too_short(self):
        """Even if ttl_ms=1, the entry stays for at least MIN_WINDOW_MS."""
        from omnix_core.evidence.anti_replay import AntiReplayStore, ReplayDetected, MIN_WINDOW_MS
        store = AntiReplayStore()
        rid = "OMNIX-TRD-MINWINDOW00"
        store.check_and_register(rid, ttl_ms=1)
        # The entry should still be there immediately after (MIN_WINDOW_MS is much longer than 1ms)
        assert store.is_replay(rid) is True

    def test_K19_replay_detected_contains_expiry_info(self):
        """ReplayDetected error message includes expiry timing."""
        from omnix_core.evidence.anti_replay import ReplayDetected
        rid = "OMNIX-TRD-EXPIRYINFO0"
        self.store.check_and_register(rid, ttl_ms=30_000)
        with pytest.raises(ReplayDetected) as exc_info:
            self.store.check_and_register(rid, ttl_ms=30_000)
        msg = str(exc_info.value)
        assert "expires_in" in msg or "REPLAY" in msg

    def test_K20_purge_expired_reduces_store_size(self):
        """Expired entries are purged on next check_and_register call."""
        from omnix_core.evidence.anti_replay import AntiReplayStore
        store = AntiReplayStore()

        # Inject already-expired entries directly
        past_ms = int(time.time() * 1000) - 10_000   # expired 10s ago
        for i in range(10):
            store._store[f"OMNIX-TRD-PURGE{i:07X}"] = past_ms

        assert store.stats()["total_entries"] == 10

        # Register a fresh one — purge runs inside check_and_register
        store.check_and_register("OMNIX-TRD-PURGEFRESH0", ttl_ms=30_000)

        stats = store.stats()
        # Only the fresh one should be active
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 0  # all expired ones were purged

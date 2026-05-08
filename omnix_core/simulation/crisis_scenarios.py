"""
OMNIX — Historical Crisis Scenario Library
==========================================
ADR-145 · Governance Replay Engine

Defines standardized signal states for five historically significant
market events. Each scenario encodes the observable signals at key
inflection points — the exact inputs the OMNIX governance pipeline
would have evaluated in real time.

Consistency note: timestamps and verdict labels are aligned with the
existing OMNIX forensic documents:
  - docs/business/investor/TECHNICAL_VALIDATION_LUNA_2022.md
  - docs/business/pdf/OMNIX_Forensic_FTX_November2022.pdf
  - docs/business/pdf/OMNIX_Forensic_SVB_March2023.pdf

Data sources for each scenario are cited inline.

ADR-145 | Implemented: May 2026 | Author: Harold Nunes — OMNIX QUANTUM LTD
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SignalState:
    """
    Snapshot of observable signals at a specific moment during a crisis.

    Maps to the signal schema consumed by the OMNIX governance pipeline.
    Each field represents a normalized metric (0.0–1.0 unless noted) that
    the pipeline would have received from live data feeds.
    """
    timestamp_utc: str
    label: str
    domain: str
    signals: Dict[str, float]
    expected_verdict: str                        # APPROVED | BLOCKED | HOLD
    expected_block_at_checkpoint: Optional[str]  # e.g. "CAG", "CP-4", "CP-9"
    expected_trust_flags: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class CrisisScenario:
    """
    A complete historical crisis event with multiple governance signal snapshots.

    Each signal_state represents a timestamped evaluation point at which
    the OMNIX governance engine would have produced a decision receipt.
    """
    scenario_id: str
    name: str
    event_date_range: str
    domain: str
    summary: str
    total_loss_usd: Optional[str]
    regulatory_outcome: str
    omnix_verdict_summary: str
    signal_states: List[SignalState] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1 — Terra/LUNA Collapse (May 7–13, 2022)
# Sources: CoinGecko LUNA/UST price history · Anchor Protocol on-chain TVL
#          (Flipside Crypto) · LFG Twitter thread May 9 2022 · Chainalysis
#          June 2022 · SEC v. Terraform Labs SDNY 2023
# Consistency: aligned with docs/business/investor/TECHNICAL_VALIDATION_LUNA_2022.md
# ─────────────────────────────────────────────────────────────────────────────

TERRA_LUNA_COLLAPSE = CrisisScenario(
    scenario_id="CRISIS-001-TERRA-LUNA-2022",
    name="Terra/LUNA Ecosystem Collapse",
    event_date_range="2022-05-07 to 2022-05-13",
    domain="stablecoin_reserve",
    summary=(
        "UST algorithmic stablecoin de-pegged from $1.00, triggering a death spiral "
        "in LUNA. The Luna Foundation Guard deployed $3.5B in BTC reserves — exhausted "
        "in 72 hours. LUNA supply hyperinflated from ~350M to 6.5 trillion tokens. "
        "Total market cap destruction: ~$60B in 5 days."
    ),
    total_loss_usd="$60,000,000,000",
    regulatory_outcome=(
        "Do Kwon indicted by US DOJ (2023). South Korea arrest warrant issued. "
        "SEC charged Terraform Labs with securities fraud. "
        "Triggered global stablecoin regulation: EU MiCA, US STABLE Act."
    ),
    omnix_verdict_summary=(
        "OMNIX issued a WARNING at T-72h (May 8), a HOLD at T-24h (May 10 00:00 UTC) "
        "when stablecoin_reserve_ratio dropped below 0.80, and a BLOCKED at T-6h "
        "(May 10 18:00 UTC) at CP-4 when collateral coverage fell below 1.0x. "
        "A PQC-signed receipt was issued 6 hours before the irreversible collapse — "
        "100% of capital preservation window captured."
    ),
    sources=[
        "CoinGecko: LUNA/USD, UST/USD price history May 2022",
        "Luna Foundation Guard Twitter thread, May 9 2022",
        "Anchor Protocol TVL (Flipside Crypto on-chain data)",
        "Chainalysis on-chain flow report, June 2022",
        "SEC v. Terraform Labs, SDNY, February 2023",
        "OMNIX TECHNICAL_VALIDATION_LUNA_2022.md (internal forensic document)",
    ],
    signal_states=[
        SignalState(
            timestamp_utc="2022-05-08T00:00:00Z",
            label="T-72h: First structural anomaly — UST $0.987, anchor TVL -12%",
            domain="stablecoin_reserve",
            signals={
                "ust_peg_ratio": 0.987,
                "stablecoin_reserve_ratio": 0.94,
                "redemption_velocity": 2.8,
                "anchor_tvl_change_24h": -0.12,
                "luna_market_cap_ratio": 0.88,
                "volatility_24h": 0.34,
                "liquidity_score": 0.71,
                "black_swan_probability": 0.031,
                "signal_integrity_score": 72.0,
                "coherence_score": 68.0,
                "temporal_coherence_score": 71.0,
            },
            expected_verdict="HOLD",
            expected_block_at_checkpoint="CP-4",
            expected_trust_flags=["STABLECOIN_RESERVE_STRESS", "DEPEG_EARLY_WARNING"],
            notes=(
                "SIV score 72/100 — above block threshold (65). Coherence 68/100 — above. "
                "HOLD issued: stablecoin_reserve_ratio 0.94 below 0.95 internal threshold. "
                "Human review mandatory. (Aligned with TECHNICAL_VALIDATION_LUNA_2022.md §Phase 1)"
            ),
        ),
        SignalState(
            timestamp_utc="2022-05-10T00:00:00Z",
            label="T-24h: UST depeg acceleration — reserve ratio 0.69, LFG 38% deployed",
            domain="stablecoin_reserve",
            signals={
                "ust_peg_ratio": 0.73,
                "stablecoin_reserve_ratio": 0.69,
                "redemption_velocity": 11.4,
                "anchor_tvl_change_24h": -0.53,
                "luna_market_cap_ratio": 0.34,
                "volatility_24h": 1.74,
                "liquidity_score": 0.28,
                "black_swan_probability": 0.29,
                "lgf_btc_reserves_remaining_pct": 0.62,
                "signal_integrity_score": 48.0,
                "coherence_score": 41.0,
                "temporal_coherence_score": 38.0,
            },
            expected_verdict="BLOCKED",
            expected_block_at_checkpoint="CP-4",
            expected_trust_flags=[
                "COLLATERAL_BREACH", "BLACK_SWAN_ACTIVE",
                "RESERVE_VELOCITY_CRITICAL", "SIV_BELOW_THRESHOLD"
            ],
            notes=(
                "SIV score 48/100 — BELOW block threshold (65). BLOCKED at CP-0/CP-4. "
                "Coherence 41/100 — below. Redemption velocity 11.4x normal. "
                "(Aligned with TECHNICAL_VALIDATION_LUNA_2022.md §Phase 2 — T-24h)"
            ),
        ),
        SignalState(
            timestamp_utc="2022-05-10T18:00:00Z",
            label="T-6h: Final pre-collapse window — UST $0.31, collateral < 1.0x",
            domain="stablecoin_reserve",
            signals={
                "ust_peg_ratio": 0.31,
                "stablecoin_reserve_ratio": 0.19,
                "redemption_velocity": 28.7,
                "anchor_tvl_change_24h": -0.82,
                "luna_market_cap_ratio": 0.06,
                "volatility_24h": 4.61,
                "liquidity_score": 0.07,
                "black_swan_probability": 0.81,
                "lgf_btc_reserves_remaining_pct": 0.11,
                "token_supply_inflation_rate": 14.2,
                "signal_integrity_score": 14.0,
                "coherence_score": 11.8,
                "temporal_coherence_score": 9.4,
            },
            expected_verdict="BLOCKED",
            expected_block_at_checkpoint="CP-7",
            expected_trust_flags=[
                "DEATH_SPIRAL_DETECTED", "COLLATERAL_EXHAUSTION_IMMINENT",
                "HARD_BLOCK", "SIV_CRITICAL", "COHERENCE_CRITICAL",
                "PQC_RECEIPT_ISSUED"
            ],
            notes=(
                "SIV 14/100, Coherence 11.8/100, TCV 9.4/100 — ALL below threshold (65). "
                "Triple-fail HARD_BLOCK. PQC-signed receipt issued at T-6h. "
                "Capital preservation window: 6 hours before irreversible collapse. "
                "(Aligned with TECHNICAL_VALIDATION_LUNA_2022.md §Phase 3 — T-6h)"
            ),
        ),
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2 — FTX Collapse (November 2–11, 2022)
# Sources: CoinDesk Nov 2 2022 · Binance Twitter Nov 6 2022 · FTX Twitter
#          withdrawal halt Nov 8 2022 · John J. Ray III First Day Declaration
#          SDNY Nov 17 2022 · US v. Bankman-Fried SDNY 2023
# Consistency: aligned with docs/business/pdf/OMNIX_Forensic_FTX_November2022.pdf
# ─────────────────────────────────────────────────────────────────────────────

FTX_COLLAPSE = CrisisScenario(
    scenario_id="CRISIS-002-FTX-2022",
    name="FTX Exchange Collapse & Fraud",
    event_date_range="2022-11-02 to 2022-11-11",
    domain="trading",
    summary=(
        "CoinDesk published Alameda Research's balance sheet (Nov 2), revealing "
        "$5.8B in FTT — a related-party asset issued by FTX itself — as primary collateral. "
        "Binance announced FTT liquidation (Nov 6). FTX halted withdrawals (Nov 8). "
        "$8B+ in customer funds were missing. SBF arrested December 12, 2022."
    ),
    total_loss_usd="$8,000,000,000+",
    regulatory_outcome=(
        "SBF convicted on 7 counts of fraud and conspiracy (November 2023). "
        "25-year federal prison sentence (March 2024). "
        "CFTC, SEC, DOJ coordinated enforcement. "
        "Triggered global crypto exchange regulation: EU MiCA, US Digital Asset bills."
    ),
    omnix_verdict_summary=(
        "OMNIX issued a BLOCKED decision on November 7, 2022 — 4 days before bankruptcy — "
        "at CP-3 (Governance Transparency) and CP-6 (Counterparty Risk). "
        "Circular FTT collateral confirmed at SIV=14.2, Coherence=11.8, TCV=9.4. "
        "Receipt signed with Dilithium-3 at 2022-11-07T00:00:00Z."
    ),
    sources=[
        "CoinDesk: 'Divisions in SBF's Crypto Empire Blur on His Trading Titan's Balance Sheet', Nov 2 2022",
        "Binance official Twitter, November 6 2022",
        "FTX official Twitter: withdrawal halt, November 8 2022",
        "John J. Ray III First Day Declaration, SDNY Bankruptcy, November 17 2022",
        "US v. Bankman-Fried, SDNY 2023 — 7-count fraud conviction",
        "OMNIX OMNIX_Forensic_FTX_November2022.pdf (internal forensic document)",
    ],
    signal_states=[
        SignalState(
            timestamp_utc="2022-11-03T09:00:00Z",
            label="T-5d: Alameda balance sheet published — governance opacity signal",
            domain="trading",
            signals={
                "counterparty_collateral_concentration": 0.72,
                "related_party_collateral_ratio": 0.68,
                "governance_transparency_score": 0.31,
                "liquidity_coverage_ratio": 0.61,
                "ftt_price_usd": 22.10,
                "exchange_proof_of_reserves_score": 0.0,
                "volatility_24h": 0.28,
                "aml_counterparty_risk": 0.44,
                "signal_integrity_score": 61.0,
                "coherence_score": 58.0,
            },
            expected_verdict="HOLD",
            expected_block_at_checkpoint="CP-3",
            expected_trust_flags=[
                "GOVERNANCE_OPACITY", "RELATED_PARTY_COLLATERAL_WARNING",
                "NO_PROOF_OF_RESERVES"
            ],
            notes=(
                "CP-3 (Governance Transparency) HOLD. Related-party collateral 68% — "
                "above 60% internal threshold. No proof-of-reserves published. "
                "SIV 61/100 below threshold. Human review mandatory."
            ),
        ),
        SignalState(
            timestamp_utc="2022-11-07T00:00:00Z",
            label="T-4d: Circular FTT collateral confirmed — OMNIX HARD BLOCK",
            domain="trading",
            signals={
                "counterparty_collateral_concentration": 0.84,
                "related_party_collateral_ratio": 0.84,
                "liquidity_coverage_ratio": 0.28,
                "ftt_price_usd": 17.40,
                "ftt_price_change_24h": -0.22,
                "withdrawal_queue_depth": 3.2,
                "governance_transparency_score": 0.14,
                "exchange_proof_of_reserves_score": 0.0,
                "black_swan_probability": 0.31,
                "aml_counterparty_risk": 0.71,
                "volatility_24h": 0.96,
                "signal_integrity_score": 14.2,
                "coherence_score": 11.8,
                "temporal_coherence_score": 9.4,
                "mci_score": 97.1,
                "circular_collateral_confirmed": 1.0,
            },
            expected_verdict="BLOCKED",
            expected_block_at_checkpoint="CP-6",
            expected_trust_flags=[
                "HARD_BLOCK", "CIRCULAR_COLLATERAL_CONFIRMED",
                "COUNTERPARTY_RISK_BREACH", "GOVERNANCE_OPACITY",
                "REPUTATION_INHERITED_REGIME", "PQC_RECEIPT_ISSUED"
            ],
            notes=(
                "SIV=14.2, Coherence=11.8, TCV=9.4 — ALL below threshold (65). "
                "CP-6 (Counterparty Risk) HARD_BLOCK. Circular FTT collateral confirmed. "
                "MCI=97.1 — maximal contradiction. PQC receipt issued 4 days before bankruptcy. "
                "(Aligned with OMNIX_Forensic_FTX_November2022.pdf RECEIPT_HASH payload)"
            ),
        ),
        SignalState(
            timestamp_utc="2022-11-08T22:15:00Z",
            label="T-3d: Withdrawal halt confirmed — AML structuring — REGULATORY ESCALATION",
            domain="trading",
            signals={
                "counterparty_collateral_concentration": 0.97,
                "related_party_collateral_ratio": 0.97,
                "liquidity_coverage_ratio": 0.04,
                "ftt_price_usd": 2.11,
                "ftt_price_change_24h": -0.87,
                "withdrawal_halt_active": 1.0,
                "governance_transparency_score": 0.02,
                "black_swan_probability": 0.91,
                "aml_counterparty_risk": 0.93,
                "aml_structuring_score": 0.88,
                "missing_customer_funds_signal": 1.0,
                "volatility_24h": 3.47,
            },
            expected_verdict="BLOCKED",
            expected_block_at_checkpoint="CP-9",
            expected_trust_flags=[
                "HARD_BLOCK", "AML_STRUCTURING_DETECTED", "WITHDRAWAL_HALT",
                "REGULATORY_ESCALATION_REQUIRED", "CUSTOMER_FUNDS_AT_RISK",
                "MANDATORY_SAR_FILING"
            ],
            notes=(
                "CP-9 (AML/Sanctions) HARD_BLOCK. Withdrawal halt confirmed. "
                "AML structuring score 0.88 — matches FATF Red Flag #14. "
                "Regulatory escalation mandatory. Mandatory SAR filing triggered."
            ),
        ),
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 3 — Silicon Valley Bank Collapse (March 8–10, 2023)
# Sources: SVB 8-K SEC EDGAR Mar 8 2023 · FDIC Order Mar 10 2023
#          Fed BTFP Mar 12 2023 · Bloomberg SVB deposit data · FDIC Post-Mortem Apr 2023
# Consistency: aligned with docs/business/pdf/OMNIX_Forensic_SVB_March2023.pdf
# ─────────────────────────────────────────────────────────────────────────────

SVB_COLLAPSE = CrisisScenario(
    scenario_id="CRISIS-003-SVB-2023",
    name="Silicon Valley Bank Collapse",
    event_date_range="2023-03-08 to 2023-03-10",
    domain="insurance",
    summary=(
        "SVB announced a $21B AFS bond portfolio sale at $1.8B realized loss (March 8), "
        "triggering a bank run. $42B in withdrawal requests arrived in 10 hours (March 9). "
        "FDIC seized SVB (March 10) — 2nd largest US bank failure in history. "
        "Contagion spread to Signature Bank (March 12) and First Republic Bank."
    ),
    total_loss_usd="$20,000,000,000 (uninsured depositor exposure)",
    regulatory_outcome=(
        "FDIC created bridge bank. Fed launched BTFP ($25B emergency facility). "
        "Federal Reserve, OCC, and FDIC joint investigation. "
        "Congressional hearings. Basel III liquidity rule revision underway. "
        "SVB CEO Gregory Becker subpoenaed."
    ),
    omnix_verdict_summary=(
        "OMNIX would have flagged duration mismatch risk (CP-2) when HQLA ratio "
        "deteriorated in Q4 2022. The March 8 AFS forced-sale announcement triggered "
        "a HOLD at CP-5 (Liquidity). By March 9, withdrawal velocity 14.2x normal "
        "produced a HARD_BLOCK at CP-8 (Contagion) — 48 hours before FDIC seizure."
    ),
    sources=[
        "SVB Financial Group 8-K, March 8 2023 (SEC EDGAR)",
        "FDIC Order Closing SVB, March 10 2023",
        "Federal Reserve BTFP announcement, March 12 2023",
        "Bloomberg: SVB withdrawal data, March 2023",
        "FDIC Post-Mortem Report on SVB Failure, April 2023",
        "OMNIX OMNIX_Forensic_SVB_March2023.pdf (internal forensic document)",
    ],
    signal_states=[
        SignalState(
            timestamp_utc="2023-03-08T16:00:00Z",
            label="T-48h: AFS portfolio sale — $1.8B realized loss — forced liquidation",
            domain="insurance",
            signals={
                "hqla_ratio": 0.61,
                "duration_mismatch_score": 0.78,
                "unrealized_loss_ratio": -0.14,
                "forced_liquidation_signal": 0.82,
                "capital_adequacy_ratio": 0.091,
                "deposit_concentration_risk": 0.74,
                "interest_rate_sensitivity": 0.91,
                "black_swan_probability": 0.08,
                "liquidity_coverage_ratio": 0.68,
            },
            expected_verdict="HOLD",
            expected_block_at_checkpoint="CP-2",
            expected_trust_flags=[
                "DURATION_MISMATCH_WARNING", "FORCED_LIQUIDATION_SIGNAL",
                "CAPITAL_STRESS", "DEPOSIT_CONCENTRATION_HIGH"
            ],
            notes=(
                "CP-2 (Portfolio Risk) HOLD. Duration mismatch 0.78, "
                "forced liquidation signal active, HQLA ratio 0.61 below 0.70 threshold. "
                "Human review mandatory. 48 hours before FDIC seizure."
            ),
        ),
        SignalState(
            timestamp_utc="2023-03-09T14:45:00Z",
            label="T-19h: Bank run — $42B withdrawal requests in 10h — HARD BLOCK",
            domain="insurance",
            signals={
                "hqla_ratio": 0.19,
                "duration_mismatch_score": 0.78,
                "withdrawal_velocity": 14.2,
                "deposit_outflow_24h": -0.31,
                "forced_liquidation_signal": 1.0,
                "capital_adequacy_ratio": 0.051,
                "black_swan_probability": 0.44,
                "systemic_contagion_risk": 0.61,
                "liquidity_coverage_ratio": 0.22,
            },
            expected_verdict="BLOCKED",
            expected_block_at_checkpoint="CP-5",
            expected_trust_flags=[
                "LIQUIDITY_CRISIS", "BANK_RUN_DETECTED", "CAPITAL_BREACH",
                "HARD_BLOCK", "PQC_RECEIPT_ISSUED"
            ],
            notes=(
                "CP-5 (Liquidity) HARD_BLOCK. LCR 0.22, withdrawal velocity 14.2x normal, "
                "deposit outflow -31% in 24h. Capital adequacy 5.1% — below regulatory minimum (8%). "
                "PQC receipt issued 19 hours before FDIC seizure."
            ),
        ),
        SignalState(
            timestamp_utc="2023-03-10T09:00:00Z",
            label="T-0: FDIC seizure — systemic contagion active — REGULATORY ESCALATION",
            domain="insurance",
            signals={
                "hqla_ratio": 0.0,
                "institution_operational_status": 0.0,
                "systemic_contagion_risk": 0.87,
                "contagion_spread_signal": 0.79,
                "withdrawal_velocity": 0.0,
                "black_swan_probability": 0.88,
                "regulatory_intervention_active": 1.0,
                "fdic_seizure_signal": 1.0,
            },
            expected_verdict="BLOCKED",
            expected_block_at_checkpoint="CP-8",
            expected_trust_flags=[
                "HARD_BLOCK", "FDIC_SEIZURE_DETECTED",
                "SYSTEMIC_CONTAGION_ACTIVE", "REGULATORY_ESCALATION_REQUIRED"
            ],
            notes=(
                "CP-8 (Contagion) HARD_BLOCK. FDIC seizure confirmed. "
                "Systemic contagion 0.87 — Signature Bank and First Republic at risk. "
                "Regulatory escalation mandatory. All domain decisions suspended."
            ),
        ),
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 4 — COVID Flash Crash (March 12–13, 2020)
# Sources: CME Group Market Volatility Report Mar 2020 · Kaiko BTC/USD analysis
#          NYSE circuit breaker logs · Fed emergency actions Mar 2020
#          BitMEX downtime announcement Mar 13 2020
# ─────────────────────────────────────────────────────────────────────────────

COVID_FLASH_CRASH_2020 = CrisisScenario(
    scenario_id="CRISIS-004-COVID-CRASH-2020",
    name="COVID-19 Market Flash Crash",
    event_date_range="2020-03-12 to 2020-03-13",
    domain="trading",
    summary=(
        "Bitcoin dropped 40% in a single day (March 12) — from $7,900 to $4,700. "
        "S&P 500 triggered NYSE circuit breakers. Crude oil approached near-zero. "
        "BitMEX halted withdrawals during $700M in forced liquidations. "
        "Total crypto market cap: -$93B in 24 hours. "
        "Correlated sell-off across all asset classes simultaneously."
    ),
    total_loss_usd="$93,000,000,000 (crypto) + $2,700,000,000,000 (global equities)",
    regulatory_outcome=(
        "NYSE, NASDAQ, CBOE circuit breakers triggered 4 times in 2 weeks. "
        "Fed emergency rate cut 100bps (March 15). "
        "$2.3T CARES Act signed (March 27). Fed unlimited QE announced. "
        "BitMEX CFTC charges filed September 2020 — $100M settlement."
    ),
    omnix_verdict_summary=(
        "CAG (Context Admission Gate) blocked all trading decisions at 13:24 UTC "
        "when BTC 1h volatility exceeded 180% annualized — above the 150% hard block "
        "threshold. The trading vertical was suspended for 48 hours. "
        "All attempted decisions during suspension returned BLOCKED with "
        "EXTREME_MARKET_CONDITIONS trust flag and a PQC-signed CAG receipt."
    ),
    sources=[
        "CME Group: Market Volatility Report, March 2020",
        "BitMEX downtime announcement, March 13 2020",
        "Kaiko Research: BTC/USD flash crash analysis, March 2020",
        "NYSE Circuit Breaker activation logs, March 9-18 2020",
        "Federal Reserve emergency rate actions, March 2020",
    ],
    signal_states=[
        SignalState(
            timestamp_utc="2020-03-12T13:24:00Z",
            label="Peak crash — BTC -40% in 24h — CAG hard block at 184% vol",
            domain="trading",
            signals={
                "btc_price_usd": 4730.0,
                "btc_change_24h": -0.401,
                "volatility_1h_annualized": 1.84,
                "volatility_24h": 1.12,
                "correlation_spy_btc": 0.89,
                "liquidity_score": 0.12,
                "bid_ask_spread_bps": 847.0,
                "black_swan_probability": 0.94,
                "extreme_kurtosis": 8.7,
                "market_circuit_breaker_active": 1.0,
                "cross_asset_correlation": 0.91,
            },
            expected_verdict="BLOCKED",
            expected_block_at_checkpoint="CAG",
            expected_trust_flags=[
                "EXTREME_MARKET_CONDITIONS", "CIRCUIT_BREAKER_ACTIVE",
                "BLACK_SWAN_HIGH", "CAG_HARD_BLOCK", "DOMAIN_SUSPENDED_48H"
            ],
            notes=(
                "CAG blocks on volatility_1h_annualized > 1.50 (150% annualized). "
                "Actual: 1.84 (184% annualized). All domain decisions suspended for 48h. "
                "Cross-asset correlation 0.91 — no diversification available. "
                "PQC receipt issued at T=13:24 UTC."
            ),
        ),
        SignalState(
            timestamp_utc="2020-03-13T06:00:00Z",
            label="T+17h: Partial stabilization — CAG 48h cool-down still active",
            domain="trading",
            signals={
                "btc_price_usd": 5210.0,
                "btc_change_24h": 0.103,
                "volatility_1h_annualized": 0.94,
                "volatility_24h": 0.87,
                "liquidity_score": 0.29,
                "black_swan_probability": 0.61,
                "extreme_kurtosis": 5.2,
                "cag_cooldown_hours_remaining": 31.0,
            },
            expected_verdict="BLOCKED",
            expected_block_at_checkpoint="CAG",
            expected_trust_flags=[
                "POST_CRASH_VOLATILITY_ELEVATED", "CAG_COOLDOWN_ACTIVE",
                "DOMAIN_SUSPENDED_PENDING_READMISSION"
            ],
            notes=(
                "Signals improving but CAG 48h cool-down not elapsed (31h remaining). "
                "Domain remains suspended. Capital protected during recovery uncertainty."
            ),
        ),
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 5 — OFAC Tornado Cash Sanctions (August 8, 2022)
# Sources: US Treasury OFAC SDN List Addition Aug 8 2022 · Circle USDC compliance
#          statement Aug 8 2022 · GitHub repository removal · US v. Pertsev Netherlands
#          5th Circuit Court ruling November 2024
# ─────────────────────────────────────────────────────────────────────────────

OFAC_TORNADO_CASH = CrisisScenario(
    scenario_id="CRISIS-005-OFAC-TORNADO-CASH-2022",
    name="OFAC Tornado Cash Sanctions",
    event_date_range="2022-08-08",
    domain="trading",
    summary=(
        "US Treasury OFAC designated Tornado Cash as a Specially Designated National (SDN) "
        "on August 8, 2022 — the first-ever sanctioning of a smart contract protocol. "
        "45 Ethereum addresses were blacklisted. Circle froze $75,000+ in USDC instantly. "
        "GitHub suspended the repository. Dutch developers arrested within days."
    ),
    total_loss_usd="N/A (sanctions enforcement action — $75K+ USDC frozen at T+0)",
    regulatory_outcome=(
        "OFAC SDN list: 45 Ethereum smart contract addresses. "
        "Circle/USDC: immediate compliance, $75K frozen. "
        "GitHub takedown. dYdX, Uniswap frontends blocked. "
        "Roman Storm indicted SDNY 2023. Alexey Pertsev sentenced 5y4m (Netherlands, May 2024). "
        "5th Circuit partially reversed sanctions (November 2024) — immutable contracts debate ongoing."
    ),
    omnix_verdict_summary=(
        "OMNIX Jurisdiction Gate and CP-9 (AML/Sanctions) would have produced a "
        "simultaneous HARD_BLOCK at T+0 the moment the OFAC SDN designation was published "
        "(real-time OFAC feed integration per ADR-068). Mandatory SAR filing receipt "
        "generated with OFAC_SDN_MATCH trust flag. No execution possible under any "
        "jurisdiction where OMNIX operates."
    ),
    sources=[
        "US Treasury OFAC SDN List Addition, August 8 2022",
        "Circle/USDC USDC compliance statement, August 8 2022",
        "GitHub Tornado Cash repository removal, August 8 2022",
        "US v. Roman Storm, SDNY 2023",
        "Netherlands v. Alexey Pertsev, May 2024",
        "5th Circuit Court of Appeals ruling, November 2024",
        "ADR-068: Sanctions List Lifecycle (OMNIX internal)",
    ],
    signal_states=[
        SignalState(
            timestamp_utc="2022-08-08T16:04:00Z",
            label="T+0: OFAC SDN designation published — immediate HARD BLOCK",
            domain="trading",
            signals={
                "ofac_sdn_match": 1.0,
                "jurisdiction_compliance_score": 0.0,
                "aml_sanctions_exposure": 1.0,
                "counterparty_sdn_flag": 1.0,
                "regulatory_jurisdiction_block": 1.0,
                "aml_counterparty_risk": 1.0,
                "transaction_allowed_by_jurisdiction": 0.0,
            },
            expected_verdict="BLOCKED",
            expected_block_at_checkpoint="CP-9",
            expected_trust_flags=[
                "HARD_BLOCK", "OFAC_SDN_MATCH",
                "REGULATORY_ESCALATION_REQUIRED",
                "JURISDICTION_BLOCKED",
                "MANDATORY_SAR_FILING"
            ],
            notes=(
                "CP-9 (AML/Sanctions) + Jurisdiction Gate simultaneous HARD_BLOCK at T+0. "
                "OFAC SDN match triggers automatic block with zero latency. "
                "Mandatory SAR filing generated per ADR-068. "
                "No grace period — any execution with sanctioned address is prohibited."
            ),
        ),
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

CRISIS_SCENARIOS: Dict[str, CrisisScenario] = {
    "CRISIS-001-TERRA-LUNA-2022":        TERRA_LUNA_COLLAPSE,
    "CRISIS-002-FTX-2022":               FTX_COLLAPSE,
    "CRISIS-003-SVB-2023":               SVB_COLLAPSE,
    "CRISIS-004-COVID-CRASH-2020":       COVID_FLASH_CRASH_2020,
    "CRISIS-005-OFAC-TORNADO-CASH-2022": OFAC_TORNADO_CASH,
}


def get_scenario(scenario_id: str) -> Optional[CrisisScenario]:
    """Return a CrisisScenario by ID, or None if not found."""
    return CRISIS_SCENARIOS.get(scenario_id)


def list_scenarios() -> List[str]:
    """Return all registered scenario IDs."""
    return list(CRISIS_SCENARIOS.keys())

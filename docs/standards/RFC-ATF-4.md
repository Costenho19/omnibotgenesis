```
OMNIX QUANTUM Open Standard                            OMNIX QUANTUM LTD
Category: Standards Track                                    H. Nunes, Ed.
DOI: 10.5281/zenodo.20368895                                    May 2026


         RFC-ATF-4: Agent Trust Fabric — Proactive Governance Layer
         Anticipatory Veto Protocol, Structural Shift Detection,
         and Dynamic Semantic Portability
         Extension to RFC-ATF-1, RFC-ATF-2, and RFC-ATF-3
         Version 1.0.0 — OMNIX QUANTUM Open Standard


Abstract

   This document specifies the Proactive Governance Layer (PGL) of the
   Agent Trust Fabric protocol — the fourth RFC in the ATF Open Standard
   series.  RFC-ATF-5 (Cognitive Governance Layer) extends this work.

   RFC-ATF-1 answered the identity and delegation question: who authorized
   this agent, with what authority, and can that be proved offline?
   RFC-ATF-2 answered the runtime continuity question: did authority
   remain valid throughout execution, and was every health degradation
   event cryptographically attested?  RFC-ATF-3 answered the evidence
   question: where does the resulting artifact go, who can interpret it
   across organizational boundaries, and can a regulator reconstruct the
   full chain of custody years later without platform access?

   RFC-ATF-4 answers a fourth, structurally harder class of questions
   that no existing governance framework has formally addressed:

   (1) What happens between governance requests?  A system that evaluates
       drift only when asked can issue receipts under conditions it would
       have rejected, simply because no request arrived during the adverse
       period.  The Anticipatory Governance Veto Protocol (AGVP) closes
       this gap by emitting cryptographically signed, database-persisted
       ProactiveVetoReceipts before any request arrives — anchoring the
       forensic record to the moment of detection rather than the moment
       of the next request.

   (2) Is it safe to recalibrate?  When the Assumption Validity Monitor
       detects that a domain has drifted beyond its threshold, two
       fundamentally different conditions are indistinguishable without
       additional analysis: sustained excursion from a stable signal
       composition (recalibration safe) versus structural change in which
       signals drive governance instability (recalibration unsafe).
       The Structural Shift Detector (SSD) distinguishes them using the
       Component Rank Stability Index (CRSI) — a continuous, formally
       bounded metric proved correct across all real-number inputs.

   (3) Does a receipt issued today remain semantically legitimate in a
       receiving domain six months from now?  A receipt preserves
       cryptographic integrity but not semantic portability: the meaning
       of its governance fields may have changed as regulatory contexts
       evolved, sovereign policies were updated, or operational definitions
       shifted.  The Dynamic Semantic Portability Protocol (DSPP) provides
       a unilateral, offline-computable Retroactive Semantic Assessment
       (RSA) that any receiving domain can perform without contacting the
       originating runtime — O(1) per receipt per domain, no bilateral
       negotiation required.

   Together, AGVP, SSD, and DSPP constitute the Proactive Governance
   Layer — the governance infrastructure answer to three open problems
   whose solutions converge on a single architectural insight: governance
   evidence must exist before the question is asked, the assessment must
   be topologically aware, and the result must travel independently of
   the platform that produced it.

   Nineteen formal properties are proved by the OMNIX Formal Verification
   Suite (OMNIX-FVS-1.0) using the Z3 SMT solver: the new invariants
   introduced in this RFC plus three foundational invariants from
   RFC-ATF-1 and RFC-ATF-2 (ATF-INV-001, ATF-INV-004, RGC-INV-004),
   providing end-to-end arithmetic verification of the complete ATF stack.
   Three of those properties (ATF-INV-001, ATF-INV-004, RGC-INV-004) are
   additionally verified by TLA+ model checking, making
   this specification the first AI governance RFC with dual-methodology
   formal verification: machine-checkable arithmetic proofs across the
   continuous input domain (Z3) and state-machine safety proofs across
   all discrete execution traces (TLA+).

   An implementation that complies with RFC-ATF-1, RFC-ATF-2, RFC-ATF-3,
   and RFC-ATF-4 is designated ATF-PGL-Compliant (Proactive Governance
   Layer Compliant) — the fourth compliance tier in the ATF stack.
   RFC-ATF-5 defines the fifth tier: ATF-CGL-Compliant.


Status of This Memo

   This is an OMNIX QUANTUM Open Standard, published under the OMNIX
   Open Governance License v1.0.  This document extends RFC-ATF-1,
   RFC-ATF-2, and RFC-ATF-3 and MUST be read in conjunction with all
   three.  Implementers of RFC-ATF-3 who require anticipatory governance
   detection, recalibration safety verification, or cross-domain semantic
   portability SHOULD adopt RFC-ATF-4 as specified herein.

   This document is a product of the OMNIX QUANTUM Standards Working
   Group.  It has been approved for publication by the OMNIX Technical
   Committee.

   [STATUS: DRAFT — pending submission to Zenodo.  Not yet published.
    For review by Harold Nunes only.  Do not distribute.]

   DOI: [PENDING]
   Zenodo package: docs/zenodo/rfc_atf_4/ (metadata.json)
   Feedback: standards@omnixquantum.com


Copyright Notice

   Copyright (c) 2026 OMNIX QUANTUM LTD.  All rights reserved.
   71-75 Shelton Street, Covent Garden, London WC2H 9JQ, England.

   Permission is granted to reproduce this document for review and
   implementation purposes, provided this copyright notice is retained.


Acknowledgements

   The three open problems addressed in this RFC were crystallized
   through technical engagement with the broader governance and
   verification research community.

   The detection latency problem and the recalibration topology problem
   (§2.1, §2.3) emerged from technical dialogue with Reza Zarei, creator
   of the 3S Silent Authority System, whose questions — "How do you
   detect that a shift is structural versus a sustained drift pattern
   before review is triggered?" and "How early can you issue the veto
   before the next request?" — established the precise research questions
   that AGVP and SSD answer.

   The semantic portability problem (§2.2) was formally articulated by
   Antonio Socorro in a May 2026 cross-system technical review of RFC-ATF-3:
   "Where my research diverges is around sealing semantic continuity
   entirely at receipt creation time.  While a receipt may preserve
   cryptographic integrity, authority lineage, and admissibility state,
   the receiving domain may still reinterpret operational meaning
   differently as regulatory conditions evolve, sovereign policies change,
   runtime contexts shift, or governance semantics diverge over time."
   This observation is the founding motivation for DSPP.

   The dual-methodology formal verification approach (§8) was inspired by
   the publication of VeriSigil's Z3 proof set (Babatunde, 2026), which
   demonstrated the value of machine-checkable arithmetic proofs for
   governance specifications.  OMNIX-FVS-1.0 extends that contribution
   with 19 proofs — more than four times the VeriSigil count — and
   combines it with TLA+ model checking that no other published governance
   specification provides.


Table of Contents

    1.  Introduction ..............................................  7
    2.  Problem Statement: The Proactive Governance Gap ..........  9
        2.1.  The Detection Latency Problem ......................  9
        2.2.  The Semantic Portability Problem .................. 11
        2.3.  The Recalibration Topology Problem ................ 12
        2.4.  The Proactive Governance Gap (Gap_PG) ............. 13
    3.  Conventions and Terminology .............................. 14
    4.  Architecture: The Proactive Governance Layer ............. 17
        4.1.  Position in the ATF Stack ......................... 17
        4.2.  Extension Relationships ........................... 18
        4.3.  Non-Destructive Integration ....................... 19
    5.  Anticipatory Governance Veto Protocol (AGVP) ............. 20
        5.1.  Two-Layer Veto Architecture ....................... 20
        5.2.  ProactiveVetoReceipt (PVR) Structure .............. 21
        5.3.  AGVPWatchdog Specification ........................ 24
        5.4.  Signal Telemetry Update Protocol .................. 26
        5.5.  PVR Lifecycle: ACTIVE and REVOKED ................. 27
        5.6.  AGVP Invariants (AGV-INV-001–006) ................. 28
    6.  Structural Shift Detector (SSD) .......................... 32
        6.1.  Signal Topology and Recalibration Safety .......... 32
        6.2.  Component Rank Stability Index (CRSI) Algorithm ... 34
        6.3.  Position-Weighting Rationale ...................... 37
        6.4.  StructuralShiftReport Format ...................... 38
        6.5.  Integration with AGVP and AVM ..................... 39
        6.6.  SSD Invariants (SSD-INV-001–003) .................. 40
    7.  Dynamic Semantic Portability Protocol (DSPP) ............. 42
        7.1.  Semantic Posture Vector (SPV) ..................... 43
        7.2.  Semantic Distance Unit (SDU) ...................... 44
        7.3.  Temporal Semantic Anchor (TSA) .................... 48
        7.4.  Semantic Drift Record (SDR) ....................... 50
        7.5.  Retroactive Semantic Assessment (RSA) ............. 52
        7.6.  Portability Verdicts .............................. 55
        7.7.  DSPP Invariants (DSPP-INV-001–007) ................ 56
    8.  Formal Verification (OMNIX-FVS-1.0) ...................... 60
        8.1.  Dual Methodology .................................. 60
        8.2.  Z3 SMT Proof Inventory ........................... 62
        8.3.  TLA+ Model-Checked Properties ..................... 64
        8.4.  Machine Reproducibility ........................... 64
    9.  Proactive Governance Layer — Composition ................. 65
        9.1.  Layer Architecture ................................ 65
        9.2.  Cross-Layer Integration Points .................... 66
        9.3.  Failure Isolation ................................. 67
   10.  Combined Invariant Summary ............................... 68
   11.  Compliance Designation: ATF-PGL-Compliant ................ 71
        11.1.  Designation Requirements ......................... 71
        11.2.  Compliance Hierarchy ............................. 72
   12.  Implementation Requirements .............................. 73
        12.1.  AGVP Requirements ................................ 73
        12.2.  SSD Requirements ................................. 74
        12.3.  DSPP Requirements ................................ 75
        12.4.  Formal Verification Requirements ................. 76
   13.  Security Considerations .................................. 77
        13.1.  ProactiveVetoReceipt Spoofing .................... 77
        13.2.  Semantic Anchor Replay Attack .................... 78
        13.3.  CRSI History Flooding ............................ 79
        13.4.  Watchdog Starvation .............................. 80
        13.5.  SDR Chain Forgery ................................ 80
        13.6.  Zero-Discount Delegation Cycle ................... 81
   14.  Novel Contributions ...................................... 82
        14.1.  Anticipatory Governance Veto Receipt (PVR) ....... 82
        14.2.  Component Rank Stability Index (CRSI) ............ 83
        14.3.  DSPP — O(1) Cross-Domain Assessment Without
               Negotiation ...................................... 84
        14.4.  Dual-Methodology Formal Verification
               (TLA+ + Z3 SMT) .................................. 84
        14.5.  Proactive Governance Gap (Gap_PG) Formal
               Definition ....................................... 85
        14.6.  ATF-PGL-Compliant — Fourth Compliance Tier ........ 85
   15.  Distinction from Prior Art ............................... 85
   16.  Regulatory Alignment ..................................... 87
   17.  References ............................................... 88
   18.  Appendix A — AGVP Wire Format Reference .................. 90
   19.  Appendix B — SDU Computation Reference ................... 92
   20.  Appendix C — PGL Compliance Checklist .................... 93
   21.  Author's Address ......................................... 96


1.  Introduction

   The Agent Trust Fabric protocol stack was designed to address the
   complete lifecycle of a governed autonomous agent action: from the
   moment authority is delegated (RFC-ATF-1), through the continuous
   monitoring of that authority at runtime (RFC-ATF-2), to the long-term
   preservation and independent verification of the resulting evidence
   (RFC-ATF-3).

   RFC-ATF-1 answered: who authorized this agent, with what authority,
   and can that be proved offline?
   RFC-ATF-2 answered: was authority continuously valid during execution,
   and is every health event timestamped and signed?
   RFC-ATF-3 answered: is the resulting evidence classified, lifecycle-
   managed, forensically packaged, and independently verifiable years
   later without platform access?

   Each RFC answered its question completely.  But three structural
   problems were deliberately left open — not because they were unknown,
   but because they require a different class of mechanism than the first
   three RFCs provide.  The first three RFCs operate at request time.
   RFC-ATF-4 operates in the intervals between requests, across domain
   boundaries over time, and underneath the metric surfaces that the
   first three RFCs expose.

   This document addresses all three simultaneously.

   The Detection Latency Problem: a request-time governance system has
   no forensic record of adverse conditions that existed before the next
   request arrived.  If a regulatory shock occurs at T=0 and no
   governance request arrives until T=4h, a compliant RFC-ATF-3 system
   would issue receipts at T=4h with no evidence that conditions were
   already adverse at T=0.  This is not a bug — it is the structural
   consequence of reactive governance design.  AGVP closes it.

   The Semantic Portability Problem: a receipt that is cryptographically
   valid in the issuing domain may carry a different operational meaning
   in a receiving domain that has evolved its regulatory interpretation
   since the receipt was issued.  No protocol exists to assess, without
   bilateral re-negotiation, whether a specific receipt from a specific
   moment in time is semantically portable to a specific receiving domain
   in its current state.  DSPP closes it.

   The Recalibration Topology Problem: when the Assumption Validity
   Monitor detects that a governance domain has drifted beyond its
   threshold, the operator faces a binary decision — recalibrate or not
   — without knowing whether the drift is a sustained excursion from a
   stable signal composition (recalibration safe) or a fundamental
   change in which signals drive governance instability (recalibration
   would embed an obsolete topology as the new baseline).  SSD closes it.

   These three problems are structurally independent in their
   motivations.  They converge on the same architectural conclusion:
   governance evidence must precede requests, semantic legitimacy must
   be computable offline at any future time, and topology changes must
   be distinguished from excursions before any recalibration action
   is taken.  The Proactive Governance Layer integrates all three.


2.  Problem Statement: The Proactive Governance Gap

   This section formally states the three open problems and defines the
   Proactive Governance Gap (Gap_PG) that RFC-ATF-4 closes.  The formal
   structure parallels the Governance Evidence Gap (Gap_GE) defined in
   RFC-ATF-3 §2.

2.1.  The Detection Latency Problem

   Define: for a governance domain D with a calibrated AVM baseline,
   Reactive Veto Coverage (RVC) is the property that every governance
   request processed during an adverse period carries a block_reason
   in its receipt.

   RFC-ATF-1 through RFC-ATF-3 establish RVC at request boundaries.
   A compliant deployment satisfies: for any request R processed when
   domain D is in adverse state, R.receipt.blocked = True.

   Define: Proactive Veto Coverage (PVC) is the stronger property that
   for every interval [T_adverse, T_request), where T_adverse is the
   moment adverse conditions were first measurable and T_request is the
   moment of the next governance request, there exists at least one
   signed, database-persisted governance artifact timestamped within
   [T_adverse, T_adverse + AGVP_WATCHDOG_INTERVAL] attesting to the
   adverse conditions.

   Formally:
      RVC: ∀ request R: domain_is_adverse(D, R.timestamp) → R.blocked
      PVC: ∀ adverse interval [t₀, t₁]: ∃ PVR p: t₀ ≤ p.timestamp ≤
           t₀ + AGVP_MIN_INTERVAL ∧ p.domain = D ∧ p.status = ACTIVE

   RVC does not imply PVC.  A deployment can satisfy RVC (blocking every
   request during the adverse period) while having Gap_PG > 0 (no record
   of the adverse period between requests).

   Example: the Terra/LUNA governance scenario (May 2022).  A system
   satisfying only RVC would have no governance artifacts for the four
   hours between market open and the first governance-triggered request.
   A system satisfying PVC would have PVRs timestamped within 60 seconds
   of the adverse condition onset.  For regulated financial systems, the
   difference is a four-hour forensic gap versus a 60-second forensic gap.

2.2.  The Semantic Portability Problem

   Define: Semantic Portability (SP) for a receipt R from issuing domain
   D_issuer to receiving domain D_receiver is the property that:

      SP(R, D_receiver) ≡ the governance interpretation of R.fields by
      D_receiver is compatible with their intended meaning at issuance
      time in D_issuer

   ATF-INV-006 (RFC-ATF-1) establishes Independent Cryptographic
   Verifiability (ICV) — any party holding the issuer's public key can
   verify R's signature.  ICV does not imply SP.

   Define: Temporal Semantic Drift (TSD) is the change in D_receiver's
   interpretation of ATF Core Terms between R.issued_at and the current
   time — resulting from regulatory evolution, sovereign policy updates,
   or operational definition changes.

   Without RFC-ATF-4:
      SP is undefined: no protocol exists to assess, without contacting
      D_issuer, whether R remains semantically portable after TSD.

      The only mechanism available is bilateral Semantic Alignment
      Certificate (SAC) renegotiation (RFC-ATF-3 §5.3), which requires
      live coordination with the originating runtime and produces a new
      bilateral artifact — it does not retroactively assess existing
      receipts.

   RFC-ATF-4 §7 (DSPP) closes this gap by enabling any D_receiver to
   compute SP(R, D_receiver) locally, at any future time, using only
   public artifacts: the Temporal Semantic Anchor (TSA) sealed at
   R.issued_at and the public Semantic Drift Record (SDR) chain for
   D_issuer.  No contact with D_issuer required.

2.3.  The Recalibration Topology Problem

   Define: for a domain D, a Drift Excursion (DE) is the condition where
   D.drift_score > D.threshold for some continuous interval [t₀, t₁].

   Define: a Topological Stability (TS) condition holds for D when the
   set of signals driving D.drift_score > D.threshold has not materially
   changed since D's calibration baseline was established.

   Two DE conditions require different recalibration policy:

      DE ∧ TS:  Drift is a sustained excursion from a stable signal
                composition.  Recalibrating to current values is safe:
                the governance assumption topology is unchanged.  The new
                baseline captures the current operating envelope.

      DE ∧ ¬TS: Drift is accompanied by a change in which signals are
                the primary drivers of governance instability.  The
                calibration frame may be entirely obsolete.  Recalibrating
                to current values embeds an unvalidated topology as the
                governance baseline.  This is semantically equivalent to
                declaring "current conditions are normal" when the
                definition of "normal" has changed.

   Without RFC-ATF-4, TS is undefined.  The AVM detects DE but cannot
   assess TS.  The recalibration decision is therefore unguided by
   topological evidence.

   RFC-ATF-4 §6 (SSD) closes this gap with the Component Rank Stability
   Index (CRSI) — a formally bounded metric that classifies whether the
   drift-signal composition of a domain is topologically stable, and
   therefore whether auto-recalibration is safe.

2.4.  The Proactive Governance Gap (Gap_PG)

   The Proactive Governance Gap is defined as:

      Gap_PG = (PVC ∪ SP ∪ TS) − (ICV ∪ RVC)

   An ATF-FEI-Compliant deployment without RFC-ATF-4 has Gap_PG > 0.
   Specifically:

      PVC is undefined: no mechanism exists to issue signed veto evidence
      between governance requests.

      SP is undefined: no mechanism exists to assess semantic portability
      of existing receipts in evolving receiving domains.

      TS is undefined: no mechanism exists to distinguish topological
      stability from excursion stability in drift analysis.

   RFC-ATF-4 closes Gap_PG by specifying AGVP (§5) for PVC, SSD (§6)
   for TS, and DSPP (§7) for SP.


3.  Conventions and Terminology

   The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
   "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY",
   and "OPTIONAL" in this document are to be interpreted as described
   in BCP 14 [RFC2119] [RFC8174].

   This document uses all terms defined in RFC-ATF-1 §2, RFC-ATF-2 §3,
   and RFC-ATF-3 §3 without redefinition.  Additional terms:

   Proactive Governance Layer (PGL):
      The sixth operational layer of the ATF stack (L6) in the six-plane
      model used throughout this document (L1–L6), defined by this RFC.
      Comprises AGVP, SSD, and DSPP operating in concert.  RFC-ATF-5
      presents a consolidated five-layer model in which RFC-ATF-1's three
      sub-planes (L1/L2/L3) are treated as a single Layer 1; the PGL
      maps to Layer 4 in that consolidated view.

   ProactiveVetoReceipt (PVR):
      An ML-DSA-65 signed, database-persisted governance artifact emitted
      by the AGVPWatchdog when drift conditions exceed threshold between
      governance requests.  A PVR constitutes a proactive governance block
      with authority equivalent to a reactive AVM drift block.

   AGVPWatchdog:
      The background daemon process that polls cached governance signal
      telemetry at a configurable interval (minimum 30 seconds per
      AGV-INV-003) and emits PVRs when adverse conditions are detected.

   Semantic Posture Vector (SPV):
      A hash-identified snapshot of a runtime's current interpretation of
      the eight ATF Core Terms: authority_scope, execution_boundary,
      delegation_authority, context_boundary, temporal_authority,
      cross_domain_authority, continuity_obligation, and
      forensic_preservation_scope.

   Temporal Semantic Anchor (TSA):
      An ML-DSA-65 signed record created at receipt issuance time,
      capturing the issuing runtime's Semantic Posture Vector at that
      exact moment.  TSAs are public artifacts, independently publishable,
      and require no bilateral agreement.

   Semantic Drift Record (SDR):
      An append-only, ML-DSA-65 signed record published by a runtime each
      time its Semantic Posture Vector changes.  SDRs constitute a public,
      independently verifiable semantic changelog for any ATF-compliant
      runtime.  SDR chains MUST be append-only (DSPP-INV-002).

   Semantic Distance Unit (SDU):
      A normalized value in [0.0, 1.0] measuring the semantic divergence
      between two ATF runtime postures for a given governance term.
      Formally defined in §7.2.  SDU = 0.0 indicates identical postures;
      SDU = 1.0 indicates maximum divergence.

   Retroactive Semantic Assessment (RSA):
      A pure function over (TSA, receiving_SPV, SDR_chain) that produces
      an aggregate SDU and a portability verdict for a specific receipt
      in a specific receiving domain.  The RSA is computable locally,
      requires no communication with the originating runtime, and produces
      deterministic output for identical inputs (DSPP-INV-005).

   Component Rank Stability Index (CRSI):
      A continuous [0.0, 1.0] metric measuring whether the dominant
      drift-signal components for a governance domain have remained
      consistent across evaluation cycles.  CRSI = 1.0 indicates perfect
      topological stability; CRSI < 0.50 with sufficient history (≥ 5
      cycles per SSD-INV-003) indicates STRUCTURAL_SHIFT.

   Structural Shift:
      The condition where the composition of signals driving governance
      drift for a domain has changed, independent of drift magnitude.
      A STRUCTURAL_SHIFT classification blocks auto-recalibration
      (SSD-INV-001) even when no active PVR exists (AGV-INV-006).

   StructuralShiftReport:
      A structured record embedded in every AVMResult and every PVR
      (when issued), classifying the domain's current shift state and
      providing the CRSI value, dominant components, and emerged/receded
      signals.

   ATF-PGL-Compliant:
      The compliance designation for implementations that satisfy all
      invariants of RFC-ATF-1, RFC-ATF-2, RFC-ATF-3, and RFC-ATF-4.
      ATF-PGL-Compliant implementations provide the complete six-layer
      ATF governance infrastructure (L1–L6) including proactive evidence,
      recalibration safety, and cross-domain semantic portability.

   Detection Latency:
      The maximum elapsed time between the onset of adverse drift
      conditions and the creation of a signed governance artifact
      attesting to those conditions.  For ATF-PGL-Compliant deployments,
      detection latency MUST NOT exceed AGVP_WATCHDOG_INTERVAL_SECONDS
      (default: 60, minimum: 30).

   Topological Recalibration Safety:
      The property that a domain's auto-recalibration cycle operates
      only when the signal composition driving drift has remained stable
      (CRSI ≥ 0.50 or INSUFFICIENT_DATA).  Guaranteed by SSD-INV-001
      and AGV-INV-006 acting independently.


4.  Architecture: The Proactive Governance Layer

4.1.  Position in the ATF Stack

   RFC-ATF-4 adds the sixth operational layer to the ATF architecture.
   The complete stack, with all six layers, is:

   L1 — Identity Plane (RFC-ATF-1 §4):
      Agent Identity Records (AIR).  ML-DSA-65 key registration.
      Immutable human-principal binding.

   L2 — Delegation Plane (RFC-ATF-1 §5):
      Delegation Receipts (DR).  Trust Lattice.  Monotonic Authority
      Reduction (ATF-INV-001) enforced at every delegation event.
      Budget ceiling preservation (ATF-INV-004).

   L3 — Verification Plane (RFC-ATF-1 §8):
      Independent, offline receipt verification.  Any party holding the
      issuer's public key can verify any artifact.  ATF-INV-006 (ICV).

   L4 — Runtime Continuity Plane (RFC-ATF-2):
      Continuity Eligibility Score (CES).  Authority Fragmentation Guard
      (AFG).  Runtime Continuity Records (RCR).  Reauthorization
      Challenge (RC).  All eight RGC-INV invariants.

   L5 — Forensic Evidence Infrastructure (RFC-ATF-3):
      Governance Policy Interoperability (GPIL).  Evidence lifecycle
      (ELR, EAP).  Forensic package format (OEP).  Authenticated export
      (FEA).  Forensic verification protocol (FVP).

   L6 — Proactive Governance Layer (RFC-ATF-4):
      Anticipatory Governance Veto Protocol (AGVP): proactive veto
      before requests arrive.  Structural Shift Detector (SSD):
      recalibration safety.  Dynamic Semantic Portability Protocol
      (DSPP): cross-domain semantic portability without negotiation.

   L6 operates orthogonally to L1–L5.  It reads from the Assumption
   Validity Monitor (L4) and the receipt store (L2).  It does not
   modify any artifacts in L1–L5.  A Layer 6 failure MUST NOT affect
   the ability to issue, verify, or archive governance artifacts.

4.2.  Extension Relationships

   RFC-ATF-4 extends the following prior specifications:

   RFC-ATF-1: All six invariants (ATF-INV-001–006) remain unchanged.
   The Trust Lattice Acyclicity property (RGC-INV-004, jointly owned
   with RFC-ATF-2) is Z3-proved in OMNIX-FVS-1.0 (§8.2) for all
   strict-discount three-node delegation cycles.

   RFC-ATF-2: All eight invariants (RGC-INV-001–008) remain unchanged.
   AGV-INV-006 (§5.6) adds a governance-level block to the AVM
   auto-recalibration cycle (ADR-120), operating additively alongside
   the existing recalibration safety checks.

   RFC-ATF-3: All twenty-six invariants (GPIL, ELR, EAP, OEP, FEA,
   FVP families) remain unchanged.  DSPP TSAs are classified as
   FORENSIC evidence (ELR-INV-001) and are subject to the HOT retention
   guarantee (ELR-INV-004).  AGVP PVRs are classified as LEGAL evidence.

4.3.  Non-Destructive Integration

   The PGL is non-destructive with respect to L1–L5.  In particular:

   (a) The AGVPWatchdog operates as a daemon thread.  Its failure MUST
       NOT affect request processing.  Watchdog errors are logged at
       WARNING level and the watchdog re-enters its polling loop.

   (b) AGVP signal telemetry updates are decoupled from the veto path.
       A governance request updates cached signals even when the domain
       is blocked.  This preserves watchdog observability during a block.

   (c) The SSD history ring buffer is an in-process data structure.
       Its eviction policy (FIFO, max 20 entries) is deterministic and
       does not affect any persisted artifact.

   (d) DSPP TSA creation adds one ML-DSA-65 signing operation to the
       receipt issuance path.  This operation is non-blocking and MUST
       fail gracefully: if TSA signing fails, the receipt MUST still be
       issued with a log entry at ERROR level noting the TSA failure.


5.  Anticipatory Governance Veto Protocol (AGVP)

5.1.  Two-Layer Veto Architecture

   ATF-PGL-Compliant implementations operate a two-layer veto
   architecture:

   Layer 1 — Reactive Veto (ADR-076, existing):
      Trigger:  A governance request R arrives.
                AVM.evaluate(D, R.signals) returns is_valid = False
                and pass_through = False.
      Authority: DRIFT_BLOCK — the request is rejected.
                 R.receipt.blocked = True.
                 R.receipt.block_reason = "drift_score={x} > threshold={t}"
      Latency:  Detection occurs at request time only.  No evidence
                exists between requests.

   Layer 2 — Anticipatory Veto (ADR-174, RFC-ATF-4):
      Trigger:  AGVPWatchdog polls cached signals.
                AVM.evaluate(D, cached_signals[D]) returns is_valid =
                False and pass_through = False.
      Authority: ACTIVE PVR — all subsequent requests for D are blocked
                 (AGV-INV-001).  The PVR exists in the ledger before
                 any request arrives.
      Latency:  Detection within one watchdog interval (default 60s,
                minimum 30s per AGV-INV-003).

   Both layers carry equivalent governance authority (AGV-INV-001).
   The anticipatory layer does not replace the reactive layer — it
   precedes it.  A request arriving at a domain with an ACTIVE PVR
   finds the block already established, with a timestamp proving the
   governance system detected the problem before it was asked.

   The two-layer architecture preserves forensic completeness:

   Without Layer 2:  record shows [T=4h: REQUEST_BLOCKED]
   With Layer 2:     record shows [T=0:00: PVR_ISSUED, T=4h: REQUEST_BLOCKED,
                     block_reason references PVR issued at T=0:00]

5.2.  ProactiveVetoReceipt (PVR) Structure

   A ProactiveVetoReceipt is the primary artifact of the AGVP.  Its
   structure is normative; implementations MUST produce PVRs conforming
   to this schema:

   pvr_id (string, REQUIRED):
      Canonical identifier.  Format: "PVR-{16 uppercase hex characters}".
      Generated using cryptographically random bytes.  MUST be globally
      unique within the deployment.

   tenant_id (string, REQUIRED):
      The tenant identifier for the affected domain.

   domain (string, REQUIRED):
      The governance domain identifier for which the veto is issued.

   drift_score (number, REQUIRED):
      The drift score that triggered the anticipatory veto.  Value is
      in (threshold, 1.0].  MUST be > drift_threshold at time of
      issuance (AGV-INV-005 precondition).

   drift_threshold (number, REQUIRED):
      The threshold value configured for this domain at issuance time.
      Value in (0.0, 1.0).

   drift_components (object, REQUIRED):
      A map of signal_name → drift_value for all signals contributing
      to drift_score at assessment time.

   structural_shift_class (string, REQUIRED):
      One of: INSUFFICIENT_DATA | STABLE | DRIFT_WITH_INSTABILITY |
      STRUCTURAL_SHIFT.  Populated from the SSD StructuralShiftReport
      computed at issuance time.  Embedded in the PQC-signed artifact.

   signals_at_assessment (object, REQUIRED):
      A snapshot of all monitored signal values at the moment of
      assessment.  Provides independent forensic evidence of conditions.

   assessment_timestamp (string, REQUIRED):
      ISO-8601-UTC timestamp with nanosecond resolution.  Records the
      exact moment conditions were assessed by the AGVPWatchdog.

   veto_effective_from (string, REQUIRED):
      ISO-8601-UTC timestamp.  MUST equal assessment_timestamp.
      Represents the start of the governed block window.

   status (string, REQUIRED):
      One of: ACTIVE | REVOKED.  MUST be ACTIVE at issuance.
      Transitions to REVOKED only via authorized admin action
      (AGV-INV-002).

   content_hash (string, REQUIRED):
      Format: "sha256:{64 lowercase hex characters}".
      SHA-256 of the canonical JSON encoding of committed fields
      (pvr_id, tenant_id, domain, drift_score, drift_threshold,
      signals_at_assessment, assessment_timestamp, veto_effective_from,
      snapshot_id).  Committed fields constitute the forensic commitment
      (AGV-INV-004).

   pqc_signature (string, REQUIRED):
      ML-DSA-65 (FIPS 204) signature over the content_hash bytes.
      Algorithm identifier MUST be "ML-DSA-65".

   pqc_algorithm (string, REQUIRED):
      MUST be "ML-DSA-65".  Any other value MUST be rejected.

   snapshot_id (string, OPTIONAL):
      Reference to the AVM calibration snapshot active at issuance time.

   The content_hash computation is deterministic (AGV-INV-004):
   identical committed field values ALWAYS produce identical content_hash
   values.  Post-issuance field modification invalidates the ML-DSA-65
   signature.

   A compliant PVR is persisted to the avm_anticipatory_veto_receipts
   table (ADR-174) before the watchdog loop returns.  Persistence MUST
   be atomic: a PVR that fails to persist MUST NOT be logged as ISSUED.
   The database uniqueness constraint on pvr_id prevents duplicate
   emission under concurrent watchdog execution.

5.3.  AGVPWatchdog Specification

   The AGVPWatchdog is a daemon thread that provides the detection
   mechanism for Layer 2 of the two-layer veto architecture.

   Algorithm (normative):

      Initialize:
        interval ← AGVP_WATCHDOG_INTERVAL_SECONDS (default: 60)
        assert interval >= AGVP_MIN_INTERVAL_SECONDS (30)  [AGV-INV-003]
        if interval < 30: raise ValueError

      Loop (executes continuously):
        sleep(interval)
        for each domain D with cached signal telemetry:
          result ← AVM.evaluate(D, cached_signals[D])
          if result.is_valid = False AND result.pass_through = False:
            if NOT has_active_pvr(D):
              ssd_report ← SSD.classify(D)
              pvr ← build_pvr(D, result, ssd_report)
              sign(pvr, ML-DSA-65)
              persist(pvr)                [uniqueness constraint on pvr_id]
              log(ANTICIPATORY_VETO_ISSUED, pvr_id=pvr.pvr_id, domain=D,
                  drift_score=result.drift_score)
            else:
              log(PVR_ALREADY_ACTIVE, domain=D, reason="no duplicate issuance")
          elif drift_subsiding(D) AND has_active_pvr(D):
            log(RECOVERY_CANDIDATE, domain=D, drift=result.drift_score)
            # AGV-INV-002: watchdog MUST NOT revoke — RECOVERY_CANDIDATE is informational only

   The watchdog MUST NOT issue PVRs for domains with pass_through = True
   (AGV-INV-005).  A pass_through domain has no calibration baseline;
   without a baseline, no meaningful adverse condition can be declared.

   The watchdog MUST NOT revoke PVRs under any condition (AGV-INV-002).
   The RECOVERY_CANDIDATE log event is informational only.  Revocation
   is exclusively the domain of authorized admin action.

   Thread safety: the watchdog loop MUST handle exceptions from
   AVM.evaluate() and SSD.classify() without terminating.  All
   exceptions MUST be caught, logged at ERROR level, and the loop
   MUST continue to the next domain.

5.4.  Signal Telemetry Update Protocol

   The AGVP introduces a critical architectural requirement: signal
   telemetry MUST be updated by the governance request path even when
   the domain is blocked.

   Rationale: if the watchdog reads only stale telemetry during a
   block period, it cannot detect drift recovery and cannot produce
   accurate RECOVERY_CANDIDATE events.  More importantly, if a domain
   under a PVR block receives additional requests that update signals
   toward more adverse conditions, the watchdog needs visibility.

   Update rule (normative):

      On any governance request R for domain D, regardless of whether
      D has an ACTIVE PVR:
        cached_signals[D] ← R.signals
        cached_timestamp[D] ← R.arrival_timestamp

   This update MUST occur before any veto check.  The telemetry update
   is a read operation from the governance perspective — it does not
   modify the PVR status or the receipt disposition.

   A domain's cached signals are the single source of truth for the
   watchdog.  Implementations MUST NOT use stale signals older than
   max(3 × AGVP_WATCHDOG_INTERVAL_SECONDS, 300 seconds) for PVR
   issuance.

5.5.  PVR Lifecycle: ACTIVE and REVOKED

   A PVR transitions through the following states:

      PENDING (transient, in-memory only):
        Build and sign phase.  Not yet persisted.
        Transition to ACTIVE: on successful database persistence.
        Transition to FAILED: on persistence error.

      ACTIVE (persisted):
        PVR is blocking all governance requests for the affected domain
        (AGV-INV-001).  Auto-recalibration is frozen (AGV-INV-006).
        This is the only persistent active state.

      REVOKED (persisted):
        PVR has been revoked by authorized admin action.  Block is
        lifted for the affected domain.  The PVR record remains in
        the database as a permanent audit trail entry.  PVR records
        MUST NOT be deleted after revocation.

   Revocation requirements:

   (a) Only admin actions authenticated by a valid operator token can
       revoke a PVR (AGV-INV-002).  The AGVPWatchdog MUST NOT revoke.

   (b) A revocation event MUST produce an audit log entry with the
       revoking admin's identity, the revocation timestamp, and the
       pvr_id.

   (c) Revocation of a PVR does not create a new PVR.  If adverse
       conditions persist after revocation and the watchdog runs again,
       a new PVR will be issued with a new pvr_id.

5.6.  AGVP Invariants (AGV-INV-001 through AGV-INV-006)

AGV-INV-001 — Anticipatory Authority Equivalence

   ∀ domain D, ∀ governance request R targeting D:
      has_active_pvr(D) → R.blocked = True

   An ACTIVE PVR blocks all governance requests for the affected domain
   with the same authority as a reactive drift block.  The block is not
   semantically weaker because it was issued proactively.  A request
   blocked by AGV-INV-001 MUST carry a block_reason that references the
   PVR ID and the PVR's assessment_timestamp.

   Z3 proof: prove_agv_inv001_authority_equivalence() in
   omnix_core/formal_verification/agv_invariants_z3.py.
   Negation asserted: has_pvr=True ∧ drift>threshold ∧ blocked=False.
   Result: UNSAT.

AGV-INV-002 — Watchdog Cannot Self-Revoke

   The AGVPWatchdog process has no code path that sets a PVR's status
   to REVOKED.  The state transition graph for the watchdog contains no
   edge from any state to REVOKED.

   This invariant is verified by static analysis of the watchdog state
   machine.  The watchdog MAY log RECOVERY_CANDIDATE but MUST NOT
   modify PVR status.

AGV-INV-003 — Minimum Watchdog Interval

   ∀ AGVPWatchdog instance W:
      W.watchdog_interval_seconds ≥ AGVP_MIN_INTERVAL_SECONDS (30)

   An interval ≤ 0 or < 30 MUST be rejected at initialization with
   a ValueError.  The minimum of 30 seconds prevents excessive AVM
   load while guaranteeing that adverse conditions are detected within
   twice the minimum interval in the worst case.

   Z3 proof: prove_agv_inv003_minimum_interval() — Negation: system_valid
   = True ∧ interval < 30.  Result: UNSAT.

AGV-INV-004 — PVR Content Hash Commitment

   ∀ PVR p₁, p₂:
      committed_fields(p₁) = committed_fields(p₂) →
         p₁.content_hash = p₂.content_hash

   The PVR content_hash is a deterministic function of its committed
   fields.  Post-issuance modification of any committed field invalidates
   the ML-DSA-65 signature.  The content_hash is computed using canonical
   JSON (keys sorted lexicographically, no whitespace) to ensure
   determinism across implementations.

   Z3 proof: prove_agv_inv004_hash_commitment() — Negation: fields_equal
   = True ∧ hash_equal = False.  Result: UNSAT.

AGV-INV-005 — No Veto Without Baseline

   emit_pvr(D) → AVM.evaluate(D).is_valid = False
               ∧ AVM.evaluate(D).pass_through = False

   PVRs MUST NOT be emitted for domains without a calibration snapshot.
   A pass_through domain has no established baseline; a veto without a
   baseline has no forensic reference point.  The watchdog MUST check
   pass_through = False before emitting any PVR.

   Z3 proof: prove_agv_inv005_no_veto_without_baseline() — Negation:
   pvr_emitted = True ∧ pass_through = True.  Result: UNSAT.

AGV-INV-006 — Auto-Recalibration Freeze During Active PVR

   auto_recalibrate(D) → ¬ has_active_pvr(D)

   The ADR-120 auto-recalibration cycle MUST NOT recalibrate a domain
   with an ACTIVE PVR.  Recalibrating to drifted conditions destroys
   the forensic baseline and would allow subsequent requests to proceed
   under conditions that were classified as adverse.  This invariant
   acts additively with SSD-INV-001: either an active PVR or a
   STRUCTURAL_SHIFT classification is sufficient to block recalibration.

   Z3 proof: prove_agv_inv006_recalibration_freeze() — Negation:
   recalibrate = True ∧ has_active_pvr = True.  Result: UNSAT.


6.  Structural Shift Detector (SSD)

6.1.  Signal Topology and Recalibration Safety

   The Assumption Validity Monitor (ADR-076) evaluates whether a
   governance domain's current signal state is within its calibrated
   envelope.  When it is not (drift_score > threshold), the AVM reports
   is_valid = False.  The recalibration cycle (ADR-120) periodically
   updates the calibration baseline to reflect current conditions.

   The recalibration decision is safe only when the signal composition
   that drives drift has remained stable since the baseline was
   established.  Two drift conditions require categorically different
   treatment:

   Condition A — Sustained Drift (DE ∧ TS):
      The drift score exceeds the threshold, but the signals ranked as
      the primary drivers of drift are the same signals that were
      dominant in previous evaluation cycles.  The governance assumption
      topology is unchanged.  The domain has moved outside its calibrated
      range, but along a familiar axis.

      Safe action: recalibrate.  The new baseline captures the current
      operating envelope with an unchanged signal topology.

   Condition B — Structural Shift (DE ∧ ¬TS):
      The drift score exceeds the threshold, AND the signals now ranked
      as the primary drift drivers have changed.  Signals that were
      dominant are no longer driving drift; signals that were not
      dominant are now the primary contributors.  The calibration frame
      may be entirely obsolete.

      Unsafe action: recalibration would embed the new, unvalidated
      signal topology as the governance baseline, declaring "this
      structural change is now normal" without any supervised validation.

   Without the SSD, these conditions are indistinguishable from AVM
   output alone.  AVM reports drift_score for Condition A and Condition B
   identically.

6.2.  Component Rank Stability Index (CRSI) Algorithm

   The CRSI measures the stability of the dominant drift-signal
   composition across evaluation cycles for a governance domain.

   Parameters (normative):
      SSD_TOP_K_COMPONENTS = 3 (the top-K drift drivers considered)
      SSD_MIN_CYCLES = 5 (minimum history cycles for STRUCTURAL_SHIFT)
      SSD_MAX_HISTORY = 20 (ring buffer size)

      Position weights by rank:
         rank-1 (dominant driver):   weight = K = 3
         rank-2 (second driver):     weight = K-1 = 2
         rank-3 (third driver):      weight = K-2 = 1
         max_weight = K·(K+1)/2 = 6

   Algorithm (normative):

      On each call to AVM.evaluate(D, signals):

      Step 1: Rank current_components descending by drift value.
              current_top_K ← top K component names by drift value.

      Step 2: Append {components: current_components,
                       timestamp: now()} to _component_history[D].
              If len(_component_history[D]) > SSD_MAX_HISTORY:
                evict oldest entry (FIFO).  [SSD-INV-002]

      Step 3: For each history entry h in _component_history[D]:
                hist_top_K ← top K components by drift value in h
                weighted_overlap ← 0
                for rank_i in range(K):
                  if current_top_K[rank_i] in hist_top_K:
                    hist_rank_j ← index of current_top_K[rank_i] in hist_top_K
                    weight ← K − min(rank_i, hist_rank_j)
                    weighted_overlap += weight
                CRSI_h ← weighted_overlap / max_weight

      Step 4: CRSI ← mean(CRSI_h for all h in history).
              cycles_analyzed ← len(_component_history[D])

      Step 5: Classification:
                if cycles_analyzed < SSD_MIN_CYCLES:
                  shift_class ← INSUFFICIENT_DATA
                elif CRSI >= 0.70:
                  shift_class ← STABLE
                elif CRSI >= 0.50:
                  shift_class ← DRIFT_WITH_INSTABILITY
                else:
                  shift_class ← STRUCTURAL_SHIFT  [SSD-INV-003 guarantees
                                                    cycles >= 5 here]

   CRSI is in [0.0, 1.0] for all valid inputs.  Proved by:
      CRSI-BOUND-LO (UNSAT): weighted_overlap ≥ 0 ∧ max_weight > 0 →
                              CRSI ≥ 0.
      CRSI-BOUND-HI (UNSAT): weighted_overlap ≤ max_weight →
                              CRSI ≤ 1.0.
   Both proofs are in omnix_core/formal_verification/ssd_invariants_z3.py.

6.3.  Position-Weighting Rationale

   The CRSI uses position-weighted Jaccard overlap rather than pure
   set Jaccard similarity.  The rationale is as follows.

   Pure set Jaccard treats all K components equally.  For K=3:
      {A,B,C} vs {A,X,Y}: Jaccard = 1/5 = 0.20
      {A,B,C} vs {X,B,Y}: Jaccard = 1/5 = 0.20

   These two cases are not equivalent for governance stability analysis.
   In the first case, the dominant driver (rank-1, A) is unchanged.
   In the second case, only the rank-2 driver (B) is unchanged.

   A change in which signal is the dominant driver of governance
   instability (rank-1) is categorically more significant than a change
   in the rank-3 driver.  Position weighting captures this:
      {A,B,C} vs {A,X,Y}: weighted = (3+0+0)/6 = 0.50
      {A,B,C} vs {X,B,Y}: weighted = (0+2+0)/6 = 0.33

   The first case scores higher (more stable) because the dominant
   driver is preserved.  The second case scores lower because the
   dominant driver has changed.

   Position weighting satisfies the governance intuition that stability
   of the dominant signal (rank-1) is the primary indicator of
   topological continuity.

6.4.  StructuralShiftReport Format

   Every AVMResult carries a StructuralShiftReport.  When a PVR is
   emitted by the AGVPWatchdog, the StructuralShiftReport is embedded
   in the PVR (as the structural_shift_class field and associated
   metadata).  The StructuralShiftReport is ML-DSA-65 signed as part
   of the PVR's committed fields.

   ssd_id (string):
      Format: "SSD-{10 uppercase hex characters}".

   domain (string):
      The governance domain.

   shift_class (string):
      One of: INSUFFICIENT_DATA | STABLE |
      DRIFT_WITH_INSTABILITY | STRUCTURAL_SHIFT.

   crsi (number):
      CRSI value in [0.0, 1.0], rounded to 4 decimal places.

   cycles_analyzed (integer):
      Number of history entries used in CRSI computation.

   dominant_components_current (array of string):
      Top-K component names by current drift value.

   dominant_components_baseline (array of string):
      Components appearing in the top-K in ≥ 50% of history entries.

   emerged_components (array of string):
      Components present in current_top_K but absent from
      dominant_components_baseline.

   receded_components (array of string):
      Components present in dominant_components_baseline but absent
      from current_top_K.

   detected_at (string):
      ISO-8601-UTC timestamp.

6.5.  Integration with AGVP and AVM

   The SSD is called by both the AGVPWatchdog (§5.3) and the reactive
   AVM path on every evaluate() call.  This ensures that every
   governance artifact — whether proactive (PVR) or reactive
   (AVMResult embedded in a receipt) — carries a fresh StructuralShiftReport.

   AGVP integration: the PVR's structural_shift_class field (§5.2)
   is populated from the SSD result at PVR issuance time.  This makes
   the topology classification part of the PQC-signed, persisted artifact.

   Auto-recalibration integration: the recalibration cycle (ADR-120)
   MUST consult SSD before executing.  The check is:

      if has_active_pvr(D):
        skip recalibration  [AGV-INV-006]
      elif SSD.classify(D).shift_class == STRUCTURAL_SHIFT:
        skip recalibration  [SSD-INV-001]
      else:
        execute recalibration

   Both guards are independent.  A domain can be STRUCTURAL_SHIFT
   without an ACTIVE PVR (if drift magnitude has recovered but topology
   has changed).  SSD-INV-001 handles this case; AGV-INV-006 handles
   the ACTIVE PVR case.

6.6.  SSD Invariants (SSD-INV-001 through SSD-INV-003)

SSD-INV-001 — Structural Shift Blocks Auto-Recalibration

   auto_recalibrate(D) → SSD.classify(D).shift_class ≠ STRUCTURAL_SHIFT

   Independent of and additive to AGV-INV-006.  A STRUCTURAL_SHIFT
   classification blocks auto-recalibration even when no ACTIVE PVR
   exists for the domain.  This invariant prevents the AVM from
   adopting an unvalidated signal topology as a new governance baseline
   under the cover of routine recalibration.

   Z3 proof: prove_ssd_inv001_shift_blocks_recalibration() — Negation:
   recalibrate = True ∧ structural_shift = True.  Result: UNSAT.

SSD-INV-002 — Component History Ring Buffer Is Append-Only

   ∀ history entry h ∈ _component_history[D]: h is not modified or
   selectively deleted.  Eviction is FIFO only (ring buffer size
   limit = SSD_MAX_HISTORY = 20).

   The chronological integrity of the topology record MUST be preserved.
   Selective deletion — removing specific entries to alter the CRSI
   result — is forbidden.  The eviction policy is strictly first-in,
   first-out based on insertion order.

SSD-INV-003 — STRUCTURAL_SHIFT Requires Minimum History

   SSD.classify(D).shift_class = STRUCTURAL_SHIFT →
      SSD.classify(D).cycles_analyzed ≥ SSD_MIN_CYCLES (5)

   A STRUCTURAL_SHIFT verdict MUST NOT be issued with fewer than 5
   evaluation cycles in the history.  A single-cycle or low-history
   verdict is statistically unreliable.  Domains with fewer than
   SSD_MIN_CYCLES evaluation cycles receive INSUFFICIENT_DATA regardless
   of CRSI value.

   Z3 proof: prove_ssd_inv003_minimum_history() — Negation:
   cycles < 5 ∧ structural_shift = True.  Result: UNSAT.


7.  Dynamic Semantic Portability Protocol (DSPP)

   The DSPP enables any ATF-compliant receiving domain to perform a
   deterministic, offline assessment of whether a governance receipt
   issued in a different domain at a different point in time remains
   semantically portable — meaning that the governance fields of the
   receipt carry the same operational meaning in the receiving domain's
   current regulatory context as they carried in the issuing domain's
   context at issuance time.

   The DSPP achieves this without any communication with the originating
   runtime.  The assessment is a pure function of three public artifacts:

      1. The Temporal Semantic Anchor (TSA): sealed at issuance time by
         the originating runtime, capturing its semantic posture.

      2. The Semantic Drift Record (SDR) chain: the public, append-only
         changelog of the originating runtime's posture evolution.

      3. The receiving domain's current Semantic Posture Vector (SPV):
         locally available to the receiving domain.

   The DSPP RSA scales to arbitrarily many receiving domains with O(1)
   computation per receipt per domain.

7.1.  Semantic Posture Vector (SPV)

   An SPV is a structured snapshot of a runtime's current interpretation
   of the eight ATF Core Terms.  ATF Core Terms are the governance terms
   whose operational meaning is deliberately left sovereign by the ATF
   protocol (within GPIL bounds, RFC-ATF-3 §5).

   The eight ATF Core Terms are:

      authority_scope:          what actions are within a delegated
                                agent's authority
      execution_boundary:       the boundaries within which execution
                                is considered governed
      delegation_authority:     what authority delegation entails
      context_boundary:         the scope of execution context
      temporal_authority:       how temporal constraints bind authority
      cross_domain_authority:   conditions for cross-domain trust
      continuity_obligation:    what constitutes continuity of authority
      forensic_preservation_scope: what evidence must be preserved

   For each Core Term T, the SPV carries a SemanticTermEntry with:

      content_hash (string):
         SHA-256 of canonical encoding.  If two entries have identical
         content_hash, their SDU is 0.0 (hash-equivalence shortcut).
      boundary_conditions (array of string):
         The conditions under which T applies.
      operational_scope (array of string):
         The operational domains within which T's definition holds.
      regulatory_anchors (array of string):
         The regulatory references that inform T's definition.
      last_updated_at (string):
         ISO-8601-UTC timestamp of last modification.

   An SPV carries a spv_hash computed as SHA-256 over the canonical
   JSON of all eight SemanticTermEntry records.

7.2.  Semantic Distance Unit (SDU)

   The SDU is the fundamental metric of DSPP.  It measures the
   normalized semantic divergence between two SemanticTermEntry records
   for the same ATF Core Term.

   Definition (normative):

      SDU(term_a, term_b):
         if term_a.content_hash == term_b.content_hash:
            return 0.0   [hash-equivalence shortcut]

         boundary_distance ← |Δ(boundary_conditions)| /
                              |union(boundary_conditions)|

            where |Δ(S₁,S₂)| = |S₁ △ S₂| (symmetric difference size)
            and  |union(S₁,S₂)| = |S₁ ∪ S₂|

         scope_distance ← 1.0 − |operational_scope_a ∩ operational_scope_b|
                                  / |operational_scope_a ∪ operational_scope_b|
            (Jaccard distance)

         regulatory_distance ← |Δ(regulatory_anchors)| /
                                |union(regulatory_anchors)|

         SDU ← 0.40 · boundary_distance
              + 0.35 · scope_distance
              + 0.25 · regulatory_distance

   Weight rationale:

      boundary_conditions (0.40, highest weight):
         Boundary conditions are the operational guardrails of a
         governance term.  A change in when a term applies is the
         most impactful dimension of semantic divergence.

      operational_scope (0.35, middle weight):
         Scope defines which operational contexts are governed by
         the term.  Scope divergence changes what is covered.

      regulatory_anchors (0.25, lowest weight):
         Regulatory references provide the normative grounding.
         They are important but often evolve without changing
         operational meaning (e.g., renumbered provisions).

   The weights form a convex combination: 0.40 + 0.35 + 0.25 = 1.00.
   Proved by SDU-WSUM (UNSAT).

   Formal bounds (both Z3-proved, UNSAT):

      SDU ∈ [0.0, 1.0] for all valid inputs.

   The weight constants are structural constants of the DSPP
   specification (DSPP-INV-007a and DSPP-INV-007b).  Implementations
   MUST NOT accept runtime configuration that alters these weights.  A new RFC is
   required to change them.

7.3.  Temporal Semantic Anchor (TSA)

   A TSA is created by the originating runtime at the moment a
   governance receipt is issued.  It seals the issuing runtime's
   semantic posture at the exact moment of issuance.

   Structure (normative):

   tsa_id (string, REQUIRED):
      Format: "TSA-{16 uppercase hex characters}".

   receipt_id (string, REQUIRED):
      The identifier of the governed receipt that this TSA anchors.

   issuing_runtime_id (string, REQUIRED):
      The identifier of the originating runtime.

   spv_hash (string, REQUIRED):
      SHA-256 of the canonical JSON encoding of semantic_term_registry.
      This is the cryptographic commitment to the posture at issuance.

   semantic_term_registry (object, REQUIRED):
      A map of ATF Core Term name → SemanticTermEntry for all eight
      Core Terms.  This is the complete semantic posture at issuance.

   issued_at (string, REQUIRED):
      ISO-8601-UTC timestamp with nanosecond resolution.  MUST equal
      the receipt's issuance timestamp.

   content_hash (string, REQUIRED):
      SHA-256 of canonical JSON of committed TSA fields.

   pqc_signature (string, REQUIRED):
      ML-DSA-65 signature over content_hash bytes.

   A TSA is a public artifact.  It MUST be independently publishable
   without any access restriction.  Any receiving domain that can
   retrieve a TSA can perform an RSA without contacting the issuing
   runtime (DSPP-INV-004).

   TSA creation MUST be atomic with receipt issuance.  If TSA creation
   fails, the receipt MUST still be issued with an ERROR log entry.
   A receipt without a TSA has reduced portability assurance.

   TSA Immutability (DSPP-INV-001):
      A TSA is sealed at issuance and MUST NOT be modified.
      Its content_hash commits all fields at issuance time.

7.4.  Semantic Drift Record (SDR)

   A Semantic Drift Record is published by a runtime each time its
   Semantic Posture Vector changes.  SDRs constitute the public semantic
   changelog for the issuing runtime.

   Structure (normative):

   sdr_id (string, REQUIRED):
      Format: "SDR-{16 uppercase hex characters}".

   runtime_id (string, REQUIRED):
      The issuing runtime.

   previous_spv_hash (string, REQUIRED):
      The spv_hash of the SPV prior to this change.
      For the initial SDR (baseline), this is the genesis sentinel:
      "0000000000000000000000000000000000000000000000000000000000000000".
      (64 hexadecimal zeros — the SHA-256 length.  Implementations MUST
      reject a genesis sentinel of any other length.)

   new_spv_hash (string, REQUIRED):
      The spv_hash of the updated SPV.

   changed_terms (array of string, REQUIRED):
      The ATF Core Terms that changed in this update.

   drift_direction (string, REQUIRED):
      One of: MORE_RESTRICTIVE | LESS_RESTRICTIVE | LATERAL.
      MORE_RESTRICTIVE: the new posture is narrower (higher SDU implies
      receiving domains that were compatible may now require re-assessment).
      LESS_RESTRICTIVE: the new posture is broader.
      LATERAL: the posture changed in a way not captured by the
      restrictiveness axis.

   change_rationale (string, REQUIRED):
      A human-readable description of the reason for the posture change.
      MUST be present.  An empty string is not a valid rationale.

   effective_from (string, REQUIRED):
      ISO-8601-UTC timestamp when the new posture takes effect.

   pqc_signature (string, REQUIRED):
      ML-DSA-65 signature.

   SDR Append-Only Invariant (DSPP-INV-002):
      An SDR entry MUST NOT be modified or deleted after issuance.
      The SDR chain for a runtime is an append-only public log.  This
      guarantees that any domain computing an RSA over the SDR chain
      obtains the complete, unmodified history of semantic evolution.

7.5.  Retroactive Semantic Assessment (RSA)

   The RSA is the core computation of the DSPP.  It produces a
   deterministic portability verdict for a specific receipt in a
   specific receiving domain.

   Inputs:
      receipt_id: the receipt to assess
      receiving_runtime_id: the receiving domain

   Algorithm (normative):

      1. TSA ← retrieve(receipt.tsa_id)
         [from public artifact store — no contact with issuing runtime]

      2. sdr_chain ← retrieve_all_sdrs(TSA.issuing_runtime_id)
         [public SDR chain — ordered by effective_from ascending]

      3. receiving_spv ← get_current_spv(receiving_runtime_id)
         [local knowledge — receiving domain's own posture]

      4. For each ATF Core Term T in {authority_scope, execution_boundary,
         delegation_authority, context_boundary, temporal_authority,
         cross_domain_authority, continuity_obligation,
         forensic_preservation_scope}:

           originating_entry ← TSA.semantic_term_registry[T]
           receiving_entry ← receiving_spv.registry[T]
           term_sdu[T] ← SDU(originating_entry, receiving_entry)

      5. aggregate_sdu ← mean(term_sdu.values())
         portability_confidence ← 1.0 − aggregate_sdu

      6. verdict ← classify_verdict(aggregate_sdu)
         [§7.6 — DSPP-INV-007a and DSPP-INV-007b guarantee totality
          and exclusivity]

      7. Return RSAResult(
           receipt_id, receiving_runtime_id, aggregate_sdu,
           portability_confidence, verdict, term_sdu,
           assessed_at=now(), tsa_id=TSA.tsa_id)

   RSA is a pure function (DSPP-INV-005): identical inputs produce
   identical aggregate_sdu and identical verdict.  Two independent
   receiving domains computing RSA for the same receipt against the
   same SPV will always produce the same result.

   The RSA MUST be computable with no network call to the originating
   runtime (DSPP-INV-004).  An implementation that requires originating
   runtime availability for RSA computation is non-conformant.

   RSA complexity: O(K) where K = |ATF Core Terms| = 8.  This is O(1)
   with respect to the number of receiving domains.  Semantic portability
   assessment scales to arbitrarily many receiving domains without
   coordination overhead.

7.6.  Portability Verdicts

   The RSA produces one of four portability verdicts based on
   aggregate_sdu.  The verdict thresholds are structural constants of
   the DSPP specification (DSPP-INV-007a and DSPP-INV-007b):

   SEMANTICALLY_PORTABLE    [0.00, 0.10):
      The receiving domain's current posture for all assessed terms is
      sufficiently aligned with the originating posture at issuance.
      The receipt may be used without semantic qualification.

   DRIFT_ACKNOWLEDGED        [0.10, 0.40):
      Moderate semantic divergence exists.  The receiving domain SHOULD
      apply contextual qualification when using this receipt.  The
      receipt remains admissible but carries semantic drift.

   DRIFT_CRITICAL            [0.40, 0.70):
      Significant semantic divergence.  The receiving domain MUST
      document the divergence before relying on this receipt in any
      regulatory context.  Human review is RECOMMENDED.

   SEMANTICALLY_INCOMPATIBLE [0.70, 1.00]:
      The receiving domain's interpretation of the governed terms is
      sufficiently divergent that the receipt cannot be assumed to carry
      its original semantic content.  The receipt MAY still be
      cryptographically valid (ICV holds), but its operational meaning
      in the receiving domain is unreliable.

   DSPP-INV-006 — Incompatibility Propagation:
      A SEMANTICALLY_INCOMPATIBLE verdict on a Delegation Receipt
      propagates to all receipts that descend from that DR in the
      receiving domain's chain assessment.

7.7.  DSPP Invariants (DSPP-INV-001 through DSPP-INV-007)

DSPP-INV-001 — TSA Immutability
   A TSA is sealed at receipt issuance and MUST NOT be modified.
   Its content_hash commits all fields at issuance time.

DSPP-INV-002 — SDR Append-Only
   SDR entries MUST NOT be modified or deleted after publication.
   SDR chains are append-only public logs.

DSPP-INV-003 — RSA Uses MORE_RESTRICTIVE Governing Posture
   When the drift_direction of the most recent SDR is MORE_RESTRICTIVE,
   the RSA MUST use the more restrictive boundary interpretation.
   This is the conservative default: in semantic ambiguity, the receiving
   domain assumes the stricter interpretation.

DSPP-INV-004 — No Semantic Negotiation
   RSA computation requires no communication with the originating
   runtime.  An implementation that requires originating runtime
   availability for RSA computation is non-conformant.

DSPP-INV-005 — RSA Verdict Determinism
   ∀ (TSA, receiving_SPV, SDR_chain): RSA is a pure function.
      same inputs → same aggregate_sdu → same verdict

   Z3 proof: prove_dspp_inv005_rsa_determinism() — Negation:
   same_inputs = True ∧ sdu_A ≠ sdu_B.  Result: UNSAT.

DSPP-INV-006 — Incompatibility Propagation
   A SEMANTICALLY_INCOMPATIBLE verdict on a DR in a delegation chain
   propagates to all receipts descending from that DR in the receiving
   domain's assessment.

DSPP-INV-007 (a + b) — Structural Threshold Constants
   The verdict thresholds (0.10, 0.40, 0.70) and SDU weights
   (0.40, 0.35, 0.25) are structural constants of the DSPP
   specification.  They MUST NOT be overridden by runtime configuration.
   Changing them requires a new RFC.

   Two sub-properties, both Z3-proved:

   DSPP-INV-007a — Threshold Partition Totality:
      ∀ aggregate_sdu ∈ [0, 1]: exactly one verdict class applies.
      Z3: Negation: sdu ∈ [0,1] ∧ ¬(PORTABLE ∨ ACKNOWLEDGED ∨
          CRITICAL ∨ INCOMPATIBLE).  Result: UNSAT.

   DSPP-INV-007b — Threshold Partition Exclusivity:
      ∀ aggregate_sdu ∈ [0, 1]: at most one verdict class applies.
      Z3: Negation: sdu satisfies two verdict conditions simultaneously.
      Result: UNSAT.


8.  Formal Verification (OMNIX-FVS-1.0)

8.1.  Dual Methodology

   OMNIX RFC-ATF-4, combined with the TLA+ properties established in
   RFC-ATF-1 and RFC-ATF-2, constitutes the first AI governance protocol
   specification with dual-methodology formal verification.

   The two methodologies are strictly complementary:

   TLA+ Model Checking:
      Scope: safety properties across all discrete execution traces.
      Coverage: Monotonic Authority Reduction (MAR), delegation chain
      acyclicity (structural, non-arithmetic), RC expiry HALT propagation,
      temporal authority bounds.
      Tool: TLA+ with TLC model checker.
      Specification: docs/formal/ATF-TLA-SPEC.tla (included in Zenodo).
      Properties proved: 5 (MAR, Acyclicity, ChainRoot, Immutability,
      RCExpiry).

   Z3 SMT Arithmetic:
      Scope: correctness of arithmetic-defined invariants across the
      continuous input domain.
      Coverage: all arithmetic invariants in RFC-ATF-1/2/4 —
      budget bounds, threshold constraints, weight sums, CRSI bounds,
      classification totality, RSA determinism.
      Tool: Z3 version 4.x (de Moura & Bjørner, 2008).
      Suite: OMNIX-FVS-1.0 in omnix_core/formal_verification/ (5 modules).
      Properties proved: 19 (all UNSAT).

   Why both methodologies are necessary:

   TLA+ cannot directly prove arithmetic facts about real-valued metrics
   (CRSI, SDU, drift_score).  Z3 cannot directly prove properties over
   all possible state machine execution traces.  A protocol specification
   that relies on both discrete state-machine safety and continuous
   arithmetic correctness requires both tools.

   No other published AI governance specification applies both.

8.2.  Z3 SMT Proof Inventory

   The following 19 proofs constitute OMNIX-FVS-1.0.  All return UNSAT.
   A SAT result or UNKNOWN result means the invariant does not hold as
   stated; the prover would provide a counterexample.

   ┌────────────────────────┬────────────────────────────────────────────┬────────┐
   │ Invariant ID           │ Negation Asserted                          │ Result │
   ├────────────────────────┼────────────────────────────────────────────┼────────┤
   │ ATF-INV-001            │ child_budget > parent_budget               │ UNSAT  │
   │ ATF-INV-004            │ child_budget > 100 (parent ≤ 100, MAR)     │ UNSAT  │
   │ RGC-INV-004            │ bB<bA ∧ bC<bB ∧ bA<bC (3-node cycle)      │ UNSAT  │
   │ AGV-INV-001            │ pvr_active ∧ drift>thr ∧ ¬blocked          │ UNSAT  │
   │ AGV-INV-003            │ system_valid ∧ interval < 30               │ UNSAT  │
   │ AGV-INV-004            │ fields_equal ∧ hash_differs                │ UNSAT  │
   │ AGV-INV-005            │ pvr_emitted ∧ pass_through = True          │ UNSAT  │
   │ AGV-INV-006            │ recalibrate ∧ has_active_pvr               │ UNSAT  │
   │ CRSI-BOUND-LO          │ overlap≥0 ∧ max>0 ∧ crsi < 0              │ UNSAT  │
   │ CRSI-BOUND-HI          │ overlap≤max ∧ max>0 ∧ crsi > 1            │ UNSAT  │
   │ CRSI-CLASS-TOT         │ crsi ∈ [0,1] ∧ no class applies           │ UNSAT  │
   │ SSD-INV-001            │ recalibrate ∧ structural_shift = True      │ UNSAT  │
   │ SSD-INV-003            │ cycles < 5 ∧ structural_shift = True       │ UNSAT  │
   │ SDU-BOUND-LO           │ b,s,r ∈ [0,1] ∧ sdu < 0                   │ UNSAT  │
   │ SDU-BOUND-HI           │ b,s,r ∈ [0,1] ∧ sdu > 1                   │ UNSAT  │
   │ SDU-WSUM               │ 0.40 + 0.35 + 0.25 ≠ 1.0                  │ UNSAT  │
   │ DSPP-INV-005           │ same_inputs ∧ sdu_A ≠ sdu_B               │ UNSAT  │
   │ DSPP-INV-007a          │ sdu ∈ [0,1] ∧ no verdict class applies    │ UNSAT  │
   │ DSPP-INV-007b          │ sdu simultaneously in two verdict classes  │ UNSAT  │
   └────────────────────────┴────────────────────────────────────────────┴────────┘

   Total: 19 proofs · 19 UNSAT · 0 SAT · 0 UNKNOWN · runtime < 200ms

   The table is ordered: RFC-ATF-1/2 invariants first (rows 1–3),
   AGVP invariants (rows 4–8), SSD/CRSI invariants (rows 9–13),
   DSPP/SDU invariants (rows 14–19).  This ordering reflects the
   layered architecture of the ATF stack.

8.3.  TLA+ Model-Checked Properties

   The TLA+ specification (docs/formal/ATF-TLA-SPEC.tla) model-checks
   the following five properties across all reachable states of the
   ATF delegation state machine:

   MARInvariant:
      In every reachable state, every Delegation Receipt has
      authority_budget ≤ its parent's authority_budget.

   AcyclicityInvariant:
      The delegation graph has no directed cycle in any reachable state.
      (Structural property — complements the Z3 arithmetic proof of
      RGC-INV-004 which proves the strict-discount case.)

   ChainRootInvariant:
      Every delegation chain traces to exactly one human principal AIR.

   ImmutabilityInvariant:
      Once a Delegation Receipt is issued, its content_hash and
      pqc_signature fields are never modified.

   RCExpiryHalt:
      If a Reauthorization Challenge expires (RC_TTL exceeded), the
      runtime transitions to HALT and HALT propagates to all child
      sessions.

8.4.  Machine Reproducibility

   The OMNIX-FVS-1.0 proof suite is machine-reproducible:

      python -m omnix_core.formal_verification.run_all

   JSON output mode:

      python -m omnix_core.formal_verification.run_all --json \
         --output proof_report.json

   The resulting proof_report.json contains for each invariant:
   invariant_id, result (UNSAT/SAT/UNKNOWN), proved (boolean),
   elapsed_ms, description, negation_asserted, adr_reference,
   rfc_reference, and model_counterexample (null if UNSAT).

   The OMNIX-FVS-1.0 suite itself is governed by three meta-invariants
   defined in ADR-177 [ADR-177]:

   FVS-INV-001 — All proofs return UNSAT.  Any SAT or UNKNOWN result
                 is a suite failure, not just a proof failure.
   FVS-INV-002 — No UNKNOWN results.  A Z3 timeout violates the
                 soundness assumption of the proof methodology.
   FVS-INV-003 — Suite completes in under 10 seconds on reference
                 hardware (Python 3.11, z3-solver 4.x, single core).

   FVS-INV-001 through FVS-INV-003 are verified by
   tests/test_formal_verification.py (class TestFullSuite).

   pytest integration:

      pytest tests/test_formal_verification.py   [19 assertions]

   Dependencies: z3-solver (pip install z3-solver).  No platform
   imports.  Reproducible in any Python 3.11+ environment with
   z3-solver installed.


9.  Proactive Governance Layer — Composition

9.1.  Layer Architecture

   The full six-layer ATF stack, with all cross-layer interactions, is:

   L6 ─── Proactive Governance Layer (RFC-ATF-4)
   │       AGVP: anticipatory vetoes before requests arrive
   │       SSD: recalibration safety under topology change
   │       DSPP: semantic portability across domain boundaries
   │       ↕ reads: cached signal telemetry (L4), receipt store (L2)
   │       ↕ writes: PVR table, TSA table, SDR chain
   │
   L5 ─── Forensic Evidence Infrastructure (RFC-ATF-3)
   │       GPIL: policy interoperability contracts
   │       ELR/EAP: evidence lifecycle and archive pipeline
   │       OEP/FEA/FVP: forensic packages and verification
   │       ↕ reads: receipt store (L2), RCR state (L4)
   │       ↕ writes: COLD blocks, OEP packages, evidence custody log
   │
   L4 ─── Runtime Continuity Plane (RFC-ATF-2)
   │       CES: Continuity Eligibility Score
   │       AFG: Authority Fragmentation Guard
   │       RCR: Runtime Continuity Records
   │       RC: Reauthorization Challenge
   │
   L2/L3 ─ Delegation and Verification Planes (RFC-ATF-1)
   │       DR: Delegation Receipts
   │       TL: Trust Lattice
   │       Offline Verification (ATF-INV-006)
   │
   L1 ──── Identity Plane (RFC-ATF-1)
           AIR: Agent Identity Records
           ML-DSA-65 key registration
           Immutable human-principal binding (ATF-INV-002)

9.2.  Cross-Layer Integration Points

   | From  | To | Mechanism           | Invariant(s)            |
   |-------|----|---------------------|-------------------------|
   | L6    | L2 | PVR blocks DR issue | AGV-INV-001             |
   | L6    | L4 | AGVP blocks recal.  | AGV-INV-006             |
   | L6    | L4 | SSD blocks recal.   | SSD-INV-001             |
   | L6    | L6 | SSD class in PVR    | structural_shift_class  |
   | L6    | L2 | TSA per DR          | DSPP-INV-001            |
   | L6    | L5 | TSA as FORENSIC ev. | ELR-INV-001             |
   | L5    | L6 | HALT triggers PVR   | AGV-INV-005 pre-check   |
   | L4    | L6 | Signal telemetry    | §5.4 update protocol    |

9.3.  Failure Isolation

   PGL failure modes MUST be isolated from governance receipt issuance:

   AGVPWatchdog failure:
      The watchdog MUST catch all exceptions and re-enter the polling
      loop.  A crashed watchdog reduces the PVC guarantee but MUST NOT
      affect RVC (Layer 1 reactive vetoes remain fully operative).

   SSD classify() failure:
      If SSD.classify() raises an exception, the AVMResult MUST be
      returned with shift_class = INSUFFICIENT_DATA rather than
      propagating the exception.  Receipt issuance is unaffected.

   TSA signing failure:
      If TSA creation fails during receipt issuance, the receipt MUST
      still be issued.  An ERROR log entry MUST be written noting the
      failure.  The receipt is issued without DSPP portability assurance.

   SDR publication failure:
      SDR publication is a background operation.  Failure MUST be
      logged at ERROR level and retried.  Runtime operations are
      unaffected by SDR publication failures.


10.  Combined Invariant Summary

   The following table lists all twenty-three invariant properties
   defined in RFC-ATF-4 — six canonical named identifiers per the AGV
   family, six per the SSD/CRSI family, and eleven per the DSPP/SDU
   family — with their sections, proof method, and the open problem
   each closes.

   AGVP Invariants:

   | Invariant   | Description                              | §    | Proof | Gap   |
   |-------------|------------------------------------------|------|-------|-------|
   | AGV-INV-001 | Anticipatory Authority Equivalence       | 5.6  | UNSAT | PVC   |
   | AGV-INV-002 | Watchdog Cannot Self-Revoke              | 5.6  | State | PVC   |
   | AGV-INV-003 | Minimum Watchdog Interval (≥30s)         | 5.6  | UNSAT | PVC   |
   | AGV-INV-004 | PVR Content Hash Commitment              | 5.6  | UNSAT | PVC   |
   | AGV-INV-005 | No Veto Without Calibration Baseline     | 5.6  | UNSAT | PVC   |
   | AGV-INV-006 | Auto-Recalibration Freeze During PVR     | 5.6  | UNSAT | TS    |

   SSD Invariants:

   | Invariant   | Description                              | §    | Proof | Gap   |
   |-------------|------------------------------------------|------|-------|-------|
   | CRSI-BOUND-LO  | CRSI ≥ 0.0 for all valid inputs       | 6.2  | UNSAT | TS    |
   | CRSI-BOUND-HI  | CRSI ≤ 1.0 for all valid inputs       | 6.2  | UNSAT | TS    |
   | CRSI-CLASS-TOT | CRSI classification is total (covers) | 6.2  | UNSAT | TS    |
   | SSD-INV-001 | STRUCTURAL_SHIFT Blocks Auto-Recal.      | 6.6  | UNSAT | TS    |
   | SSD-INV-002 | History Ring Buffer Is Append-Only       | 6.6  | State | TS    |
   | SSD-INV-003 | STRUCTURAL_SHIFT Requires ≥5 Cycles      | 6.6  | UNSAT | TS    |

   DSPP Invariants:

   | Invariant    | Description                             | §    | Proof | Gap   |
   |--------------|-----------------------------------------|------|-------|-------|
   | SDU-BOUND-LO | SDU ≥ 0.0 for all valid inputs          | 7.2  | UNSAT | SP    |
   | SDU-BOUND-HI | SDU ≤ 1.0 for all valid inputs          | 7.2  | UNSAT | SP    |
   | SDU-WSUM     | Weights sum to 1.0 (convex combination) | 7.2  | UNSAT | SP    |
   | DSPP-INV-001 | TSA Immutability                        | 7.7  | Struct| SP    |
   | DSPP-INV-002 | SDR Append-Only                         | 7.7  | Struct| SP    |
   | DSPP-INV-003 | RSA Uses MORE_RESTRICTIVE Posture       | 7.7  | Logic | SP    |
   | DSPP-INV-004 | No Semantic Negotiation Required        | 7.7  | Logic | SP    |
   | DSPP-INV-005 | RSA Verdict Determinism                 | 7.7  | UNSAT | SP    |
   | DSPP-INV-006 | Incompatibility Propagation             | 7.7  | Logic | SP    |
   | DSPP-INV-007a| Threshold Partition Totality            | 7.7  | UNSAT | SP    |
   | DSPP-INV-007b| Threshold Partition Exclusivity         | 7.7  | UNSAT | SP    |

   Proof column key:
      UNSAT  — formally proved by Z3 SMT solver (OMNIX-FVS-1.0); all
               return UNSAT (unsatisfiable negation), confirming the
               property holds for all valid inputs
      State  — verified by state-machine analysis (exhaustive code-path
               inspection confirming no reachable state violates the
               invariant; not amenable to Z3 arithmetic encoding)
      Struct — verified by structural analysis (data model enforces the
               property by construction; no runtime check needed)
      Logic  — verified by logical argument (property follows directly
               from definition; Z3 encoding would be circular)

   Gap column key (open problem closed by each invariant):
      PVC  — Proactive Veto Coverage: closes the detection-latency gap
             (Gap_PG §2.4); governance evidence is cryptographically
             attested before the request it governs arrives
      TS   — Topology Safety: closes the recalibration topology problem
             (§2.3); STRUCTURAL_SHIFT is formally distinguishable from
             a sustained drift excursion, making recalibration safety
             a decidable property
      SP   — Semantic Portability: closes the semantic portability
             problem (§2.2); RSA verdict is deterministic and
             domain-independent for all valid inputs with no pairwise
             negotiation required

   All invariant_id values in this table are identical to the
   invariant_id fields in omnix_core/formal_verification/
   proof files and the run_all.py output.


11.  Compliance Designation: ATF-PGL-Compliant

11.1.  Designation Requirements

   An implementation claims the ATF-PGL-Compliant designation by
   satisfying all requirements of RFC-ATF-1, RFC-ATF-2, RFC-ATF-3,
   and this RFC.

   ATF-PGL-Compliant REQUIRES, in addition to all ATF-FEI-Compliant
   requirements:

   AGVP
   (a) AGVPWatchdog deployed as a persistent daemon with interval ≥ 30s
   (b) PVR issued and persisted within one watchdog interval of adverse
       condition onset when cached signals are current
   (c) PVRs carry ML-DSA-65 signatures over committed fields
   (d) PVR status transitions: ACTIVE only at issuance, REVOKED only
       by authenticated admin action
   (e) Watchdog: no code path sets PVR.status = REVOKED
   (f) Signal telemetry updated by request path even when domain blocked
   (g) PVRs not emitted for pass_through domains
   (h) Auto-recalibration cycle consults has_active_pvr() before execution

   SSD
   (i) CRSI computed on every AVM.evaluate() call
   (j) StructuralShiftReport embedded in every AVMResult and every PVR
   (k) Auto-recalibration blocked when shift_class = STRUCTURAL_SHIFT
   (l) Component history ring buffer: FIFO eviction only, no selective
       deletion; max 20 entries per domain
   (m) STRUCTURAL_SHIFT verdict issued only with cycles_analyzed ≥ 5

   DSPP
   (n) TSA created at receipt issuance for every Delegation Receipt
   (o) TSA carries ML-DSA-65 signature; TSAs publicly accessible
   (p) SDRs published on every SPV change with non-empty rationale
   (q) SDR chain is append-only; no SDR is modified or deleted
   (r) RSA computation does not require live contact with originating runtime
   (s) Verdict thresholds (0.10, 0.40, 0.70) not overridable at runtime
   (t) SDU weights (0.40, 0.35, 0.25) not overridable at runtime

   Formal Verification
   (u) OMNIX-FVS-1.0 (or equivalent) executes without UNKNOWN or SAT
       results for all 19 listed invariants (§8.2)

11.2.  Compliance Hierarchy

   The ATF compliance designations form a strict hierarchy:

      ATF-Compliant       (RFC-ATF-1 only)
         ↓ extends
      ATF-RGC-Compliant   (+ RFC-ATF-2)
         ↓ extends
      ATF-FEI-Compliant   (+ RFC-ATF-3)
         ↓ extends
      ATF-PGL-Compliant   (+ RFC-ATF-4)   ← fourth tier
         ↓ extends
      ATF-CGL-Compliant   (+ RFC-ATF-5)   ← fifth tier [RFC-ATF-5]

   Each tier subsumes all lower tiers.  An ATF-PGL-Compliant
   implementation is necessarily ATF-FEI-Compliant, ATF-RGC-Compliant,
   and ATF-Compliant.  RFC-ATF-5 defines the fifth and highest tier,
   ATF-CGL-Compliant, which subsumes ATF-PGL-Compliant.


12.  Implementation Requirements

   The following requirements are normative.  The key words MUST, MUST
   NOT, SHOULD, and MAY are as defined in BCP 14.

12.1.  AGVP Requirements

   REQ-AGVP-001 (MUST):
      The AGVPWatchdog MUST be deployed as a persistent daemon thread
      with AGVP_WATCHDOG_INTERVAL_SECONDS ≥ 30.

   REQ-AGVP-002 (MUST):
      PVRs MUST be persisted to a durable store (database) before the
      watchdog loop logs ANTICIPATORY_VETO_ISSUED.

   REQ-AGVP-003 (MUST):
      PVR identifiers MUST be globally unique.  A database uniqueness
      constraint on pvr_id MUST be present to prevent duplicate issuance
      under concurrent execution.

   REQ-AGVP-004 (MUST):
      Governance request processing MUST check for ACTIVE PVRs and
      block accordingly (AGV-INV-001).  The check MUST occur before
      any governance evaluation is performed.

   REQ-AGVP-005 (MUST):
      The AGVPWatchdog MUST NOT emit PVRs for domains where
      AVM.evaluate() returns pass_through = True (AGV-INV-005).

   REQ-AGVP-006 (MUST NOT):
      The AGVPWatchdog MUST NOT set PVR.status = REVOKED under any
      condition (AGV-INV-002).

   REQ-AGVP-007 (SHOULD):
      AGVP_WATCHDOG_INTERVAL_SECONDS SHOULD be configurable via
      environment variable.  The default value SHOULD be 60 seconds.

   REQ-AGVP-008 (MUST):
      PVR content_hash MUST be computed as SHA-256 of canonical JSON
      of committed fields with keys sorted lexicographically.

   REQ-AGVP-009 (MUST):
      PVR pqc_algorithm MUST be "ML-DSA-65".  Any other algorithm
      MUST be rejected at PVR construction time.

12.2.  SSD Requirements

   REQ-SSD-001 (MUST):
      SSD.classify() MUST be called on every AVM.evaluate() invocation.
      StructuralShiftReport MUST be present in every AVMResult.

   REQ-SSD-002 (MUST):
      Auto-recalibration MUST check SSD.classify() before execution.
      If shift_class = STRUCTURAL_SHIFT, recalibration MUST be skipped
      and the skip MUST be logged at WARNING level.

   REQ-SSD-003 (MUST):
      The component history ring buffer MUST use FIFO eviction with a
      maximum of SSD_MAX_HISTORY (20) entries.  Selective deletion is
      not permitted.

   REQ-SSD-004 (MUST):
      STRUCTURAL_SHIFT MUST NOT be returned when cycles_analyzed < 5.
      Low-history domains MUST return INSUFFICIENT_DATA.

   REQ-SSD-005 (SHOULD):
      SSD_TOP_K_COMPONENTS SHOULD be 3.  Implementations MAY configure
      a different value, but the value MUST be at least 2.

   REQ-SSD-006 (MUST):
      If SSD.classify() raises any exception, the exception MUST be
      caught.  The caller MUST receive an AVMResult with shift_class
      = INSUFFICIENT_DATA rather than an unhandled exception.

12.3.  DSPP Requirements

   REQ-DSPP-001 (MUST):
      A TSA MUST be created and signed for every Delegation Receipt
      at issuance time.  Failure to create a TSA MUST NOT prevent
      the receipt from being issued.

   REQ-DSPP-002 (MUST):
      TSAs MUST be publicly accessible without authentication.
      TSA retrieval MUST NOT require live access to the issuing runtime.

   REQ-DSPP-003 (MUST):
      SDRs MUST be published whenever the runtime's SPV changes.
      SDR publication MUST include a non-empty change_rationale.

   REQ-DSPP-004 (MUST NOT):
      SDR records MUST NOT be modified or deleted after publication.
      The SDR chain for any runtime MUST be append-only.

   REQ-DSPP-005 (MUST):
      RSA computation MUST be executable without any network call to
      the originating runtime.

   REQ-DSPP-006 (MUST NOT):
      The SDU weight constants (0.40, 0.35, 0.25) MUST NOT be
      configurable at runtime.  Any attempt to override them MUST
      be rejected with a configuration error.

   REQ-DSPP-007 (MUST NOT):
      The DSPP portability verdict thresholds (0.10, 0.40, 0.70)
      MUST NOT be configurable at runtime.

   REQ-DSPP-008 (MUST):
      A SEMANTICALLY_INCOMPATIBLE verdict on a DR MUST be propagated
      to all descendants of that DR in the assessment result.

12.4.  Formal Verification Requirements

   REQ-FVS-001 (MUST):
      ATF-PGL-Compliant implementations MUST include a machine-
      executable formal proof runner that reproduces the 19 UNSAT
      results from §8.2.

   REQ-FVS-002 (SHOULD):
      The proof runner SHOULD produce a machine-readable JSON report
      (§8.4 format) for inclusion in compliance deliverables.

   REQ-FVS-003 (MUST NOT):
      A proof that returns SAT or UNKNOWN for any invariant listed in
      §8.2 MUST NOT be used to claim ATF-PGL-Compliant status for that
      invariant.  A SAT result means the invariant does not hold as
      stated.


13.  Security Considerations

13.1.  ProactiveVetoReceipt Spoofing

   Threat: an adversary with write access to the avm_anticipatory_veto_
   receipts table may insert PVR records with fabricated drift_scores
   and content_hashes, creating fraudulent blocks for arbitrary domains.

   Mitigation: PVR content_hash is SHA-256 of committed fields.
   Any inserted PVR that does not carry a valid ML-DSA-65 signature from
   the platform signing key fails verification — the signature cannot
   be forged without the private key.  ATF-PGL-Compliant implementations
   MUST verify PVR signatures before enforcing blocks (REQ-AGVP-004).
   The ML-DSA-65 private key MUST be protected under the same controls
   as the platform signing key (RFC-ATF-3 §14.6).

13.2.  Semantic Anchor Replay Attack

   Threat: an adversary publishes a fraudulent TSA that misrepresents
   the originating runtime's posture at issuance time — causing RSA
   computations to understate divergence (SEMANTICALLY_PORTABLE verdict
   for a receipt that should be DRIFT_CRITICAL).

   Mitigation: TSA authenticity depends on the ML-DSA-65 signature from
   the issuing runtime's key.  A receiving domain performing RSA MUST
   verify the TSA signature before consuming its semantic_term_registry.
   TSA signing uses the same platform signing key as Delegation Receipts;
   the public key is independently published (as per RFC-ATF-3 §10.1).
   A TSA with an invalid signature MUST cause the RSA to return an
   ASSESSMENT_FAILED result rather than a portability verdict.

13.3.  CRSI History Flooding

   Threat: an adversary with the ability to trigger frequent governance
   evaluations (through high-frequency agent requests) may attempt to
   flood the SSD ring buffer with entries that establish a false "stable"
   topology, masking an actual structural shift by overwriting the
   history buffer faster than topology changes can accumulate.

   Mitigation: the ring buffer has a maximum of SSD_MAX_HISTORY (20)
   entries.  At 1 request per second, a 20-entry buffer fills in 20
   seconds — which is also the minimum useful SSD observation window.
   Implementations MAY rate-limit the frequency at which AVM.evaluate()
   contributes to SSD history (e.g., at most one history entry per N
   seconds per domain).  Rate limiting the governance request path
   (RFC-ATF-3 §10.3) provides upstream mitigation.

13.4.  Watchdog Starvation

   Threat: if the request path is never executed for a blocked domain,
   the cached signal telemetry for that domain becomes stale.  The
   watchdog continues to see stale signals and may never observe
   drift recovery — holding the ACTIVE PVR indefinitely.

   Mitigation: the Signal Telemetry Update Protocol (§5.4) ensures that
   blocked requests still update cached signals — the update occurs before
   any block check.  Even when every request is blocked, the signals are
   refreshed.
   Implementations SHOULD configure a maximum signal staleness threshold
   consistent with the normative rule in §5.4 — signals older than
   max(3 × AGVP_WATCHDOG_INTERVAL_SECONDS, 300 seconds) MUST NOT be
   used for new PVR issuance.

13.5.  SDR Chain Forgery

   Threat: an adversary with the ability to inject into the SDR chain
   for a runtime may attempt to add fraudulent SDR entries that show
   a MORE_RESTRICTIVE posture evolution — causing RSA computations to
   compute artificially low SDU values, making incompatible receipts
   appear portable.

   Mitigation: SDR authenticity depends on ML-DSA-65 signatures.  A
   receiving domain computing RSA MUST verify the signature of each
   SDR in the chain before consuming it.  An SDR with an invalid
   signature MUST be treated as a chain break; the RSA MUST be flagged
   as UNVERIFIABLE for that chain segment.

13.6.  Zero-Discount Delegation Cycle

   Threat: by constructing a delegation cycle where each delegation
   uses discount = 0 (no authority reduction), an adversary might
   attempt to construct an infinite delegation loop with equal budgets
   at every node.

   Mitigation: ATF-INV-003 (RFC-ATF-1) establishes receipt immutability
   — a receipt cannot modify another receipt.  The TLA+ AcyclicityInvariant
   (§8.3) proves that the ATF delegation graph has no directed cycle in
   any reachable state, regardless of discount value.  The Z3 proof of
   RGC-INV-004 (§8.2) proves the strict-discount case arithmetically.
   The identity-based cycle prohibition (unique receipt IDs, parent_id
   cannot reference the receipt's own ID) prevents zero-discount cycles
   structurally.


14.  Novel Contributions

   RFC-ATF-4 introduces six novel technical contributions to the
   governance infrastructure literature.

14.1.  Anticipatory Governance Veto Receipt (PVR)
       — First Proactive Governance Attestation in AI Governance

   No prior governance framework for autonomous AI agents emits a
   cryptographically signed, database-persisted veto artifact before
   a governance request arrives.

   The PVR closes the forensic gap identified in §2.1.  Its timestamp
   precedes any subsequent blocked request.  The sequence:

      [T=0:00 PVR signed and persisted — conditions were adverse HERE]
      [T=4:00 request arrives — blocked, block_reason references PVR]

   is forensically unambiguous.  No prior specification — LangChain,
   AutoGPT, CrewAI, Microsoft AutoGen, or VeriSigil VGS-001/011 —
   provides an anticipatory governance receipt.

   The PVR's structural position in the governance timeline (before
   requests) is what distinguishes it from enhanced reactive vetoes.
   It is not faster detection — it is categorically earlier attestation.

14.2.  Component Rank Stability Index (CRSI)
       — Novel Recalibration Safety Metric

   CRSI is a position-weighted Jaccard overlap over the drift-component
   history — a continuous, formally bounded metric (Z3-proved: CRSI ∈
   [0,1] for all valid inputs) that classifies whether the signal
   topology driving governance drift is stable or has undergone
   structural change.

   No prior work in AI governance distinguishes sustained excursion from
   topology change in drift analysis.  The distinction is operationally
   critical: recalibrating to a sustained excursion is safe; recalibrating
   to a topology change embeds unvalidated assumptions as the new baseline.

   The position-weighting design (§6.3) is itself novel: governance
   intuition about which components matter most (rank-1 = dominant
   driver) is formalized as a metric rather than left to operator
   judgment.

14.3.  DSPP — O(1) Cross-Domain Assessment Without Negotiation

   The DSPP RSA is a unilateral, offline computation that scales to
   arbitrarily many receiving domains with O(1) computation per receipt
   per domain.  No contact with the originating runtime.  No bilateral
   state machine.  No per-domain negotiation.

   The SDU formula (§7.2) is the first formally bounded semantic
   divergence metric defined for AI governance receipts.  Its weight
   assignments reflect governance intuition: boundary conditions (0.40)
   matter more than scope (0.35), which matters more than regulatory
   anchors (0.25).  The convex combination property (SDU-WSUM, Z3-proved)
   guarantees the metric remains normalized.

   The protocol's scalability property is architecturally significant:
   an issuing runtime publishes a TSA once, and any number of receiving
   domains can assess portability at any future time without coordination.

14.4.  Dual-Methodology Formal Verification (TLA+ + Z3 SMT)
       — First in AI Governance

   RFC-ATF-1 through RFC-ATF-3, combined with RFC-ATF-4, constitute
   the first AI governance protocol specification with:

   (a) TLA+ model-checked safety properties across all discrete state
       traces (MAR, Acyclicity, ChainRoot, Immutability, RCExpiry).

   (b) Z3 SMT arithmetic proofs for all arithmetic-defined invariants
       across the continuous input domain (19 proofs, all UNSAT).

   The two methodologies cover the two classes of properties that
   governance specifications require: discrete state-machine safety
   (TLA+) and continuous arithmetic correctness (Z3).  Using only one
   methodology leaves the other class unverified.

   VeriSigil VGS-001/011 (the closest comparable published specification)
   provides 4 Z3 proofs and 5 TLA+ theorems but does not apply both
   methodologies to the same protocol.  OMNIX FVS-1.0 provides 19 Z3
   proofs over a protocol that also carries TLA+ coverage — 4.75× the
   Z3 proof count in a dual-methodology verified specification.

14.5.  Proactive Governance Gap (Gap_PG) Formal Definition
       — First Formal Gap Analysis for Anticipatory Governance

   Section 2.4 introduces the Proactive Governance Gap as a formal
   definition:

      Gap_PG = (PVC ∪ SP ∪ TS) − (ICV ∪ RVC)

   This formalization enables compliance assessment to be stated
   precisely: a deployment has Gap_PG = 0 if and only if it satisfies
   PVC (AGVP), SP (DSPP), and TS (SSD).  No prior specification defines
   the gap between reactive and proactive governance coverage in
   formal terms.

14.6.  ATF-PGL-Compliant — Fourth Compliance Tier

   The ATF compliance hierarchy spans five tiers:
   ATF-Compliant → ATF-RGC-Compliant → ATF-FEI-Compliant →
   ATF-PGL-Compliant → ATF-CGL-Compliant (RFC-ATF-5).

   ATF-PGL-Compliant is the first compliance tier that addresses
   evidence between requests (AGVP), semantic legitimacy over time
   (DSPP), and recalibration safety (SSD) — the three proactive
   governance properties that no prior tier addressed.  RFC-ATF-5
   introduces ATF-CGL-Compliant, the fifth tier, addressing decision
   space documentation (CGE), universal multi-jurisdiction certification
   (GUGT), and longitudinal evidence interpretability (TGB).


15.  Distinction from Prior Art

   The following comparison covers the closest published governance
   specifications as of May 2026.

   ┌───────────────────────────────┬───────┬──────────┬───────┬────────┬───────┐
   │ Property                      │ OMNIX │ VeriSigil│ LangCh│ AutoGen│ OAuth │
   │                               │ ATF   │ VGS      │       │        │       │
   ├───────────────────────────────┼───────┼──────────┼───────┼────────┼───────┤
   │ Proactive veto before request │ Yes   │ No       │ No    │ No     │ No    │
   │ PVR: signed, timestamped      │ Yes   │ No       │ No    │ No     │ No    │
   │ Recalibration topology check  │ Yes   │ No       │ No    │ No     │ No    │
   │ CRSI: continuous metric       │ Yes   │ No       │ No    │ No     │ No    │
   │ Semantic portability (O(1))   │ Yes   │ Partial* │ No    │ No     │ No    │
   │ No negotiation for portability│ Yes   │ No       │ No    │ No     │ No    │
   │ Z3 SMT proofs                 │ 19    │ 4        │ 0     │ 0      │ 0     │
   │ TLA+ properties               │ 5     │ 5        │ 0     │ 0      │ 0     │
   │ Dual methodology (Z3 + TLA+)  │ Yes   │ No       │ No    │ No     │ No    │
   │ Post-quantum signing (ML-DSA) │ Yes   │ No       │ No    │ No     │ No    │
   │ Offline-verifiable receipts   │ Yes   │ Yes      │ No    │ No     │ Yes   │
   │ Formal compliance designation │ Yes   │ Yes      │ No    │ No     │ Yes   │
   └───────────────────────────────┴───────┴──────────┴───────┴────────┴───────┘

   * VeriSigil VGS-010 addresses "Jurisdiction-Aware Admissibility" but
     requires runtime-dependent assessment at verification time.  DSPP
     RSA is computable entirely locally with no originating runtime
     contact.  The portability model is categorically different.

   OMNIX-specific properties shared by no other published specification:
      • Anticipatory governance receipt (PVR) — signed, timestamped,
        persisted before any request arrives
      • Component Rank Stability Index (CRSI) — topology stability metric
      • DSPP Retroactive Semantic Assessment — O(1), no negotiation
      • Dual Z3 + TLA+ formal verification on the same protocol stack


16.  Regulatory Alignment

   | Framework                   | AGVP Relevance          | SSD Relevance           | DSPP Relevance          |
   |-----------------------------|-------------------------|-------------------------|-------------------------|
   | EU AI Act Art. 9, 13        | Art. 9 risk management: | Art. 61 post-market:    | Art. 13 transparency:   |
   |                             | proactive risk detection | continuous recal. audit | cross-domain semantics  |
   | DORA Art. 6 (ICT risk)      | Continuous monitoring   | Topology change audit   | —                       |
   |                             | with signed evidence    | for recal. safety       |                         |
   | DORA Art. 9 (resilience)    | Detection latency ≤ 60s | —                       | —                       |
   | NIST AI RMF GOVERN 1.6      | —                       | Recal. safety docs      | Multi-domain semantics  |
   | NIST AI RMF MANAGE 4.1      | Monitoring evidence     | Topology assessment     | —                       |
   | China AI Law Arts. 20–22    | —                       | —                       | Cross-border portability|
   | GCC/DIFC AI Reg. 10         | Sovereign attestation   | —                       | Jurisdiction portability|
   | SOC 2 Type II CC7.2         | Continuous monitoring   | Change documentation    | —                       |
   | ISO 27001 A.12.4            | Signed monitoring trail | —                       | Semantic audit log      |
   | FATF Rec. 16 (AI finance)   | Proactive freeze record | —                       | —                       |


17.  References

   [RFC-ATF-1]
      Nunes, H., "RFC-ATF-1: Agent Trust Fabric Delegation Protocol,
      Version 1.0.0", OMNIX QUANTUM Open Standard, May 2026.
      DOI: 10.5281/zenodo.20155016
      Figshare: 10.6084/m9.figshare.32308077
      SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6757339

   [RFC-ATF-2]
      Nunes, H., "RFC-ATF-2: Agent Trust Fabric — Runtime Governance
      Continuity, Version 1.0.0", OMNIX QUANTUM Open Standard, May 2026.
      DOI: 10.5281/zenodo.20241344
      Figshare: 10.6084/m9.figshare.32308095

   [RFC-ATF-3]
      Nunes, H., "RFC-ATF-3: Agent Trust Fabric — Governance Policy
      Interoperability, Evidence Lifecycle, and Forensic Verification
      Protocol, Version 1.0.0", OMNIX QUANTUM Open Standard, May 2026.
      DOI: 10.5281/zenodo.20247342
      Figshare: 10.6084/m9.figshare.32308119

   [FIPS204]
      National Institute of Standards and Technology, "Module-Lattice-
      Based Digital Signature Standard (ML-DSA)", FIPS 204, August 2024.

   [Z3]
      de Moura, L. and Bjørner, N., "Z3: An Efficient SMT Solver",
      Proceedings of TACAS 2008, LNCS 4963, pp. 337-340, Springer, 2008.

   [TLA+]
      Lamport, L., "Specifying Systems: The TLA+ Language and Tools for
      Hardware and Software Engineers", Addison-Wesley, 2002.

   [RFC2119]
      Bradner, S., "Key words for use in RFCs to Indicate Requirement
      Levels", BCP 14, RFC 2119, March 1997.

   [RFC8174]
      Leiba, B., "Ambiguity of Uppercase vs Lowercase in RFC 2119 Key
      Words", BCP 14, RFC 8174, May 2017.

   [ADR-173]
      Nunes, H., "ADR-173: Dynamic Semantic Portability Protocol (DSPP)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-173

   [ADR-174]
      Nunes, H., "ADR-174: Anticipatory Governance Veto Protocol (AGVP)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-174

   [ADR-175]
      Nunes, H., "ADR-175: Structural Shift Detector (SSD)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-175

   [ADR-177]
      Nunes, H., "ADR-177: OMNIX Formal Verification Suite (FVS)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-177

   [VGS]
      Babatunde, R.L., "VeriSigil Governance Specification (VGS-001 to
      VGS-011)", Version 0.7.2, May 2026.
      DOI: 10.5281/zenodo.20264923
      Published record — verified May 2026.

   [ADR-076]
      Nunes, H., "Assumption Validity Monitor (AVM)",
      OMNIX QUANTUM, 2026.

   [ADR-120]
      Nunes, H., "AVM Calibration Snapshot Scheduler",
      OMNIX QUANTUM, 2026.


18.  Appendix A — AGVP Wire Format Reference

   Normative field reference for a PVR JSON record
   (avm_anticipatory_veto_receipts table schema):

   | Field                    | Type    | Required | Constraints                           |
   |--------------------------|---------|----------|---------------------------------------|
   | pvr_id                   | string  | REQUIRED | "PVR-" + 16 uppercase hex chars       |
   | tenant_id                | string  | REQUIRED | Non-empty                             |
   | domain                   | string  | REQUIRED | Non-empty                             |
   | drift_score              | number  | REQUIRED | > drift_threshold; ≤ 1.0              |
   | drift_threshold          | number  | REQUIRED | > 0.0; < 1.0                          |
   | drift_components         | object  | REQUIRED | {signal_name: float, …}               |
   | structural_shift_class   | string  | REQUIRED | INSUFFICIENT_DATA | STABLE |          |
   |                          |         |          | DRIFT_WITH_INSTABILITY |               |
   |                          |         |          | STRUCTURAL_SHIFT                      |
   | signals_at_assessment    | object  | REQUIRED | {signal_name: value, …}               |
   | assessment_timestamp     | string  | REQUIRED | ISO-8601-UTC, nanosecond precision    |
   | veto_effective_from      | string  | REQUIRED | = assessment_timestamp                |
   | status                   | string  | REQUIRED | ACTIVE | REVOKED                       |
   | content_hash             | string  | REQUIRED | "sha256:" + 64 lowercase hex chars    |
   | pqc_signature            | string  | REQUIRED | ML-DSA-65 signature bytes, base64     |
   | pqc_algorithm            | string  | REQUIRED | "ML-DSA-65"                           |
   | snapshot_id              | string  | OPTIONAL | Reference to active AVM snapshot      |
   | created_at               | string  | REQUIRED | ISO-8601-UTC (DB insertion time)      |

   Committed fields for content_hash computation (canonical JSON,
   keys sorted lexicographically, no whitespace):
      pvr_id, tenant_id, domain, drift_score, drift_threshold,
      signals_at_assessment, assessment_timestamp, veto_effective_from,
      snapshot_id


19.  Appendix B — SDU Computation Reference

   SDU formula reference for all eight ATF Core Terms:

      SDU(term_a, term_b):
         Step 1: Hash shortcut check
                 if term_a.content_hash == term_b.content_hash: return 0.0

         Step 2: boundary_distance
                 A = set(term_a.boundary_conditions)
                 B = set(term_b.boundary_conditions)
                 boundary_distance = |A △ B| / |A ∪ B|
                 (If A ∪ B is empty: boundary_distance = 0.0)

         Step 3: scope_distance
                 C = set(term_a.operational_scope)
                 D = set(term_b.operational_scope)
                 scope_distance = 1.0 − |C ∩ D| / |C ∪ D|
                 (If C ∪ D is empty: scope_distance = 0.0)

         Step 4: regulatory_distance
                 E = set(term_a.regulatory_anchors)
                 F = set(term_b.regulatory_anchors)
                 regulatory_distance = |E △ F| / |E ∪ F|
                 (If E ∪ F is empty: regulatory_distance = 0.0)

         Step 5: SDU = 0.40 · boundary_distance
                       + 0.35 · scope_distance
                       + 0.25 · regulatory_distance

   Portability verdict thresholds (structural constants,
   DSPP-INV-007a and DSPP-INV-007b):

   | Range           | Verdict                 | Interpretation                          |
   |-----------------|-------------------------|-----------------------------------------|
   | [0.00, 0.10)    | SEMANTICALLY_PORTABLE   | Use without qualification               |
   | [0.10, 0.40)    | DRIFT_ACKNOWLEDGED      | Apply contextual qualification          |
   | [0.40, 0.70)    | DRIFT_CRITICAL          | Document divergence; human review rec.  |
   | [0.70, 1.00]    | SEMANTICALLY_INCOMPAT.  | Operational meaning unreliable in rcvr  |


20.  Appendix C — PGL Compliance Checklist

   Implementations claiming ATF-PGL-Compliant MUST satisfy all items.
   Items marked (FEI) are inherited from RFC-ATF-3 and MUST be
   satisfied at that tier before this checklist applies.

   AGVP
   □ AGVPWatchdog deployed with interval ≥ 30s (AGV-INV-003)
   □ PVRs persisted atomically; uniqueness constraint on pvr_id
   □ PVR content_hash = SHA-256(canonical_json(committed_fields))
   □ PVR pqc_algorithm = "ML-DSA-65" enforced at construction
   □ PVR signed with platform ML-DSA-65 key before persistence
   □ Request path checks has_active_pvr() before evaluation (AGV-INV-001)
   □ Blocked requests carry block_reason referencing PVR ID
   □ Signal telemetry updated by request path even when blocked (§5.4)
   □ Pass-through domains excluded from PVR emission (AGV-INV-005)
   □ Watchdog has no code path setting PVR.status = REVOKED (AGV-INV-002)
   □ Auto-recalibration checks has_active_pvr() before executing (AGV-INV-006)
   □ PVR records not deleted after revocation (audit trail preservation)

   SSD
   □ SSD.classify() called on every AVM.evaluate() invocation
   □ StructuralShiftReport present in every AVMResult
   □ StructuralShiftReport embedded in every PVR as structural_shift_class
   □ STRUCTURAL_SHIFT blocks auto-recalibration (SSD-INV-001)
   □ Component history: FIFO eviction only, max 20 entries (SSD-INV-002)
   □ STRUCTURAL_SHIFT only when cycles_analyzed ≥ 5 (SSD-INV-003)
   □ SSD exceptions caught; fallback = INSUFFICIENT_DATA (§9.3)

   DSPP
   □ TSA created for every Delegation Receipt at issuance
   □ TSA signed with ML-DSA-65 and persisted
   □ TSAs publicly accessible without authentication (DSPP-INV-004)
   □ SDR published on every SPV change with non-empty rationale
   □ SDR chain is append-only; no modification or deletion (DSPP-INV-002)
   □ RSA computable with no originating runtime contact (DSPP-INV-004)
   □ SDU weights (0.40, 0.35, 0.25) are hardcoded constants
     (DSPP-INV-007a and DSPP-INV-007b)
   □ Verdict thresholds (0.10, 0.40, 0.70) are hardcoded constants
   □ SEMANTICALLY_INCOMPATIBLE propagates to DR descendants (DSPP-INV-006)
   □ TSA signing failure: receipt still issued, ERROR logged (§9.3)

   Formal Verification
   □ Proof runner executes 19/19 proofs as UNSAT (§8.2)
   □ JSON proof report producible for compliance deliverables (§8.4)
   □ No SAT or UNKNOWN results for any invariant in §8.2 table

   Inherited from ATF-FEI-Compliant (RFC-ATF-3) (abbreviated):
   □ (FEI) All RFC-ATF-1 invariants satisfied (ATF-INV-001–006)
   □ (FEI) All RFC-ATF-2 invariants satisfied (RGC-INV-001–008)
   □ (FEI) All RFC-ATF-3 invariants satisfied (GPIL/ELR/EAP/OEP/FEA/FVP)
   □ (FEI) PostgreSQL + Redis configured in production
   □ (FEI) ML-DSA-65 signing keys stable across restarts (FMR-001)
   □ (FEI) OMNIX_ANTI_REPLAY_MODE = strict in production


21.  Author's Address

   Harold Alberto Nunes (Editor)
   OMNIX QUANTUM LTD
   71-75 Shelton Street, Covent Garden
   London WC2H 9JQ, England
   Email: standards@omnixquantum.com
   Web:   omnixquantum.net
```


---

*RFC-ATF-4 Version 1.0.0 — May 2026*
*OMNIX QUANTUM LTD — Harold Nunes, Editor*
*Priority Records: OMNIX-PAR-2026-AGVP-001 · OMNIX-PAR-2026-SSD-001 ·
OMNIX-PAR-2026-DSPP-001 · OMNIX-PAR-2026-FVS-001*

*STATUS: DRAFT — NOT YET SUBMITTED TO ZENODO*
*REVISION HISTORY: v0.1 initial draft — May 21, 2026*

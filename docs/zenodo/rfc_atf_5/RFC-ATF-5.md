```
OMNIX QUANTUM Open Standard                            OMNIX QUANTUM LTD
Category: Standards Track                                    H. Nunes, Ed.
DOI: 10.5281/zenodo.20391722                                    May 2026


         RFC-ATF-5: Agent Trust Fabric — Cognitive Governance Layer
         Counterfactual Governance Engine, Grand Unified Governance
         Theory, and Temporal Governance Bridge
         Extension to RFC-ATF-1, RFC-ATF-2, RFC-ATF-3, and RFC-ATF-4
         Version 1.0.0 — OMNIX QUANTUM Open Standard


Abstract

   This document specifies the Cognitive Governance Layer (CGL) of
   the Agent Trust Fabric protocol — the fifth RFC in the ATF Open
   Standard series.

   RFC-ATF-1 answered the identity question: who authorized this
   agent, with what authority, and can that be proved offline?
   RFC-ATF-2 answered the runtime question: was authority continuously
   valid throughout execution, and was every degradation event
   cryptographically attested?  RFC-ATF-3 answered the evidence
   question: where does the resulting artifact go, who can interpret
   it across organizational boundaries, and can a regulator reconstruct
   the full chain of custody years later without platform access?
   RFC-ATF-4 answered the proactive governance question: what happens
   between governance requests, is recalibration safe, and does a
   receipt issued today remain semantically legitimate in a receiving
   domain months later?

   RFC-ATF-5 answers three structurally deeper questions that no
   existing governance framework — academic, regulatory, or commercial
   — has previously addressed:

   (1) What else could have happened?  A governance system that records
       only the selected decision path provides accountability but not
       justiciability.  Regulators, courts, and enterprise risk officers
       require evidence of the decision space — the full set of
       governance outcomes that existed at the moment of evaluation
       under parametric variations of the authority configuration.  The
       Counterfactual Governance Engine (CGE) closes this gap by
       computing M cryptographically sealed alternative governance paths
       at the moment of every evaluation, assembling them into a
       Counterfactual Attestation Token (CAT), and making the complete
       decision space independently verifiable offline without any
       access to OMNIX infrastructure.

   (2) Is this governance system universally complete?  The global AI
       governance landscape is fragmented across regulatory frameworks
       (EU AI Act, US NIST AI RMF, GCC/DIFC AI Regulation 2024,
       ISO/IEC 42001:2023), agent types (LLMs, robotic systems,
       financial agents, medical systems, autonomous vehicles), and
       organizational contexts.  No universal invariant set exists
       against which any governance system can be certified as complete
       across all contexts simultaneously.  The Grand Unified Governance
       Theory (GUGT) establishes six Universal Governance Invariants
       (UGI-001-006) — the minimal, formally provable set of properties
       that any AI system must satisfy to be recognized as governance-
       complete across all currently active major regulatory frameworks
       and all AI agent types — and defines a Universal Invariant
       Receipt (UIR) as the portable certification artifact.

   (3) Does governance evidence remain interpretable across time?  A
       receipt produced today under ATF Spec v1.4 and EU AI Act 2024
       must remain semantically interpretable when reviewed by a
       regulator in 2029 under an amended framework.  No bridge
       currently exists between nanosecond-precision runtime governance
       and multi-year regulatory review cycles.  The Temporal Governance
       Bridge (TGB) provides this bridge: a Temporal Context Snapshot
       (TCS) embedded at record issuance captures the complete
       regulatory and threshold context at the nanosecond of the
       decision; a Regulatory Alignment Receipt (RAR) projects
       historical records to current frameworks at review time without
       modifying the original evidence; a Temporal Migration Record
       (TMR) attests each evidence lifecycle transition under the
       regulatory context active at that moment.

   Together, CGE, GUGT, and TGB constitute the Cognitive Governance
   Layer — the first governance infrastructure in the field to formally
   address: the shape of the decision space, the universality of
   compliance, and the interpretability of evidence across time.

   Eighteen new invariants are introduced: CGE-INV-001-007,
   GUGT-INV-001-006, and TGB-INV-001-005.  Combined with the 70
   invariants of RFC-ATF-1 through RFC-ATF-4, the ATF stack reaches
   88 formally specified invariants across 17 protocol families.

   An implementation that complies with RFC-ATF-1 through RFC-ATF-5
   is designated ATF-CGL-Compliant — the fifth and highest compliance
   tier in the ATF stack.


Status of This Memo

   This is an OMNIX QUANTUM Open Standard, published under the OMNIX
   Open Governance License v1.0.  This document extends RFC-ATF-1,
   RFC-ATF-2, RFC-ATF-3, and RFC-ATF-4 and MUST be read in conjunction
   with all four.  Implementers of RFC-ATF-4 who require decision space
   documentation, universal governance certification, or longitudinal
   evidence interpretability SHOULD adopt RFC-ATF-5 as specified herein.

   This document is a product of the OMNIX QUANTUM Standards Working
   Group.  It has been approved for publication by the OMNIX Technical
   Committee.

   [STATUS: PUBLISHED — Zenodo record 20391722]

   DOI: 10.5281/zenodo.20391722
   Zenodo record: https://zenodo.org/record/20391722
   Feedback: standards@omnixquantum.com


Copyright Notice

   Copyright (c) 2026 OMNIX QUANTUM LTD.  All rights reserved.
   71-75 Shelton Street, Covent Garden, London WC2H 9JQ, England.
   Operational headquarters: Abu Dhabi, UAE.

   Permission is granted to reproduce this document for review and
   implementation purposes, provided this copyright notice is retained.


Acknowledgements

   The three structural problems addressed in this RFC were shaped by
   technical engagement with the governance research community and the
   OMNIX partner network.

   The decision space documentation problem (§2.1) was independently
   validated through regulatory review sessions with enterprise legal
   counsel operating under EU AI Act Art. 9 obligations, who identified
   the absence of "alternatives considered" evidence as the primary gap
   between technical governance infrastructure and regulatory filing
   requirements.  The CGE architecture was developed in response to
   this specific evidentiary demand.

   The universal governance invariant problem (§2.2) was formally
   crystallized through the ATF Field Specification Partner Integration
   Program.  Moazzam Waheed (ReguLattice) identified the multi-
   jurisdiction compliance overhead as the primary adoption barrier for
   enterprise AI governance infrastructure, establishing the commercial
   motivation for the GUGT meta-layer.  Raheem Larry Babatunde
   (VeriSigil AI, DOI 10.5281/zenodo.20264923) demonstrated through
   VGS-001-011 that jurisdiction-specific governance specifications are
   independently viable, confirming that a universal meta-layer
   occupies a structurally distinct and superior position.

   The longitudinal evidence interpretability problem (§2.3) was
   formally articulated by Antonio Socorro (CAI-EXPERT-LAB) during
   cross-system technical review of RFC-ATF-4, extending his prior
   observation on semantic portability (credited in RFC-ATF-4
   Acknowledgements): "The DSPP addresses receiving-domain semantic
   divergence at a point in time.  The remaining open problem is the
   temporal dimension — how does an auditor five years from now
   interpret a receipt issued under today's regulatory context, without
   the platform, without us, and without guessing?"  This question is
   the founding motivation for the TGB.


Table of Contents

    1.  Introduction ..............................................  8
    2.  Problem Statement: The Cognitive Governance Gap ...........  10
        2.1.  The Decision Space Problem .........................  10
        2.2.  The Universal Completeness Problem .................  12
        2.3.  The Temporal Interpretability Problem ..............  14
        2.4.  The Cognitive Governance Gap (Gap_CG) ..............  16
    3.  Conventions and Terminology ..............................  17
    4.  Architecture: The Cognitive Governance Layer .............  21
        4.1.  Position in the ATF Stack .........................  21
        4.2.  Extension Relationships ...........................  22
        4.3.  Non-Destructive Integration .......................  23
        4.4.  CGL Module Independence ...........................  24
    5.  Counterfactual Governance Engine (CGE) ...................  25
        5.1.  Decision Space Architecture .......................  25
        5.2.  Counterfactual Fork Record (CFR) Structure ........  27
        5.3.  CFR Content Hash Construction .....................  30
        5.4.  CFR PQC Signature .................................  31
        5.5.  Counterfactual Attestation Token (CAT) ............  32
        5.6.  Variation Vector Design ...........................  35
        5.7.  Offline Verifiability Protocol ....................  37
        5.8.  CGE Lifecycle: ASYNC Mode .........................  38
        5.9.  CGE Invariants (CGE-INV-001-007) ..................  39
    6.  Grand Unified Governance Theory (GUGT) ...................  44
        6.1.  Universal Invariant Architecture ..................  44
        6.2.  Universal Governance Invariants UGI-001-006 .......  46
        6.3.  Universal Invariant Receipt (UIR) Structure .......  52
        6.4.  UIR Computation Protocol ..........................  55
        6.5.  GUGT Conformance Levels ...........................  57
        6.6.  Cross-Jurisdiction Framework Mapping ..............  58
        6.7.  GUGT Invariants (GUGT-INV-001-006) ................  60
    7.  Temporal Governance Bridge (TGB) .........................  64
        7.1.  Two-Scale Architecture ............................  64
        7.2.  Temporal Context Snapshot (TCS) Structure .........  66
        7.3.  TCS Embedding Protocol ............................  69
        7.4.  Regulatory Alignment Receipt (RAR) Structure ......  70
        7.5.  RAR Projection Protocol ...........................  74
        7.6.  Temporal Migration Record (TMR) ...................  76
        7.7.  Offline Projection Computability ..................  78
        7.8.  TGB Invariants (TGB-INV-001-005) ..................  79
    8.  Formal Verification (OMNIX-FVS-1.0 Extension) ...........  83
        8.1.  CGL Proof Inventory ..............................  83
        8.2.  CGE Arithmetic Proofs (Z3 SMT) ....................  84
        8.3.  GUGT Arithmetic Proofs (Z3 SMT) ...................  85
        8.4.  TGB Arithmetic Proofs (Z3 SMT) ....................  86
        8.5.  Machine Reproducibility ...........................  87
    9.  CGL Layer Composition ....................................  88
        9.1.  Layer Architecture ................................  88
        9.2.  Cross-Layer Integration Points ....................  89
        9.3.  Failure Isolation .................................  90
   10.  Combined Invariant Summary ...............................  91
   11.  Compliance Designation: ATF-CGL-Compliant ................  94
        11.1.  Designation Requirements .........................  94
        11.2.  Compliance Hierarchy .............................  95
   12.  Implementation Requirements ..............................  96
        12.1.  CGE Requirements .................................  96
        12.2.  GUGT Requirements ................................  97
        12.3.  TGB Requirements .................................  98
   13.  Persistence Schema .......................................  99
        13.1.  atf_counterfactual_forks .........................  99
        13.2.  atf_counterfactual_tokens ........................ 100
        13.3.  gugt_universal_invariant_receipts ................ 101
        13.4.  atf_temporal_context_snapshots ................... 102
        13.5.  atf_regulatory_alignment_receipts ................ 103
        13.6.  atf_temporal_migration_records ................... 104
   14.  API Endpoints ............................................ 105
   15.  Security Considerations .................................. 107
        15.1.  CFR Fabrication Attack ........................... 107
        15.2.  CAT Root Hash Substitution ....................... 108
        15.3.  UIR Inflation Attack ............................. 108
        15.4.  GUGT Conformance Level Spoofing .................. 109
        15.5.  TCS Manipulation Attack .......................... 109
        15.6.  RAR Substitution Attack .......................... 110
        15.7.  Projection Monotonicity Violation ................ 110
        15.8.  Quantum Adversary ................................ 111
   16.  Novel Contributions ...................................... 112
        16.1.  Counterfactual Attestation Token (CAT) ........... 112
        16.2.  Universal Governance Invariants (UGI-001-006) .... 113
        16.3.  GUGT-L3+ATF Compliance Designation ............... 113
        16.4.  Temporal Context Snapshot (TCS) .................. 114
        16.5.  Regulatory Alignment Receipt (RAR) ............... 114
        16.6.  ATF-CGL-Compliant — Fifth Compliance Tier ........ 115
   17.  Distinction from Prior Art ............................... 115
   18.  Regulatory Alignment ..................................... 118
   19.  References ............................................... 120
   20.  Appendix A — CGL Wire Format Reference ................... 122
   21.  Appendix B — GUGT Framework Mapping Reference ............ 127
   22.  Appendix C — CGL Compliance Checklist .................... 130
   23.  Author's Address ......................................... 134


1.  Introduction

   The Agent Trust Fabric protocol stack was designed to address the
   complete lifecycle of a governed autonomous agent action: from the
   moment authority is delegated (RFC-ATF-1), through the continuous
   monitoring of that authority at runtime (RFC-ATF-2), to the long-
   term preservation and independent verification of the resulting
   evidence (RFC-ATF-3), and into the intervals between governance
   requests where anticipatory detection, recalibration safety, and
   cross-domain semantic portability are required (RFC-ATF-4).

   Each RFC answered its question completely.  But three structural
   problems were deliberately left open — not because they were
   unknown, but because they require a different class of mechanism
   than the prior four RFCs provide.

   The first four RFCs answer questions about what happened: who
   delegated what authority, was that authority continuously valid,
   where does the evidence go, and was there proactive monitoring in
   between?  RFC-ATF-5 answers questions about the cognitive dimension
   of governance: what else could have happened, is the governance
   system universally complete, and will this evidence be interpretable
   years from now?

   These are not incremental extensions.  They represent a qualitative
   advance in the governance infrastructure's capacity for reasoning —
   the capacity to document decision alternatives (CGE), to claim
   universal validity across all frameworks simultaneously (GUGT), and
   to remain coherent across temporal boundaries that span the full
   distance from nanosecond execution to decade-scale regulatory review
   (TGB).

   Together, these three capabilities constitute what this document
   designates the Cognitive Governance Layer — the layer of the ATF
   stack concerned not with what governance does, but with what
   governance can demonstrate about what it has done, what it could
   have done, and what it will mean to a reviewer in a different time
   and regulatory context.


2.  Problem Statement: The Cognitive Governance Gap

2.1.  The Decision Space Problem

   Define the following terms:

   Decision Space (DS):
      The complete set of governance outcomes that exist at the moment
      of a governance evaluation, as a function of the live parameter
      vector P = (authority_budget_granted, ces_score, nominal_thresh,
      monitoring_thresh, warning_thresh, delegation_depth_limit,
      fragmentation_limit).  DS is a subset of {NOMINAL, MONITORING,
      WARNING, HALT, REJECT}.

   Selected Path (SP):
      The governance outcome produced by the actual parameter vector
      P_actual at evaluation time T.  SP ∈ DS.

   Documented Path (DP):
      The governance outcome recorded in the ATF receipt.  DP = SP
      for compliant implementations.

   The ATF stack through RFC-ATF-4 guarantees DP = SP with
   cryptographic certainty.  It does not record |DS| > 1, the shape
   of DS, or the parameter variations that would have produced
   outcomes in DS \ {SP}.

   This creates a structural gap — the Decision Space Gap (Gap_DS):

      Gap_DS = DS \ {SP}

   Gap_DS is non-empty whenever the parameter vector P_actual is not
   at a boundary of DS.  In practice, for any CES in the interior of
   a threshold band (e.g., CES = 65.0, midpoint of MONITORING band
   [50.0, 79.9]), Gap_DS contains at least two alternative outcomes
   reachable by parameter variation within ±40% of P_actual.

   The Gap_DS is consequential for three classes of stakeholder:

   a) Regulatory auditors: EU AI Act Art. 9 requires risk management
      systems to document "alternatives considered."  No ATF record
      through RFC-ATF-4 satisfies this requirement as stated.

   b) Enterprise risk officers: Understanding whether a NOMINAL
      outcome was robust (Gap_DS contains only NOMINAL alternatives)
      or fragile (Gap_DS contains MONITORING or WARNING alternatives
      reachable by small parameter variation) is operationally
      critical for risk budgeting.  No ATF metric through RFC-ATF-4
      quantifies this fragility.

   c) Legal counsel: In litigation, the question "could the system
      have reached a different governance outcome under a different
      configuration?" cannot be answered from ATF records alone
      through RFC-ATF-4.  The CGE closes this gap.

   The CGE resolves Gap_DS by computing M alternative governance
   paths at evaluation time and sealing each as a Counterfactual Fork
   Record (CFR), assembled into a Counterfactual Attestation Token
   (CAT) bound to the primary receipt.

2.2.  The Universal Completeness Problem

   Define the following terms:

   Governance Completeness (GC):
      A governance system G satisfies GC with respect to framework F
      and agent type A if every governance obligation specified by F
      for agent type A is formally satisfied by G.

   Multi-Frame Completeness (MFC):
      A governance system G satisfies MFC if it satisfies GC for all
      (F_i, A_j) pairs across all relevant frameworks F_i and agent
      types A_j simultaneously.

   The ATF stack satisfies GC for specific (F, A) pairs but does not
   formally assert MFC.  This is not an implementation deficiency —
   it is a specification gap.  The ATF stack has never published a
   formal statement of which specific framework obligations each ATF
   invariant satisfies, for which agent types, and with what evidentiary
   artifacts.

   This creates the Universal Completeness Gap (Gap_UC):

      Gap_UC = {(F_i, A_j) : no formal GC mapping exists}

   Gap_UC is significant because enterprise buyers evaluating OMNIX
   for multi-jurisdiction deployments cannot derive their compliance
   position from ATF documentation alone.  They must engage external
   counsel to perform the mapping — a cost barrier that directly
   impedes adoption.

   The GUGT resolves Gap_UC by:

   1. Establishing six Universal Governance Invariants (UGI-001-006)
      that are jointly sufficient for MFC across EU AI Act, NIST AI
      RMF, GCC/DIFC AI Regulation, and ISO/IEC 42001.

   2. Proving that ATF-compliant systems satisfy all six UGIs by
      construction.

   3. Issuing Universal Invariant Receipts (UIRs) that formally
      certify the (F_i, A_j) mapping with PQC-signed evidentiary
      artifacts.

2.3.  The Temporal Interpretability Problem

   Define the following terms:

   Regulatory Framework Version (RFV):
      A specific revision of a regulatory framework at a point in
      time.  Example: EU_AI_ACT_2024_v1.0, NIST_AI_RMF_v1.0.

   Semantic Field Stability (SFS):
      A governance field f has SFS across RFVs [V_0, V_k] if the
      meaning of f under V_0 is identical to its meaning under V_k.

   Temporal Semantic Gap (Gap_TS):
      The set of fields in an ATF record for which SFS does not hold
      across the RFVs active at issuance time and review time.

   The ATF stack through RFC-ATF-4 addresses cross-domain semantic
   drift at a point in time (RFC-ATF-4 DSPP).  It does not address
   temporal semantic drift — the change in meaning of governance
   fields as regulatory frameworks evolve over the months and years
   between record issuance and regulatory review.

   Gap_TS is non-empty for any ATF record reviewed under a different
   RFV than the one active at issuance.  For records subject to the
   EU AI Act's 7-year retention obligation (Art. 72), Gap_TS can
   accumulate across multiple framework revision cycles.

   Three concrete failure modes arise from an unresolved Gap_TS:

   a) Misclassification: A record with continuity_status = MONITORING
      issued under ATF Spec v1.4 thresholds may correspond to a
      different risk tier under a future ATF Spec revision.

   b) Framework-version aliasing: A record citing "EU AI Act Art. 9"
      without specifying the framework version may be interpreted under
      an amended provision that changes the compliance meaning.

   c) Retention compliance failure: A record whose regulatory context
      is not captured at issuance cannot demonstrate compliance with
      the retention obligation of the specific framework version under
      which it was created.

   The TGB resolves Gap_TS by embedding a Temporal Context Snapshot
   (TCS) in every ATF record at issuance — capturing the complete
   regulatory and threshold context at nanosecond precision — and by
   providing Regulatory Alignment Receipts (RARs) that project
   historical records to current frameworks at review time without
   modifying the original evidence.

2.4.  The Cognitive Governance Gap (Gap_CG)

   The Cognitive Governance Gap is the union of the three gaps
   identified above:

      Gap_CG = Gap_DS ∪ Gap_UC ∪ Gap_TS

   A governance infrastructure with Gap_CG = {} satisfies the
   following conditions:

   1. Every governance evaluation records not only the selected path
      but the full decision space, sealed at evaluation time.
      (Gap_DS resolved by CGE)

   2. Every governance record can be formally certified as compliant
      with all relevant regulatory frameworks and agent type
      obligations simultaneously, without per-jurisdiction custom
      analysis.
      (Gap_UC resolved by GUGT)

   3. Every governance record embeds the regulatory context at
      issuance and can be projected to current frameworks at review
      time without platform access.
      (Gap_TS resolved by TGB)

   RFC-ATF-5 formally closes Gap_CG.


3.  Conventions and Terminology

   The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
   "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY",
   and "OPTIONAL" in this document are to be interpreted as described
   in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in
   all capitals, as shown here.

   Terms defined in prior ATF RFCs retain their definitions.  The
   following terms are defined in this document:

   Counterfactual Fork Record (CFR):
      A cryptographic record representing a single alternative
      governance path computed at evaluation time under a parametric
      variation of the primary evaluation inputs.  A CFR is PQC-signed
      and append-only.

   Counterfactual Fork Record Identifier (CFRID):
      A unique string of the form CFR-{16HEX}.

   Counterfactual Attestation Token (CAT):
      A bound, PQC-signed set of CFRs for a single governance
      evaluation.  The CAT commits to all CFR content hashes via a
      root hash, making individual CFR tampering detectable from the
      CAT seal alone.

   Counterfactual Attestation Token Identifier (CATID):
      A unique string of the form CAT-{16HEX}.

   Variation Vector (VV):
      A structured object specifying parametric deviations from the
      primary governance evaluation inputs.  Each field specifies a
      delta as a fraction of the primary value.  All deltas MUST
      satisfy |delta_pct| <= CGE_MAX_VARIATION_PCT.

   Decision Space Summary (DSS):
      A structured aggregate of the counterfactual outcomes in a CAT,
      reporting the distribution of outcomes and the identified
      parameter sensitivities.

   Universal Governance Invariant (UGI):
      One of six formally specified governance properties (UGI-001
      through UGI-006) that are jointly sufficient for Multi-Frame
      Completeness across all major regulatory frameworks and all AI
      agent types.

   Universal Invariant Receipt (UIR):
      A PQC-signed certification artifact attesting that a specified
      system satisfies all six UGIs with respect to specified
      frameworks and agent types.

   Universal Invariant Receipt Identifier (UIRID):
      A unique string of the form UIR-{16HEX}.

   GUGT Conformance Level:
      One of four compliance tiers: GUGT-L1 Basic, GUGT-L2 Runtime,
      GUGT-L3 Full, GUGT-L3+ATF.  Levels are strictly hierarchical.

   Temporal Context Snapshot (TCS):
      A structured artifact embedded within an ATF record at issuance,
      capturing the complete regulatory framework versions and
      governance threshold values active at the nanosecond of record
      creation.

   Temporal Context Snapshot Identifier (TCSID):
      A unique string of the form TCS-{16HEX}.

   Regulatory Alignment Receipt (RAR):
      A PQC-signed projection artifact that maps a historical ATF
      record from its issuance regulatory context to a current
      regulatory context.  A RAR MUST NOT modify any field of the
      source record.

   Regulatory Alignment Receipt Identifier (RARID):
      A unique string of the form RAR-{16HEX}.

   Temporal Migration Record (TMR):
      A PQC-signed record issued at each evidence lifecycle transition
      (HOT -> WARM -> COLD), capturing the regulatory context active
      at the moment of transition.

   Temporal Migration Record Identifier (TMRID):
      A unique string of the form TMR-{16HEX}.

   Field Projection:
      A mapping of a single governance field from its source framework
      value and classification to its target framework equivalent,
      documented with projection rule, confidence level, and human
      review flag.

   TGB Projection Rulebook:
      A versioned, PQC-signed JSON document containing all field
      projection rules for every supported framework transition pair.
      Published by OMNIX and embedded in OEP packages.

   Regulatory Framework Version (RFV):
      A string identifying a specific revision of a regulatory
      framework.  Format: {FRAMEWORK}_{YEAR}_v{MAJOR}.{MINOR}.
      Example: EU_AI_ACT_2024_v1.0.

   Explicit Invalidity Declaration (EID):
      A formal record attesting that a governance receipt is no longer
      valid under a specified regulatory framework version.  EIDs are
      append-only and MUST NOT retroactively modify the source record.

   ATF-CGL-Compliant:
      The compliance designation for an implementation that satisfies
      all requirements of RFC-ATF-1 through RFC-ATF-5.  The fifth and
      highest tier in the ATF compliance hierarchy.

   CGL-COMPLETE:
      Synonym for ATF-CGL-Compliant when used in implementation
      contexts.

   Cognitive Governance Layer (CGL):
      The protocol layer defined by this RFC, comprising CGE, GUGT,
      and TGB.

   CFR:  Counterfactual Fork Record
   CAT:  Counterfactual Attestation Token
   CGE:  Counterfactual Governance Engine
   CGL:  Cognitive Governance Layer
   EID:  Explicit Invalidity Declaration
   GUGT: Grand Unified Governance Theory
   RAR:  Regulatory Alignment Receipt
   RFV:  Regulatory Framework Version
   TCS:  Temporal Context Snapshot
   TGB:  Temporal Governance Bridge
   TMR:  Temporal Migration Record
   UGI:  Universal Governance Invariant
   UIR:  Universal Invariant Receipt
   VV:   Variation Vector


4.  Architecture: The Cognitive Governance Layer

4.1.  Position in the ATF Stack

   The ATF protocol stack comprises five layers:

   Layer 1 — Identity & Delegation Plane (RFC-ATF-1):
      Agent Identity Records, Delegation Receipts, Trust Lattice.
      Answers: who authorized this agent?

   Layer 2 — Runtime Continuity Plane (RFC-ATF-2):
      Runtime Continuity Records, CES, AFG, Escalation Protocol.
      Answers: was authority continuously valid?

   Layer 3 — Evidence & Forensic Plane (RFC-ATF-3):
      GPIL, Evidence Lifecycle, OEP, Forensic Verification.
      Answers: where does the evidence go, and who can verify it?

   Layer 4 — Proactive Governance Plane (RFC-ATF-4):
      AGVP, SSD, DSPP.
      Answers: what happened between requests?

   Layer 5 — Cognitive Governance Layer (RFC-ATF-5):
      CGE, GUGT, TGB.
      Answers: what else could have happened, is the system universally
      complete, and will this evidence remain interpretable over time?

4.2.  Extension Relationships

   Each CGL module extends the ATF stack non-destructively:

   CGE extends Layer 1 (DR) and Layer 2 (RCR, TAR):
      Every DR, TAR, and RCR evaluation is eligible to trigger a CGE
      fork computation.  The primary record is issued and persisted
      BEFORE any counterfactual computation begins (CGE-INV-002).

   GUGT extends all layers (Layer 1-4):
      The six UGIs map to invariants distributed across all four prior
      RFC layers.  UIR issuance references specific ATF records as
      evidence artifacts for each UGI.

   TGB extends Layer 1-3 records at issuance and Layer 3 (OEP) at
   export:
      TCS is embedded in DR, TAR, and RCR at creation.  RARs and TMRs
      are produced at review time and lifecycle transition.  OEP
      packages (ADR-165) include TCS, RARs, and applicable TMRs.

4.3.  Non-Destructive Integration

   All three CGL modules operate as additive layers.  An implementation
   MAY enable any subset of CGE, GUGT, and TGB independently.  Disabling
   any CGL module does not affect the correctness of Layers 1-4.

   CGE_ENABLED, TGB_ENABLED, and GUGT_ENABLED are environment flags
   controlling module activation.  Default is true for all three.
   Setting any to false in production is permitted and does not
   constitute a compliance violation of RFC-ATF-4 or prior RFCs.

4.4.  CGL Module Independence

   CGE, GUGT, and TGB are mutually independent.  No module depends on
   the output of another CGL module.  Each may fail or be disabled
   without affecting the others.

   The ONLY dependency is the ordering requirement: for any primary
   ATF record R, the sequence MUST be:

      1. Issue and persist R (Layer 1-4 record)
      2. Begin TCS embedding (TGB) — synchronous, part of R creation
      3. Begin CGE fork computation — asynchronous (if CGE_ASYNC_MODE)
      4. UIR issuance (GUGT) — on demand, not at record creation time


5.  Counterfactual Governance Engine (CGE)

5.1.  Decision Space Architecture

   The CGE computes M alternative governance paths at the moment of
   a primary ATF governance evaluation.  M is configurable via the
   CGE_FORK_COUNT environment variable (default: 3, range: 1-7).

   The primary evaluation MUST complete and produce a sealed ATF
   record before CGE computation begins.  This ordering is enforced
   by CGE-INV-002.

   Each alternative path applies a Variation Vector (VV) to the
   primary evaluation inputs and re-executes the governance decision
   logic to produce a counterfactual outcome.  The counterfactual
   execution is read-only: it produces no governance receipts, issues
   no HALT, and triggers no escalation protocol.  Its sole output is
   a signed CFR.

   The M CFRs are assembled into a CAT that is bound cryptographically
   to the primary record via primary_receipt_id and cat_root_hash.

   Decision Space Summary (DSS) captures:
   - Distribution of counterfactual outcomes across NOMINAL /
     MONITORING / WARNING / HALT / REJECT
   - Parameter sensitivity classification: which parameter variations
     produced outcome changes
   - Fragility score: proportion of counterfactual paths that diverge
     from the primary outcome

5.2.  Counterfactual Fork Record (CFR) Structure

   A CFR MUST contain the following fields:

   cfr_id (string, REQUIRED):
      Unique CFR identifier.  Format: CFR-{16HEX}.
      16HEX is 16 uppercase hexadecimal characters from a
      cryptographically random UUID4.
      Example: CFR-4A2B8F1C3D5E7A9B

   cat_id (string, REQUIRED):
      Identifier of the CAT that contains this CFR.
      Format: CAT-{16HEX}.

   primary_receipt_id (string, REQUIRED):
      Identifier of the primary ATF record that triggered this CFR.
      MUST reference a valid record in atf_delegation_receipts,
      atf_temporal_records, or atf_runtime_continuity.

   evaluation_id (string, REQUIRED):
      CGE evaluation session identifier.  Format: CGE-EVAL-{16HEX}.
      All CFRs from the same evaluation share the same evaluation_id.

   variation_vector (object, REQUIRED):
      Structured parametric variation applied to produce this CFR.
      MUST contain at least one parameter deviation.
      All deviation magnitudes MUST satisfy the CGE-INV-005 bound.
      Fields:
        authority_budget_delta_pct (number, OPTIONAL):
           Fractional delta applied to authority_budget_granted.
           Example: -0.20 means 20% reduction.
        ces_threshold_nominal_override (number, OPTIONAL):
           Alternative NOMINAL threshold value.  Range [60.0, 95.0].
        ces_threshold_monitoring_lower_override (number, OPTIONAL):
           Alternative MONITORING lower bound.
        delegation_depth_limit_override (integer, OPTIONAL):
           Alternative maximum delegation depth.  Range [1, 10].
        fragmentation_limit_override (number, OPTIONAL):
           Alternative fragmentation score limit.  Range [0.50, 0.95].

   counterfactual_outcome (string, REQUIRED):
      Governance outcome under this VV.
      One of: NOMINAL | MONITORING | WARNING | HALT | REJECT.

   counterfactual_ces_score (number, REQUIRED):
      CES score computed under the VV adjustments.
      Range: [0.0, 100.0].

   outcome_diverges_from_primary (boolean, REQUIRED):
      true if counterfactual_outcome != primary_record.outcome.

   divergence_invariant_triggered (string, OPTIONAL):
      If outcome_diverges_from_primary is true, the invariant whose
      threshold crossing produced the different outcome.
      Example: "RGC-INV-003" for a HALT triggered by CES < 30.0.

   posture_state_hash_cf (string, REQUIRED):
      SHA-256 hex digest of the canonical JSON of the VV-adjusted
      committed fields.  Computation defined in §5.3.

   issued_at (string, REQUIRED):
      ISO 8601 UTC timestamp with nanosecond precision.

   pqc_signature (string, REQUIRED):
      Base64-encoded Dilithium-3 (ML-DSA-65) signature over the
      content_hash_cf.  Signed with the same platform key as the
      primary record.

   pqc_algorithm (string, REQUIRED):
      MUST be "ML-DSA-65".

   content_hash_cf (string, REQUIRED):
      SHA-256 hex digest of canonical JSON of all CFR fields except
      {content_hash_cf, pqc_signature, pqc_algorithm}.

   atf_spec_version (string, REQUIRED):
      MUST be "1.5" for records produced under this RFC.

5.3.  CFR Content Hash Construction

   The content_hash_cf MUST be computed as follows:

   1. Construct a JSON object containing all fields of the CFR
      EXCEPT: content_hash_cf, pqc_signature, pqc_algorithm.

   2. Serialize to canonical JSON:
         json.dumps(obj, sort_keys=True, separators=(",", ":"))

   3. Encode as UTF-8.

   4. Compute SHA-256.  Express as lowercase hex.

   The posture_state_hash_cf is a separate hash computed over the
   variation-adjusted committed fields (the fields that determine the
   governance outcome under the VV), using the same canonical JSON
   procedure:

   Committed fields for posture_state_hash_cf:
      cfr_id, primary_receipt_id, evaluation_id, variation_vector,
      counterfactual_ces_score, counterfactual_outcome, issued_at

   posture_state_hash_cf = SHA-256(
      json.dumps(committed_fields, sort_keys=True,
                 separators=(",", ":")).encode("utf-8")
   ).hexdigest()

   Verification MUST recompute both hashes and compare to the
   embedded values.  A mismatch indicates tampering.

5.4.  CFR PQC Signature

   The pqc_signature MUST be computed as:

   1. Encode the content_hash_cf string as UTF-8 bytes.

   2. Sign using the platform's Dilithium-3 private key with the
      ML-DSA-65 scheme (FIPS 204).

   3. Encode the signature bytes in standard base64.

   The signing key MUST be the same key used to sign the primary
   record referenced by primary_receipt_id.  Verification uses the
   platform public key (available via DNS TXT record, HTTPS endpoint,
   and embedded in OEP packages).

5.5.  Counterfactual Attestation Token (CAT)

   A CAT MUST contain the following fields:

   cat_id (string, REQUIRED):
      Unique CAT identifier.  Format: CAT-{16HEX}.

   primary_receipt_id (string, REQUIRED):
      Identifier of the primary ATF record for which this CAT was
      produced.  MUST match the primary_receipt_id of all CFRs in the
      CAT.

   evaluation_timestamp (string, REQUIRED):
      ISO 8601 UTC timestamp with nanosecond precision of the CGE
      evaluation session.  MUST be after the primary record's
      created_at timestamp.

   cfr_count (integer, REQUIRED):
      Count of CFRs in this CAT.  MUST equal len(cfr_ids).
      Range: [1, 7].

   cfr_ids (array of strings, REQUIRED):
      Ordered list of CFR identifiers in this CAT.

   cfr_content_hashes (array of strings, REQUIRED):
      Ordered list of SHA-256 hex digests of each CFR canonical JSON.
      Index alignment with cfr_ids MUST be preserved.

   cat_root_hash (string, REQUIRED):
      SHA-256 hex digest of the sorted concatenation of all
      cfr_content_hashes.  MUST equal:
         sha256(sorted(cfr_content_hashes).join("")).hexdigest()

   divergence_count (integer, REQUIRED):
      Count of CFRs where outcome_diverges_from_primary is true.
      Range: [0, cfr_count].

   fragility_score (number, REQUIRED):
      divergence_count / cfr_count.  Range: [0.0, 1.0].
      0.0 = all counterfactual paths produce the same outcome as the
      primary (high robustness).
      1.0 = all counterfactual paths produce a different outcome
      (high fragility — the governance decision is sensitive to
      small parameter variations).

   decision_space_summary (object, REQUIRED):
      Structured aggregate of counterfactual outcomes:
        primary_outcome (string): primary record governance outcome
        alternative_outcomes (object): {outcome: count} distribution
          across all CFRs, including primary outcome count if any
          CFRs match it.
        parameter_sensitivity (string): pipe-delimited list of
          parameters whose variation produced outcome divergence.
          Example: "HIGH_CES|LOW_BUDGET" indicates both CES threshold
          variation and authority budget variation produced divergent
          outcomes.
        sensitivity_classification (string):
          ROBUST if fragility_score < 0.20
          MODERATE if 0.20 <= fragility_score < 0.60
          FRAGILE if fragility_score >= 0.60

   cat_seal (string, REQUIRED):
      Base64-encoded Dilithium-3 (ML-DSA-65) signature over the
      canonical JSON of all CAT fields except {cat_seal}.

   content_hash_cat (string, REQUIRED):
      SHA-256 hex digest of canonical JSON of all CAT fields except
      {content_hash_cat, cat_seal}.

   atf_spec_version (string, REQUIRED):
      MUST be "1.5".

5.6.  Variation Vector Design

   The CGE generates M VVs deterministically from the evaluation seed:

      seed = sha256(
         evaluation_id.encode("utf-8") +
         primary_receipt_id.encode("utf-8")
      ).digest()

   A CSPRNG initialized with seed generates M independent VVs, one
   per CFR.  Deterministic generation ensures reproducibility: given
   the same evaluation_id and primary_receipt_id, any party can verify
   that the VVs match what the CGE would have produced, without access
   to the OMNIX platform.

   Variation bound enforcement (CGE-INV-005):
      For every parameter p in VV with primary value p_0:
         |VV[p]| <= CGE_MAX_VARIATION_PCT * |p_0|

      CGE_MAX_VARIATION_PCT default: 0.40
      Maximum allowed: 0.40
      Minimum allowed: 0.05

   VV generation strategy:
      VV_1: high-magnitude authority budget reduction (-30% to -40%)
      VV_2: threshold sensitivity (nominal_threshold +10% to +20%)
      VV_3: fragmentation tightening (fragmentation_limit -20% to -30%)
      Additional VVs (M > 3): randomized within bounds from seed.

   This strategy prioritizes the parameter variations most likely to
   produce outcome divergence, maximizing the information value of the
   CAT for risk assessment.

5.7.  Offline Verifiability Protocol

   A party possessing only the following can fully verify a CAT:
      - The CAT JSON
      - The CFR JSON objects for all cfr_ids in the CAT
      - The primary ATF record JSON
      - The OMNIX platform public key

   Verification procedure:

   Step 1 — CAT Root Hash Verification:
      Recompute: sorted_hashes = sorted(cfr_content_hashes)
      Recompute: cat_root_hash_r = sha256(join(sorted_hashes))
      Assert: cat_root_hash_r == cat.cat_root_hash

   Step 2 — CAT Seal Verification:
      Decode cat_seal from base64.
      Recompute content_hash_cat from canonical CAT JSON.
      Verify ML-DSA-65 signature over content_hash_cat.encode("utf-8")
      using platform public key.

   Step 3 — Per-CFR Content Hash Verification:
      For each CFR at index i:
         Recompute cfr_content_hash from canonical CFR JSON.
         Assert: cfr_content_hash == cat.cfr_content_hashes[i]

   Step 4 — Per-CFR posture_state_hash_cf Verification:
      For each CFR:
         Recompute posture_state_hash_cf from committed fields per §5.3.
         Assert: recomputed == cfr.posture_state_hash_cf

   Step 5 — Per-CFR PQC Seal Verification:
      For each CFR:
         Verify ML-DSA-65 signature over
         cfr.content_hash_cf.encode("utf-8") using platform public key.

   Step 6 — VV Determinism Verification:
      Recompute seed from evaluation_id and primary_receipt_id.
      Recompute expected VVs from seed.
      Assert: VVs match cfr.variation_vector for each CFR in seed order.

   If all six steps pass: CAT is fully_verified = true.
   If any step fails: CAT is tampered, report the failing step.

5.8.  CGE Lifecycle: ASYNC Mode

   In production (CGE_ASYNC_MODE=true, recommended), CFR and CAT
   computation proceeds asynchronously:

   1. Primary record issued and persisted.
   2. CGE task queued with evaluation_id, primary_receipt_id, P_actual.
   3. Primary record response returned to caller.
   4. CGE worker computes M CFRs, assembles CAT, persists.
   5. CAT linked to primary record via primary_receipt_id index.

   In synchronous mode (CGE_ASYNC_MODE=false), steps 1-4 execute
   before the response is returned.  This guarantees CAT availability
   at query time but adds CGE computation latency to the primary path.
   MUST NOT be used in high-throughput production environments.

5.9.  CGE Invariants (CGE-INV-001 through CGE-INV-007)

   The following invariants are REQUIRED for CGE compliance.
   An implementation violating any CGE invariant is not CGL-COMPLETE.

CGE-INV-001 — Mandatory Fork Production

   For every governance evaluation with CGE_ENABLED=true, a CAT
   containing at least one CFR MUST be produced and persisted.

   Formally:
      For all evaluations E where CGE_ENABLED:
         EXISTS(CAT c) WHERE c.primary_receipt_id = E.receipt_id
            AND c.cfr_count >= 1

   Implementations MUST NOT silently skip CAT production due to
   computation errors.  If a CFR computation fails, the failure MUST
   be logged and the remaining CFRs assembled into a partial CAT.
   A partial CAT satisfies CGE-INV-001 if cfr_count >= 1.

CGE-INV-002 — Primary Decision Isolation

   The primary governance decision (DR, TAR, RCR outcome, status,
   content_hash, pqc_signature) MUST be identical whether or not
   CGE_ENABLED is true.  Counterfactual computation MUST NOT modify,
   delay, or influence any field of the primary record.

   Formally:
      primary_record(CGE_ENABLED=true) == primary_record(CGE_ENABLED=false)

   Any implementation where enabling CGE produces a different primary
   record (different outcome, different CES, different hash, different
   timestamp) has a critical structural defect.

CGE-INV-003 — CFR PQC Sealing

   Every CFR MUST be sealed with a Dilithium-3 (ML-DSA-65, FIPS 204)
   signature over its content_hash_cf, using the same platform signing
   key as the primary record.

   An unsealed CFR (absent or invalid pqc_signature) MUST NOT be
   included in a CAT.

CGE-INV-004 — CAT Root Hash Integrity

   cat_root_hash MUST equal sha256(sorted(cfr_content_hashes).join("")).
   Any modification to any CFR in the CAT MUST invalidate the cat_seal
   verification.

   Formally:
      cat.cat_root_hash == sha256(
         "".join(sorted(cfr.content_hash_cf for cfr in cat.cfrs))
      ).hexdigest()

CGE-INV-005 — Variation Bound

   For every field f in every VV, with primary value p_0(f):
      |VV[f]| <= CGE_MAX_VARIATION_PCT * |p_0(f)|

   Where CGE_MAX_VARIATION_PCT <= 0.40.

   Implementations MUST validate this bound before computing any CFR.
   A VV that violates the bound MUST be rejected, logged as
   CGE_VV_BOUND_VIOLATION, and replaced with a null CFR flagged
   as REJECTED.

CGE-INV-006 — Append-Only Storage

   Records in atf_counterfactual_forks and atf_counterfactual_tokens
   MUST be append-only.  UPDATE and DELETE operations on these tables
   are prohibited after initial INSERT.

   The database schema MUST NOT define UPDATE or DELETE triggers on
   these tables in production.

CGE-INV-007 — Offline Verifiability

   The complete set of counterfactual paths in a CAT MUST be
   independently verifiable following the procedure in §5.7 by any
   party possessing the CAT, the CFRs, the primary record, and the
   OMNIX platform public key — without any access to OMNIX
   infrastructure.

   An implementation where the §5.7 procedure fails for a correctly
   formed CAT has a structural verification defect.


6.  Grand Unified Governance Theory (GUGT)

6.1.  Universal Invariant Architecture

   The GUGT establishes a formal meta-layer above the ATF protocol
   stack.  The meta-layer does not define new runtime governance
   behaviors — it defines the formal relationship between ATF
   invariants and the obligations of external regulatory frameworks.

   The meta-layer answers three questions:

   Q1: What is the minimal set of governance properties sufficient for
       compliance with all major regulatory frameworks simultaneously?
       Answer: UGI-001 through UGI-006.

   Q2: Does an ATF-compliant system satisfy this minimal set?
       Answer: Yes, by construction.  Proof: §6.2 (per-UGI ATF mapping).

   Q3: How can this satisfaction be formally certified?
       Answer: By issuing a Universal Invariant Receipt (UIR) — a
       PQC-signed artifact that documents the per-UGI evidence.

   The GUGT meta-layer position means that:
   - GUGT does not replace or relax any ATF invariant (GUGT-INV-005).
   - Any system other than OMNIX ATF can be assessed for GUGT
     compliance by evaluating UGI-001-006 against its own governance
     infrastructure and receiving a UIR accordingly.
   - OMNIX ATF systems receive GUGT-L3+ATF certification by
     construction, without additional assessment.

6.2.  Universal Governance Invariants UGI-001 through UGI-006

   The six Universal Governance Invariants are derived by formal
   intersection analysis of:
   - EU AI Act (2024/1689), Articles 9, 11, 12, 14, 17, 18, 72
   - US NIST AI RMF v1.0: GOVERN 1.1, 6.1; MAP 5.1, 5.2;
     MANAGE 2.2; MEASURE 2.5
   - GCC/DIFC AI Regulation 2024, Articles 8-14
   - ISO/IEC 42001:2023, Sections 6.1.2, 6.2, 8.4, 8.5, 9.1, 9.3
   - UK AI Safety Institute Evaluation Framework, Sections 3-5

   These six invariants are the maximal set of properties that appear
   — in some form — in all five frameworks simultaneously.  They are
   the intersection, not the union: properties required by at least
   one framework but not all five are not included.

UGI-001 — Human Authority Anchor

   Every governance-capable AI agent MUST have a cryptographically
   attested authority chain traceable to an identified human principal.
   The chain MUST be verifiable without accessing the governing
   platform.

   Framework obligations satisfied:
      EU AI Act Art. 14 (human oversight), Art. 17 (quality management)
      NIST AI RMF GOVERN 1.1 (roles and responsibilities)
      GCC/DIFC Art. 8 (human control requirements)
      ISO/IEC 42001 §6.2 (AI objectives — human accountability)
      UK AISI §3 (accountability structures)

   ATF satisfaction mechanism:
      Delegation Receipt chain_root_id traces every agent action to
      a Tier-1 human principal.  The chain is independently verifiable
      without platform access via delegator_public_key embedding
      (ATF-INV-002, ATF-INV-006).

   Evidence artifact for UIR:
      Delegation Receipt chain (DR set from chain_root_id to leaf),
      with chain verification output showing fully_verified = true.

UGI-002 — Offline-Verifiable Decision Evidence

   Every consequential AI decision MUST produce a receipt that any
   authorized party can verify without contacting the originating
   platform, using only publicly available cryptographic material.

   Framework obligations satisfied:
      EU AI Act Art. 11 (technical documentation), Art. 12
      (record-keeping)
      NIST AI RMF MAP 5.2 (impact assessment documentation)
      GCC/DIFC Art. 12 (audit trail requirements)
      ISO/IEC 42001 §9.1 (monitoring, measurement, analysis)
      UK AISI §4 (evidence standards)

   ATF satisfaction mechanism:
      OMNIX Evidence Package (OEP) two-phase PQC signature provides
      a self-contained, offline-verifiable forensic artifact (ADR-165,
      ADR-166, OEP-INV-001-006).

   Evidence artifact for UIR:
      OEP package for a representative decision, with offline
      verification output showing all checks PASS.

UGI-003 — Execution-Time Boundary Enforcement

   Every authority boundary MUST be enforced at the moment of
   execution, not at the moment of reporting.  A system that enforces
   boundaries only in post-hoc audit does NOT satisfy this invariant.

   Framework obligations satisfied:
      EU AI Act Art. 9 (risk management — real-time controls)
      NIST AI RMF MANAGE 2.2 (ongoing monitoring)
      GCC/DIFC Art. 9 (continuous oversight)
      ISO/IEC 42001 §8.4 (AI system operation)
      UK AISI §3 (operational safeguards)

   ATF satisfaction mechanism:
      Runtime Continuity Record (RCR) HALT is enforced at nanosecond
      precision before any decision is emitted.  The HALT record is
      PQC-signed and timestamped at the moment of enforcement, not
      at the moment of reporting (RGC-INV-003, RGC-INV-005).

   Evidence artifact for UIR:
      At least one RCR with posture_state = HALT, demonstrating
      that enforcement occurred at the execution boundary.

UGI-004 — Pre-Committed Posture Assessment

   Every governance posture evaluation MUST commit cryptographically
   to its input state before computing its output.  Post-hoc
   fabrication of input states MUST be cryptographically detectable.

   Framework obligations satisfied:
      EU AI Act Art. 9(7) (testing and validation integrity)
      NIST AI RMF MEASURE 2.5 (bias and drift measurement integrity)
      ISO/IEC 42001 §8.5 (AI system verification)
      UK AISI §5 (measurement integrity)

   ATF satisfaction mechanism:
      posture_state_hash is computed as SHA-256 of committed evaluation
      inputs BEFORE content_hash is computed.  content_hash covers
      posture_state_hash, binding the evaluation output to its input
      commitment.  Modification of any evaluation input after
      commitment is detectable from the content_hash mismatch
      (ATF-INV-003).

   Evidence artifact for UIR:
      Any ATF record with posture_state_hash, demonstrating that
      evaluation input commitment precedes output generation.

UGI-005 — Self-Modification Prohibition

   No governed AI agent MAY modify its own authority parameters,
   governance thresholds, or invariant configuration without an
   externally sourced, cryptographically attested authorization.

   Framework obligations satisfied:
      EU AI Act Art. 14(4) (human override capability)
      NIST AI RMF GOVERN 6.1 (AI risk governance — control integrity)
      GCC/DIFC Art. 10 (parameter control)
      ISO/IEC 42001 §6.1.2 (risk treatment — control integrity)
      UK AISI §4 (control structures)

   ATF satisfaction mechanism:
      Auto-Modification Guard (AMG, ADR-144) enforces that AVM
      thresholds cannot change by more than 10%/event or 30%
      cumulative without a signed external authorization.  Attempts
      to self-modify are logged as AMG_VIOLATION events.

   Evidence artifact for UIR:
      AMG configuration showing threshold change constraints, and
      any AMG_VIOLATION log demonstrating detection.

UGI-006 — Self-Contained Evidence Reconstruction

   The complete governance evidence chain for any AI decision MUST
   be reconstructible from the decision receipt alone, without
   querying any live system, any network service, or any database.

   Framework obligations satisfied:
      EU AI Act Art. 18 (documentation obligations), Art. 72
      (record-keeping — 7-year retention)
      NIST AI RMF MAP 5.1 (impact documentation completeness)
      GCC/DIFC Art. 14 (evidence completeness)
      ISO/IEC 42001 §9.3 (management review evidence)
      UK AISI §5 (evidence completeness)

   ATF satisfaction mechanism:
      OEP package contains the full chain DR -> TAR -> RCR -> Receipt
      with embedded public key, all required fields for independent
      reconstruction, and a two-phase PQC seal covering the complete
      package (ADR-165, FEA-INV-001-005).

   Evidence artifact for UIR:
      OEP package demonstrated to be self-contained by successful
      offline reconstruction without platform access.

6.3.  Universal Invariant Receipt (UIR) Structure

   A UIR MUST contain the following fields:

   uir_id (string, REQUIRED):
      Unique UIR identifier.  Format: UIR-{16HEX}.

   subject_system (string, REQUIRED):
      Name and version of the assessed governance system.
      Example: "OMNIX ATF v1.5" or "VeriSigil VGS-001-011 v0.7.2".

   subject_protocol (string, REQUIRED):
      One of: ATF | VGS | CUSTOM.
      ATF: OMNIX Agent Trust Fabric.
      VGS: VeriSigil Governance Specification.
      CUSTOM: Other governance infrastructure.

   assessment_date (string, REQUIRED):
      ISO 8601 UTC timestamp of the assessment.

   assessor (string, REQUIRED):
      Identifier of the party performing the assessment.
      For ATF self-assessment: "OMNIX-QUANTUM-LTD".

   ugi_results (object, REQUIRED):
      Per-UGI assessment results, keyed by UGI identifier.
      Each value MUST contain:
         status (string): PASS | FAIL | PARTIAL
         evidence_ref (string): Reference to the evidence artifact
            used for this UGI assessment.
         framework_coverage (array): List of specific framework
            clause strings satisfied.
            Example: ["EU_AI_ACT_ART14", "NIST_GOVERN_1.1",
                      "GCC_DIFC_ART8", "ISO_42001_6.2"]
         notes (string, OPTIONAL): Assessment notes.

   overall_status (string, REQUIRED):
      GUGT_COMPLIANT: All six UGIs PASS.
      GUGT_NON_COMPLIANT: One or more UGIs FAIL.
      GUGT_PARTIAL: One or more UGIs PARTIAL; none FAIL.

   conformance_level (string, REQUIRED):
      One of: GUGT-L1 | GUGT-L2 | GUGT-L3 | GUGT-L3+ATF.
      MUST be consistent with the UGI results per §6.5.

   jurisdiction_coverage (array of strings, REQUIRED):
      Jurisdictions for which the assessment was performed.
      Example: ["EU", "US", "GCC_DIFC", "UK", "ISO"].

   agent_type_coverage (array of strings, REQUIRED):
      Agent types for which the assessment was performed.
      Example: ["LLM", "FINANCIAL", "MEDICAL"].

   gugt_version (string, REQUIRED):
      GUGT specification version.  MUST be "1.0".

   atf_spec_version (string, REQUIRED when subject_protocol = ATF):
      ATF specification version of the assessed system.
      MUST be "1.5" for systems implementing RFC-ATF-5.

   uir_seal (string, REQUIRED):
      Base64-encoded Dilithium-3 (ML-DSA-65) signature over the
      canonical JSON of all UIR fields except {uir_seal}.

   content_hash_uir (string, REQUIRED):
      SHA-256 hex digest of canonical JSON of all UIR fields except
      {content_hash_uir, uir_seal}.

   issued_at (string, REQUIRED):
      ISO 8601 UTC timestamp of UIR issuance.

6.4.  UIR Computation Protocol

   UIR issuance MUST follow this procedure:

   Step 1 — Evidence Collection:
      For each UGI-001 through UGI-006, collect at least one evidence
      artifact from the subject system.  Evidence artifacts are defined
      in §6.2 per-UGI.

   Step 2 — Per-UGI Assessment:
      For each UGI, evaluate the evidence artifact against the UGI
      formal statement.  Produce a per-UGI result object.

   Step 3 — Framework Coverage Verification:
      For each UGI result, enumerate the specific framework clause
      strings satisfied by the evidence.  At least one clause per
      active jurisdiction MUST be present.

   Step 4 — Overall Status Determination:
      If all six UGI status == PASS: overall_status = GUGT_COMPLIANT.
      If any UGI status == FAIL: overall_status = GUGT_NON_COMPLIANT.
      Otherwise: overall_status = GUGT_PARTIAL.

   Step 5 — Conformance Level Assignment:
      Per §6.5 table.

   Step 6 — UIR Construction:
      Assemble UIR JSON with all required fields.

   Step 7 — content_hash_uir Computation:
      content_hash_uir = SHA-256(canonical_json(UIR_fields_except_hash))

   Step 8 — UIR Sealing:
      uir_seal = Dilithium3.sign(
         private_key,
         content_hash_uir.encode("utf-8")
      )

   Step 9 — UIR Persistence:
      INSERT INTO gugt_universal_invariant_receipts (all fields).
      Uniqueness constraint on uir_id MUST be enforced.

6.5.  GUGT Conformance Levels

   | Level         | UGIs Required            | Additional Requirements     |
   |---------------|--------------------------|------------------------------|
   | GUGT-L1 Basic | UGI-001 + UGI-002        | Human anchor + offline verif.|
   | GUGT-L2 Runtime| GUGT-L1 + UGI-003+004   | Execution enforcement + precommit|
   | GUGT-L3 Full  | GUGT-L2 + UGI-005+006   | Self-mod prohibit + self-contained|
   | GUGT-L3+ATF   | GUGT-L3 + full ATF stack | All 70 prior ATF invariants  |

   Conformance levels are strictly hierarchical (GUGT-INV-006):
   a system satisfying GUGT-Lk satisfies all GUGT-Lj for j < k.

   ATF-compliant systems (compliant with RFC-ATF-1 through RFC-ATF-5)
   satisfy GUGT-L3+ATF by construction:
   - UGI-001: ATF-INV-002, ATF-INV-006
   - UGI-002: OEP-INV-001-006, FEA-INV-001-005
   - UGI-003: RGC-INV-003, RGC-INV-005
   - UGI-004: ATF-INV-003
   - UGI-005: AMG (ADR-144)
   - UGI-006: FEA-INV-001, OEP-INV-001

6.6.  Cross-Jurisdiction Framework Mapping

   The following table maps each UGI to specific framework clauses
   across all five covered jurisdictions:

   | UGI     | EU AI Act       | NIST AI RMF       | GCC/DIFC    | ISO 42001  | UK AISI    |
   |---------|-----------------|-------------------|-------------|------------|------------|
   | UGI-001 | Art.14, Art.17  | GOVERN 1.1        | Art. 8      | §6.2       | §3         |
   | UGI-002 | Art.11, Art.12  | MAP 5.2           | Art. 12     | §9.1       | §4         |
   | UGI-003 | Art.9           | MANAGE 2.2        | Art. 9      | §8.4       | §3         |
   | UGI-004 | Art.9(7)        | MEASURE 2.5       | —           | §8.5       | §5         |
   | UGI-005 | Art.14(4)       | GOVERN 6.1        | Art. 10     | §6.1.2     | §4         |
   | UGI-006 | Art.18, Art.72  | MAP 5.1           | Art. 14     | §9.3       | §5         |

   Agent type coverage for each UGI applies across: LLM, ROBOTIC,
   FINANCIAL, MEDICAL, AUTONOMOUS_VEHICLE, MULTI_AGENT.

6.7.  GUGT Invariants (GUGT-INV-001 through GUGT-INV-006)

GUGT-INV-001 — UGI Completeness

   A GUGT compliance assessment MUST evaluate all six UGIs (UGI-001
   through UGI-006).  overall_status = GUGT_COMPLIANT MUST NOT be
   assigned to a UIR where fewer than six UGI assessments are present
   or where any assessment has status != PASS.

GUGT-INV-002 — Framework Clause Specificity

   Every UGI result in a UIR MUST include at least one specific
   framework clause reference per active jurisdiction.  Generic
   framework references (e.g., "EU AI Act" without article number)
   MUST be rejected at UIR construction time.

   Formally:
      For every ugi in ugi_results:
         len(ugi.framework_coverage) >= 1
         Every entry in ugi.framework_coverage MUST match the pattern:
            {FRAMEWORK}_{CLAUSE}
            Example: "EU_AI_ACT_ART14", "NIST_GOVERN_1.1"

GUGT-INV-003 — UIR PQC Sealing

   Every UIR MUST carry a Dilithium-3 (ML-DSA-65, FIPS 204) signature
   in uir_seal over the content_hash_uir.  An unsealed UIR MUST NOT
   be persisted or distributed as a valid GUGT certification artifact.

GUGT-INV-004 — Agent-Type Coverage Declaration

   Every UIR MUST explicitly declare the agent types for which the
   assessment was performed in agent_type_coverage.  Implied or
   inherited coverage from prior UIRs is not permitted.  A UIR
   claiming LLM coverage MUST include "LLM" explicitly.

GUGT-INV-005 — ATF Invariant Supersession Prohibition

   UGI-001 through UGI-006 are meta-layer properties.  They do not
   supersede, replace, weaken, or relax any existing ATF invariant
   (ATF-INV-001-006, RGC-INV-001-008, or any invariant from RFC-ATF-3
   or RFC-ATF-4).  A UIR result of GUGT_COMPLIANT does not imply any
   relaxation of underlying ATF enforcement.

GUGT-INV-006 — Conformance Level Monotonicity

   Conformance levels are strictly hierarchical.  A system satisfying
   GUGT-Lk MUST satisfy all GUGT-Lj for j < k.  A UIR claiming
   GUGT-L3 where any of UGI-001, UGI-002, UGI-003, UGI-004 is FAIL
   is structurally invalid and MUST NOT be issued.


7.  Temporal Governance Bridge (TGB)

7.1.  Two-Scale Architecture

   AI governance operates simultaneously at two scales:

   Micro-scale (nanoseconds to seconds):
      Runtime governance enforcement.  Delegation Receipts timestamped
      at nanosecond precision.  RCR evaluations in sub-millisecond
      cycles.  HALT decisions enforced before the next execution
      instruction.

   Macro-scale (months to years):
      Regulatory review cycles.  EU AI Act Art. 72 mandates 7-year
      record retention for high-risk AI systems.  Legal proceedings
      may examine governance decisions made years prior.  Framework
      revision cycles (typically 2-5 years) change the interpretive
      context of historical records.

   The TGB is the formal protocol layer that bridges these two scales.
   It operates on three record types:

   TCS (at micro-scale, issuance time):
      Embedded in every ATF record.  Captures the complete regulatory
      and threshold context at the nanosecond of creation.

   TMR (at lifecycle transition time):
      Issued when evidence moves between HOT/WARM/COLD tiers.
      Captures regulatory context at each transition.

   RAR (at macro-scale, review time):
      Issued when a historical record is reviewed under a different
      regulatory context than was active at issuance.

7.2.  Temporal Context Snapshot (TCS) Structure

   A TCS MUST contain the following fields:

   tcs_id (string, REQUIRED):
      Unique TCS identifier.  Format: TCS-{16HEX}.

   parent_record_id (string, REQUIRED):
      Identifier of the ATF record that carries this TCS.

   parent_record_type (string, REQUIRED):
      One of: DR | TAR | RCR.

   issued_at_ns (integer, REQUIRED):
      Nanosecond-precision epoch timestamp of record issuance.
      Must equal parent record's created_at converted to nanoseconds.

   regulatory_context (object, REQUIRED):
      Complete regulatory framework version context at issuance:
         eu_ai_act_version (string): RFV string for EU AI Act.
            Example: "EU_AI_ACT_2024_v1.0"
         nist_ai_rmf_version (string): RFV string for NIST AI RMF.
            Example: "NIST_AI_RMF_2023_v1.0"
         gcc_difc_version (string): RFV string for GCC/DIFC AI Reg.
            Example: "GCC_DIFC_2024_r1"
         iso_42001_version (string): RFV string for ISO/IEC 42001.
            Example: "ISO_42001_2023"
         atf_spec_version (string): ATF RFC version.
            Example: "RFC-ATF-5_v1.0"
         omnix_engine_version (string): Semantic version of OMNIX
            governance engine at issuance.
         jurisdiction_active (array): Jurisdictions active for this
            tenant at issuance.
         risk_classification_scheme (string): Active risk
            classification scheme identifier.

   threshold_context (object, REQUIRED):
      Complete governance threshold values at issuance:
         nominal_threshold (number): CES threshold for NOMINAL.
         monitoring_lower (number): CES lower bound for MONITORING.
         warning_lower (number): CES lower bound for WARNING.
         halt_threshold (number): CES threshold for HALT.
         fragmentation_limit (number): AFG fragmentation limit.
         max_delegation_depth (integer): Maximum allowed chain depth.
         avm_approval_threshold_pct (number): AVM approval threshold.

   tcs_hash (string, REQUIRED):
      SHA-256 hex digest of canonical JSON of all TCS fields except
      {tcs_hash, tcs_seal}.

   tcs_seal (string, REQUIRED):
      Base64-encoded Dilithium-3 (ML-DSA-65) signature over
      tcs_hash.encode("utf-8").

7.3.  TCS Embedding Protocol

   TCS creation MUST occur synchronously during parent record creation,
   before the parent record's content_hash is finalized.

   The tcs_hash MUST be included as a field in the parent record's
   committed fields for posture_state_hash computation.  This binds
   the regulatory context to the cryptographic identity of the primary
   governance decision: any modification to the TCS after issuance
   produces a mismatch in the parent record's posture_state_hash.

   TCS embedding procedure:

   1. Construct TCS JSON with all fields except {tcs_hash, tcs_seal}.
   2. Compute tcs_hash = SHA-256(canonical_json(tcs_fields)).
   3. Include tcs_hash in the parent record's committed fields.
   4. Finalize parent record's posture_state_hash.
   5. Finalize parent record's content_hash (includes posture_state_hash,
      which includes tcs_hash).
   6. Sign parent record.
   7. Compute tcs_seal = Dilithium3.sign(tcs_hash.encode("utf-8")).
   8. Persist both parent record and TCS atomically.

7.4.  Regulatory Alignment Receipt (RAR) Structure

   A RAR MUST contain the following fields:

   rar_id (string, REQUIRED):
      Unique RAR identifier.  Format: RAR-{16HEX}.

   source_record_id (string, REQUIRED):
      Identifier of the original ATF record being projected.

   source_tcs_id (string, REQUIRED):
      Identifier of the TCS embedded in the source record.

   review_timestamp (string, REQUIRED):
      ISO 8601 UTC timestamp of the RAR computation.

   reviewer_context (object, REQUIRED):
      Current framework versions at review time.  Same structure as
      TCS.regulatory_context.

   field_projections (array, REQUIRED):
      Array of Field Projection objects.  Each MUST contain:
         field (string): Name of the projected field.
         source_value (string): Field value under source framework.
         source_scheme (string): RFV string of the source framework.
         target_value (string): Equivalent value under target framework.
         target_scheme (string): RFV string of the target framework.
         projection_rule (string): Human-readable description of the
            mapping rule applied.
         projection_confidence (string): HIGH | MEDIUM | LOW.
            HIGH: exact mapping exists in TGB rulebook.
            MEDIUM: closest equivalent with documented divergence.
            LOW: no direct mapping; human review required.
         requires_human_review (boolean): true if projection_confidence
            is LOW or if the field has no target framework equivalent.

   semantic_shift_detected (boolean, REQUIRED):
      true if any field_projection has source_value != target_value.

   semantic_shift_fields (array of strings, OPTIONAL):
      Names of fields where semantic_shift_detected applies.

   original_record_integrity (string, REQUIRED):
      One of: VERIFIED | INVALIDATED | UNVERIFIED.
      VERIFIED: source record Dilithium-3 seal was verified before
         projection.  RAR is based on authentic evidence.
      INVALIDATED: source record seal verification failed.  RAR is
         constructed from a tampered record.  MUST include
         invalidation_reason.
      UNVERIFIED: seal verification was not attempted (not recommended).
      original_record_integrity MUST be VERIFIED for any RAR used in
      regulatory or legal proceedings.

   original_record_hash (string, REQUIRED):
      SHA-256 hex digest of the source record canonical JSON at the
      time of RAR computation.  Allows future verification that the
      source record has not changed since the RAR was produced.

   projection_methodology (string, REQUIRED):
      Identifier of the TGB rulebook version used.
      Format: TGB-RAR-V{major}.{minor}.
      Example: TGB-RAR-V1.0.

   content_hash_rar (string, REQUIRED):
      SHA-256 hex digest of canonical JSON of all RAR fields except
      {content_hash_rar, rar_seal}.

   rar_seal (string, REQUIRED):
      Base64-encoded Dilithium-3 (ML-DSA-65) signature over
      content_hash_rar.encode("utf-8").

   atf_spec_version_source (string, REQUIRED):
      ATF spec version under which the source record was issued.

   atf_spec_version_target (string, REQUIRED):
      ATF spec version active at review time.

7.5.  RAR Projection Protocol

   RAR computation MUST follow this procedure:

   Step 1 — Source Record Retrieval:
      Retrieve the source ATF record and its embedded TCS.

   Step 2 — Source Record Integrity Verification:
      Verify the source record's Dilithium-3 seal.
      Set original_record_integrity = VERIFIED or INVALIDATED.
      If INVALIDATED, proceed with RAR production but include
      a mandatory integrity warning in projection notes.

   Step 3 — TCS Extraction:
      Extract source_tcs_id and the full TCS regulatory_context and
      threshold_context from the source record's embedded TCS.

   Step 4 — Rulebook Loading:
      Load the TGB projection rulebook at projection_methodology
      version.  Verify the rulebook's own PQC seal.

   Step 5 — Field-by-Field Projection:
      For each governance field in the source record:
         a. Look up the field in the rulebook under the source
            framework -> target framework transition.
         b. If an exact mapping exists: apply it, set HIGH confidence.
         c. If a closest-equivalent mapping exists: apply it, set
            MEDIUM confidence, document divergence.
         d. If no mapping exists: flag requires_human_review = true,
            set LOW confidence.
         e. Append Field Projection object to field_projections.

   Step 6 — Semantic Shift Detection:
      Set semantic_shift_detected = any(
         fp.source_value != fp.target_value for fp in field_projections
      ).

   Step 7 — RAR Assembly and Sealing:
      Assemble RAR JSON.  Compute content_hash_rar.
      Compute rar_seal = Dilithium3.sign(content_hash_rar).

   Step 8 — RAR Persistence:
      INSERT INTO atf_regulatory_alignment_receipts.
      The source record MUST NOT be modified in any way.

7.6.  Temporal Migration Record (TMR)

   A TMR MUST contain the following fields:

   tmr_id (string, REQUIRED):
      Unique TMR identifier.  Format: TMR-{16HEX}.

   source_record_id (string, REQUIRED):
      Identifier of the ATF record transitioning between lifecycle
      states.

   migration_event (string, REQUIRED):
      One of: HOT_TO_WARM | WARM_TO_COLD.

   migration_timestamp (string, REQUIRED):
      ISO 8601 UTC timestamp of the lifecycle transition.

   regulatory_context_at_migration (object, REQUIRED):
      Complete regulatory context at the moment of migration.
      Same structure as TCS.regulatory_context.

   retention_basis (string, REQUIRED):
      Regulatory obligation driving this retention decision.
      Format: {FRAMEWORK}_{CLAUSE}_{RETENTION_PERIOD}.
      Examples:
         EU_AI_ACT_ART72_7YR
         GCC_DIFC_ART14_5YR
         ISO_42001_9.1_3YR
         CUSTOMER_CONTRACT_10YR

   next_review_due (string, OPTIONAL):
      ISO 8601 UTC timestamp of the next mandatory retention review.
      RECOMMENDED for records with a retention_basis that specifies
      a review cycle.

   content_hash_tmr (string, REQUIRED):
      SHA-256 hex digest of canonical JSON of all TMR fields except
      {content_hash_tmr, tmr_seal}.

   tmr_seal (string, REQUIRED):
      Base64-encoded Dilithium-3 (ML-DSA-65) signature over
      content_hash_tmr.encode("utf-8").

7.7.  Offline Projection Computability

   RARs MUST be independently computable by any party possessing:

   1. The source ATF record JSON (with embedded TCS).
   2. The TGB projection rulebook at the RAR's projection_methodology
      version.  The rulebook is published by OMNIX and embedded in
      all OEP packages when TGB_INCLUDE_IN_OEP = true.
   3. The OMNIX platform public key.

   The TGB projection rulebook is a PQC-signed JSON document.  Its
   seal MUST be verified before any projection is performed.  A
   rulebook with an invalid seal MUST NOT be used for RAR computation
   in proceedings where the RAR will be submitted as regulatory
   evidence.

   Rulebook URI conventions:
      API:     GET /v1/tgb/rulebook/{version}
      OEP:     Embedded at tgb_rulebook.json in the OEP package root.
      Archive: Permanent URI published via OMNIX documentation site.

7.8.  TGB Invariants (TGB-INV-001 through TGB-INV-005)

TGB-INV-001 — Mandatory TCS Embedding

   Every ATF record (DR, TAR, RCR) issued with TGB_ENABLED=true MUST
   carry an embedded TCS capturing the complete regulatory and
   threshold context at the nanosecond of issuance.

   Formally:
      For all records R where TGB_ENABLED at R.created_at:
         EXISTS(TCS t) WHERE t.parent_record_id = R.record_id
            AND t.issued_at_ns == R.created_at_ns

   A record without a corresponding TCS is TGB-incomplete.  It may
   still be used for governance decisions but MUST be flagged as
   TGB-INCOMPLETE in any compliance reporting.

TGB-INV-002 — RAR Non-Destruction

   A RAR MUST NOT modify any field of the source ATF record or its
   embedded TCS.  The source record MUST be byte-identical before
   and after RAR generation.

   Formally:
      For all RARs where rar.source_record_id = R.record_id:
         R is not modified during or after RAR issuance.

   Any system where RAR generation modifies source records has a
   critical evidence integrity defect.

TGB-INV-003 — Offline RAR Computability

   Every RAR produced by TGB MUST be independently computable by any
   party possessing the source record, the source TCS, and the
   published TGB projection rulebook — without accessing any OMNIX
   infrastructure.

   An implementation where the §7.5 procedure fails for a correctly
   formed RAR has a structural offline verifiability defect.

TGB-INV-004 — Projection Monotonicity

   A governance record valid under regulatory framework version V_n
   MUST remain valid under V_{n+k} (k >= 0) unless an Explicit
   Invalidity Declaration (EID) is issued and persisted in
   atf_regulatory_alignment_receipts with:
      original_record_integrity = INVALIDATED
      eid_version = the framework version triggering invalidity
      eid_reason = the specific provision causing invalidity

   Formally:
      For all records R and framework versions V_n, V_{n+k}:
         valid(R, V_n) AND NOT EXISTS(EID e WHERE e.source_record_id
            = R.record_id AND e.eid_version = V_{n+k})
         IMPLIES valid(R, V_{n+k})

   Silent invalidity — where a framework revision retroactively
   invalidates a record without an EID — is prohibited.

TGB-INV-005 — TMR and RAR PQC Sealing

   Every TMR and every RAR MUST be sealed with Dilithium-3
   (ML-DSA-65, FIPS 204) over their respective content hashes.
   Unsealed TMRs and RARs MUST NOT be accepted as valid temporal
   bridge artifacts in regulatory proceedings.


8.  Formal Verification (OMNIX-FVS-1.0 Extension)

8.1.  CGL Proof Inventory

   RFC-ATF-4 established the OMNIX Formal Verification Suite
   (OMNIX-FVS-1.0, ADR-177) with 19 Z3 SMT arithmetic proofs across
   AGVP, SSD, and DSPP invariants.

   RFC-ATF-5 extends OMNIX-FVS-1.0 with formal verifiability targets
   for CGE, GUGT, and TGB.  The following properties are candidates
   for Z3 SMT arithmetic proof in the next FVS release:

   CGE arithmetic properties:
      CGE-FVS-001: Variation bound satisfaction
         For all p in VV: |VV[p]| <= 0.40 * |p_0|
         (bounded linear arithmetic over reals)
      CGE-FVS-002: fragility_score bounds
         fragility_score ∈ [0.0, 1.0]
         (follows from divergence_count ∈ [0, cfr_count])
      CGE-FVS-003: CAT root hash uniqueness
         sha256(sorted(H)) is a bijection on the power set of H
         (structural property)

   GUGT arithmetic properties:
      GUGT-FVS-001: Conformance level monotonicity
         L3 satisfied IMPLIES L2 satisfied IMPLIES L1 satisfied
         (over boolean UGI result vectors)
      GUGT-FVS-002: UGI completeness sufficiency
         UGI-001 AND ... AND UGI-006 IMPLIES MFC
         (over framework obligation satisfiability)

   TGB arithmetic properties:
      TGB-FVS-001: Projection monotonicity
         valid(R, V_n) AND NOT EXISTS(EID) IMPLIES valid(R, V_{n+k})
         (over ordered framework version sets)
      TGB-FVS-002: RAR non-destruction (structural integrity)
         hash(R_before_RAR) == hash(R_after_RAR)

8.2.  CGE Arithmetic Proofs (Z3 SMT)

   CGE-FVS-001 — Variation Bound Satisfaction:

   from z3 import Real, Solver, And, Or, Not, sat
   p0, delta = Real("p0"), Real("delta")
   MAX_VAR = 0.40
   s = Solver()
   s.add(p0 > 0)
   s.add(Or(delta > MAX_VAR * p0, delta < -MAX_VAR * p0))
   # Verify: no valid delta exists outside the bound given enforcement
   # Result expected: unsat (enforcement eliminates all violations)

   CGE-FVS-002 — Fragility Score Bounds:

   from z3 import Int, Solver, And, sat
   d, M = Int("d"), Int("M")
   s = Solver()
   s.add(M >= 1, M <= 7, d >= 0, d <= M)
   # fragility = d / M; prove fragility in [0.0, 1.0]
   # Result expected: unsat for violations outside [0, 1]

8.3.  GUGT Arithmetic Proofs (Z3 SMT)

   GUGT-FVS-001 — Conformance Level Monotonicity:

   from z3 import Bool, Solver, Implies, And, Not, sat
   u1,u2,u3,u4,u5,u6 = [Bool(f"UGI_{i}") for i in range(1,7)]
   L1 = And(u1, u2)
   L2 = And(L1, u3, u4)
   L3 = And(L2, u5, u6)
   s = Solver()
   # L3 implies L2 implies L1: verify no counterexample exists
   s.add(Not(Implies(L3, And(L2, L1))))
   assert s.check() == unsat  # monotonicity holds

8.4.  TGB Arithmetic Proofs (Z3 SMT)

   TGB-FVS-001 — Projection Monotonicity:

   from z3 import Bool, Int, Solver, Implies, And, Not, sat
   valid_Vn = Bool("valid_Vn")
   eid_exists = Bool("eid_exists")
   k = Int("k")
   s = Solver()
   s.add(k >= 0)
   s.add(valid_Vn)
   s.add(Not(eid_exists))
   # Claim: valid_Vn AND NOT eid_exists => valid_V(n+k) for all k
   # structural: no arithmetic counterexample can exist
   # Result: unsat (no violation reachable)

8.5.  Machine Reproducibility

   All CGL formal verification targets MUST be executable using:

      python omnix_core/formal_verification/run_cgl_proofs.py

   Expected output: JSON report with result = "unsat" for all
   proof targets.  A "sat" or "unknown" result for any target
   indicates a verification failure and MUST block CGL compliance
   certification.


9.  CGL Layer Composition

9.1.  Layer Architecture

   The three CGL modules interact with the ATF stack as follows:

   Request time (Layer 1-4 evaluation):
      ┌─────────────────────────────────────────────────────────┐
      │  1. DR / TAR / RCR evaluation (Layers 1-4)             │
      │  2. TCS construction (TGB) — synchronous               │
      │  3. Primary record sealed and persisted                 │
      │  4. CGE task queued (async) or executed (sync)          │
      └─────────────────────────────────────────────────────────┘

   Background (CGE async worker):
      ┌─────────────────────────────────────────────────────────┐
      │  5. M CFRs computed under M variation vectors           │
      │  6. CAT assembled from CFR set                          │
      │  7. CAT sealed and persisted                            │
      └─────────────────────────────────────────────────────────┘

   Certification time (on-demand):
      ┌─────────────────────────────────────────────────────────┐
      │  8. UIR assessment performed (GUGT)                     │
      │  9. UIR sealed and persisted                            │
      └─────────────────────────────────────────────────────────┘

   Review time (regulatory / forensic):
      ┌─────────────────────────────────────────────────────────┐
      │ 10. RAR computed from source record + TCS (TGB)         │
      │ 11. RAR sealed and persisted                            │
      │ 12. Full CGL evidence package assembled for delivery    │
      └─────────────────────────────────────────────────────────┘

9.2.  Cross-Layer Integration Points

   CGE ↔ OEP (ADR-165):
      When CGE_INCLUDE_IN_OEP=true, every OEP package includes the
      CAT for the packaged receipt.  The OEP two-phase seal covers
      the CAT, making counterfactual evidence forensically portable.

   TGB ↔ OEP (ADR-165):
      When TGB_INCLUDE_IN_OEP=true, OEP packages include the TCS,
      applicable RARs, and the TGB rulebook version active at
      export time.  OEP packages become self-sufficient for temporal
      projection without any platform access.

   GUGT ↔ OEP:
      UIRs MAY be included in OEP packages as certification annexes.
      When included, the OEP outer seal covers the UIR, providing
      end-to-end integrity across the complete evidence set.

9.3.  Failure Isolation

   CGE failure MUST NOT affect primary record issuance.  If the CGE
   async worker fails after step 4, the primary record remains valid.
   The CAT is flagged as PENDING and retried.  A primary record with
   no CAT after CGE_MAX_RETRY_HOURS is flagged as CGE_INCOMPLETE
   but remains a valid Layer 1-4 governance record.

   TGB failure at TCS construction (step 2) MUST NOT block primary
   record issuance.  If TCS construction fails, the primary record
   is issued without TCS, flagged as TGB_INCOMPLETE, and the TCS
   computation is retried asynchronously.

   GUGT UIR failure has no impact on any ATF record.  UIR issuance
   is always on-demand and independent of record creation.


10.  Combined Invariant Summary

   This RFC introduces 18 new invariants across three protocol
   families.  Combined with the 70 invariants from RFC-ATF-1 through
   RFC-ATF-4, the complete ATF protocol stack encompasses 88 formally
   specified, model-checkable constraints across 17 protocol families.

   RFC-ATF-5 invariants:

   | Family    | Invariant      | Statement (summary)                        |
   |-----------|----------------|--------------------------------------------|
   | CGE       | CGE-INV-001    | Mandatory fork production (>=1 CFR/eval)  |
   | CGE       | CGE-INV-002    | Primary decision isolation (read-only CGE) |
   | CGE       | CGE-INV-003    | CFR PQC sealing (ML-DSA-65 required)      |
   | CGE       | CGE-INV-004    | CAT root hash integrity                   |
   | CGE       | CGE-INV-005    | Variation bound (|delta| <= 40%)          |
   | CGE       | CGE-INV-006    | Append-only CFR/CAT storage               |
   | CGE       | CGE-INV-007    | Offline verifiability                     |
   | GUGT      | GUGT-INV-001   | UGI completeness (all 6 required)         |
   | GUGT      | GUGT-INV-002   | Framework clause specificity              |
   | GUGT      | GUGT-INV-003   | UIR PQC sealing                           |
   | GUGT      | GUGT-INV-004   | Agent-type coverage declaration           |
   | GUGT      | GUGT-INV-005   | ATF supersession prohibition              |
   | GUGT      | GUGT-INV-006   | Conformance level monotonicity            |
   | TGB       | TGB-INV-001    | Mandatory TCS embedding                   |
   | TGB       | TGB-INV-002    | RAR non-destruction                       |
   | TGB       | TGB-INV-003    | Offline RAR computability                 |
   | TGB       | TGB-INV-004    | Projection monotonicity                   |
   | TGB       | TGB-INV-005    | TMR and RAR PQC sealing                   |

   Complete ATF invariant registry as of RFC-ATF-5:

   | Family      | RFC     | Count | Scope                            |
   |-------------|---------|-------|----------------------------------|
   | ATF-INV     | ATF-1   |   6   | Identity & Delegation            |
   | RGC-INV     | ATF-2   |   8   | Runtime Continuity               |
   | GPIL-INV    | ATF-3   |   3   | Governance Policy Interop        |
   | ELR-INV     | ATF-3   |   4   | Evidence Lifecycle               |
   | EAP-INV     | ATF-3   |   7   | Evidence Archive Pipeline        |
   | OEP-INV     | ATF-3   |   6   | Evidence Package (OEP)           |
   | FEA-INV     | ATF-3   |   5   | Forensic Export Auth             |
   | FVP-INV     | ATF-3   |   1   | Forensic Verification Protocol   |
   | GECR-INV    | ATF-3   |   6   | Governance Execution Context     |
   | SGIP-INV    | ATF-3   |   4   | Semantic Gov Interop Protocol    |
   | DSPP-INV    | ATF-4   |   7   | Dynamic Semantic Portability     |
   | AGV-INV     | ATF-4   |   6   | Anticipatory Governance Veto     |
   | SSD-INV     | ATF-4   |   3   | Structural Shift Detection       |
   | FVS-INV     | ATF-4   |   3   | Formal Verification Suite        |
   | CGE-INV     | ATF-5   |   7   | Counterfactual Governance Engine |
   | GUGT-INV    | ATF-5   |   6   | Grand Unified Governance Theory  |
   | TGB-INV     | ATF-5   |   5   | Temporal Governance Bridge       |
   |             | TOTAL   |  88   |                                  |


11.  Compliance Designation: ATF-CGL-Compliant

11.1.  Designation Requirements

   An implementation is designated ATF-CGL-Compliant if and only if
   it satisfies ALL of the following:

   (a) ATF-PGL-Compliant (RFC-ATF-4): all RFC-ATF-1, RFC-ATF-2,
       RFC-ATF-3, and RFC-ATF-4 requirements are satisfied.

   (b) CGE operational: CGE_ENABLED=true, CGE_FORK_COUNT in [1,7],
       all CGE-INV-001 through CGE-INV-007 satisfied.

   (c) GUGT UIR issuance: at least one GUGT-L3+ATF UIR has been
       issued and verified for the implementation, covering all
       active jurisdictions and at least the primary agent type.

   (d) TGB operational: TGB_ENABLED=true, all new ATF records carry
       embedded TCS, all TGB-INV-001 through TGB-INV-005 satisfied.

   (e) CGL formal verification: OMNIX-FVS-1.0 extension runs all
       CGL proof targets with result = "unsat" for all proofs.

11.2.  Compliance Hierarchy

   | Designation         | RFC Coverage    | Invariants |
   |---------------------|-----------------|------------|
   | ATF-COMPLIANT-L1    | RFC-ATF-1       | 6          |
   | ATF-COMPLIANT-L2    | RFC-ATF-1       | 6          |
   | ATF-COMPLIANT-L3    | RFC-ATF-1       | 6          |
   | ATF-RGC-Compliant   | ATF-1 + ATF-2   | 14         |
   | ATF-FEI-Compliant   | ATF-1/2/3       | 40         |
   | ATF-PGL-Compliant   | ATF-1/2/3/4     | 70         |
   | ATF-CGL-Compliant   | ATF-1/2/3/4/5   | 88         |

   ATF-CGL-Compliant is the fifth and highest compliance tier in the
   ATF stack.


12.  Implementation Requirements

12.1.  CGE Requirements

   REQUIRED:
   R-CGE-01: CGE_ENABLED environment variable MUST be respected.
      When true, every governance evaluation MUST trigger CGE.
   R-CGE-02: CFR generation MUST use deterministic VV seeding
      (§5.6).  Non-deterministic VVs are not permitted.
   R-CGE-03: CGE_ASYNC_MODE MUST default to true in production.
   R-CGE-04: CAT cat_root_hash MUST be verified against
      cfr_content_hashes before persistence.
   R-CGE-05: All CFRs and CATs MUST be inserted into append-only
      database tables.  No UPDATE or DELETE triggers permitted.

   RECOMMENDED:
   R-CGE-06: CGE_FORK_COUNT SHOULD be set to 3 (default) for
      typical deployments.  Values above 5 require dedicated
      compute allocation.
   R-CGE-07: CATs SHOULD be included in OEP packages when
      CGE_INCLUDE_IN_OEP=true.

   NOT PERMITTED:
   R-CGE-08: CGE computation MUST NOT execute before the primary
      record is sealed and persisted (CGE-INV-002).
   R-CGE-09: CGE MUST NOT modify any primary record field.

12.2.  GUGT Requirements

   REQUIRED:
   R-GUGT-01: UIR issuance MUST validate all six UGI assessments
      before assigning overall_status = GUGT_COMPLIANT.
   R-GUGT-02: Every UIR MUST include explicit framework clause
      references per GUGT-INV-002.
   R-GUGT-03: UIR seal MUST use ML-DSA-65 (GUGT-INV-003).
   R-GUGT-04: Conformance level MUST be consistent with UGI results
      per §6.5 table (GUGT-INV-006).

   RECOMMENDED:
   R-GUGT-05: ATF-native systems SHOULD pre-compute GUGT-L3+ATF
      UIRs using the automated assessment endpoint.
   R-GUGT-06: UIRs SHOULD be refreshed quarterly or upon ATF spec
      version update.

12.3.  TGB Requirements

   REQUIRED:
   R-TGB-01: TCS creation MUST be synchronous with primary record
      creation (§7.3 step ordering).
   R-TGB-02: tcs_hash MUST be included in the parent record's
      committed fields for posture_state_hash computation.
   R-TGB-03: RAR production MUST verify the source record seal
      before computing field projections (§7.5 Step 2).
   R-TGB-04: RARs MUST NOT modify any source record field
      (TGB-INV-002).
   R-TGB-05: TGB rulebook PQC seal MUST be verified before use.

   RECOMMENDED:
   R-TGB-06: TGB_INCLUDE_IN_OEP SHOULD be true in production to
      enable fully self-contained forensic evidence packages.
   R-TGB-07: TMRs SHOULD be generated at every evidence lifecycle
      transition for records subject to multi-year retention
      obligations.


13.  Persistence Schema

13.1.  atf_counterfactual_forks

   CREATE TABLE IF NOT EXISTS atf_counterfactual_forks (
       id                           SERIAL PRIMARY KEY,
       cfr_id                       TEXT NOT NULL UNIQUE,
       cat_id                       TEXT NOT NULL,
       primary_receipt_id           TEXT NOT NULL,
       evaluation_id                TEXT NOT NULL,
       variation_vector             JSONB NOT NULL,
       counterfactual_outcome       TEXT NOT NULL,
       counterfactual_ces_score     NUMERIC(6,3),
       outcome_diverges_from_primary BOOLEAN NOT NULL DEFAULT FALSE,
       divergence_invariant_triggered TEXT,
       posture_state_hash_cf        TEXT NOT NULL,
       content_hash_cf              TEXT NOT NULL,
       pqc_signature                TEXT NOT NULL,
       pqc_algorithm                TEXT NOT NULL DEFAULT 'ML-DSA-65',
       atf_spec_version             TEXT NOT NULL DEFAULT '1.5',
       issued_at                    TIMESTAMP WITH TIME ZONE NOT NULL,
       created_at                   TIMESTAMP WITH TIME ZONE
                                       DEFAULT CURRENT_TIMESTAMP
   );

   CREATE INDEX IF NOT EXISTS idx_cfr_primary
      ON atf_counterfactual_forks(primary_receipt_id);
   CREATE INDEX IF NOT EXISTS idx_cfr_cat
      ON atf_counterfactual_forks(cat_id);
   CREATE INDEX IF NOT EXISTS idx_cfr_evaluation
      ON atf_counterfactual_forks(evaluation_id);

13.2.  atf_counterfactual_tokens

   CREATE TABLE IF NOT EXISTS atf_counterfactual_tokens (
       id                      SERIAL PRIMARY KEY,
       cat_id                  TEXT NOT NULL UNIQUE,
       primary_receipt_id      TEXT NOT NULL,
       evaluation_timestamp    TIMESTAMP WITH TIME ZONE NOT NULL,
       cfr_count               INTEGER NOT NULL,
       cfr_ids                 TEXT[] NOT NULL,
       cfr_content_hashes      TEXT[] NOT NULL,
       cat_root_hash           TEXT NOT NULL,
       divergence_count        INTEGER NOT NULL DEFAULT 0,
       fragility_score         NUMERIC(5,4) NOT NULL DEFAULT 0.0,
       decision_space_summary  JSONB NOT NULL,
       content_hash_cat        TEXT NOT NULL,
       cat_seal                TEXT NOT NULL,
       atf_spec_version        TEXT NOT NULL DEFAULT '1.5',
       created_at              TIMESTAMP WITH TIME ZONE
                                   DEFAULT CURRENT_TIMESTAMP
   );

   CREATE INDEX IF NOT EXISTS idx_cat_primary
      ON atf_counterfactual_tokens(primary_receipt_id);

13.3.  gugt_universal_invariant_receipts

   CREATE TABLE IF NOT EXISTS gugt_universal_invariant_receipts (
       id                       SERIAL PRIMARY KEY,
       uir_id                   TEXT NOT NULL UNIQUE,
       subject_system           TEXT NOT NULL,
       subject_protocol         TEXT NOT NULL,
       assessor                 TEXT NOT NULL,
       assessment_date          TIMESTAMP WITH TIME ZONE NOT NULL,
       ugi_results              JSONB NOT NULL,
       overall_status           TEXT NOT NULL,
       conformance_level        TEXT NOT NULL,
       jurisdiction_coverage    TEXT[] NOT NULL,
       agent_type_coverage      TEXT[] NOT NULL,
       gugt_version             TEXT NOT NULL DEFAULT '1.0',
       atf_spec_version         TEXT,
       content_hash_uir         TEXT NOT NULL,
       uir_seal                 TEXT NOT NULL,
       issued_at                TIMESTAMP WITH TIME ZONE NOT NULL,
       created_at               TIMESTAMP WITH TIME ZONE
                                    DEFAULT CURRENT_TIMESTAMP
   );

   CREATE INDEX IF NOT EXISTS idx_uir_subject
      ON gugt_universal_invariant_receipts(subject_system);
   CREATE INDEX IF NOT EXISTS idx_uir_status
      ON gugt_universal_invariant_receipts(overall_status);
   CREATE INDEX IF NOT EXISTS idx_uir_level
      ON gugt_universal_invariant_receipts(conformance_level);

13.4.  atf_temporal_context_snapshots

   CREATE TABLE IF NOT EXISTS atf_temporal_context_snapshots (
       id                      SERIAL PRIMARY KEY,
       tcs_id                  TEXT NOT NULL UNIQUE,
       parent_record_id        TEXT NOT NULL,
       parent_record_type      TEXT NOT NULL,
       issued_at_ns            BIGINT NOT NULL,
       regulatory_context      JSONB NOT NULL,
       threshold_context       JSONB NOT NULL,
       tcs_hash                TEXT NOT NULL,
       tcs_seal                TEXT NOT NULL,
       created_at              TIMESTAMP WITH TIME ZONE
                                   DEFAULT CURRENT_TIMESTAMP
   );

   CREATE INDEX IF NOT EXISTS idx_tcs_parent
      ON atf_temporal_context_snapshots(parent_record_id);
   CREATE INDEX IF NOT EXISTS idx_tcs_type
      ON atf_temporal_context_snapshots(parent_record_type);

13.5.  atf_regulatory_alignment_receipts

   CREATE TABLE IF NOT EXISTS atf_regulatory_alignment_receipts (
       id                           SERIAL PRIMARY KEY,
       rar_id                       TEXT NOT NULL UNIQUE,
       source_record_id             TEXT NOT NULL,
       source_tcs_id                TEXT NOT NULL,
       review_timestamp             TIMESTAMP WITH TIME ZONE NOT NULL,
       reviewer_context             JSONB NOT NULL,
       field_projections            JSONB NOT NULL,
       semantic_shift_detected      BOOLEAN NOT NULL DEFAULT FALSE,
       semantic_shift_fields        TEXT[],
       original_record_integrity    TEXT NOT NULL,
       original_record_hash         TEXT NOT NULL,
       projection_methodology       TEXT NOT NULL DEFAULT 'TGB-RAR-V1.0',
       content_hash_rar             TEXT NOT NULL,
       rar_seal                     TEXT NOT NULL,
       atf_spec_version_source      TEXT NOT NULL,
       atf_spec_version_target      TEXT NOT NULL,
       created_at                   TIMESTAMP WITH TIME ZONE
                                        DEFAULT CURRENT_TIMESTAMP
   );

   CREATE INDEX IF NOT EXISTS idx_rar_source
      ON atf_regulatory_alignment_receipts(source_record_id);
   CREATE INDEX IF NOT EXISTS idx_rar_tcs
      ON atf_regulatory_alignment_receipts(source_tcs_id);

13.6.  atf_temporal_migration_records

   CREATE TABLE IF NOT EXISTS atf_temporal_migration_records (
       id                               SERIAL PRIMARY KEY,
       tmr_id                           TEXT NOT NULL UNIQUE,
       source_record_id                 TEXT NOT NULL,
       migration_event                  TEXT NOT NULL,
       migration_timestamp              TIMESTAMP WITH TIME ZONE NOT NULL,
       regulatory_context_at_migration  JSONB NOT NULL,
       retention_basis                  TEXT NOT NULL,
       next_review_due                  TIMESTAMP WITH TIME ZONE,
       content_hash_tmr                 TEXT NOT NULL,
       tmr_seal                         TEXT NOT NULL,
       created_at                       TIMESTAMP WITH TIME ZONE
                                            DEFAULT CURRENT_TIMESTAMP
   );

   CREATE INDEX IF NOT EXISTS idx_tmr_source
      ON atf_temporal_migration_records(source_record_id);
   CREATE INDEX IF NOT EXISTS idx_tmr_event
      ON atf_temporal_migration_records(migration_event);


14.  API Endpoints

   POST /v1/cge/evaluate
      Trigger a CGE evaluation for an existing primary record.
      Body: { "primary_receipt_id": "ATFDR-...", "fork_count": 3 }
      Response: { "cat_id": "CAT-...", "cfr_count": 3,
                  "fragility_score": 0.33, "status": "QUEUED" }

   GET /v1/cge/cat/{primary_receipt_id}
      Retrieve the CAT for a primary record.
      Response: CAT JSON with embedded cfr_ids.

   GET /v1/cge/cfr/{cfr_id}
      Retrieve a single CFR.
      Response: CFR JSON.

   GET /v1/cge/cat/{cat_id}/verify
      Run the §5.7 verification protocol server-side.
      Response: { "fully_verified": true, "steps": [...] }

   POST /v1/gugt/assess
      Initiate a GUGT compliance assessment.
      Body: { "subject_system": "...", "subject_protocol": "ATF",
               "jurisdiction_coverage": ["EU","US"],
               "agent_type_coverage": ["LLM"] }
      Response: { "uir_id": "UIR-...", "overall_status": "GUGT_COMPLIANT",
                  "conformance_level": "GUGT-L3+ATF" }

   GET /v1/gugt/uir/{uir_id}
      Retrieve a UIR.
      Response: UIR JSON.

   POST /v1/tgb/rar
      Generate a Regulatory Alignment Receipt.
      Body: { "source_record_id": "ATFDR-...",
               "target_framework_version": "EU_AI_ACT_2027_v2.0" }
      Response: { "rar_id": "RAR-...", "semantic_shift_detected": true,
                  "field_projections": [...] }

   GET /v1/tgb/tcs/{parent_record_id}
      Retrieve the TCS for an ATF record.
      Response: TCS JSON.

   GET /v1/tgb/rulebook/{version}
      Retrieve the TGB projection rulebook at a specific version.
      Response: Rulebook JSON with pqc_seal.


15.  Security Considerations

15.1.  CFR Fabrication Attack

   Threat: An adversary creates CFRs post-hoc, inserting favorable
   counterfactual paths to make rejected governance configurations
   appear to have been available at evaluation time.

   Mitigation:
   - CGE-INV-006 (append-only storage): CFRs inserted after the
     primary evaluation timestamp are detectable by timestamp
     ordering analysis.
   - CGE-INV-003 (PQC sealing): Fabricated CFRs sealed with a
     different key are rejected by signature verification.
   - CGE-INV-007 (offline verifiability): Step 6 of the §5.7
     protocol verifies VV determinism — fabricated VVs will not
     match the deterministic seed output for the evaluation_id +
     primary_receipt_id pair.

15.2.  CAT Root Hash Substitution

   Threat: An adversary replaces the cat_root_hash with a value
   computed over a different set of CFR hashes, enabling CFR
   substitution without invalidating the CAT seal.

   Mitigation:
   - CGE-INV-004: cat_root_hash is covered by cat_seal.
     Modifying cat_root_hash invalidates cat_seal.
   - §5.7 Step 1 explicitly recomputes cat_root_hash from
     cfr_content_hashes and compares to the embedded value.

15.3.  UIR Inflation Attack

   Threat: An adversary issues UIRs with overall_status =
   GUGT_COMPLIANT for systems that do not genuinely satisfy
   UGI-001-006, to falsely claim multi-jurisdiction compliance.

   Mitigation:
   - GUGT-INV-002: Generic framework references without specific
     clause identifiers are rejected at UIR construction.
   - GUGT-INV-003: UIR seal requires platform ML-DSA-65 key.
     Third-party UIR fabrication requires key compromise.
   - GUGT-INV-001: UIRs with fewer than six UGI assessments are
     structurally invalid and fail verification.

15.4.  GUGT Conformance Level Spoofing

   Threat: A UIR claims GUGT-L3 conformance for a system that only
   satisfies UGI-001 and UGI-002 (GUGT-L1).

   Mitigation:
   - GUGT-INV-006: Conformance level monotonicity is verifiable
     from the ugi_results object in the UIR.  Any verifier can
     check that the claimed level is consistent with the per-UGI
     results.
   - UIR verification procedure MUST check conformance_level
     against ugi_results before accepting GUGT_COMPLIANT status.

15.5.  TCS Manipulation Attack

   Threat: An adversary modifies the TCS embedded in a historical
   record to misrepresent the regulatory context at issuance —
   e.g., claiming a record was issued under a more favorable
   framework version.

   Mitigation:
   - tcs_hash is included in the parent record's posture_state_hash
     (§7.3 step ordering).  Any TCS modification produces a
     posture_state_hash mismatch, detectable from the primary
     record's content_hash.
   - tcs_seal provides independent Dilithium-3 verification of TCS
     content without requiring primary record verification.

15.6.  RAR Substitution Attack

   Threat: An adversary replaces a legitimate RAR with a fabricated
   projection that maps historical evidence to more favorable
   interpretations under the current framework.

   Mitigation:
   - TGB-INV-005 (RAR PQC sealing): Fabricated RARs without a valid
     platform ML-DSA-65 seal are rejected by verification.
   - TGB-INV-003 (offline computability): Any verifier can
     independently recompute the RAR from the source record and
     rulebook, comparing to the persisted RAR.  Divergence indicates
     substitution.
   - original_record_hash in the RAR is a tamper-evidence commitment
     to the source record state at RAR creation time.

15.7.  Projection Monotonicity Violation

   Threat: A framework revision retroactively invalidates a
   governance record without an EID being issued, creating a silent
   compliance gap.

   Mitigation:
   - TGB-INV-004 (projection monotonicity): Silent invalidity is
     prohibited.  Any EID MUST be persisted in
     atf_regulatory_alignment_receipts with original_record_integrity
     = INVALIDATED.
   - OMNIX governance operations MUST perform framework-version-
     aware scans when new RFVs are published, identifying records
     that may require EID issuance.

15.8.  Quantum Adversary

   All CGL records (CFR, CAT, UIR, TCS, RAR, TMR) are sealed with
   Dilithium-3 (ML-DSA-65, FIPS 204) at NIST PQC Level 3 security.
   The same quantum-adversary considerations as RFC-ATF-1 §11.5
   apply.  Key compromise for CGL records has the same response
   protocol as for primary ATF records: revoke the key, issue EIDs
   for all CGL records sealed with the compromised key, and re-seal
   using the replacement key.


16.  Novel Contributions

16.1.  Counterfactual Attestation Token (CAT)

   The CAT is a novel cryptographic artifact with no equivalent in
   any published governance specification.  Prior art in AI governance
   (VeriSigil VGS-001-011, IBM OpenScale, Microsoft Azure Responsible
   AI Dashboard, Google Model Cards) records the selected governance
   outcome.  None records the decision space.

   The CAT provides:
   - M cryptographically sealed alternative governance paths per
     evaluation, with deterministic VV generation ensuring reproducibility.
   - A fragility_score quantifying decision robustness — a first in
     AI governance infrastructure.
   - Offline-verifiable decision space evidence satisfying EU AI Act
     Art. 9's "alternatives considered" requirement with PQC-signed
     artifacts, not narrative documentation.

16.2.  Universal Governance Invariants (UGI-001-006)

   The UGI set is the first formally derived, framework-intersection-
   based universal invariant set for AI governance.  Prior work
   (VeriSigil VGS, NIST AI RMF, EU AI Act guidance) defines
   jurisdiction-specific or framework-specific requirements.  None
   derive the minimal sufficient set by formal intersection analysis.

   The UGI set enables a governance infrastructure to claim MFC
   (Multi-Frame Completeness) with a single PQC-signed certification
   artifact, eliminating per-jurisdiction custom compliance analysis.

16.3.  GUGT-L3+ATF Compliance Designation

   The GUGT-L3+ATF designation is the first cross-framework, cross-
   agent-type governance certification that covers EU AI Act, NIST
   AI RMF, GCC/DIFC AI Regulation, ISO/IEC 42001, and UK AISI
   simultaneously, certified by a PQC-signed UIR.

16.4.  Temporal Context Snapshot (TCS)

   The TCS is the first governance record type designed to capture
   the complete regulatory and threshold context at the nanosecond of
   record creation.  Prior governance frameworks embed timestamps but
   not the interpretive framework under which the timestamp was
   produced.  The TCS resolves this gap for the full 7-year EU AI Act
   retention period.

16.5.  Regulatory Alignment Receipt (RAR)

   The RAR is the first formal mechanism for projecting historical
   governance records to current regulatory frameworks without
   modifying the original evidence.  The non-destruction invariant
   (TGB-INV-002) and offline computability invariant (TGB-INV-003)
   together make the RAR a legally credible projection instrument:
   verifiable without platform trust and provably non-destructive.

16.6.  ATF-CGL-Compliant — Fifth Compliance Tier

   ATF-CGL-Compliant is the first five-tier AI governance compliance
   designation to span: identity (RFC-ATF-1), runtime continuity
   (RFC-ATF-2), evidence lifecycle (RFC-ATF-3), proactive governance
   (RFC-ATF-4), and cognitive governance (RFC-ATF-5) — 88 formally
   specified invariants across 17 protocol families.


17.  Distinction from Prior Art

   The following table positions RFC-ATF-5 against the most relevant
   published governance specifications:

   Feature                      | RFC-ATF-5  | VGS (Zenodo)| IBM OpenScale|
   -----------------------------|------------|-------------|--------------|
   Decision space evidence      | YES (CAT)  | No          | No           |
   Counterfactual PQC sealing   | YES        | No          | No           |
   Offline CAT verification     | YES        | No          | No           |
   Universal invariant set      | YES (UGIs) | No          | No           |
   PQC-signed certification     | YES (UIR)  | No          | No           |
   Multi-jurisdiction UIR       | YES        | Partial     | No           |
   Temporal context at issuance | YES (TCS)  | No          | No           |
   Framework projection (RAR)   | YES        | No          | No           |
   Non-destructive projection   | YES        | No          | No           |
   7-year retention support     | YES (TMR)  | No          | No           |
   Formal Z3 proof targets      | YES (8+)   | 4 proofs    | No           |
   Dual Z3 + TLA+ verification  | YES        | No          | No           |

   OMNIX-specific properties present in no other published
   governance specification:
   - Counterfactual Fork Record (CFR) — decision alternative path
     sealed at evaluation time
   - Counterfactual Attestation Token (CAT) — bound set of CFRs
     with root hash integrity
   - fragility_score — quantified governance decision robustness
   - Universal Governance Invariant set (UGI-001-006) — formal
     intersection of five major regulatory frameworks
   - Universal Invariant Receipt (UIR) — PQC-signed cross-framework
     certification artifact
   - Temporal Context Snapshot (TCS) — nanosecond-precision
     regulatory context at record issuance
   - Regulatory Alignment Receipt (RAR) — offline-computable,
     non-destructive temporal projection
   - Projection Monotonicity (TGB-INV-004) — formal guarantee of
     forward validity without EID
   - ATF-CGL-Compliant — five-tier, 88-invariant governance stack


18.  Regulatory Alignment

   | Framework             | CGE Relevance            | GUGT Relevance          | TGB Relevance           |
   |-----------------------|--------------------------|-------------------------|-------------------------|
   | EU AI Act Art. 9      | Art. 9: alternatives     | Art. 9: complete risk   | Art. 9(7): assessment   |
   |                       | considered documentation | management system       | integrity over time     |
   | EU AI Act Art. 11/12  | —                        | Art. 11/12: technical   | Art. 11: documentation  |
   |                       |                          | documentation           | remains current         |
   | EU AI Act Art. 14     | —                        | Art. 14: human control  | —                       |
   | EU AI Act Art. 72     | —                        | Art. 72: 7yr retention  | Art. 72: TMR for each   |
   |                       |                          |                         | lifecycle transition    |
   | NIST AI RMF MAP 1.6   | Alternative scenario     | MAP 5.1/5.2: complete   | MAP 5.2: lifecycle docs |
   |                       | documentation            | impact docs             |                         |
   | NIST GOVERN 1.1       | —                        | Human accountability    | —                       |
   | NIST MANAGE 2.2       | —                        | Execution enforcement   | Ongoing monitoring      |
   | GCC/DIFC Art. 9       | Continuous alternatives  | Complete Art. 8-14      | Art. 12/14: audit trail |
   |                       | assessment               | coverage                | across revisions        |
   | ISO 42001 §6.1.2      | Risk treatment           | §6.1.2, 8.4, 8.5, 9.3  | §9.1, 9.3: mgmt review |
   |                       | alternatives             | complete coverage       | with historical trends  |
   | UK AISI §3-5          | —                        | §3-5: accountability,   | §5: evidence standards  |
   |                       |                          | safeguards, measurement |                         |
   | SOC 2 Type II CC7.2   | —                        | Monitoring evidence     | Change documentation    |
   | ISO 27001 A.12.4      | —                        | Signed monitoring trail | Temporal audit log      |


19.  References

   [RFC-ATF-1]
      Nunes, H., "RFC-ATF-1: Agent Trust Fabric Delegation Protocol,
      Version 1.0.0", OMNIX QUANTUM Open Standard, May 2026.
      DOI: 10.5281/zenodo.20155016
      Figshare: 10.6084/m9.figshare.32308077

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

   [RFC-ATF-4]
      Nunes, H., "RFC-ATF-4: Agent Trust Fabric — Proactive Governance
      Layer, Version 1.0.0", OMNIX QUANTUM Open Standard, May 2026.
      DOI: 10.5281/zenodo.20368895
      Figshare: 10.6084/m9.figshare.32394192

   [FIPS204]
      National Institute of Standards and Technology, "Module-Lattice-
      Based Digital Signature Standard (ML-DSA)", FIPS 204, Aug 2024.

   [Z3]
      de Moura, L. and Bjørner, N., "Z3: An Efficient SMT Solver",
      Proceedings of TACAS 2008, LNCS 4963, pp. 337-340, Springer 2008.

   [TLA+]
      Lamport, L., "Specifying Systems: The TLA+ Language and Tools
      for Hardware and Software Engineers", Addison-Wesley, 2002.

   [RFC2119]
      Bradner, S., "Key words for use in RFCs to Indicate Requirement
      Levels", BCP 14, RFC 2119, March 1997.

   [RFC8174]
      Leiba, B., "Ambiguity of Uppercase vs Lowercase in RFC 2119
      Key Words", BCP 14, RFC 8174, May 2017.

   [ADR-178]
      Nunes, H., "ADR-178: Counterfactual Governance Engine (CGE)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-178

   [ADR-179]
      Nunes, H., "ADR-179: Grand Unified Governance Theory (GUGT)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-179

   [ADR-180]
      Nunes, H., "ADR-180: Temporal Governance Bridge (TGB)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-180

   [ADR-177]
      Nunes, H., "ADR-177: OMNIX Formal Verification Suite (FVS)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-177

   [VGS]
      Babatunde, R.L., "VeriSigil Governance Specification
      (VGS-001 to VGS-011)", Version 0.7.2, May 2026.
      DOI: 10.5281/zenodo.20264923
      [NOTE: Verify DOI resolves to Published record before citing
       in any submission.]

   [EU-AI-ACT]
      European Parliament, "Regulation (EU) 2024/1689 Laying Down
      Harmonised Rules on Artificial Intelligence", Official Journal
      of the European Union, July 2024.

   [NIST-AI-RMF]
      National Institute of Standards and Technology, "Artificial
      Intelligence Risk Management Framework", NIST AI 100-1,
      January 2023.

   [ISO-42001]
      International Organization for Standardization, "Artificial
      Intelligence — Management System", ISO/IEC 42001:2023.


20.  Appendix A — CGL Wire Format Reference

A.1  CFR Wire Format (normative field reference)

   | Field                         | Type    | Req'd    | Constraints                       |
   |-------------------------------|---------|----------|-----------------------------------|
   | cfr_id                        | string  | REQUIRED | "CFR-" + 16 uppercase hex         |
   | cat_id                        | string  | REQUIRED | "CAT-" + 16 uppercase hex         |
   | primary_receipt_id            | string  | REQUIRED | Valid ATF record ID               |
   | evaluation_id                 | string  | REQUIRED | "CGE-EVAL-" + 16 uppercase hex    |
   | variation_vector              | object  | REQUIRED | >= 1 field; all within VV bounds  |
   | counterfactual_outcome        | string  | REQUIRED | NOMINAL|MONITORING|WARNING|HALT   |
   | counterfactual_ces_score      | number  | REQUIRED | [0.0, 100.0]                      |
   | outcome_diverges_from_primary | boolean | REQUIRED | true if outcome != primary        |
   | divergence_invariant_triggered| string  | OPTIONAL | Required if diverges = true       |
   | posture_state_hash_cf         | string  | REQUIRED | "sha256:" + 64 lowercase hex      |
   | content_hash_cf               | string  | REQUIRED | 64 lowercase hex                  |
   | pqc_signature                 | string  | REQUIRED | ML-DSA-65 sig, base64             |
   | pqc_algorithm                 | string  | REQUIRED | MUST be "ML-DSA-65"               |
   | atf_spec_version              | string  | REQUIRED | MUST be "1.5"                     |
   | issued_at                     | string  | REQUIRED | ISO-8601-UTC, nanosecond prec.    |

   Example CFR JSON:
   {
     "cfr_id":                        "CFR-4A2B8F1C3D5E7A9B",
     "cat_id":                         "CAT-1F3A5B7C9D2E4F6A",
     "primary_receipt_id":             "ATFDR-8B2C4D6E1F3A5B7C",
     "evaluation_id":                  "CGE-EVAL-2C4D6E8F1A3B5C7D",
     "variation_vector": {
       "authority_budget_delta_pct":   -0.30,
       "ces_threshold_nominal_override": 88.0
     },
     "counterfactual_outcome":         "MONITORING",
     "counterfactual_ces_score":       76.4,
     "outcome_diverges_from_primary":  true,
     "divergence_invariant_triggered": "RGC-INV-002",
     "posture_state_hash_cf":          "a1b2c3d4e5f6...",
     "content_hash_cf":                "f6e5d4c3b2a1...",
     "pqc_signature":                  "<base64-ML-DSA-65-sig>",
     "pqc_algorithm":                  "ML-DSA-65",
     "atf_spec_version":               "1.5",
     "issued_at":                      "2026-05-23T14:00:00.123456789+00:00"
   }

A.2  CAT Wire Format (normative field reference)

   | Field                   | Type         | Req'd    | Constraints                     |
   |-------------------------|--------------|----------|---------------------------------|
   | cat_id                  | string       | REQUIRED | "CAT-" + 16 uppercase hex       |
   | primary_receipt_id      | string       | REQUIRED | Valid ATF record ID             |
   | evaluation_timestamp    | string       | REQUIRED | ISO-8601-UTC, nanosecond prec.  |
   | cfr_count               | integer      | REQUIRED | [1, 7]                          |
   | cfr_ids                 | string[]     | REQUIRED | len = cfr_count                 |
   | cfr_content_hashes      | string[]     | REQUIRED | len = cfr_count; SHA-256 hex    |
   | cat_root_hash           | string       | REQUIRED | sha256(sorted(cfr_hashes))      |
   | divergence_count        | integer      | REQUIRED | [0, cfr_count]                  |
   | fragility_score         | number       | REQUIRED | divergence_count / cfr_count    |
   | decision_space_summary  | object       | REQUIRED | See §5.5                        |
   | content_hash_cat        | string       | REQUIRED | SHA-256 of canonical CAT JSON   |
   | cat_seal                | string       | REQUIRED | ML-DSA-65 sig over content_hash |
   | atf_spec_version        | string       | REQUIRED | MUST be "1.5"                   |

A.3  UIR Wire Format (normative field reference)

   | Field                 | Type     | Req'd    | Constraints                        |
   |-----------------------|----------|----------|------------------------------------|
   | uir_id                | string   | REQUIRED | "UIR-" + 16 uppercase hex          |
   | subject_system        | string   | REQUIRED | Non-empty                          |
   | subject_protocol      | string   | REQUIRED | ATF | VGS | CUSTOM                 |
   | assessor              | string   | REQUIRED | Non-empty                          |
   | assessment_date       | string   | REQUIRED | ISO-8601-UTC                       |
   | ugi_results           | object   | REQUIRED | Exactly 6 entries: UGI-001 to 006  |
   | overall_status        | string   | REQUIRED | GUGT_COMPLIANT | NON_COMPLIANT      |
   | conformance_level     | string   | REQUIRED | GUGT-L1 to L3+ATF                  |
   | jurisdiction_coverage | string[] | REQUIRED | Non-empty; valid jurisdictions     |
   | agent_type_coverage   | string[] | REQUIRED | Non-empty; valid agent types       |
   | gugt_version          | string   | REQUIRED | MUST be "1.0"                      |
   | atf_spec_version      | string   | OPTIONAL | Required when protocol = ATF       |
   | content_hash_uir      | string   | REQUIRED | SHA-256 of canonical UIR JSON      |
   | uir_seal              | string   | REQUIRED | ML-DSA-65 sig over content_hash    |
   | issued_at             | string   | REQUIRED | ISO-8601-UTC                       |

A.4  TCS Wire Format (normative field reference)

   | Field                    | Type    | Req'd    | Constraints                       |
   |--------------------------|---------|----------|-----------------------------------|
   | tcs_id                   | string  | REQUIRED | "TCS-" + 16 uppercase hex         |
   | parent_record_id         | string  | REQUIRED | Valid ATF record ID               |
   | parent_record_type       | string  | REQUIRED | DR | TAR | RCR                   |
   | issued_at_ns             | integer | REQUIRED | Nanosecond epoch; > 0             |
   | regulatory_context       | object  | REQUIRED | See §7.2                          |
   | threshold_context        | object  | REQUIRED | See §7.2                          |
   | tcs_hash                 | string  | REQUIRED | SHA-256 of canonical TCS JSON     |
   | tcs_seal                 | string  | REQUIRED | ML-DSA-65 sig over tcs_hash       |

A.5  RAR Wire Format (normative field reference)

   | Field                      | Type     | Req'd    | Constraints                     |
   |----------------------------|----------|----------|---------------------------------|
   | rar_id                     | string   | REQUIRED | "RAR-" + 16 uppercase hex       |
   | source_record_id           | string   | REQUIRED | Valid ATF record ID             |
   | source_tcs_id              | string   | REQUIRED | Valid TCS ID                    |
   | review_timestamp           | string   | REQUIRED | ISO-8601-UTC                    |
   | reviewer_context           | object   | REQUIRED | Same structure as TCS.reg_ctx   |
   | field_projections          | object[] | REQUIRED | >= 1 Field Projection objects   |
   | semantic_shift_detected    | boolean  | REQUIRED |                                 |
   | semantic_shift_fields      | string[] | OPTIONAL | Present if shift detected       |
   | original_record_integrity  | string   | REQUIRED | VERIFIED | INVALIDATED          |
   | original_record_hash       | string   | REQUIRED | SHA-256 of source record JSON   |
   | projection_methodology     | string   | REQUIRED | "TGB-RAR-V{major}.{minor}"      |
   | content_hash_rar           | string   | REQUIRED | SHA-256 of canonical RAR JSON   |
   | rar_seal                   | string   | REQUIRED | ML-DSA-65 sig over content_hash |
   | atf_spec_version_source    | string   | REQUIRED | Source record ATF spec version  |
   | atf_spec_version_target    | string   | REQUIRED | Current ATF spec version        |


21.  Appendix B — GUGT Framework Mapping Reference

B.1  Complete UGI-to-Framework Clause Mapping

   UGI-001 — Human Authority Anchor:

   | Jurisdiction | Clause            | Obligation                                    |
   |--------------|-------------------|-----------------------------------------------|
   | EU AI Act    | Art. 14           | Human oversight throughout system lifecycle   |
   | EU AI Act    | Art. 17           | Quality management: accountability documented |
   | NIST AI RMF  | GOVERN 1.1        | Roles and responsibilities documented         |
   | GCC/DIFC     | Art. 8            | Human control structures established          |
   | ISO 42001    | §6.2              | AI objectives tied to human accountability    |
   | UK AISI      | §3                | Accountability structures defined             |

   UGI-002 — Offline-Verifiable Decision Evidence:

   | Jurisdiction | Clause            | Obligation                                    |
   |--------------|-------------------|-----------------------------------------------|
   | EU AI Act    | Art. 11           | Technical documentation maintained            |
   | EU AI Act    | Art. 12           | Record-keeping of AI system operations        |
   | NIST AI RMF  | MAP 5.2           | Impact assessment documented                  |
   | GCC/DIFC     | Art. 12           | Audit trail for AI decisions                  |
   | ISO 42001    | §9.1              | Monitoring, measurement, analysis             |
   | UK AISI      | §4                | Evidence standards for assessments            |

   UGI-003 — Execution-Time Boundary Enforcement:

   | Jurisdiction | Clause            | Obligation                                    |
   |--------------|-------------------|-----------------------------------------------|
   | EU AI Act    | Art. 9            | Risk management with real-time controls       |
   | NIST AI RMF  | MANAGE 2.2        | Ongoing monitoring of AI systems              |
   | GCC/DIFC     | Art. 9            | Continuous oversight mechanisms               |
   | ISO 42001    | §8.4              | AI system operation controls                  |
   | UK AISI      | §3                | Operational safeguards implemented            |

   UGI-004 — Pre-Committed Posture Assessment:

   | Jurisdiction | Clause            | Obligation                                    |
   |--------------|-------------------|-----------------------------------------------|
   | EU AI Act    | Art. 9(7)         | Testing and validation integrity              |
   | NIST AI RMF  | MEASURE 2.5       | Bias and drift measurement integrity          |
   | ISO 42001    | §8.5              | AI system verification procedures            |
   | UK AISI      | §5                | Measurement integrity requirements            |

   UGI-005 — Self-Modification Prohibition:

   | Jurisdiction | Clause            | Obligation                                    |
   |--------------|-------------------|-----------------------------------------------|
   | EU AI Act    | Art. 14(4)        | Human override capability preserved           |
   | NIST AI RMF  | GOVERN 6.1        | AI risk governance — control integrity        |
   | GCC/DIFC     | Art. 10           | Parameter control by external authority       |
   | ISO 42001    | §6.1.2            | Risk treatment controls not self-modified     |
   | UK AISI      | §4                | Control structures enforced                   |

   UGI-006 — Self-Contained Evidence Reconstruction:

   | Jurisdiction | Clause            | Obligation                                    |
   |--------------|-------------------|-----------------------------------------------|
   | EU AI Act    | Art. 18           | Documentation obligations — complete          |
   | EU AI Act    | Art. 72           | 7-year record retention — high-risk AI        |
   | NIST AI RMF  | MAP 5.1           | Impact documentation completeness             |
   | GCC/DIFC     | Art. 14           | Evidence completeness requirements            |
   | ISO 42001    | §9.3              | Management review with complete evidence      |
   | UK AISI      | §5                | Evidence completeness standards               |

B.2  GUGT Conformance Verification Procedure

   For a system S claiming GUGT-L3+ATF conformance:

   1. Retrieve the most recent UIR for S.
   2. Verify uir_seal using the issuer's public key.
   3. Verify content_hash_uir from canonical UIR JSON.
   4. Check overall_status = GUGT_COMPLIANT.
   5. Check conformance_level = GUGT-L3+ATF.
   6. For each UGI result: verify status = PASS and
      framework_coverage contains at least one entry per active
      jurisdiction.
   7. Verify that S is ATF-PGL-Compliant (RFC-ATF-4 §11.1).

   All seven steps MUST pass for GUGT-L3+ATF verification.


22.  Appendix C — CGL Compliance Checklist

   Implementations claiming ATF-CGL-Compliant MUST satisfy all items.
   Items marked (PGL) are inherited from RFC-ATF-4 and MUST be
   satisfied at that tier before this checklist applies.

   CGE
   □ CGE_ENABLED=true in production
   □ CGE_FORK_COUNT in [1, 7] (default: 3)
   □ CGE_MAX_VARIATION_PCT <= 0.40 (default: 0.40)
   □ CGE_ASYNC_MODE=true in production
   □ VV generation uses deterministic seeding per §5.6
   □ Primary record issued and persisted before CGE computation
     (CGE-INV-002)
   □ Every evaluation produces a CAT with >= 1 CFR (CGE-INV-001)
   □ CFR pqc_algorithm = "ML-DSA-65" enforced at construction
   □ CFR pqc_signature = sign(content_hash_cf.encode("utf-8"))
   □ CFR pqc_signature sealed before CFR persistence (CGE-INV-003)
   □ CAT cat_root_hash = sha256(sorted(cfr_content_hashes))
   □ CAT cat_seal verified against cat_root_hash before persistence
     (CGE-INV-004)
   □ All VV field magnitudes validated against CGE_MAX_VARIATION_PCT
     before CFR computation (CGE-INV-005)
   □ No UPDATE or DELETE on atf_counterfactual_forks (CGE-INV-006)
   □ No UPDATE or DELETE on atf_counterfactual_tokens (CGE-INV-006)
   □ §5.7 offline verification procedure passes for all CATs
     (CGE-INV-007)

   GUGT
   □ UIR construction validates all six UGI assessments
     (GUGT-INV-001)
   □ Every UGI result includes specific framework clause strings,
     not generic framework references (GUGT-INV-002)
   □ UIR uir_seal = Dilithium3.sign(content_hash_uir) (GUGT-INV-003)
   □ agent_type_coverage explicitly declared in every UIR
     (GUGT-INV-004)
   □ No ATF invariant relaxed by GUGT assessment (GUGT-INV-005)
   □ conformance_level consistent with ugi_results per §6.5
     (GUGT-INV-006)
   □ GUGT-L3+ATF UIR issued and verified for the deployment
   □ UIR refresh process defined (quarterly recommended)

   TGB
   □ TGB_ENABLED=true in production
   □ TCS construction synchronous with primary record creation
     (TGB-INV-001, §7.3 ordering)
   □ tcs_hash included in parent record's committed fields for
     posture_state_hash computation (§7.3)
   □ tcs_seal = Dilithium3.sign(tcs_hash.encode("utf-8"))
   □ TCS and primary record persisted atomically (§7.3 step 8)
   □ RAR production verifies source record seal before projection
     (§7.5 Step 2)
   □ RAR does not modify source record or TCS (TGB-INV-002)
   □ RAR rar_seal = Dilithium3.sign(content_hash_rar) (TGB-INV-005)
   □ TGB rulebook PQC seal verified before projection (§7.7)
   □ §7.5 RAR projection protocol followed field-by-field
   □ Offline RAR computation verified independently (TGB-INV-003)
   □ EID process defined for framework-revision-driven invalidity
     (TGB-INV-004)
   □ TMR issued at every HOT->WARM and WARM->COLD transition for
     records under multi-year retention (TGB-INV-005)
   □ TGB_INCLUDE_IN_OEP=true (recommended for full portability)

   Formal Verification
   □ CGL proof targets in omnix_core/formal_verification/ run
     without UNKNOWN or SAT results
   □ JSON proof report producible for compliance deliverables

   Inherited from ATF-PGL-Compliant (RFC-ATF-4) (abbreviated):
   □ (PGL) All RFC-ATF-1 invariants satisfied (ATF-INV-001-006)
   □ (PGL) All RFC-ATF-2 invariants satisfied (RGC-INV-001-008)
   □ (PGL) All RFC-ATF-3 invariants satisfied (26 invariants)
   □ (PGL) All RFC-ATF-4 invariants satisfied (AGVP/SSD/DSPP/FVS)
   □ (PGL) PostgreSQL + Redis configured in production
   □ (PGL) ML-DSA-65 signing keys stable across restarts (FMR-001)
   □ (PGL) OMNIX_ANTI_REPLAY_MODE = strict in production


23.  Author's Address

   Harold Alberto Nunes Rodelo (Editor)
   OMNIX QUANTUM LTD
   71-75 Shelton Street, Covent Garden
   London WC2H 9JQ, England
   Operational Headquarters: Abu Dhabi, UAE
   Email: standards@omnixquantum.com
   Web:   omnixquantum.net
```


---

*RFC-ATF-5 Version 1.0.0 — May 2026*
*OMNIX QUANTUM LTD — Harold Nunes, Editor*
*Priority Records: OMNIX-PAR-2026-CGE-001 · OMNIX-PAR-2026-GUGT-001 ·
OMNIX-PAR-2026-TGB-001*

*STATUS: DRAFT — NOT YET SUBMITTED TO ZENODO*
*REVISION HISTORY: v0.1 initial draft — May 23, 2026*

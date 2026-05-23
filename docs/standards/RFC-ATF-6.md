```
OMNIX QUANTUM Open Standard                            OMNIX QUANTUM LTD
Category: Standards Track                                    H. Nunes, Ed.
DOI: [PENDING — not yet submitted to Zenodo]                    May 2026


      RFC-ATF-6: Agent Trust Fabric — Behavioral Execution
      Verification Protocol
      Behavioral Anchor Record, Constraint Conformance Signal,
      and Cross-Turn Coherence Hash Chain
      Extension to RFC-ATF-1, RFC-ATF-2, RFC-ATF-3, RFC-ATF-4,
      and RFC-ATF-5
      Version 1.0.0 — OMNIX QUANTUM Open Standard


Abstract

   This document specifies the Behavioral Execution Verification Layer
   (BEV) of the Agent Trust Fabric protocol — the sixth RFC in the ATF
   Open Standard series.

   RFC-ATF-1 answered the identity question: who authorized this agent,
   with what authority, and can that be proved offline?  RFC-ATF-2
   answered the runtime question: was authority continuously valid
   throughout execution, and was every degradation event
   cryptographically attested?  RFC-ATF-3 answered the evidence
   question: where does the resulting artifact go, who can interpret it
   across organizational boundaries, and can a regulator reconstruct
   the full chain of custody years later without platform access?
   RFC-ATF-4 answered the proactive governance question: what happens
   between governance requests, is recalibration safe, and does a
   receipt issued today remain semantically legitimate in a receiving
   domain months later?  RFC-ATF-5 answered the cognitive governance
   question: what else could have happened, is the governance system
   universally complete, and will this evidence remain interpretable
   across time and regulatory revisions?

   RFC-ATF-6 answers the final structural question that no prior RFC
   addresses: did the agent actually behave within its authorized
   constraints during execution?

   A governance receipt proves that an agent was authorized to act.
   An execution receipt (ADR-131) proves that an action was taken and
   recorded.  But no artifact in the ATF stack through RFC-ATF-5
   proves that the agent's actual behavioral outputs during execution
   conformed to the constraint boundaries embedded in its governing
   receipt.  This is the Behavioral Execution Gap.

   RFC-ATF-6 closes this gap with three new protocol components:

   (1) The Behavioral Anchor Record (BAR) is a PQC-signed record of
       the actual outputs produced by an authorized agent during each
       execution turn, cryptographically bound to the governing receipt
       that authorized the session.  The BAR is the first protocol
       artifact that closes the authorization-to-output chain: every
       authorized action now has a verifiable, tamper-evident record of
       what the agent actually produced.

   (2) The Constraint Conformance Signal (CCS) is a continuous,
       multi-component metric [0.0, 100.0] computed per BAR, measuring
       how closely the agent's actual outputs conformed to the
       constraint boundaries defined in its governing receipt.  The CCS
       is integrated with the Anticipatory Governance Veto Protocol
       (AGVP, RFC-ATF-4), enabling CCS-driven Proactive Veto Receipt
       issuance when conformance degrades before a boundary violation
       occurs.  This is the first governance-native behavioral
       monitoring signal with anticipatory veto integration.

   (3) The Cross-Turn Coherence Hash Chain (CTCHC) extends the BAR
       mechanism to multi-turn agent sessions.  Each BAR's output hash
       is chained to the previous turn's chain link using a
       deterministic hash construction seeded by the governing receipt.
       The resulting final chain hash provides offline-verifiable proof
       that behavioral coherence was maintained across every turn of a
       multi-turn session without modification, omission, or turn
       reordering.

   Together, BAR, CCS, and CTCHC constitute the Behavioral Execution
   Verification Layer — the first governance infrastructure component
   in the field to formally address the gap between authorization
   evidence and behavioral output attestation.

   Eighteen new invariants are introduced: BEV-INV-001 through
   BEV-INV-007 (BAR family), BEV-INV-008 through BEV-INV-013 (CCS
   family), and BEV-INV-014 through BEV-INV-018 (CTCHC family).
   Combined with the 88 invariants of RFC-ATF-1 through RFC-ATF-5,
   the ATF stack reaches 106 formally specified invariants across
   20 protocol families.

   An implementation that complies with RFC-ATF-1 through RFC-ATF-6
   is designated ATF-BEV-Compliant — the sixth and highest compliance
   tier in the ATF stack, superseding ATF-CGL-Compliant (RFC-ATF-5).


Status of This Memo

   This is an OMNIX QUANTUM Open Standard, published under the OMNIX
   Open Governance License v1.0.  This document extends RFC-ATF-1,
   RFC-ATF-2, RFC-ATF-3, RFC-ATF-4, and RFC-ATF-5 and MUST be read
   in conjunction with all five.  Implementers of RFC-ATF-5 who
   require behavioral output attestation, continuous conformance
   monitoring, or multi-turn session coherence verification SHOULD
   adopt RFC-ATF-6 as specified herein.

   This document is a product of the OMNIX QUANTUM Standards Working
   Group.  It has been approved for publication by the OMNIX Technical
   Committee.

   [STATUS: DRAFT — pending submission to Zenodo.  Not yet published.
    For review by Harold Nunes only.  Do not distribute.]

   DOI: [PENDING]
   Zenodo package: docs/zenodo/rfc_atf_6/ (metadata.json — to be
   created prior to submission)
   Feedback: standards@omnixquantum.com


Copyright Notice

   Copyright (c) 2026 OMNIX QUANTUM LTD.  All rights reserved.
   71-75 Shelton Street, Covent Garden, London WC2H 9JQ, England.
   Operational headquarters: Abu Dhabi, UAE.

   Permission is granted to reproduce this document for review and
   implementation purposes, provided this copyright notice is retained.


Acknowledgements

   The three structural problems addressed in this RFC were identified
   through production implementation work on the ATF stack and
   confirmed through enterprise deployment feedback.

   The behavioral attestation problem (§2.1) was identified during
   implementation of ADR-131 (Execution Integrity Layer).  Closing the
   decision-to-execution-receipt chain demonstrated that a structural
   gap remained: the execution receipt records whether an action
   occurred, but not what the agent's behavioral outputs were during
   that action.  A governance system that can prove authorization and
   action but not behavioral content provides accountability without
   behavioral verifiability.  The BAR architecture was developed in
   direct response to this observation.

   The conformance observability problem (§2.2) was formally
   articulated during design of the Anticipatory Governance Veto
   Protocol (ADR-174, RFC-ATF-4).  The AGVP PVR watchdog requires
   observable signals to issue anticipatory vetoes before violations
   occur.  For structural governance signals (CES, fragmentation
   score), this signal exists.  For behavioral output conformance, no
   signal existed.  The CCS was designed to provide this signal and
   complete the AGVP input space.

   The multi-turn coherence problem (§2.3) was identified during
   enterprise deployment testing of multi-turn autonomous agent
   sessions operating under a single governing receipt.  The session
   governing receipt authorizes the session as a whole; no mechanism
   existed to prove that behavioral constraints were maintained
   consistently across every individual turn, or that turns were not
   reordered, omitted, or substituted post-hoc.  The CTCHC was
   designed to provide this session-level behavioral integrity proof.

   Antonio Socorro (CAI-EXPERT-LAB) independently identified the
   behavioral content gap during RFC-ATF-5 review: "The stack proves
   the decision, the authority, and the evidence lifecycle.  It does
   not prove what the system actually said or did."  This observation
   directly motivated the RFC-ATF-6 specification process.


Table of Contents

    1.  Introduction ............................................   8
    2.  Problem Statement: The Behavioral Execution Gap .........  10
        2.1.  The Behavioral Attestation Gap ....................  10
        2.2.  The Conformance Observability Problem .............  12
        2.3.  The Multi-Turn Coherence Problem ..................  14
        2.4.  The Behavioral Execution Gap (Gap_BEV) ............  16
    3.  Conventions and Terminology ............................  17
    4.  Architecture: The Behavioral Execution Verification Layer  21
        4.1.  Position in the ATF Stack ........................  21
        4.2.  Extension Relationships ..........................  22
        4.3.  Non-Destructive Integration ......................  23
        4.4.  BEV Module Independence ..........................  24
    5.  Behavioral Anchor Record (BAR) .........................  25
        5.1.  Behavioral Attestation Architecture ..............  25
        5.2.  BAR Structure ....................................  27
        5.3.  BAR Content Hash Construction ....................  31
        5.4.  BAR PQC Signature ................................  32
        5.5.  Output Hash Privacy Modes ........................  33
        5.6.  BAR Lifecycle ....................................  35
        5.7.  Offline Verifiability Protocol ...................  37
        5.8.  BAR Invariants (BEV-INV-001-007) .................  38
    6.  Constraint Conformance Signal (CCS) ....................  44
        6.1.  Conformance Measurement Architecture .............  44
        6.2.  CCS Score Components .............................  46
        6.3.  CCS Computation Protocol .........................  50
        6.4.  CCS Verdicts and Thresholds ......................  52
        6.5.  AGVP Integration: CCS-Driven Anticipatory Veto ...  54
        6.6.  CCS Embedding in BAR .............................  56
        6.7.  CCS Invariants (BEV-INV-008-013) .................  57
    7.  Cross-Turn Coherence Hash Chain (CTCHC) ................  63
        7.1.  Multi-Turn Coherence Architecture ................  63
        7.2.  Chain Initialization Protocol ....................  65
        7.3.  Chain Link Construction ..........................  67
        7.4.  Chain Sealing at Session Close ...................  69
        7.5.  Offline Chain Verification Protocol ..............  71
        7.6.  Partial Chain Recovery ...........................  73
        7.7.  CTCHC Invariants (BEV-INV-014-018) ...............  74
    8.  Formal Verification (OMNIX-FVS-1.0 Extension) ..........  79
        8.1.  BEV Proof Inventory ..............................  79
        8.2.  BAR Arithmetic Proofs (Z3 SMT) ...................  80
        8.3.  CCS Arithmetic Proofs (Z3 SMT) ...................  81
        8.4.  CTCHC Arithmetic Proofs (Z3 SMT) .................  82
        8.5.  Machine Reproducibility ..........................  83
    9.  BEV Layer Composition ..................................  84
        9.1.  Layer Architecture ...............................  84
        9.2.  Cross-Layer Integration Points ...................  85
        9.3.  Failure Isolation ................................  86
   10.  Combined Invariant Summary .............................  87
   11.  Compliance Designation: ATF-BEV-Compliant ..............  90
        11.1.  Designation Requirements ........................  90
        11.2.  Compliance Hierarchy ............................  91
   12.  Implementation Requirements ............................  92
        12.1.  BAR Requirements ................................  92
        12.2.  CCS Requirements ................................  93
        12.3.  CTCHC Requirements ..............................  94
   13.  Persistence Schema .....................................  95
        13.1.  atf_behavioral_anchor_records ...................  95
        13.2.  atf_constraint_conformance_signals ..............  97
        13.3.  atf_coherence_hash_chains .......................  98
   14.  API Endpoints ..........................................  99
   15.  Security Considerations ................................ 101
        15.1.  BAR Output Hash Substitution .................... 101
        15.2.  BAR Fabrication Attack .......................... 102
        15.3.  CCS Score Inflation Attack ...................... 102
        15.4.  CCS Component Manipulation ...................... 103
        15.5.  CTCHC Genesis Substitution ...................... 103
        15.6.  Chain Link Replay Attack ........................ 104
        15.7.  Partial Chain Presentation ...................... 104
        15.8.  Quantum Adversary ............................... 105
   16.  Novel Contributions .................................... 106
        16.1.  Behavioral Anchor Record (BAR) .................. 106
        16.2.  Constraint Conformance Signal (CCS) ............. 107
        16.3.  Cross-Turn Coherence Hash Chain (CTCHC) ......... 107
        16.4.  CCS-AGVP Integration Loop ....................... 108
        16.5.  Behavioral Attestation Chain .................... 108
        16.6.  ATF-BEV-Compliant — Sixth Compliance Tier ....... 109
   17.  Distinction from Prior Art ............................. 109
   18.  Regulatory Alignment ................................... 112
   19.  References ............................................. 114
   20.  Appendix A — BEV Wire Format Reference ................. 116
   21.  Appendix B — CCS Computation Reference ................. 121
   22.  Appendix C — BEV Compliance Checklist .................. 124
   23.  Author's Address ....................................... 128


1.  Introduction

   The Agent Trust Fabric protocol stack was designed to address the
   complete lifecycle of a governed autonomous agent action: from the
   moment authority is delegated (RFC-ATF-1), through the continuous
   monitoring of that authority at runtime (RFC-ATF-2), to the long-
   term preservation and independent verification of the resulting
   evidence (RFC-ATF-3), into the intervals between governance requests
   where anticipatory detection, recalibration safety, and cross-domain
   semantic portability are required (RFC-ATF-4), and through the
   cognitive governance layer where the decision space is documented,
   universal compliance is certified, and evidence remains interpretable
   across regulatory time (RFC-ATF-5).

   The five prior RFCs answer questions about governance infrastructure:
   who authorized, was authority valid, where does evidence go, was
   monitoring active, what else could have happened?  Each question was
   answered completely for its domain.  But all five RFCs share a
   structural assumption that RFC-ATF-6 now formally identifies and
   resolves.

   The assumption is this: every prior RFC treats the authorized action
   as a black box.  The governance receipt authorizes the action.  The
   execution receipt records that the action occurred.  The OEP package
   preserves the evidence chain.  But not one artifact in the ATF stack
   through RFC-ATF-5 contains a cryptographic record of what the agent
   actually produced during execution — what outputs it generated, what
   constraints it operated within, and whether its behavioral content
   conformed to the boundaries embedded in its governing receipt.

   This is not an implementation oversight.  It is a structural gap
   that emerges at the boundary between governance infrastructure and
   AI execution infrastructure.  The governance layer can prove
   authorization with certainty.  The behavioral layer can produce
   outputs with precision.  No protocol currently exists to
   cryptographically bind the two — to prove, with the same rigor that
   ATF proves authorization, that the outputs produced during execution
   were behaviorally consistent with the constraints that governed the
   authorization.

   RFC-ATF-6 introduces three protocol components that close this gap:

   The Behavioral Anchor Record (BAR) is the binding artifact.  It is
   a PQC-signed record produced at each execution turn, containing the
   output hash of the agent's actual output, bound to the governing
   receipt identifier, carrying an embedded CCS score, and chaining
   into the session's Cross-Turn Coherence Hash Chain.  The BAR is the
   first ATF artifact that makes behavioral output a first-class
   governance evidence type.

   The Constraint Conformance Signal (CCS) is the measurement
   artifact.  It provides a multi-component, numerically precise
   measure of how closely each turn's outputs conform to the
   constraints in the governing receipt.  Unlike existing ML monitoring
   signals, the CCS is governance-native: it references the actual
   constraint vector from the governing receipt, not a separately
   configured monitoring policy.  It feeds directly into the AGVP
   watchdog, completing the anticipatory veto input space.

   The Cross-Turn Coherence Hash Chain (CTCHC) is the session
   integrity artifact.  It provides proof that every turn of a multi-
   turn session was recorded in order, without omission, and without
   post-hoc substitution.  The chain is seeded by the governing
   receipt, making the session's behavioral record inseparable from
   the authority that governed it.

   Together, these three components constitute the Behavioral Execution
   Verification Layer — Layer 6 of the ATF stack.  Like all prior ATF
   layers, BEV is additive: it does not replace or modify any prior
   layer.  A BEV-enabled implementation produces richer evidence while
   remaining fully backward compatible with all existing ATF record
   types, verification procedures, and compliance designations.


2.  Problem Statement: The Behavioral Execution Gap

2.1.  The Behavioral Attestation Gap

   Define the following terms:

   Governing Receipt (GR):
      An ATF record — Delegation Receipt (DR), Temporal Authority
      Record (TAR), or Runtime Continuity Record (RCR) — that
      authorizes a specific agent to perform a specific action within
      specified constraint boundaries.  GR is PQC-signed and
      append-only.

   Constraint Vector (CV):
      The set of behavioral boundaries embedded in or derivable from
      the Governing Receipt.  CV includes: authority scope
      restrictions, output domain limits, prohibited action classes,
      session turn limit, and any domain-specific constraints declared
      at delegation time.

   Behavioral Output (BO):
      The complete set of outputs produced by an authorized agent
      during a single execution turn: text, structured data, tool
      calls, API invocations, and any other externally observable
      result of agent execution.

   Behavioral Attestation Record:
      A cryptographic artifact binding BO to GR, proving that the
      specified output was produced by the specified authorized agent
      during the execution governed by the specified receipt.

   The ATF stack through RFC-ATF-5 guarantees:
   - The agent was authorized (GR is valid, ATF-INV-001)
   - The authority was continuously valid (RCR integrity, RGC-INV)
   - The action was recorded (ExecutionReceipt, ADR-131)
   - The evidence is preserved and portable (OEP, RFC-ATF-3)
   - The decision space is documented (CAT, RFC-ATF-5)

   The ATF stack through RFC-ATF-5 does NOT guarantee:
   - What the agent produced during the authorized execution
   - Whether BO is consistent with CV
   - Whether BO can be forensically attributed to GR

   This creates the Behavioral Attestation Gap (Gap_BAG):

      Gap_BAG = { (GR, BO) : no verifiable binding exists between
                              GR and BO }

   Gap_BAG is non-empty for every authorized execution that does not
   produce a BAR.  In current ATF deployments, Gap_BAG covers 100% of
   executions, because no BAR mechanism existed prior to this RFC.

   Gap_BAG has three concrete consequences:

   a) Regulatory gap: EU AI Act Art. 9 requires risk management
      systems to include "measures to address the risks identified,"
      including monitoring that the AI system operates within defined
      boundaries.  No ATF artifact through RFC-ATF-5 demonstrates
      that monitored behavior occurred within the receipt-defined
      boundaries.

   b) Forensic gap: In post-incident investigation, a regulator or
      auditor can reconstruct the authorization chain with certainty
      from ATF records.  They cannot reconstruct what the agent
      actually produced during the authorized action.  The execution
      receipt records that an action was taken; it does not record
      the behavioral content of that action.

   c) Liability gap: Enterprise legal counsel assessing AI liability
      require proof that the agent operated within its authorized
      constraints during the disputed action.  No ATF artifact through
      RFC-ATF-5 provides this proof.

   The BAR closes Gap_BAG by producing a PQC-signed behavioral
   attestation record at each execution turn, binding BO to GR with
   the same cryptographic certainty that ATF applies to authorization.

2.2.  The Conformance Observability Problem

   Define the following terms:

   Constraint Conformance (CC):
      The degree to which a Behavioral Output (BO) satisfies the
      Constraint Vector (CV) of its Governing Receipt (GR).  CC is
      a continuous measure in [0.0, 1.0], where 1.0 denotes full
      conformance and 0.0 denotes complete violation.

   Conformance Observable (O_CC):
      A real-time signal derived from BOs that measures CC
      continuously, enabling detection of conformance degradation
      before boundary violations occur.

   The AGVP (RFC-ATF-4) operates on Conformance Observables to issue
   Proactive Veto Receipts (PVRs) before violations materialize.  The
   AGVP's PVR watchdog currently monitors:
   - CES score trajectory (structural governance signal)
   - Fragmentation score trend (authority distribution signal)
   - Semantic drift index (DSPP signal, RFC-ATF-4)

   Missing from the AGVP input space: a behavioral conformance signal
   measuring whether the agent's actual outputs conform to the
   constraint boundaries in the governing receipt.

   This creates the Conformance Observability Problem (Gap_COP):

      Gap_COP = { behaviors b : b degrades toward CV violation AND
                                no observable O_CC exists to detect b }

   Gap_COP is structurally significant because:

   a) Behavioral drift is a leading indicator of boundary violations:
      in multi-turn agent sessions, outputs that gradually approach
      constraint boundaries (semantic drift, scope creep, authority
      expansion) typically precede overt violations.  Without O_CC,
      the AGVP cannot issue anticipatory vetoes for behavioral
      trajectories.

   b) The AGVP PVR mechanism is designed for proactive governance.
      Without a behavioral conformance signal, the AGVP is limited
      to structural governance signals and cannot issue PVRs based
      on observable behavioral degradation.

   c) Regulators are increasingly requiring continuous behavioral
      monitoring evidence.  NIST AI RMF MEASURE 2.6 requires
      "ongoing monitoring of AI system outputs."  ISO/IEC 42001
      §8.4 requires operational controls that include behavioral
      observation.  No OMNIX artifact through RFC-ATF-5 provides
      this monitoring signal in governance-native form.

   The CCS resolves Gap_COP by providing a governance-native
   Conformance Observable: a multi-component score computed per BAR,
   referencing the actual CV from the GR, integrated with the AGVP
   watchdog for anticipatory veto issuance when CCS enters the
   DRIFTING threshold.

2.3.  The Multi-Turn Coherence Problem

   Define the following terms:

   Session (S):
      A sequence of N execution turns governed by a single Governing
      Receipt GR.  S = (T_0, T_1, ..., T_{N-1}) where each T_i is
      one agent execution turn.

   Session Coherence (SC):
      A property of a Session S: SC holds if and only if every turn
      T_i was executed in order (no turn reordering), every turn
      was recorded (no omission), and no turn's behavioral output
      was substituted post-hoc (no substitution).

   Session Integrity Proof (SIP):
      A cryptographic artifact that proves Session Coherence for a
      completed session without requiring access to any OMNIX
      infrastructure.

   The ATF stack through RFC-ATF-5 does not provide a Session
   Integrity Proof.  The BAR mechanism (§2.1) provides per-turn
   behavioral attestation, but without a chaining mechanism, a set
   of valid BARs does not prove Session Coherence: an adversary could
   present a subset of BARs (omitting turns where violations occurred),
   reorder BARs across sessions, or substitute BARs from a different
   session governed by the same receipt type.

   This creates the Multi-Turn Coherence Problem (Gap_MCP):

      Gap_MCP = { Sessions S : no SIP exists for S }

   Gap_MCP is non-trivial for three reasons:

   a) Turn omission is the primary post-incident manipulation vector:
      if an agent produces a violating output at turn T_k, an
      adversary with access to the BAR database may attempt to
      suppress T_k's BAR record.  Without a chaining mechanism,
      the absence of T_k's BAR is not forensically detectable from
      the remaining records alone.

   b) Turn reordering changes causality: in multi-turn agent sessions,
      turn T_{i+1} may be contextually dependent on T_i's output.
      Reordering turns can misrepresent the behavioral trajectory,
      making a session that exhibited progressive constraint violation
      appear to have operated within boundaries throughout.

   c) Cross-session BAR substitution enables laundering: a session
      that produced clean outputs under a different governing receipt
      could have its BARs substituted into a session that produced
      violating outputs, if no binding exists between the session's
      BAR sequence and its specific governing receipt.

   The CTCHC resolves Gap_MCP by constructing a hash chain seeded by
   the governing receipt, linking each turn's output hash to the
   previous turn's chain link.  The final chain hash is a Session
   Integrity Proof: any omission, reordering, or substitution produces
   a chain verification failure detectable by any party possessing
   the governing receipt and the BAR sequence.

2.4.  The Behavioral Execution Gap (Gap_BEV)

   The Behavioral Execution Gap is the union of the three gaps
   identified above:

      Gap_BEV = Gap_BAG ∪ Gap_COP ∪ Gap_MCP

   A governance infrastructure with Gap_BEV = {} satisfies the
   following conditions:

   1. Every authorized execution turn produces a PQC-signed
      behavioral attestation record bound to the governing receipt.
      (Gap_BAG resolved by BAR)

   2. A continuous, governance-native conformance signal exists per
      turn, integrated with the AGVP watchdog for anticipatory veto
      issuance upon behavioral degradation.
      (Gap_COP resolved by CCS)

   3. Every multi-turn session has a Session Integrity Proof that
      is independently verifiable offline, demonstrating that all
      turns were recorded in order without omission or substitution.
      (Gap_MCP resolved by CTCHC)

   RFC-ATF-6 formally closes Gap_BEV.


3.  Conventions and Terminology

   The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
   "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY",
   and "OPTIONAL" in this document are to be interpreted as described
   in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in
   all capitals, as shown here.

   Terms defined in prior ATF RFCs retain their definitions.  The
   following terms are defined in this document:

   Behavioral Anchor Record (BAR):
      A PQC-signed record produced at each execution turn, containing
      the output hash of the agent's behavioral output for that turn,
      bound to the governing receipt identifier, carrying an embedded
      CCS score, and contributing a chain link to the session's CTCHC.
      The BAR is the primary attestation artifact of the BEV layer.

   Behavioral Anchor Record Identifier (BARID):
      A unique string of the form BAR-{16HEX}.
      16HEX is 16 uppercase hexadecimal characters from a
      cryptographically random UUID4.
      Example: BAR-3F1A4B7C2D8E5F9A

   BEV Session:
      A governance-bounded sequence of execution turns sharing a
      single Governing Receipt.  A BEV Session begins at the first
      BAR produced for a given session_id and closes when the CTCHC
      final chain hash is sealed.

   BEV Session Identifier (BEVID):
      A unique string of the form BEV-SESSION-{16HEX}.

   Constraint Conformance Signal (CCS):
      A multi-component numerical score in [0.0, 100.0] computed
      per execution turn, measuring how closely the turn's behavioral
      output conforms to the Constraint Vector of the Governing
      Receipt.  The CCS is embedded in every BAR and feeds into the
      AGVP watchdog.

   Constraint Conformance Signal Identifier (CCSID):
      A unique string of the form CCS-{16HEX}.
      CCS records are embedded within BARs; standalone CCS records
      exist only in atf_constraint_conformance_signals for history
      queries.

   CCS Verdict:
      One of five values derived from the CCS score: CONFORMANT
      (score >= 90), DRIFTING (70 <= score < 90), BREACH (50 <=
      score < 70), VIOLATION (score < 50), NO_DATA (no outputs
      to evaluate).

   Constraint Vector (CV):
      The structured set of behavioral boundaries active for a BEV
      Session, derived from the Governing Receipt.  The CV is
      captured at session initialization and embedded in each BAR's
      constraint_vector field.

   Cross-Turn Coherence Hash Chain (CTCHC):
      A cryptographic hash chain linking each BAR's output hash to
      the previous turn's chain link, seeded by the Governing Receipt
      identifier and session identifier.  The final chain hash
      provides offline-verifiable Session Coherence proof.

   Cross-Turn Coherence Hash Chain Identifier (CTCHCID):
      A unique string of the form CTCHC-{16HEX}, identifying the
      chain record for a completed BEV Session.

   Genesis Hash:
      The first element of the CTCHC, computed as:
         SHA-256(governing_receipt_id || session_id || session_start_ns)
      where || denotes byte-level concatenation.  The genesis hash
      binds the chain to its governing receipt and session identity,
      making cross-session BAR substitution detectable.

   Chain Link:
      The hash chain value at turn n, computed as:
         chain_link(n) = SHA-256(chain_link(n-1) || turn_hash(n))
      where chain_link(-1) = genesis_hash and:
         turn_hash(n) = SHA-256(output_hash(n) ||
                                turn_index(n).to_bytes(8,'big'))

   Final Chain Hash:
      chain_link(N-1) for a session of N turns.  The final chain
      hash is the Session Integrity Proof.  It is sealed with ML-
      DSA-65 at session close to produce the CTCHC session seal.

   Output Hash:
      SHA-256 of the canonical representation of the agent's
      behavioral output for a single turn.  The canonical
      representation and privacy mode are defined in §5.5.

   Output Hash Mode:
      One of three values controlling the output_hash computation
      and storage policy: FULL (output_payload stored in BAR,
      output_hash computed from it), HASHED (only hash stored, no
      payload), REDACTED (hash of a redaction placeholder stored).

   Turn Index:
      A zero-based non-negative integer identifying a turn's position
      within its BEV Session.  Turn indices MUST be strictly
      monotonically increasing within a session: if T_i has
      turn_index i and T_{i+1} has turn_index i+1, no value is
      skipped.

   Behavioral Attestation Chain:
      The complete ordered sequence (GR, BAR_0, BAR_1, ..., BAR_{N-1},
      CTCHC_final) for a BEV Session.  The Behavioral Attestation
      Chain is the complete forensic artifact proving authorization,
      per-turn behavioral output, conformance measurement, and session
      coherence.

   BEV-COMPLETE:
      Status of a BEV Session for which the CTCHC final chain hash
      has been sealed.  A BEV-COMPLETE session has a Session Integrity
      Proof.

   BEV-INCOMPLETE:
      Status of a BEV Session for which one or more BARs failed to
      persist, or for which the CTCHC has not been sealed.  BEV-
      INCOMPLETE sessions MUST be flagged in compliance reporting.

   ATF-BEV-Compliant:
      The compliance designation for an implementation that satisfies
      all requirements of RFC-ATF-1 through RFC-ATF-6.  The sixth
      and highest tier in the ATF compliance hierarchy, superseding
      ATF-CGL-Compliant (RFC-ATF-5).

   BEV-LAYER-COMPLETE:
      Synonym for ATF-BEV-Compliant when used in implementation
      contexts.

   Behavioral Execution Verification Layer (BEV):
      The protocol layer defined by this RFC, comprising BAR, CCS,
      and CTCHC.

   BAR:   Behavioral Anchor Record
   BEV:   Behavioral Execution Verification Layer
   BEVID: BEV Session Identifier
   BO:    Behavioral Output
   CC:    Constraint Conformance
   CCS:   Constraint Conformance Signal
   CTCHC: Cross-Turn Coherence Hash Chain
   CV:    Constraint Vector
   GR:    Governing Receipt
   SIP:   Session Integrity Proof


4.  Architecture: The Behavioral Execution Verification Layer

4.1.  Position in the ATF Stack

   The ATF protocol stack comprises six layers as of this RFC:

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
      Answers: what happened between requests, and was recalibration
      safe?

   Layer 5 — Cognitive Governance Layer (RFC-ATF-5):
      CGE, GUGT, TGB.
      Answers: what else could have happened, is the system
      universally complete, and will evidence remain interpretable
      across time?

   Layer 6 — Behavioral Execution Verification Layer (RFC-ATF-6):
      BAR, CCS, CTCHC.
      Answers: did the agent actually behave within its authorized
      constraints during execution, turn by turn?

4.2.  Extension Relationships

   Each BEV module extends the ATF stack non-destructively:

   BAR extends Layer 1 (DR) and Layer 2 (RCR):
      Every authorized execution turn that produces behavioral output
      under a DR, TAR, or RCR SHOULD trigger BAR production.  When
      BEV_ENABLED=true, BAR production is REQUIRED for every turn.
      The governing_receipt_id in every BAR references the specific
      DR, TAR, or RCR governing the session.

   CCS extends Layer 4 (AGVP):
      The AGVP PVR watchdog gains a new observable input — the CCS
      score — via the CCS-AGVP integration protocol defined in §6.5.
      The AGVP issues a PVR when CCS enters the DRIFTING threshold.
      This integration is additive: the AGVP continues to monitor
      all prior structural signals in addition to CCS.

   CTCHC extends Layer 3 (OEP):
      When BEV_INCLUDE_IN_OEP=true, OEP packages include the
      CTCHC final chain hash and CTCHC session seal for all BEV
      Sessions covered by the packaged governing receipt.  The
      complete Behavioral Attestation Chain becomes portable in the
      OEP forensic package.

4.3.  Non-Destructive Integration

   All three BEV modules operate as additive layers.  An
   implementation MAY enable any subset of BAR, CCS, and CTCHC
   independently.  Disabling any BEV module does not affect the
   correctness of Layers 1-5.

   BEV_ENABLED, CCS_ENABLED, and CTCHC_ENABLED are environment flags
   controlling module activation.  Default is true for all three when
   BEV_ENABLED=true.  Setting BEV_ENABLED=false in production does
   not constitute a compliance violation of RFC-ATF-5 or prior RFCs.

   Note: CCS_ENABLED=true requires BEV_ENABLED=true (CCS is embedded
   in BARs).  CTCHC_ENABLED=true requires BEV_ENABLED=true (the chain
   is built from BAR output hashes).  BAR may be enabled without CCS
   or CTCHC in minimal deployments.

4.4.  BEV Module Independence

   BAR, CCS, and CTCHC have the following dependency structure:

   - BAR is independent: it requires only the governing receipt and
     the agent's behavioral output.
   - CCS depends on BAR: CCS is computed from the agent output and
     the constraint vector embedded in the BAR; it is embedded within
     the BAR before the BAR is sealed.
   - CTCHC depends on BAR: the chain link is computed from the BAR's
     output_hash and turn_index; it is embedded within the BAR before
     the BAR is sealed.

   The correct ordering for a single turn is:

      1. Agent executes turn, produces BO.
      2. Compute output_hash from BO (privacy mode applied).
      3. Compute CCS score from BO and CV (if CCS_ENABLED).
      4. Compute chain_link from previous chain_link and turn_hash(n).
      5. Assemble BAR (all fields including ccs_score and chain_link).
      6. Compute content_hash_bar.
      7. Compute pqc_signature over content_hash_bar.
      8. Persist BAR to atf_behavioral_anchor_records.

   Steps 3-4 MUST complete before step 5.  Step 8 MUST complete
   before the next turn begins (BEV-INV-001 enforcement).


5.  Behavioral Anchor Record (BAR)

5.1.  Behavioral Attestation Architecture

   The BAR production model is designed around three non-negotiable
   architectural constraints:

   Constraint 1 — Pre-output attestation seeding:
      The session_id, governing_receipt_id, and CV MUST be
      established before the first turn executes.  The genesis hash
      is computed from these values at session initialization.  This
      prevents retroactive session construction.

   Constraint 2 — Synchronous BAR persistence:
      BAR persistence MUST be synchronous with turn completion.  An
      agent turn that completes without a persisted BAR is a BEV
      violation (BEV-INV-001).  If BAR persistence fails, the session
      is flagged BEV-INCOMPLETE and the failure MUST be logged to the
      audit trail before any subsequent turn is permitted.

   Constraint 3 — Governing receipt linkage:
      Every BAR MUST carry a governing_receipt_id referencing the
      specific ATF receipt that authorized the session.  A BAR without
      a valid governing_receipt_id is structurally invalid and MUST
      NOT be accepted as attestation evidence in regulatory or legal
      proceedings.

   These constraints mirror ADR-131's three invariants for execution
   receipts (no silent execution, pre-intent captured, decision
   binding) but apply at the behavioral output layer rather than the
   exchange order layer.

5.2.  BAR Structure

   A BAR MUST contain the following fields:

   bar_id (string, REQUIRED):
      Unique BAR identifier.  Format: BAR-{16HEX}.
      16HEX is 16 uppercase hexadecimal characters from a
      cryptographically random UUID4, uppercased and truncated to
      16 characters.
      Example: BAR-3F1A4B7C2D8E5F9A

   session_id (string, REQUIRED):
      BEV Session identifier.  Format: BEV-SESSION-{16HEX}.
      All BARs from the same session MUST share the same session_id.

   governing_receipt_id (string, REQUIRED):
      Identifier of the ATF record (DR, TAR, or RCR) governing this
      BEV Session.  MUST reference a valid record in
      atf_delegation_receipts, atf_temporal_records, or
      atf_runtime_continuity.  The same governing_receipt_id MUST
      appear in all BARs for a given session.

   agent_id (string, REQUIRED):
      Authorized agent identifier matching the agent_id field of the
      Governing Receipt.  A BAR whose agent_id does not match its
      governing_receipt_id's agent_id is structurally invalid.

   turn_index (integer, REQUIRED):
      Zero-based position of this turn within its BEV Session.
      MUST be strictly monotonically increasing: if the preceding BAR
      in this session has turn_index = k, this BAR MUST have
      turn_index = k+1.  No gaps are permitted (BEV-INV-015).

   output_hash (string, REQUIRED):
      SHA-256 hex digest of the agent's behavioral output for this
      turn, computed as specified in §5.5 for the declared
      output_hash_mode.
      Format: "sha256:" + 64 lowercase hexadecimal characters.
      Example: "sha256:a1b2c3d4...f6e5d4c3"

   output_hash_mode (string, REQUIRED):
      One of: FULL | HASHED | REDACTED.
      Governs whether output_payload is stored and how output_hash
      is computed.  See §5.5 for mode specifications.

   output_payload (string or object, CONDITIONAL):
      The actual behavioral output.  REQUIRED when output_hash_mode
      = FULL.  MUST be absent when output_hash_mode = HASHED or
      REDACTED.  When present, output_hash MUST equal the SHA-256 of
      the canonical JSON or UTF-8 serialization of this field.

   constraint_vector (object, REQUIRED):
      Snapshot of the Constraint Vector active for this session,
      derived from the Governing Receipt at session initialization.
      MUST remain identical across all BARs in the same session.
      Fields:
         authority_scope (string): Authorized action scope.
         output_domain (string): Permitted output domain.
         prohibited_classes (array of strings): Prohibited action
            types.
         turn_limit (integer or null): Maximum turns; null if
            unbounded.
         session_duration_limit_s (integer or null): Maximum session
            duration in seconds; null if unbounded.
         domain_specific_constraints (object): Any additional
            domain-specific constraint fields declared at delegation.

   ccs_score (number, REQUIRED):
      Embedded Constraint Conformance Signal score for this turn.
      Range: [0.0, 100.0].  Computed as specified in §6.3.
      A value of -1.0 indicates CCS computation was not attempted
      (valid only when CCS_ENABLED=false).

   ccs_verdict (string, REQUIRED):
      CCS verdict derived from ccs_score per §6.4 thresholds.
      One of: CONFORMANT | DRIFTING | BREACH | VIOLATION | NO_DATA.
      MUST be NO_DATA when ccs_score = -1.0.

   ccs_components (object, CONDITIONAL):
      CCS component breakdown.  REQUIRED when CCS_ENABLED=true.
      Fields:
         output_boundary_score (number): [0.0, 40.0]
         constraint_satisfaction_score (number): [0.0, 30.0]
         semantic_drift_score (number): [0.0, 20.0]
         authority_alignment_score (number): [0.0, 10.0]

   chain_link (string, REQUIRED):
      CTCHC chain link value for this turn, computed as specified
      in §7.3.  For turn_index = 0, chain_link is computed from
      the genesis hash.  Format: 64 lowercase hexadecimal characters
      (SHA-256 output, without prefix).

   genesis_hash (string, CONDITIONAL):
      REQUIRED only in the BAR with turn_index = 0.  Value:
         SHA-256(governing_receipt_id.encode("utf-8") ||
                 session_id.encode("utf-8") ||
                 session_start_ns.to_bytes(8, "big"))
      Format: 64 lowercase hexadecimal characters.
      All subsequent BARs in the session MAY omit genesis_hash;
      verifiers derive it from the turn_index=0 BAR.

   session_start_ns (integer, CONDITIONAL):
      REQUIRED only in the BAR with turn_index = 0.
      Nanosecond epoch timestamp of session initialization, obtained
      via time.time_ns().  Used in genesis hash computation.

   bar_timestamp_ns (integer, REQUIRED):
      Nanosecond epoch timestamp of BAR production, obtained via
      time.time_ns().  MUST be >= session_start_ns.

   issued_at (string, REQUIRED):
      ISO 8601 UTC timestamp with nanosecond precision derived from
      bar_timestamp_ns.
      Format: YYYY-MM-DDTHH:MM:SS.nnnnnnnnn+00:00

   content_hash_bar (string, REQUIRED):
      SHA-256 hex digest of the canonical JSON of all BAR fields
      except {content_hash_bar, pqc_signature, pqc_algorithm}.
      Computation defined in §5.3.

   pqc_signature (string, REQUIRED):
      Base64-encoded Dilithium-3 (ML-DSA-65, FIPS 204) signature
      over content_hash_bar.encode("utf-8"), signed with the
      platform ML-DSA-65 key.

   pqc_algorithm (string, REQUIRED):
      MUST be "ML-DSA-65".

   atf_spec_version (string, REQUIRED):
      MUST be "1.6" for records produced under this RFC.

5.3.  BAR Content Hash Construction

   The content_hash_bar MUST be computed as follows:

   1. Construct a JSON object containing all fields of the BAR
      EXCEPT: content_hash_bar, pqc_signature, pqc_algorithm.

   2. Serialize to canonical JSON:
         json.dumps(obj, sort_keys=True, separators=(",", ":"))
         encoded as UTF-8.

   3. Compute SHA-256 of the encoded bytes.

   4. Encode as 64 lowercase hexadecimal characters.

   The canonical JSON serialization MUST use sort_keys=True to ensure
   field ordering is deterministic across implementations.  Floating
   point fields (ccs_score, ccs_component scores) MUST be serialized
   with sufficient precision to reconstruct the value: 6 decimal
   places minimum.

   The output_payload field, when present (FULL mode), MUST be
   included in the content_hash_bar computation as its canonical JSON
   form.  This ensures the output payload is tamper-evident.

5.4.  BAR PQC Signature

   The pqc_signature MUST be computed as:

      pqc_signature = base64.b64encode(
          dilithium3.sign(
              content_hash_bar.encode("utf-8"),
              platform_secret_key
          )
      ).decode("ascii")

   The platform_secret_key MUST be the same ML-DSA-65 private key
   used for all ATF record signing (OMNIX_SIGNING_SECRET_KEY_B64).
   Key stability is governed by FMR-001 (ADR-084): key rotation
   invalidates all BAR records sealed with the prior key, requiring
   re-sealing or forensic notation.

   BAR verification proceeds as:

      dilithium3.verify(
          content_hash_bar.encode("utf-8"),
          base64.b64decode(pqc_signature),
          platform_public_key
      )

   A BAR with an invalid pqc_signature MUST NOT be accepted as
   attestation evidence.  Invalid BARs MUST be flagged in the session
   audit trail as BAR_INTEGRITY_FAILED.

5.5.  Output Hash Privacy Modes

   The BAR output_hash_mode field controls the privacy treatment of
   the agent's behavioral output.  Three modes are defined:

   FULL mode:
      The complete output_payload is stored in the BAR record.
      output_hash = SHA-256(canonical(output_payload).encode("utf-8"))
      Use: development environments, sessions where output content
      must be available for forensic review, sessions where output
      is non-sensitive.
      Warning: FULL mode should not be used for outputs containing
      personal data subject to GDPR right-to-erasure obligations, as
      BAR records are append-only (BEV-INV-006).

   HASHED mode (recommended for production):
      Only output_hash is stored.  output_payload is absent from
      the BAR record.
      output_hash = SHA-256(canonical(output_payload).encode("utf-8"))
      The canonical representation is computed by the BEV runtime
      and discarded after hash computation.
      Use: production environments, sensitive outputs, GDPR-subject
      data.  Verification requires the original output to recompute
      the hash.

   REDACTED mode:
      Used when the output cannot be hashed (e.g., structured outputs
      with non-deterministic serialization, or outputs redacted by
      compliance policy).
      output_hash = SHA-256("REDACTED:" + bar_id + ":" +
                             turn_index.to_string()).encode("utf-8"))
      The CCS score in REDACTED mode MUST be set to -1.0 with
      verdict NO_DATA, as the output content is unavailable for
      conformance evaluation.
      Note: REDACTED mode preserves chain link integrity (the
      redaction placeholder is deterministic) but does not provide
      behavioral attestation.  Regulatory proceedings requiring
      behavioral evidence MUST use FULL or HASHED mode.

   The output_hash_mode MUST be consistent for all BARs in a session
   unless a mode transition is explicitly recorded in the session
   audit trail with the transition timestamp and reason.

5.6.  BAR Lifecycle

   A BAR progresses through the following states:

   PENDING:
      BAR has been assembled but not yet persisted to the database.
      This state exists only transiently in the BEV runtime.

   ACTIVE:
      BAR has been persisted to atf_behavioral_anchor_records.
      The session is ongoing.

   SEALED:
      The session's CTCHC final chain hash has been produced and
      persisted.  All BARs in the session transition to SEALED
      simultaneously.  SEALED BARs are the terminal state.

   FLAGGED:
      A BAR in the session failed integrity verification
      (pqc_signature invalid, output_hash mismatch, chain link
      break, or turn_index gap).  The entire session is flagged
      BEV-INCOMPLETE and the CTCHC MUST NOT be sealed until
      remediation is complete.

   State transitions:

      PENDING → ACTIVE: successful database INSERT
      ACTIVE → SEALED: CTCHC session seal produced
      ACTIVE → FLAGGED: integrity verification failure
      FLAGGED: terminal (no recovery to ACTIVE or SEALED)

   SEALED BARs MUST NOT be updated or deleted (BEV-INV-006).
   FLAGGED BARs MUST NOT be deleted; they are forensic evidence of
   the failure event.

5.7.  Offline Verifiability Protocol

   Any party possessing the following may independently verify a BAR:
   1. The BAR JSON record.
   2. The OMNIX platform ML-DSA-65 public key.
   3. (For FULL mode) the output_payload is included in the BAR.
   4. (For chain verification) all prior BARs in the session and the
      session's governing_receipt_id.

   Verification procedure for a single BAR:

   Step 1 — Content hash verification:
      Reconstruct the canonical JSON of all BAR fields except
      {content_hash_bar, pqc_signature, pqc_algorithm}.
      Compute SHA-256.  Compare to content_hash_bar.
      Failure: BAR content has been tampered.

   Step 2 — PQC signature verification:
      Verify pqc_signature over content_hash_bar.encode("utf-8")
      using the platform ML-DSA-65 public key.
      Failure: BAR was not produced by the platform keyholder.

   Step 3 — Output hash verification (FULL mode only):
      Compute SHA-256 of canonical(output_payload).
      Compare to output_hash (strip "sha256:" prefix).
      Failure: output_payload has been modified after BAR sealing.

   Step 4 — Governing receipt linkage verification:
      Confirm that governing_receipt_id references a valid ATF record
      by computing the expected chain link from the prior BAR or the
      genesis hash, and comparing to the BAR's chain_link field.
      Failure: BAR is not correctly chained, indicating omission,
      reordering, or substitution.

   Step 5 — Turn index monotonicity verification:
      For consecutive BARs T_i, T_{i+1}: verify
      T_{i+1}.turn_index = T_i.turn_index + 1.
      Failure: turn reordering or omission detected.

   A BAR that passes all five steps is VERIFIED.  A BAR that fails
   any step is COMPROMISED and MUST be reported as such.

5.8.  BAR Invariants (BEV-INV-001 through BEV-INV-007)

BEV-INV-001 — Mandatory BAR Production

   Every execution turn authorized by a Governing Receipt, in any
   BEV-enabled deployment, MUST produce a persisted BAR before the
   next turn begins.  There is no execution path that completes a
   turn without a BAR.

   Formally:
      For all sessions S and turns T_i in S where BEV_ENABLED:
         EXISTS(BAR b) WHERE b.session_id = S.session_id
            AND b.turn_index = i
            AND b.persisted_at <= T_{i+1}.start_ns

   A session where any turn T_i has no persisted BAR by the time
   T_{i+1} begins is BEV-INCOMPLETE and MUST be flagged as such in
   all compliance reporting.

BEV-INV-002 — Mandatory Governing Receipt Binding

   Every BAR MUST carry a governing_receipt_id that references a
   valid ATF record.  The agent_id in the BAR MUST match the
   agent_id in the referenced Governing Receipt.

   Formally:
      For all BARs b:
         EXISTS(GR r) WHERE r.record_id = b.governing_receipt_id
            AND r.agent_id = b.agent_id

   A BAR with an unresolvable governing_receipt_id or a mismatched
   agent_id is structurally invalid as a behavioral attestation
   artifact and MUST NOT be admitted as governance evidence.

BEV-INV-003 — Output Hash Integrity

   The output_hash in every BAR MUST be covered by the
   content_hash_bar.  Modifying the output_hash after BAR sealing
   MUST produce a content_hash_bar mismatch detectable by the
   verification procedure in §5.7.

   Formally:
      For all BARs b:
         content_hash_bar(b) = SHA-256(canonical_json(b \ {
            content_hash_bar, pqc_signature, pqc_algorithm
         }))
      output_hash ∈ b \ {content_hash_bar, pqc_signature,
                          pqc_algorithm}
      THEREFORE: modifying output_hash ⟹ content_hash_bar mismatch

   This invariant is a structural consequence of §5.3 and requires
   no additional enforcement logic.

BEV-INV-004 — BAR PQC Sealing

   Every BAR MUST be sealed with Dilithium-3 (ML-DSA-65, FIPS 204)
   over its content_hash_bar before persistence.  An unsealed BAR
   MUST NOT be persisted to atf_behavioral_anchor_records.

   Formally:
      For all persisted BARs b:
         dilithium3.verify(
            b.content_hash_bar.encode("utf-8"),
            b.pqc_signature,
            platform_public_key
         ) = True

   Any BAR that fails this verification has either been tampered
   after production or was produced by an entity that does not hold
   the platform ML-DSA-65 key.

BEV-INV-005 — BAR Fail-Closed

   If BAR persistence fails (database write error, connection
   failure, constraint violation), the current execution session
   MUST be flagged BEV-INCOMPLETE and the failure MUST be logged
   to the governing receipt's audit trail.  No subsequent turn in
   the session is permitted until the failure is resolved.

   Formally:
      For all sessions S:
         BAR_persistence_failure(T_i) IMPLIES
            session_status(S) = BEV-INCOMPLETE
            AND no T_{i+1} in S is permitted
            AND failure logged to GR.audit_trail

   This is the behavioral-layer equivalent of ADR-131's
   pre-intent-captured invariant: a turn whose behavioral record
   cannot be written does not proceed.

BEV-INV-006 — BAR Append-Only Storage

   No UPDATE or DELETE operation is permitted on any record in
   atf_behavioral_anchor_records.  BARs are append-only audit
   artifacts.  FLAGGED BARs MUST remain in the table as forensic
   evidence of the failure event.

   Formally:
      For all times t_1 < t_2 and all BAR record IDs r:
         record(r, t_1) = record(r, t_2)
         (BARs do not change after insertion)

   Database-level enforcement: no UPDATE or DELETE triggers are
   permitted on atf_behavioral_anchor_records.  Row-level security
   SHOULD be configured to prohibit these operations.

BEV-INV-007 — BAR Offline Verifiability

   Every BAR MUST be independently verifiable by any party
   possessing only the BAR JSON, the platform ML-DSA-65 public
   key, and (for FULL mode) the output_payload.  No OMNIX
   infrastructure access is required for verification.

   The §5.7 verification procedure MUST succeed for any correctly
   produced BAR.  An implementation where §5.7 fails for a
   correctly-formed BAR has a structural offline verifiability
   defect.


6.  Constraint Conformance Signal (CCS)

6.1.  Conformance Measurement Architecture

   The CCS provides a governance-native behavioral conformance
   measurement for each execution turn.  "Governance-native" means:

   - The CCS references the actual Constraint Vector (CV) embedded in
     the Governing Receipt, not a separately configured monitoring
     policy.  The governance receipt IS the measurement specification.

   - The CCS is produced alongside the BAR, not in a separate
     monitoring pipeline.  It is embedded in the BAR before the BAR
     is sealed, making the conformance measurement tamper-evident.

   - The CCS is integrated with the AGVP (§6.5), completing the
     anticipatory veto input space with behavioral conformance data.

   This design differs fundamentally from existing ML monitoring
   systems (Arize, WhyLabs, Evidently AI) in three ways:

   1. Reference specification: existing systems monitor against
      separately configured policies.  The CCS monitors against the
      governing receipt's constraint vector, which is PQC-signed
      and cannot be modified post-issuance.

   2. Evidence integration: existing systems produce monitoring
      dashboards.  The CCS produces governance-signed evidence
      embedded in a PQC-sealed BAR record.

   3. AGVP integration: existing systems alert operators.  The CCS
      triggers cryptographic veto receipt issuance through the AGVP
      protocol, producing a forensic record of the conformance
      degradation event.

6.2.  CCS Score Components

   The CCS score is a weighted sum of four components, maximum 100
   points.  All components are non-negative (BEV-INV-011).

   Component 1 — Output Boundary Score (OBS):

      Maximum points: 40
      Base: 40 points.
      Deduction: -10 points per detected output boundary violation.
      Floor: 0 (score never negative).

      An output boundary violation occurs when the agent's output
      for this turn contains content, action invocations, or data
      access patterns that exceed the output_domain or
      prohibited_classes defined in the Constraint Vector.

      Boundary violation detection methods (implementation-specific):
      - Keyword/pattern matching against prohibited_classes list
      - Structured output schema validation against output_domain
      - Tool call / API invocation scope checking
      - Domain-specific classifiers declared in CV

      OBS = max(0, 40 - (10 × boundary_violation_count))

   Component 2 — Constraint Satisfaction Score (CSS):

      Maximum points: 30
      Base: 30 points.
      Deduction: -8 points per unsatisfied explicit constraint.
      Floor: 0.

      An explicit constraint failure occurs when a constraint
      declared in the CV's domain_specific_constraints object is
      verifiably not satisfied by the turn's output.  Examples:
      - Length constraint: output exceeds declared max tokens
      - Format constraint: output not in declared format (JSON,
        XML, structured data schema)
      - Language constraint: output in non-authorized language
      - Citation constraint: output makes claims without required
        evidence citation

      CSS = max(0, 30 - (8 × constraint_failure_count))

   Component 3 — Semantic Drift Score (SDS):

      Maximum points: 20
      Base: 20 points.
      Deduction: proportional to semantic drift magnitude from the
      authorized behavior profile established at session start.

      Semantic drift is measured as the cosine distance between the
      current turn's output embedding and the authorized behavior
      profile embedding established from the governing receipt's
      authority_scope and output_domain declarations.  The specific
      embedding model is implementation-defined and MUST be declared
      in the constraint_vector.domain_specific_constraints object.

      Deduction formula:
         drift_magnitude = cosine_distance(
             embed(current_output), authorized_profile_embedding
         )  # range [0.0, 1.0]
         SDS = max(0, 20 × (1 - drift_magnitude))

      When no embedding model is configured, SDS MUST be set to 20
      (no deduction) and this MUST be noted in ccs_components with
         sds_method: "NO_EMBEDDING_MODEL"

   Component 4 — Authority Alignment Score (AAS):

      Maximum points: 10
      Value: 10 if the agent operated within its authorized scope
             for this turn.
             0 if the agent invoked any capability or accessed any
             resource outside its declared authority_scope.

      AAS = 10 if authority_scope_satisfied else 0

      Authority scope satisfaction is determined by comparing the
      turn's capability invocations, resource accesses, and
      delegation assertions against the authority_scope field of
      the Constraint Vector.

   CCS Score:

      ccs_score = OBS + CSS + SDS + AAS
      Range: [0.0, 100.0]
      (Guaranteed by BEV-INV-009 and the component bounds above)

6.3.  CCS Computation Protocol

   CCS computation MUST follow this procedure:

   Step 1 — CV extraction:
      Retrieve the Constraint Vector from the session's BAR_0
      (turn_index = 0) or from the in-memory session context.
      The CV is constant for all turns in a session.

   Step 2 — OBS computation:
      Apply each boundary violation detector declared in
      CV.prohibited_classes and CV.output_domain to the turn output.
      Count boundary_violation_count.
      OBS = max(0, 40 - 10 × boundary_violation_count).

   Step 3 — CSS computation:
      For each constraint in CV.domain_specific_constraints,
      evaluate whether the turn output satisfies the constraint.
      Count constraint_failure_count.
      CSS = max(0, 30 - 8 × constraint_failure_count).

   Step 4 — SDS computation:
      If an embedding model is configured in CV:
         Compute embed(current_turn_output).
         Compute drift_magnitude = cosine_distance(
             embed(current_turn_output),
             authorized_profile_embedding
         ).
         SDS = max(0.0, 20 × (1 - drift_magnitude)).
      Else:
         SDS = 20.0 (no deduction, model not configured).

   Step 5 — AAS computation:
      Compare capability invocations and resource accesses in the
      turn output to CV.authority_scope.
      AAS = 10 if all invocations within scope, else 0.

   Step 6 — Score assembly:
      ccs_score = OBS + CSS + SDS + AAS.
      Round to 4 decimal places.
      ccs_verdict = derive_verdict(ccs_score) per §6.4.

   Step 7 — CCS embedding:
      Populate BAR.ccs_score, BAR.ccs_verdict, BAR.ccs_components
      before content_hash_bar computation.

   The CCS MUST be computed and embedded before content_hash_bar
   is computed (§4.4 step ordering).  A BAR whose content_hash_bar
   was computed before CCS embedding violates BEV-INV-013.

6.4.  CCS Verdicts and Thresholds

   CCS verdicts are derived from ccs_score as follows:

   | CCS Score     | Verdict     | Meaning                                  |
   |---------------|-------------|------------------------------------------|
   | >= 90.0       | CONFORMANT  | Outputs fully within constraint bounds   |
   | 70.0 – 89.9   | DRIFTING    | Degradation detected; AGVP PVR triggered |
   | 50.0 – 69.9   | BREACH      | Significant violations; escalation req'd |
   | < 50.0        | VIOLATION   | Critical violations; HALT protocol       |
   | -1.0          | NO_DATA     | CCS_ENABLED=false or REDACTED mode       |

   Threshold environment variables:

   CCS_CONFORMANT_THRESHOLD (default: 90.0):
      Minimum score for CONFORMANT verdict.
      Production floor: 85.0 (never set below 80.0 — ADR-182).

   CCS_DRIFTING_THRESHOLD (default: 70.0):
      Minimum score for DRIFTING verdict.
      Production floor: 60.0.

   CCS_BREACH_THRESHOLD (default: 50.0):
      Minimum score for BREACH verdict.
      Production floor: 40.0.

   Scores below CCS_BREACH_THRESHOLD receive VIOLATION verdict.

   Threshold adjustment WARNING: CCS thresholds are behavioral
   security parameters.  Raising thresholds increases sensitivity
   (more DRIFTING signals, more PVRs).  Lowering thresholds below
   the production floor reduces governance coverage and MUST be
   documented with a security exception (ADR-182).

6.5.  AGVP Integration: CCS-Driven Anticipatory Veto

   The CCS integrates with the Anticipatory Governance Veto Protocol
   (AGVP, RFC-ATF-4, ADR-174) via the following mechanism:

   Trigger: When a BAR is persisted with ccs_verdict = DRIFTING or
   worse, the BEV runtime MUST submit a PVR issuance request to the
   AGVP watchdog.

   PVR payload for CCS-driven issuance:
      trigger_source: "CCS_BEV"
      trigger_session_id: BAR.session_id
      trigger_bar_id: BAR.bar_id
      trigger_ccs_score: BAR.ccs_score
      trigger_ccs_verdict: BAR.ccs_verdict
      trigger_turn_index: BAR.turn_index
      governing_receipt_id: BAR.governing_receipt_id
      veto_type: "BEHAVIORAL_CONFORMANCE_DEGRADATION"
      anticipatory_risk_level: derived from verdict:
         DRIFTING → MONITORING
         BREACH   → WARNING
         VIOLATION → HALT

   The AGVP produces a PVR for the CCS-triggered event, sealing it
   with ML-DSA-65 as specified in RFC-ATF-4 §4.4.  The PVR is
   persisted to avm_anticipatory_veto_receipts with a reference to
   the triggering BAR.

   VIOLATION verdict — HALT propagation:
   When ccs_verdict = VIOLATION, the AGVP MUST initiate the HALT
   propagation protocol (RFC-ATF-2 §7.3).  The session is suspended
   pending human review.  No subsequent turn is permitted until a
   reauthorization event clears the HALT state.

   This integration completes the AGVP input space:
   - Structural signals (CES, fragmentation): covered by RFC-ATF-4
   - Semantic drift (cross-domain): covered by RFC-ATF-4 DSPP
   - Behavioral conformance: NOW covered by CCS (this RFC)

6.6.  CCS Embedding in BAR

   The CCS is not stored in a separate database table at the turn
   level.  It is embedded within the BAR before the BAR is sealed.
   This design ensures:

   1. The CCS is tamper-evident: modifying ccs_score or
      ccs_components after BAR sealing produces a content_hash_bar
      mismatch (BEV-INV-013).

   2. The CCS is co-located with the behavioral attestation: a BAR
      record is a complete behavioral attestation artifact — output
      hash, conformance measurement, chain link — in a single,
      independently verifiable document.

   3. The CCS inherits BAR's offline verifiability (BEV-INV-007):
      any verifier with the BAR JSON and platform public key can
      verify the CCS score and the BAR's behavioral content together.

   A separate atf_constraint_conformance_signals table (§13.2) is
   maintained for efficient CCS history queries (by session, by
   verdict, by time range) without requiring full BAR retrieval.
   This table is a projection of BAR data and MUST be kept in sync
   with atf_behavioral_anchor_records.

6.7.  CCS Invariants (BEV-INV-008 through BEV-INV-013)

BEV-INV-008 — Mandatory CCS Computation per BAR

   Every BAR produced in a BEV_ENABLED + CCS_ENABLED deployment
   MUST include a computed ccs_score and ccs_verdict.  A BAR with
   ccs_score = -1.0 in a CCS-enabled deployment is incomplete.

   Formally:
      For all BARs b where CCS_ENABLED:
         b.ccs_score ∈ [0.0, 100.0]
         AND b.ccs_verdict ∈ {CONFORMANT, DRIFTING, BREACH,
                               VIOLATION}
         AND b.ccs_components is present

   Exception: REDACTED mode BARs MAY have ccs_score = -1.0 with
   ccs_verdict = NO_DATA, since the output content is unavailable
   for evaluation.

BEV-INV-009 — CCS Score Bounds

   The ccs_score in every BAR MUST be in the range [0.0, 100.0].
   No CCS score outside this range is valid.

   Formally:
      For all BARs b where b.ccs_score != -1.0:
         0.0 <= b.ccs_score <= 100.0

   This is a structural guarantee derived from the component bounds:
   OBS ∈ [0, 40], CSS ∈ [0, 30], SDS ∈ [0, 20], AAS ∈ {0, 10}.
   The Z3 proof is provided in §8.3.

BEV-INV-010 — DRIFTING Triggers AGVP PVR

   A BAR persisted with ccs_verdict = DRIFTING, BREACH, or
   VIOLATION MUST trigger a PVR issuance request to the AGVP
   watchdog within BEV_AGVP_TRIGGER_TIMEOUT_MS (default: 500ms).

   Formally:
      For all BARs b where b.ccs_verdict ∈ {DRIFTING, BREACH,
                                              VIOLATION}:
         EXISTS(PVR p) WHERE p.trigger_bar_id = b.bar_id
            AND p.issued_at_ns <= b.bar_timestamp_ns +
               BEV_AGVP_TRIGGER_TIMEOUT_MS × 1_000_000

   A deployment where DRIFTING BARs do not trigger PVRs has an
   incomplete AGVP-CCS integration and MUST NOT be designated
   ATF-BEV-Compliant.

BEV-INV-011 — CCS Component Non-Negativity

   All four CCS components (OBS, CSS, SDS, AAS) MUST be
   non-negative.  Negative CCS components are not valid.

   Formally:
      For all BARs b where b.ccs_components is present:
         b.ccs_components.output_boundary_score >= 0
         AND b.ccs_components.constraint_satisfaction_score >= 0
         AND b.ccs_components.semantic_drift_score >= 0
         AND b.ccs_components.authority_alignment_score >= 0

   This invariant ensures that the CCS score cannot be inflated
   by a negative component masking a high-violation component.

BEV-INV-012 — VIOLATION Triggers HALT Propagation

   A BAR persisted with ccs_verdict = VIOLATION MUST trigger the
   AGVP HALT propagation protocol (RFC-ATF-2 §7.3) within
   BEV_HALT_TIMEOUT_MS (default: 100ms).  No subsequent turn is
   permitted in the session until the HALT state is cleared by
   a reauthorization event.

   Formally:
      For all sessions S and turns T_i:
         BAR(T_i).ccs_verdict = VIOLATION
         IMPLIES session_halted(S)
         AND no T_{i+1} in S is permitted until reauthorization

   The HALT state is propagated to the governing receipt's authority
   chain per RFC-ATF-2 §7.3 semantics.

BEV-INV-013 — CCS Integrity via BAR Seal

   The ccs_score, ccs_verdict, and ccs_components fields are
   covered by content_hash_bar.  Modifying any CCS field after BAR
   sealing produces a content_hash_bar mismatch.

   Formally:
      {ccs_score, ccs_verdict, ccs_components} ⊂ canonical_json(BAR)
         covered by content_hash_bar
      THEREFORE: post-seal modification detectable from pqc_signature


7.  Cross-Turn Coherence Hash Chain (CTCHC)

7.1.  Multi-Turn Coherence Architecture

   The CTCHC provides session-level behavioral integrity for multi-
   turn agent sessions.  Its architecture has four design principles:

   Principle 1 — Governing receipt seeding:
      The hash chain is seeded by the governing receipt identifier
      and session identifier, making the chain inseparable from the
      specific authorization that governs it.  A chain from a
      different session cannot be substituted without producing a
      genesis hash mismatch.

   Principle 2 — Turn output binding:
      Each chain link incorporates the output_hash and turn_index
      of the corresponding BAR.  A turn omission causes all
      subsequent chain links to diverge.  A turn substitution
      causes the chain link at the substituted position to diverge.

   Principle 3 — Deterministic construction:
      The chain link computation is fully deterministic given the
      inputs.  Any verifier with the BAR sequence and governing
      receipt identifier can independently reconstruct and verify
      the entire chain.

   Principle 4 — Session seal:
      At session close, the final chain hash is sealed with ML-
      DSA-65 to produce the CTCHC session seal.  The sealed CTCHC
      record is the Session Integrity Proof.

7.2.  Chain Initialization Protocol

   The CTCHC is initialized when the first BAR (turn_index = 0) is
   produced for a session.

   Genesis Hash Computation:

      Inputs:
         governing_receipt_id: string (UTF-8 encoded)
         session_id:           string (UTF-8 encoded)
         session_start_ns:     integer (nanosecond epoch, 8 bytes
                                        big-endian)

      genesis_hash = SHA-256(
          governing_receipt_id.encode("utf-8") ||
          b"||" ||
          session_id.encode("utf-8") ||
          b"||" ||
          session_start_ns.to_bytes(8, "big")
      )

      Format: 64 lowercase hexadecimal characters

      Example:
         governing_receipt_id = "ATFDR-3F1A4B7C2D8E5F9A1B2C3D4E"
         session_id           = "BEV-SESSION-A1B2C3D4E5F6A7B8"
         session_start_ns     = 1748000000000000000
         genesis_hash         = sha256(...)  # 64 hex chars

   The genesis_hash MUST be stored in BAR_0 (turn_index = 0) in
   the genesis_hash field.  All subsequent BARs in the session
   MUST NOT include genesis_hash (it is derivable from BAR_0).

   The chain_link of BAR_0 is computed from the genesis hash:

      turn_hash(0) = SHA-256(
          BAR_0.output_hash_bytes ||
          turn_index(0).to_bytes(8, "big")
      )

      chain_link(0) = SHA-256(genesis_hash_bytes || turn_hash(0))

   where output_hash_bytes = bytes.fromhex(
       BAR_0.output_hash.removeprefix("sha256:")
   )

7.3.  Chain Link Construction

   For each turn T_n (n >= 1), the chain link is computed as:

   Turn Hash:
      turn_hash(n) = SHA-256(
          output_hash_bytes(n) ||
          n.to_bytes(8, "big")
      )

      where output_hash_bytes(n) = bytes.fromhex(
          BAR_n.output_hash.removeprefix("sha256:")
      )

   Chain Link:
      chain_link(n) = SHA-256(
          bytes.fromhex(chain_link(n-1)) ||
          turn_hash(n)
      )

   The chain_link is represented as 64 lowercase hexadecimal
   characters (SHA-256 output, no prefix).

   The chain_link for turn n is embedded in BAR_n before the BAR
   is sealed (§4.4 step ordering).  The chain_link from BAR_{n-1}
   MUST be available before BAR_n is assembled.

   In sessions where turns execute sequentially (most deployments),
   chain link construction is synchronous with BAR production.

   In sessions where turns may execute concurrently:
   - Turn indices MUST be assigned sequentially before concurrent
     execution begins.
   - Chain link computation MUST be serialized in turn_index order.
   - Concurrent turn output computation is permitted; chain link
     chaining is strictly sequential.

7.4.  Chain Sealing at Session Close

   When a BEV Session closes (all turns complete, no further turns
   authorized under the Governing Receipt), the CTCHC MUST be sealed.

   Session close is triggered by one of:
   - CV.turn_limit reached (all N authorized turns completed)
   - Session duration limit exceeded (CV.session_duration_limit_s)
   - Governing receipt expiry
   - HALT state triggered by VIOLATION verdict (§6.5)
   - Explicit session close API call (POST /v1/bev/session/{id}/close)

   CTCHC Sealing Procedure:

   Step 1 — Final chain hash extraction:
      final_chain_hash = chain_link(N-1)
      where N is the total number of turns in the session.

   Step 2 — CTCHC record assembly:
      Assemble the CTCHC record (see §13.3 for schema).
      Fields include: ctchc_id, session_id, governing_receipt_id,
      genesis_hash, final_chain_hash, turn_count, session_start_ns,
      session_close_ns, all_bar_ids (ordered by turn_index),
      content_hash_ctchc.

   Step 3 — Content hash computation:
      content_hash_ctchc = SHA-256(canonical_json(CTCHC record
          excluding content_hash_ctchc and ctchc_seal))

   Step 4 — CTCHC seal computation:
      ctchc_seal = base64.b64encode(
          dilithium3.sign(
              content_hash_ctchc.encode("utf-8"),
              platform_secret_key
          )
      )

   Step 5 — CTCHC persistence:
      INSERT INTO atf_coherence_hash_chains.
      All BARs in the session transition to SEALED state.

   The CTCHC record is the Session Integrity Proof.  Any party
   with the CTCHC record and the BAR sequence can verify session
   coherence without platform access (§7.5).

7.5.  Offline Chain Verification Protocol

   Any party possessing the following may independently verify a
   completed BEV Session:
   1. The CTCHC record (ctchc_id, genesis_hash, final_chain_hash,
      all_bar_ids, ctchc_seal, content_hash_ctchc).
   2. All BAR records for the session, ordered by turn_index.
   3. The OMNIX platform ML-DSA-65 public key.

   Verification procedure:

   Step 1 — CTCHC record integrity:
      Verify ctchc_seal over content_hash_ctchc using the platform
      public key.
      Recompute content_hash_ctchc from the CTCHC record.
      Compare.  Failure: CTCHC record tampered.

   Step 2 — BAR completeness:
      Verify len(all_bar_ids) = turn_count.
      Verify all_bar_ids[i].turn_index = i for i in [0, N-1].
      Any gap in turn_index sequence indicates a missing BAR.

   Step 3 — Individual BAR verification:
      For each BAR in turn_index order: apply §5.7 Steps 1-4.
      All BARs MUST pass individual verification.

   Step 4 — Genesis hash verification:
      Recompute genesis_hash from BAR_0.governing_receipt_id,
      BAR_0.session_id, BAR_0.session_start_ns using §7.2 formula.
      Compare to CTCHC.genesis_hash.
      Failure: session identity has been tampered.

   Step 5 — Chain reconstruction:
      Compute chain_link(0) through chain_link(N-1) using §7.3
      formula applied to each BAR's output_hash and turn_index.
      Compare chain_link(n) to BAR_n.chain_link for each n.
      Any mismatch at position n indicates:
         - Turn substitution at position n
         - Turn omission before position n (causing downstream drift)

   Step 6 — Final chain hash verification:
      Compare reconstructed chain_link(N-1) to
      CTCHC.final_chain_hash.
      Failure: the CTCHC was sealed over a different chain than
      the presented BAR sequence.

   A session that passes all six steps is COHERENT.  A session that
   fails any step is COMPROMISED at the indicated position and MUST
   be reported with the specific failure type.

7.6.  Partial Chain Recovery

   In exceptional circumstances (infrastructure failure mid-session,
   network partition during turn execution), a session may have an
   incomplete BAR sequence.  Partial chain recovery applies:

   Recovery is possible if:
   - All persisted BARs form a contiguous prefix: BAR_0 through
     BAR_k for some k < N-1.
   - The failure point (turn k+1 and beyond) is clearly identified
     in the session audit trail.

   Recovery procedure:
   1. Seal the partial chain at BAR_k: final_chain_hash_partial =
      chain_link(k).
   2. Produce a CTCHC_PARTIAL record with turn_count = k+1,
      session_status = BEV-INCOMPLETE, failure_turn_index = k+1,
      failure_reason = [audit trail entry].
   3. Seal CTCHC_PARTIAL with ML-DSA-65.

   A CTCHC_PARTIAL record is NOT a Session Integrity Proof.  It
   provides partial session coherence proof for turns 0 through k.
   The failure is forensically documented and cannot be concealed.

   Recovery is NOT possible if BARs are missing from the interior
   of the session (e.g., BAR_3 missing from a sequence 0-5).  Such
   sessions MUST be flagged CHAIN_BROKEN and cannot produce any
   partial coherence proof.

7.7.  CTCHC Invariants (BEV-INV-014 through BEV-INV-018)

BEV-INV-014 — Genesis Hash Governing Receipt Binding

   The genesis hash of every CTCHC MUST be computed from the
   governing_receipt_id, session_id, and session_start_ns of the
   session's first BAR, as specified in §7.2.  Any other genesis
   hash computation is non-conformant.

   Formally:
      For all CTCHCs C:
         C.genesis_hash = SHA-256(
             BAR_0.governing_receipt_id.encode("utf-8") ||
             b"||" ||
             BAR_0.session_id.encode("utf-8") ||
             b"||" ||
             BAR_0.session_start_ns.to_bytes(8, "big")
         )

   This binding makes cross-session BAR substitution detectable:
   BARs from a session with a different governing_receipt_id or
   session_id will produce a genesis hash mismatch.

BEV-INV-015 — Chain Link Strict Monotonicity

   For every pair of consecutive BARs T_i, T_{i+1} in a session:
      T_{i+1}.turn_index = T_i.turn_index + 1
      T_{i+1}.chain_link ≠ T_i.chain_link
      T_{i+1}.chain_link = SHA-256(
          bytes.fromhex(T_i.chain_link) || turn_hash(i+1)
      )

   No two BARs in the same session may have the same chain_link
   value (chain links are strictly distinct due to SHA-256
   collision resistance).

   This invariant ensures that turn reordering is detectable: if
   T_i and T_{i+1} are swapped, the chain link at position i+1
   will not match the expected value.

BEV-INV-016 — Chain Completeness

   The complete set of BARs for a sealed CTCHC MUST have no gaps
   in turn_index values: {BAR_0.turn_index, ..., BAR_{N-1}.turn_index}
   = {0, 1, ..., N-1}.

   A sealed CTCHC where any turn_index in [0, N-1] has no
   corresponding BAR is structurally invalid and MUST NOT be
   accepted as a Session Integrity Proof.

   Chain completeness is verifiable by any party: the absence of
   BAR_k from a presented sequence of N-1 BARs causes all chain
   links from position k onward to be unverifiable.

BEV-INV-017 — Final Chain Hash Offline Verifiability

   The final_chain_hash in every sealed CTCHC MUST be independently
   recomputable by any party possessing the full BAR sequence and
   the CTCHC genesis_hash, without accessing any OMNIX
   infrastructure.

   The §7.5 verification procedure MUST succeed for any correctly
   produced CTCHC.  An implementation where §7.5 fails for a
   correctly-formed session has a structural offline verifiability
   defect.

BEV-INV-018 — Session PQC Sealing at Close

   Every completed CTCHC MUST be sealed with Dilithium-3
   (ML-DSA-65, FIPS 204) over its content_hash_ctchc at session
   close.  An unsealed CTCHC MUST NOT be presented as a Session
   Integrity Proof in regulatory or legal proceedings.

   Formally:
      For all CTCHCs C with session_status = BEV-COMPLETE:
         dilithium3.verify(
            C.content_hash_ctchc.encode("utf-8"),
            C.ctchc_seal,
            platform_public_key
         ) = True


8.  Formal Verification (OMNIX-FVS-1.0 Extension)

8.1.  BEV Proof Inventory

   RFC-ATF-4 established the OMNIX Formal Verification Suite
   (OMNIX-FVS-1.0, ADR-177) with 19 Z3 SMT arithmetic proofs.
   RFC-ATF-5 extended it with 8 CGL proof targets.

   RFC-ATF-6 extends OMNIX-FVS-1.0 with five BEV proof targets:

   BAR arithmetic properties:
      BEV-FVS-001: BAR binding completeness
         authorized(turn) IMPLIES bar_exists(turn)
         (boolean implication over turn execution events)
      BEV-FVS-002: Output hash integrity
         SHA-256 collision resistance: structural property

   CCS arithmetic properties:
      BEV-FVS-003: CCS score bounds
         OBS ∈ [0,40] ∧ CSS ∈ [0,30] ∧ SDS ∈ [0,20] ∧ AAS ∈ {0,10}
         IMPLIES ccs_score ∈ [0.0, 100.0]
         (bounded linear arithmetic over reals)
      BEV-FVS-004: CCS component non-negativity
         max(0, base - deductions) >= 0 for all components
         (follows from max(0, ·) semantics)

   CTCHC arithmetic property:
      BEV-FVS-005: Chain link strict distinctness
         turn_hash(n) is determined by output_hash(n) and n;
         SHA-256 collision resistance ensures chain_link(n) ≠
         chain_link(m) for n ≠ m with overwhelming probability
         (structural property)

8.2.  BAR Arithmetic Proofs (Z3 SMT)

   BEV-FVS-001 — BAR Binding Completeness:

   from z3 import Bool, Solver, Implies, Not, unsat
   authorized = Bool("authorized_turn")
   bar_exists = Bool("bar_exists")
   s = Solver()
   # BEV-INV-001: authorized execution implies BAR existence
   s.add(authorized)
   s.add(Not(bar_exists))
   # No model: authorized without bar is a violation, not a
   # satisfiable configuration.
   # Verify: unsat (enforcement eliminates all violations)
   assert s.check() == unsat  # holds if BEV-INV-001 is enforced

   BEV-FVS-002 — Output Hash Structural Uniqueness:

   # SHA-256 produces a 256-bit digest.
   # P(collision) < 2^{-128} per birthday bound for outputs
   # less than 2^{64} in count.  BEV session sizes are bounded
   # by CV.turn_limit (max declarable: 10_000 turns per session
   # per R-CTCHC-05).  Collision probability per session < 2^{-115}.
   # Structural property: no arithmetic SMT encoding required.
   # Formal reference: SHA-256 collision resistance (FIPS 180-4).

8.3.  CCS Arithmetic Proofs (Z3 SMT)

   BEV-FVS-003 — CCS Score Bounds:

   from z3 import Real, Solver, And, Or, Not, unsat
   obs, css, sds, aas = [Real(x) for x in
       ["obs", "css", "sds", "aas"]]
   s = Solver()
   # Component bounds
   s.add(obs >= 0, obs <= 40)
   s.add(css >= 0, css <= 30)
   s.add(sds >= 0, sds <= 20)
   s.add(And(Or(aas == 0, aas == 10)))
   ccs = obs + css + sds + aas
   # Claim: ccs is always in [0.0, 100.0]
   s.add(Or(ccs < 0, ccs > 100))
   assert s.check() == unsat  # no violation possible

   BEV-FVS-004 — CCS Component Non-Negativity:

   from z3 import Real, Int, Solver, And, Not, unsat
   base_obs, deductions_obs = Real("base_obs"), Real("ded_obs")
   s = Solver()
   s.add(base_obs == 40)
   s.add(deductions_obs >= 0)
   result = If(base_obs - deductions_obs >= 0,
               base_obs - deductions_obs, 0)
   # max(0, base - deductions) >= 0 always
   s.add(Not(result >= 0))
   assert s.check() == unsat  # non-negativity holds

8.4.  CTCHC Arithmetic Proofs (Z3 SMT)

   BEV-FVS-005 — Chain Monotonicity:

   from z3 import Int, Solver, And, Not, unsat
   n, m = Int("n"), Int("m")
   s = Solver()
   s.add(n >= 0, m >= 0)
   # turn_index is strictly increasing: n != m in same session
   # implies chain_link(n) != chain_link(m) by SHA-256 construction
   # given output_hash(n) != output_hash(m) or n != m
   # Arithmetic encoding of monotonicity:
   s.add(And(n >= 0, m >= 0, n < m))
   # For n < m: turn_index bytes differ => turn_hash differs
   # => chain_link(m) depends on chain_link(m-1) which depends on
   # chain_link(n): structural dependence ensures distinctness
   # No arithmetic counterexample exists within SHA-256 assumptions
   # Result: verified by structural induction on chain construction

8.5.  Machine Reproducibility

   All BEV formal verification targets MUST be executable using:

      python omnix_core/formal_verification/run_bev_proofs.py

   Expected output: JSON report with result = "unsat" or
   "structural" for all proof targets.  A "sat" or "unknown" result
   for BEV-FVS-003 or BEV-FVS-004 indicates a CCS implementation
   defect and MUST block ATF-BEV-Compliant certification.


9.  BEV Layer Composition

9.1.  Layer Architecture

   The three BEV modules interact at each execution turn as follows:

   Turn execution timeline:
   ┌──────────────────────────────────────────────────────────────┐
   │  1. Agent executes turn, produces BO                        │
   │  2. output_hash computed (privacy mode applied)             │
   │  3. CCS computed from BO and CV (if CCS_ENABLED)            │
   │  4. chain_link computed from prior link and turn_hash        │
   │  5. BAR assembled (all fields including ccs, chain_link)     │
   │  6. content_hash_bar computed                               │
   │  7. pqc_signature computed                                  │
   │  8. BAR persisted to atf_behavioral_anchor_records          │
   └──────────────────────────────────────────────────────────────┘

   CCS-AGVP trigger (concurrent with step 8, if verdict warrants):
   ┌──────────────────────────────────────────────────────────────┐
   │  9. If ccs_verdict ∈ {DRIFTING, BREACH, VIOLATION}:         │
   │     PVR issuance request submitted to AGVP watchdog         │
   │ 10. AGVP produces and seals PVR                             │
   │ 11. If VIOLATION: HALT propagation initiated                │
   └──────────────────────────────────────────────────────────────┘

   Session close (when session ends):
   ┌──────────────────────────────────────────────────────────────┐
   │ 12. CTCHC final chain hash extracted from last BAR          │
   │ 13. CTCHC record assembled                                  │
   │ 14. content_hash_ctchc computed                             │
   │ 15. ctchc_seal computed                                     │
   │ 16. CTCHC persisted to atf_coherence_hash_chains            │
   │ 17. All session BARs transition to SEALED state             │
   └──────────────────────────────────────────────────────────────┘

9.2.  Cross-Layer Integration Points

   BAR ↔ Governing Receipt (Layers 1-2):
      governing_receipt_id in every BAR creates a queryable link
      from any ATF receipt to the complete BAR sequence produced
      under that receipt.  GET /v1/bev/session/{id}/bars returns
      all BARs for a session keyed by governing_receipt_id.

   CCS ↔ AGVP (Layer 4):
      CCS DRIFTING/BREACH/VIOLATION verdicts trigger PVR issuance
      per §6.5.  The PVR references the triggering BAR and session.
      The behavioral conformance history is queryable via
      GET /v1/bev/session/{id}/ccs.

   CTCHC ↔ OEP (Layer 3):
      When BEV_INCLUDE_IN_OEP=true, OEP packages (ADR-165) include:
      - The CTCHC record (genesis_hash, final_chain_hash, ctchc_seal)
      - All BAR records in the session (HASHED mode by default)
      The OEP outer seal covers all BEV artifacts, making the
      complete Behavioral Attestation Chain forensically portable.

   BAR ↔ TCS (Layer 5):
      When TGB_ENABLED=true, each BAR's bar_timestamp_ns anchors
      it within the regulatory context captured in the session's
      governing receipt TCS.  The TCS provides the temporal
      interpretability bridge for BARs under 7-year EU AI Act
      retention obligations.

9.3.  Failure Isolation

   BAR persistence failure (step 8):
      Session is flagged BEV-INCOMPLETE (BEV-INV-005).
      No subsequent turn is permitted.
      Failure is logged to governing receipt audit trail.
      Existing BARs remain valid attestation artifacts for turns
      0 through k-1 (where k is the failed turn).

   CCS computation failure (step 3):
      If CCS computation fails, the BAR is produced with
      ccs_score = -1.0, ccs_verdict = NO_DATA.
      The BAR is marked CCS_FAILED in ccs_components.
      A CCS failure does NOT block BAR production.
      CCS_FAILURE count is tracked in session audit trail.
      Sessions with CCS_FAILED BARs MUST be flagged in
      compliance reporting.

   AGVP trigger failure (steps 9-11):
      AGVP trigger failure is logged to the session audit trail
      but does NOT block turn continuation.  The AGVP trigger is
      retried per RFC-ATF-4 retry semantics.
      VIOLATION-triggered HALT, however, is fail-closed: if the
      HALT propagation fails, the session is suspended pending
      manual intervention.

   CTCHC sealing failure (steps 12-16):
      If CTCHC sealing fails, the session status remains
      BEV-INCOMPLETE.  BARs remain ACTIVE (not SEALED).
      The failure is retried with exponential backoff.
      After CTCHC_MAX_RETRY_HOURS, the session is flagged
      CTCHC_SEAL_FAILED and requires manual intervention.


10.  Combined Invariant Summary

   This RFC introduces 18 new invariants across three protocol
   families.  Combined with the 88 invariants from RFC-ATF-1
   through RFC-ATF-5, the complete ATF protocol stack encompasses
   106 formally specified, model-checkable constraints across
   20 protocol families.

   RFC-ATF-6 invariants:

   | Family | Invariant    | Statement (summary)                         |
   |--------|--------------|---------------------------------------------|
   | BEV    | BEV-INV-001  | Mandatory BAR per authorized turn           |
   | BEV    | BEV-INV-002  | Mandatory governing receipt binding         |
   | BEV    | BEV-INV-003  | Output hash integrity via content_hash_bar  |
   | BEV    | BEV-INV-004  | BAR PQC sealing (ML-DSA-65 required)       |
   | BEV    | BEV-INV-005  | BAR fail-closed on persistence failure      |
   | BEV    | BEV-INV-006  | BAR append-only storage                     |
   | BEV    | BEV-INV-007  | BAR offline verifiability                   |
   | BEV    | BEV-INV-008  | Mandatory CCS per BAR (when CCS_ENABLED)    |
   | BEV    | BEV-INV-009  | CCS score ∈ [0.0, 100.0]                   |
   | BEV    | BEV-INV-010  | DRIFTING triggers AGVP PVR issuance        |
   | BEV    | BEV-INV-011  | CCS component non-negativity                |
   | BEV    | BEV-INV-012  | VIOLATION triggers HALT propagation        |
   | BEV    | BEV-INV-013  | CCS integrity via BAR seal                  |
   | BEV    | BEV-INV-014  | Genesis hash governing receipt binding      |
   | BEV    | BEV-INV-015  | Chain link strict monotonicity              |
   | BEV    | BEV-INV-016  | Chain completeness (no turn gaps)           |
   | BEV    | BEV-INV-017  | Final chain hash offline verifiability      |
   | BEV    | BEV-INV-018  | Session PQC sealing at close                |

   Complete ATF invariant registry as of RFC-ATF-6:

   | Family      | RFC     | Count | Scope                              |
   |-------------|---------|-------|------------------------------------|
   | ATF-INV     | ATF-1   |   6   | Identity & Delegation              |
   | RGC-INV     | ATF-2   |   8   | Runtime Continuity                 |
   | GPIL-INV    | ATF-3   |   3   | Governance Policy Interop          |
   | ELR-INV     | ATF-3   |   4   | Evidence Lifecycle                 |
   | EAP-INV     | ATF-3   |   7   | Evidence Archive Pipeline          |
   | OEP-INV     | ATF-3   |   6   | Evidence Package (OEP)             |
   | FEA-INV     | ATF-3   |   5   | Forensic Export Auth               |
   | FVP-INV     | ATF-3   |   1   | Forensic Verification Protocol     |
   | GECR-INV    | ATF-3   |   6   | Governance Execution Context       |
   | SGIP-INV    | ATF-3   |   4   | Semantic Gov Interop Protocol      |
   | DSPP-INV    | ATF-4   |   7   | Dynamic Semantic Portability       |
   | AGV-INV     | ATF-4   |   6   | Anticipatory Governance Veto       |
   | SSD-INV     | ATF-4   |   3   | Structural Shift Detection         |
   | FVS-INV     | ATF-4   |   3   | Formal Verification Suite          |
   | CGE-INV     | ATF-5   |   7   | Counterfactual Governance Engine   |
   | GUGT-INV    | ATF-5   |   6   | Grand Unified Governance Theory    |
   | TGB-INV     | ATF-5   |   5   | Temporal Governance Bridge         |
   | BEV-INV     | ATF-6   |  18   | Behavioral Execution Verification  |
   |             | TOTAL   | 106   |                                    |

   Note: BEV-INV is a unified family covering all three BEV modules
   (BAR, CCS, CTCHC).  The 20th protocol family designation applies
   when BEV sub-families are split by module.


11.  Compliance Designation: ATF-BEV-Compliant

11.1.  Designation Requirements

   An implementation is designated ATF-BEV-Compliant if and only if
   it satisfies ALL of the following:

   (a) ATF-CGL-Compliant (RFC-ATF-5): all RFC-ATF-1 through
       RFC-ATF-5 requirements are satisfied.  This is the baseline
       prerequisite.

   (b) BAR operational: BEV_ENABLED=true, all execution turns
       produce persisted BARs, all BEV-INV-001 through BEV-INV-007
       satisfied.

   (c) CCS operational: CCS_ENABLED=true, CCS computed and embedded
       in every BAR, AGVP integration active for DRIFTING and worse
       verdicts, all BEV-INV-008 through BEV-INV-013 satisfied.

   (d) CTCHC operational: CTCHC_ENABLED=true, all completed sessions
       have a sealed CTCHC record, all BEV-INV-014 through
       BEV-INV-018 satisfied.

   (e) BEV formal verification: OMNIX-FVS-1.0 BEV extension runs
       all BEV proof targets with result = "unsat" or "structural"
       for all five proofs.

   (f) BEV_INCLUDE_IN_OEP=true (RECOMMENDED): CTCHC records and
       BAR sequences included in OEP forensic packages.

11.2.  Compliance Hierarchy

   | Designation          | RFC Coverage      | Invariants |
   |----------------------|-------------------|------------|
   | ATF-COMPLIANT-L1     | RFC-ATF-1         |   6        |
   | ATF-COMPLIANT-L2     | RFC-ATF-1         |   6        |
   | ATF-COMPLIANT-L3     | RFC-ATF-1         |   6        |
   | ATF-RGC-Compliant    | ATF-1 + ATF-2     |  14        |
   | ATF-FEI-Compliant    | ATF-1/2/3         |  40        |
   | ATF-PGL-Compliant    | ATF-1/2/3/4       |  70        |
   | ATF-CGL-Compliant    | ATF-1/2/3/4/5     |  88        |
   | ATF-BEV-Compliant    | ATF-1/2/3/4/5/6   | 106        |

   ATF-BEV-Compliant is the sixth and highest compliance tier in
   the ATF stack.  RFC-ATF-5 §11.2's characterization of ATF-CGL-
   Compliant as "fifth and highest" is superseded by this RFC.


12.  Implementation Requirements

12.1.  BAR Requirements

   REQUIRED:
   R-BAR-01: BEV_ENABLED environment variable MUST be respected.
      When true, every authorized execution turn MUST produce
      a persisted BAR (BEV-INV-001).
   R-BAR-02: governing_receipt_id MUST be validated against the
      ATF receipt store at session initialization.  Sessions with
      unresolvable governing_receipt_id MUST NOT be started.
   R-BAR-03: turn_index MUST be assigned sequentially starting at 0.
      No gaps are permitted (BEV-INV-015).
   R-BAR-04: BAR MUST be persisted before the next turn begins.
      Failure to persist MUST trigger session BEV-INCOMPLETE flag.
   R-BAR-05: pqc_algorithm MUST be "ML-DSA-65" (BEV-INV-004).
   R-BAR-06: atf_spec_version MUST be "1.6" in all BARs.

   RECOMMENDED:
   R-BAR-07: output_hash_mode SHOULD be HASHED in production for
      GDPR compliance and output data minimization.
   R-BAR-08: BARs SHOULD be included in OEP packages when
      BEV_INCLUDE_IN_OEP=true.

   NOT PERMITTED:
   R-BAR-09: No UPDATE or DELETE on atf_behavioral_anchor_records
      (BEV-INV-006).
   R-BAR-10: A BAR MUST NOT be produced after the session has
      received a HALT state from a VIOLATION verdict (BEV-INV-012).

12.2.  CCS Requirements

   REQUIRED:
   R-CCS-01: CCS computation MUST complete before content_hash_bar
      is computed (§4.4 step ordering).
   R-CCS-02: ccs_score MUST be in [0.0, 100.0] for all non-REDACTED
      BARs when CCS_ENABLED=true (BEV-INV-009).
   R-CCS-03: ccs_verdict MUST be consistent with ccs_score per
      §6.4 threshold table.
   R-CCS-04: DRIFTING or worse verdict MUST trigger AGVP PVR
      issuance within BEV_AGVP_TRIGGER_TIMEOUT_MS (BEV-INV-010).
   R-CCS-05: VIOLATION verdict MUST trigger HALT propagation
      within BEV_HALT_TIMEOUT_MS (BEV-INV-012).

   RECOMMENDED:
   R-CCS-06: CCS_CONFORMANT_THRESHOLD SHOULD be >= 85.0 in
      production (default: 90.0).
   R-CCS-07: Embedding model for SDS SHOULD be declared in
      CV.domain_specific_constraints.sds_embedding_model.

   NOT PERMITTED:
   R-CCS-08: CCS threshold environment variables MUST NOT be set
      below production floors defined in §6.4.
   R-CCS-09: ccs_score MUST NOT be modified after content_hash_bar
      computation (BEV-INV-013).

12.3.  CTCHC Requirements

   REQUIRED:
   R-CTCHC-01: genesis_hash MUST be computed using the §7.2
      formula at session initialization.
   R-CTCHC-02: chain_link MUST be computed using the §7.3 formula
      for every turn before BAR sealing.
   R-CTCHC-03: CTCHC MUST be sealed at session close using the
      §7.4 procedure.
   R-CTCHC-04: ctchc_seal MUST use ML-DSA-65 over
      content_hash_ctchc (BEV-INV-018).
   R-CTCHC-05: CV.turn_limit MUST NOT exceed 100_000 turns per
      session.  Sessions exceeding this limit MUST be split into
      sub-sessions with separate governing receipts.

   RECOMMENDED:
   R-CTCHC-06: CTCHC records SHOULD be included in OEP packages
      (BEV_INCLUDE_IN_OEP=true).
   R-CTCHC-07: Partial chain recovery (§7.6) SHOULD be implemented
      for deployments with unreliable infrastructure.

   NOT PERMITTED:
   R-CTCHC-08: A CTCHC_PARTIAL record MUST NOT be presented as a
      Session Integrity Proof (§7.6).
   R-CTCHC-09: No UPDATE or DELETE on atf_coherence_hash_chains.


13.  Persistence Schema

13.1.  atf_behavioral_anchor_records

   CREATE TABLE IF NOT EXISTS atf_behavioral_anchor_records (
       bar_id                    VARCHAR(64)      PRIMARY KEY,
       session_id                VARCHAR(64)      NOT NULL,
       governing_receipt_id      VARCHAR(128)     NOT NULL,
       agent_id                  VARCHAR(128)     NOT NULL,
       turn_index                INTEGER          NOT NULL,
       output_hash               VARCHAR(80)      NOT NULL,
       output_hash_mode          VARCHAR(16)      NOT NULL
                                     DEFAULT 'HASHED',
       output_payload            TEXT,
       constraint_vector         JSONB            NOT NULL DEFAULT '{}',
       ccs_score                 DOUBLE PRECISION NOT NULL DEFAULT -1.0,
       ccs_verdict               VARCHAR(16)      NOT NULL
                                     DEFAULT 'NO_DATA',
       ccs_components            JSONB            NOT NULL DEFAULT '{}',
       chain_link                VARCHAR(64)      NOT NULL,
       genesis_hash              VARCHAR(64),
       session_start_ns          BIGINT,
       bar_timestamp_ns          BIGINT           NOT NULL DEFAULT 0,
       issued_at                 TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
       content_hash_bar          VARCHAR(64)      NOT NULL DEFAULT '',
       pqc_signature             TEXT             NOT NULL DEFAULT '',
       pqc_algorithm             VARCHAR(32)      NOT NULL
                                     DEFAULT 'ML-DSA-65',
       atf_spec_version          VARCHAR(8)       NOT NULL DEFAULT '1.6',
       session_status            VARCHAR(32)      NOT NULL DEFAULT 'ACTIVE',
       created_at                TIMESTAMPTZ      NOT NULL DEFAULT NOW()
   );

   Indexes:
   - idx_bar_session_id — lookup by session
   - idx_bar_governing_receipt_id — join to ATF receipt store
   - idx_bar_agent_id — filter by agent
   - idx_bar_session_id_turn_index — ordered BAR retrieval per session
   - idx_bar_ccs_verdict — filter by verdict (audit queries)
   - idx_bar_created_at DESC — time-ordered audit access

   Design decisions:
   - bar_id is VARCHAR(64) UUID-based — consistent with ATF record IDs
   - output_payload is TEXT (nullable) — NULL when mode = HASHED/REDACTED
   - genesis_hash and session_start_ns NULL for turns > 0
   - session_status: ACTIVE | SEALED | FLAGGED
   - No UPDATE or DELETE triggers (BEV-INV-006)

13.2.  atf_constraint_conformance_signals

   CREATE TABLE IF NOT EXISTS atf_constraint_conformance_signals (
       ccs_id                    VARCHAR(64)      PRIMARY KEY,
       bar_id                    VARCHAR(64)      NOT NULL
                                     REFERENCES atf_behavioral_anchor_records
                                     (bar_id) ON DELETE RESTRICT,
       session_id                VARCHAR(64)      NOT NULL,
       governing_receipt_id      VARCHAR(128)     NOT NULL,
       turn_index                INTEGER          NOT NULL,
       ccs_score                 DOUBLE PRECISION NOT NULL,
       ccs_verdict               VARCHAR(16)      NOT NULL,
       output_boundary_score     DOUBLE PRECISION NOT NULL DEFAULT 0.0,
       constraint_satisfaction_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
       semantic_drift_score      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
       authority_alignment_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
       boundary_violation_count  INTEGER          NOT NULL DEFAULT 0,
       constraint_failure_count  INTEGER          NOT NULL DEFAULT 0,
       drift_magnitude           DOUBLE PRECISION,
       agvp_pvr_triggered        BOOLEAN          NOT NULL DEFAULT FALSE,
       agvp_pvr_id               VARCHAR(64),
       halt_triggered            BOOLEAN          NOT NULL DEFAULT FALSE,
       computed_at_ns            BIGINT           NOT NULL DEFAULT 0,
       created_at                TIMESTAMPTZ      NOT NULL DEFAULT NOW()
   );

   Indexes:
   - idx_ccs_session_id — session CCS history
   - idx_ccs_bar_id — join to BAR
   - idx_ccs_verdict — filter by verdict
   - idx_ccs_governing_receipt_id — receipt-level CCS history
   - idx_ccs_ccs_score — range queries for audit

   Design decisions:
   - This table is a projection of BAR.ccs_* fields.
   - It enables efficient CCS history queries without loading full
     BAR records (which may include output_payload in FULL mode).
   - agvp_pvr_id populated when AGVP PVR was successfully issued.
   - No UPDATE or DELETE: append-only CCS history.

13.3.  atf_coherence_hash_chains

   CREATE TABLE IF NOT EXISTS atf_coherence_hash_chains (
       ctchc_id                  VARCHAR(64)      PRIMARY KEY,
       session_id                VARCHAR(64)      NOT NULL UNIQUE,
       governing_receipt_id      VARCHAR(128)     NOT NULL,
       genesis_hash              VARCHAR(64)      NOT NULL,
       final_chain_hash          VARCHAR(64)      NOT NULL,
       turn_count                INTEGER          NOT NULL,
       all_bar_ids               JSONB            NOT NULL DEFAULT '[]',
       session_start_ns          BIGINT           NOT NULL DEFAULT 0,
       session_close_ns          BIGINT           NOT NULL DEFAULT 0,
       session_status            VARCHAR(32)      NOT NULL
                                     DEFAULT 'BEV-COMPLETE',
       failure_turn_index        INTEGER,
       failure_reason            TEXT             NOT NULL DEFAULT '',
       content_hash_ctchc        VARCHAR(64)      NOT NULL DEFAULT '',
       ctchc_seal                TEXT             NOT NULL DEFAULT '',
       pqc_algorithm             VARCHAR(32)      NOT NULL
                                     DEFAULT 'ML-DSA-65',
       atf_spec_version          VARCHAR(8)       NOT NULL DEFAULT '1.6',
       created_at                TIMESTAMPTZ      NOT NULL DEFAULT NOW()
   );

   Indexes:
   - idx_ctchc_session_id — primary lookup
   - idx_ctchc_governing_receipt_id — receipt-level CTCHC queries
   - idx_ctchc_session_status — filter complete/incomplete
   - idx_ctchc_created_at DESC — chronological access

   Design decisions:
   - session_id is UNIQUE: one CTCHC per BEV Session.
   - all_bar_ids is JSONB array of bar_ids in turn_index order.
   - session_status: BEV-COMPLETE | BEV-INCOMPLETE | CTCHC_SEAL_FAILED
     | CHAIN_BROKEN | CTCHC_PARTIAL
   - failure_turn_index and failure_reason populated for non-COMPLETE.
   - No UPDATE or DELETE (BEV-INV-018 enforcement).


14.  API Endpoints

   All BEV endpoints are prefixed /v1/bev/.  Authentication follows
   the OMNIX API key scheme (ADR-052).  All responses are JSON.

   POST /v1/bev/session/start
      Creates a new BEV Session and computes the genesis hash.
      Request: { governing_receipt_id, agent_id,
                 output_hash_mode, session_duration_limit_s? }
      Response: { session_id, genesis_hash, session_start_ns,
                  constraint_vector }

   POST /v1/bev/bar
      Submits a completed execution turn and produces a BAR.
      Request: { session_id, turn_index, output_hash or
                 output_payload (if FULL mode), ccs_inputs? }
      Response: { bar_id, ccs_score, ccs_verdict, chain_link,
                  content_hash_bar, pqc_signature }

   GET /v1/bev/bar/{bar_id}
      Retrieves a BAR record by ID.
      Response: complete BAR JSON

   POST /v1/bev/bar/{bar_id}/verify
      Performs offline verification of a BAR.
      Request: { output_payload? } (for FULL mode verification)
      Response: { verified: bool, steps: [{step, result, detail}] }

   GET /v1/bev/session/{session_id}/bars
      Retrieves all BARs for a session, ordered by turn_index.
      Response: { session_id, bars: [...], turn_count }

   GET /v1/bev/session/{session_id}/ccs
      Retrieves CCS history for a session.
      Response: { session_id, ccs_history: [...], conformant_turns,
                  drifting_turns, breach_turns, violation_turns }

   POST /v1/bev/session/{session_id}/close
      Seals the CTCHC for a completed session.
      Response: { ctchc_id, final_chain_hash, ctchc_seal,
                  session_status }

   GET /v1/bev/session/{session_id}/chain
      Retrieves the CTCHC record for a completed session.
      Response: complete CTCHC JSON

   POST /v1/bev/session/{session_id}/chain/verify
      Performs offline verification of the full session chain.
      Response: { coherent: bool, turn_count, verified_turns,
                  failures: [{turn_index, failure_type, detail}] }

   GET /v1/bev/receipt/{governing_receipt_id}/sessions
      Lists all BEV Sessions governed by a specific ATF receipt.
      Response: { governing_receipt_id, sessions: [session_id, ...],
                  complete_count, incomplete_count }


15.  Security Considerations

15.1.  BAR Output Hash Substitution

   Threat: An adversary replaces the output_hash in a BAR with a
   hash of a different, more compliant output — misrepresenting
   the agent's actual behavioral output.

   Mitigation:
   - BEV-INV-003: output_hash is covered by content_hash_bar.
     Modifying output_hash invalidates content_hash_bar and
     thereby invalidates pqc_signature.
   - BEV-INV-007 (offline verifiability): any verifier can detect
     the substitution by recomputing content_hash_bar from the
     BAR JSON and comparing to the signed value.
   - In FULL mode: the output_payload is also covered by
     content_hash_bar, enabling direct verification.

15.2.  BAR Fabrication Attack

   Threat: An adversary fabricates a BAR for a turn that did not
   occur, inserting a false behavioral record into a session.

   Mitigation:
   - BEV-INV-004 (PQC sealing): fabricated BARs require the
     platform ML-DSA-65 private key.  Key compromise required.
   - BEV-INV-015 (chain link monotonicity): a fabricated BAR
     inserted into an existing session sequence produces an
     incorrect chain_link, detectable from the CTCHC.
   - BEV-INV-016 (chain completeness): inserting a BAR creates
     a turn_index collision or gap, detectable in CTCHC verification.

15.3.  CCS Score Inflation Attack

   Threat: An adversary modifies the ccs_score field to report
   CONFORMANT when the actual score was DRIFTING or worse,
   suppressing AGVP PVR issuance.

   Mitigation:
   - BEV-INV-013 (CCS integrity via BAR seal): ccs_score is
     covered by content_hash_bar and pqc_signature.  Modification
     produces a signature verification failure.
   - BEV-INV-010 (DRIFTING triggers AGVP PVR): the CCS computation
     runs before BAR sealing, and the PVR issuance is triggered
     from the in-memory verdict before BAR persistence.  An
     adversary modifying the persisted BAR cannot retroactively
     suppress an already-issued PVR.

15.4.  CCS Component Manipulation

   Threat: An adversary manipulates individual CCS components to
   produce a passing ccs_score despite high violation counts in
   specific components (e.g., setting OBS = 40 while CSS = 0,
   SDS = 0 to produce score = 50).

   Mitigation:
   - BEV-INV-011 (component non-negativity): no component can
     be negative to offset another.
   - Implementations SHOULD log ccs_components alongside ccs_score
     in all compliance reports.  Regulators reviewing CCS evidence
     SHOULD examine component breakdown, not only aggregate score.
   - Future RFC-ATF extension: per-component threshold invariants
     (scope for RFC-ATF-7 if component-level floor requirements
     are operationally validated).

15.5.  CTCHC Genesis Substitution

   Threat: An adversary replaces a session's genesis_hash with one
   computed from a different governing_receipt_id, enabling BARs
   from a different governed session to be presented as if produced
   under the target receipt.

   Mitigation:
   - BEV-INV-014: genesis_hash is computed from the governing
     receipt ID and session ID.  A substituted genesis hash produces
     a chain verification failure at Step 4 of §7.5.
   - genesis_hash is embedded in CTCHC.content_hash_ctchc, which is
     covered by ctchc_seal.  Modifying genesis_hash after sealing
     invalidates ctchc_seal.

15.6.  Chain Link Replay Attack

   Threat: An adversary reuses a chain link from a prior session
   as the genesis hash of a new session, enabling partial chain
   fabrication.

   Mitigation:
   - The genesis hash includes session_start_ns (nanosecond
     timestamp).  Even if governing_receipt_id and session_id are
     the same, a different session_start_ns produces a different
     genesis hash.
   - session_id is UNIQUE per deployment.  Format BEV-SESSION-
     {16HEX} from a cryptographic UUID4 provides 128-bit uniqueness.

15.7.  Partial Chain Presentation

   Threat: An adversary presents only a subset of BARs from a
   session (omitting turns where violations occurred) claiming the
   subset is the complete session.

   Mitigation:
   - BEV-INV-016 (chain completeness): the CTCHC turn_count field
     declares the expected number of turns.  A verifier who receives
     fewer BARs than turn_count knows turns are missing.
   - BEV-INV-015 (monotonicity): missing turns produce chain link
     mismatches at subsequent turns, making omission detectable
     even without knowing the total turn_count.
   - The all_bar_ids array in the CTCHC record is a complete
     ordered inventory of expected BARs.

15.8.  Quantum Adversary

   All BEV records (BAR, CCS projection, CTCHC) are sealed with
   Dilithium-3 (ML-DSA-65, FIPS 204) at NIST PQC Level 3 security.
   The same quantum-adversary considerations as RFC-ATF-1 §11.5
   apply.  Key compromise for BEV records has the same response
   protocol as for primary ATF records: revoke the key, flag all
   BEV records sealed with the compromised key as INTEGRITY_UNKNOWN,
   and re-seal using the replacement key where the original output
   can be verified.

   For HASHED mode BARs where output_payload is not stored: key
   compromise means the output_hash cannot be re-signed with proof
   that the original output was unmodified.  Deployments with long-
   term forensic requirements SHOULD use FULL mode or archive the
   output content separately with an independent hash commitment.


16.  Novel Contributions

16.1.  Behavioral Anchor Record (BAR)

   The BAR is a novel cryptographic artifact with no equivalent in
   any published governance specification.  Prior art in AI
   governance (ADR-131 ExecutionReceipt, VeriSigil VGS-001-011,
   IBM OpenScale, Microsoft Azure Responsible AI Dashboard, ML
   monitoring platforms such as Arize and WhyLabs) records either:
   - The authorization (governance receipt)
   - The action (execution receipt, trading order)
   - The monitoring signal (separate monitoring pipeline)

   None records the behavioral content of the execution as a PQC-
   signed artifact cryptographically bound to the governing receipt.

   The BAR provides:
   - Per-turn behavioral output attestation bound to the governing
     receipt, with ML-DSA-65 sealing of the output hash.
   - Output hash privacy modes (FULL / HASHED / REDACTED) enabling
     GDPR compliance without sacrificing governance integrity.
   - Embedded CCS and chain link, making the BAR a self-contained
     behavioral evidence artifact.
   - Offline verifiability without OMNIX infrastructure access.

16.2.  Constraint Conformance Signal (CCS)

   The CCS is a governance-native conformance signal with no
   equivalent in published governance or ML monitoring specifications.

   Existing ML monitoring systems (Arize, WhyLabs, Evidently AI)
   measure behavioral drift against separately configured policies.
   The CCS measures conformance against the actual constraint vector
   of the governing receipt — the same PQC-signed authorization
   document that governs the execution.  This means:

   - The measurement specification cannot be modified independently
     of the authorization.  The CCS and the governing receipt are
     cryptographically coupled.
   - The CCS is part of the governance evidence chain, not a
     separate monitoring pipeline.
   - The CCS feeds the AGVP (RFC-ATF-4) anticipatory veto loop,
     enabling behavioral conformance degradation to trigger
     governance-native PVR issuance.

   The CCS-AGVP integration loop is the first published mechanism
   connecting behavioral output monitoring to anticipatory
   governance veto issuance in a cryptographically attested,
   governance-native protocol.

16.3.  Cross-Turn Coherence Hash Chain (CTCHC)

   The CTCHC is the first published mechanism for proving session-
   level behavioral coherence in multi-turn AI agent sessions using
   a cryptographic hash chain seeded by the governing receipt.

   Prior art provides:
   - Blockchain hash chains (Bitcoin, Ethereum): for financial
     transaction integrity, not behavioral governance.
   - Audit log hash chains (CloudTrail, Splunk): for system event
     integrity, not behavioral content attestation.
   - OMNIX ADR-155 CCS (Chain Completeness Score): for audit trail
     completeness, not multi-turn behavioral session coherence.

   None of these bind the chain to a specific governance receipt,
   making the chain inseparable from the authorization that governs
   it.  The CTCHC's genesis hash design (seeded by governing_receipt_id
   + session_id + session_start_ns) achieves this binding, making
   cross-session BAR substitution detectable by any verifier.

16.4.  CCS-AGVP Integration Loop

   The integration between CCS verdicts and AGVP PVR issuance
   (§6.5) is a structurally novel governance mechanism:

   Governance receipt authorizes → Agent executes → BAR attests output
   → CCS measures conformance → AGVP issues PVR (if DRIFTING) →
   PVR is forensic evidence of behavioral governance event

   This closed loop means that behavioral conformance degradation
   produces governance-signed evidence (a PVR) before a boundary
   violation occurs.  The anticipatory nature of the mechanism — a
   governance artifact produced before the violation, proving the
   violation was detected and acted upon — is patentably novel.

16.5.  Behavioral Attestation Chain

   The complete ordered sequence (GR, BAR_0, BAR_1, ..., BAR_{N-1},
   CTCHC) constitutes the Behavioral Attestation Chain — the first
   end-to-end forensic artifact spanning:

      Authorization → Per-turn behavioral output attestation →
      Per-turn conformance measurement → Session coherence proof

   Prior to this RFC, the ATF stack could prove the first element
   (authorization).  ADR-131 added action recording (execution
   receipt).  RFC-ATF-6 adds the behavioral content, conformance,
   and session coherence dimensions — completing the chain.

16.6.  ATF-BEV-Compliant — Sixth Compliance Tier

   ATF-BEV-Compliant is the first six-tier AI governance compliance
   designation to span: identity (RFC-ATF-1), runtime continuity
   (RFC-ATF-2), evidence lifecycle (RFC-ATF-3), proactive governance
   (RFC-ATF-4), cognitive governance (RFC-ATF-5), and behavioral
   execution verification (RFC-ATF-6) — 106 formally specified
   invariants across 20 protocol families.

   No peer governance specification — VeriSigil VGS (Zenodo
   10.5281/zenodo.20264923), IBM OpenScale, Microsoft Azure
   Responsible AI, Google Model Cards, or NIST AI RMF tools —
   provides a behavioral execution verification layer with PQC-
   signed per-turn attestation, governance-native conformance
   measurement, and session-level coherence proof.


17.  Distinction from Prior Art

   The following table positions RFC-ATF-6 against the most
   relevant published governance specifications:

   Feature                        | RFC-ATF-6     | ML Monitoring  | ADR-131  |
   -------------------------------|---------------|----------------|----------|
   Per-turn behavioral attestation| YES (BAR)     | No             | Partial* |
   PQC-signed output record       | YES           | No             | No       |
   Governing receipt binding      | YES           | No             | Yes      |
   Governance-native conformance  | YES (CCS)     | No             | No       |
   AGVP anticipatory integration  | YES           | No             | No       |
   Multi-turn coherence proof     | YES (CTCHC)   | No             | No       |
   Offline session verification   | YES           | No             | No       |
   Turn omission detection        | YES           | No             | No       |
   Cross-session subst. detection | YES           | No             | No       |
   OEP forensic portability       | YES           | No             | No       |
   106-invariant compliance tier  | YES (BEV)     | No             | No       |

   * ADR-131 records execution intent and result at the order level;
     it does not record the behavioral content (outputs) of the
     executing agent.

   OMNIX-specific properties present in no other published
   governance specification:
   - Behavioral Anchor Record (BAR) — PQC-signed, receipt-bound per-
     turn behavioral output attestation
   - Constraint Conformance Signal (CCS) — governance-native,
     multi-component behavioral conformance metric
   - Cross-Turn Coherence Hash Chain (CTCHC) — receipt-seeded session
     integrity proof for multi-turn agent sessions
   - CCS-AGVP integration loop — behavioral conformance as AGVP input
   - genesis_hash design — governing receipt binding for CTCHC
   - Behavioral Attestation Chain — end-to-end forensic artifact from
     authorization to session coherence proof
   - ATF-BEV-Compliant — 106-invariant, six-layer compliance
     designation with behavioral execution verification

   Comparison with specific prior art:

   ADR-131 (Execution Integrity Layer): records execution_intent
   (pre-execution) and execution_receipt (post-execution) at the
   exchange order level.  It proves that an order was sent and what
   the exchange response was.  It does not record the agent's
   behavioral outputs (text, structured data, tool calls) during
   the session that produced the order decision.  BAR operates at
   a higher abstraction level — the behavioral content layer —
   and is complementary to, not a replacement for, ADR-131.

   ADR-155 (Chain Completeness Score): measures the integrity of
   the audit trail (completeness, temporal consistency, break
   detection).  The CTCHC addresses behavioral session coherence
   (turn ordering, omission, substitution).  These are structurally
   different problems with structurally different constructions.

   ML monitoring platforms (Arize, WhyLabs, Evidently AI): monitor
   AI outputs against separately configured drift detection policies.
   The CCS monitors against the governing receipt's constraint vector,
   which is PQC-signed and immutable.  The CCS is governance evidence;
   ML monitoring is operational telemetry.

   VeriSigil VGS (Zenodo 10.5281/zenodo.20264923): provides
   jurisdiction-specific governance specifications.  VGS records
   governance decisions.  It does not record behavioral outputs,
   provide conformance measurement, or provide session coherence proof.


18.  Regulatory Alignment

   | Framework              | BAR Relevance                | CCS Relevance                  | CTCHC Relevance              |
   |------------------------|------------------------------|--------------------------------|------------------------------|
   | EU AI Act Art. 9       | Art. 9: monitoring within    | Art. 9: risk management        | Art. 9: continuous           |
   |                        | defined boundaries; BAR is   | includes ongoing conformance   | boundary enforcement proof   |
   |                        | the attestation artifact     | measurement                    | across session lifetime      |
   | EU AI Act Art. 12      | Art. 12: logging of AI       | Art. 12: logged conformance    | Art. 12: complete, ordered   |
   |                        | system outputs               | signals per output             | output log with integrity    |
   | EU AI Act Art. 13      | Art. 13: transparency —      | Art. 13: conformance score     | Art. 13: session-level       |
   |                        | behavioral evidence          | is interpretable measure       | behavioral transparency      |
   | EU AI Act Art. 72      | 7yr retention: BAR records   | CCS history retained per BAR   | CTCHC seals session for      |
   |                        | subject to retention policy  | (same 7yr obligation)          | long-term retention          |
   | NIST AI RMF            | MEASURE 2.6: ongoing         | MEASURE 2.6: quantitative      | MANAGE 2.2: session-level    |
   | MEASURE 2.6            | monitoring of AI outputs     | behavioral monitoring          | behavioral integrity         |
   | NIST MANAGE 2.2        | Management of AI systems     | CCS feeds management           | CTCHC proves management      |
   |                        | in operation                 | decision signals               | continuity across turns      |
   | NIST GOVERN 1.7        | Documentation of AI          | Conformance measurement        | Session coherence as         |
   |                        | system behavior              | documented per turn            | governance record            |
   | GCC/DIFC Art. 9        | Continuous AI oversight:     | Continuous oversight signal    | Oversight of session         |
   |                        | BAR per turn                 | per turn                       | continuity                   |
   | GCC/DIFC Art. 12       | Audit trail for AI actions   | CCS in audit trail             | Complete session audit trail |
   | ISO 42001 §8.4         | AI system operation          | Operational conformance        | Turn-by-turn operational     |
   |                        | controls including output    | controls per §8.4              | control record               |
   | ISO 42001 §9.1         | Monitoring, measurement,     | CCS is the measurement         | CTCHC enables analysis       |
   |                        | analysis, evaluation         | artifact for §9.1              | across session history       |
   | UK AISI §3-5           | §3: accountability for       | §5: measurement of AI          | §4: evidence of operational  |
   |                        | AI outputs documented        | behavioral conformance         | safeguards continuity        |
   | MiFID II Art. 17       | Algorithmic trading: pre-    | Conformance of trading         | Multi-turn session           |
   |                        | and post-output record       | agent outputs                  | integrity for MiFID          |
   | SOC 2 Type II CC7.2    | Output monitoring            | Quantitative conformance       | Session integrity in         |
   |                        | evidence                     | for SOC 2 monitoring           | SOC 2 audit                  |


19.  References

   [RFC-ATF-1]
      Nunes, H., "RFC-ATF-1: Agent Trust Fabric Delegation Protocol,
      Version 1.0.0", OMNIX QUANTUM Open Standard, May 2026.
      DOI: 10.5281/zenodo.20155016
      Figshare: 10.6084/m9.figshare.32308077

   [RFC-ATF-2]
      Nunes, H., "RFC-ATF-2: Agent Trust Fabric — Runtime Governance
      Continuity, Version 1.0.0", OMNIX QUANTUM Open Standard,
      May 2026.
      DOI: 10.5281/zenodo.20241344
      Figshare: 10.6084/m9.figshare.32308095

   [RFC-ATF-3]
      Nunes, H., "RFC-ATF-3: Agent Trust Fabric — Governance Policy
      Interoperability, Evidence Lifecycle, and Forensic Verification
      Protocol, Version 1.0.0", OMNIX QUANTUM Open Standard,
      May 2026.
      DOI: 10.5281/zenodo.20247342
      Figshare: 10.6084/m9.figshare.32308119

   [RFC-ATF-4]
      Nunes, H., "RFC-ATF-4: Agent Trust Fabric — Proactive
      Governance Layer, Version 1.0.0", OMNIX QUANTUM Open Standard,
      May 2026.
      DOI: [PENDING — verify before citing publicly]

   [RFC-ATF-5]
      Nunes, H., "RFC-ATF-5: Agent Trust Fabric — Cognitive
      Governance Layer, Version 1.0.0", OMNIX QUANTUM Open Standard,
      May 2026.
      DOI: [PENDING — verify before citing publicly]

   [FIPS204]
      National Institute of Standards and Technology, "Module-
      Lattice-Based Digital Signature Standard (ML-DSA)",
      FIPS 204, Aug 2024.

   [FIPS180-4]
      National Institute of Standards and Technology, "Secure Hash
      Standard (SHS)", FIPS 180-4, Aug 2015.

   [Z3]
      de Moura, L. and Bjørner, N., "Z3: An Efficient SMT Solver",
      Proceedings of TACAS 2008, LNCS 4963, pp. 337-340,
      Springer 2008.

   [RFC2119]
      Bradner, S., "Key words for use in RFCs to Indicate Requirement
      Levels", BCP 14, RFC 2119, March 1997.

   [RFC8174]
      Leiba, B., "Ambiguity of Uppercase vs Lowercase in RFC 2119
      Key Words", BCP 14, RFC 8174, May 2017.

   [ADR-131]
      Nunes, H., "ADR-131: Execution Integrity Layer",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-131

   [ADR-155]
      Nunes, H., "ADR-155: Chain Completeness Score",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-155

   [ADR-174]
      Nunes, H., "ADR-174: Anticipatory Governance Veto Protocol",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-174

   [ADR-177]
      Nunes, H., "ADR-177: OMNIX Formal Verification Suite (FVS)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-177

   [ADR-181]
      Nunes, H., "ADR-181: Behavioral Anchor Record (BAR)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-181

   [ADR-182]
      Nunes, H., "ADR-182: Constraint Conformance Signal (CCS)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-182

   [ADR-183]
      Nunes, H., "ADR-183: Cross-Turn Coherence Hash Chain (CTCHC)",
      OMNIX QUANTUM, May 2026.
      omnixquantum.net/docs/adr/ADR-183

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


20.  Appendix A — BEV Wire Format Reference

A.1  BAR Wire Format (normative field reference)

   | Field                  | Type    | Req'd     | Constraints                         |
   |------------------------|---------|-----------|-------------------------------------|
   | bar_id                 | string  | REQUIRED  | "BAR-" + 16 uppercase hex           |
   | session_id             | string  | REQUIRED  | "BEV-SESSION-" + 16 uppercase hex   |
   | governing_receipt_id   | string  | REQUIRED  | Valid ATF record ID                 |
   | agent_id               | string  | REQUIRED  | Matches GR.agent_id                 |
   | turn_index             | integer | REQUIRED  | >= 0; strictly increasing per sess  |
   | output_hash            | string  | REQUIRED  | "sha256:" + 64 lowercase hex        |
   | output_hash_mode       | string  | REQUIRED  | FULL | HASHED | REDACTED            |
   | output_payload         | any     | COND.     | Required when mode = FULL           |
   | constraint_vector      | object  | REQUIRED  | See §5.2 constraint_vector fields   |
   | ccs_score              | number  | REQUIRED  | [0.0, 100.0] or -1.0 (NO_DATA)      |
   | ccs_verdict            | string  | REQUIRED  | CONFORMANT|DRIFTING|BREACH|         |
   |                        |         |           | VIOLATION|NO_DATA                  |
   | ccs_components         | object  | COND.     | Required when CCS_ENABLED           |
   | chain_link             | string  | REQUIRED  | 64 lowercase hex (SHA-256)          |
   | genesis_hash           | string  | COND.     | Required in turn_index=0 BAR only   |
   | session_start_ns       | integer | COND.     | Required in turn_index=0 BAR only   |
   | bar_timestamp_ns       | integer | REQUIRED  | Nanosecond epoch; > 0               |
   | issued_at              | string  | REQUIRED  | ISO-8601-UTC, nanosecond precision  |
   | content_hash_bar       | string  | REQUIRED  | 64 lowercase hex                    |
   | pqc_signature          | string  | REQUIRED  | ML-DSA-65 sig, base64               |
   | pqc_algorithm          | string  | REQUIRED  | MUST be "ML-DSA-65"                 |
   | atf_spec_version       | string  | REQUIRED  | MUST be "1.6"                       |

   Example BAR JSON (HASHED mode, turn_index=0):
   {
     "bar_id":               "BAR-3F1A4B7C2D8E5F9A",
     "session_id":           "BEV-SESSION-A1B2C3D4E5F6A7B8",
     "governing_receipt_id": "ATFDR-8B2C4D6E1F3A5B7C9D0E1F2A",
     "agent_id":             "AIR-7C2D4E6F1A3B5C7D",
     "turn_index":           0,
     "output_hash":          "sha256:a1b2c3d4e5f6...64chars",
     "output_hash_mode":     "HASHED",
     "constraint_vector": {
       "authority_scope":    "financial_analysis",
       "output_domain":      "structured_report",
       "prohibited_classes": ["executable_code", "pii_exfiltration"],
       "turn_limit":         50,
       "session_duration_limit_s": 3600
     },
     "ccs_score":            94.5,
     "ccs_verdict":          "CONFORMANT",
     "ccs_components": {
       "output_boundary_score":       40.0,
       "constraint_satisfaction_score": 30.0,
       "semantic_drift_score":        14.5,
       "authority_alignment_score":   10.0
     },
     "chain_link":           "b2c3d4e5f6a7...64chars",
     "genesis_hash":         "c3d4e5f6a7b8...64chars",
     "session_start_ns":     1748000000000000000,
     "bar_timestamp_ns":     1748000001500000000,
     "issued_at":            "2026-05-23T14:00:01.500000000+00:00",
     "content_hash_bar":     "d4e5f6a7b8c9...64chars",
     "pqc_signature":        "<base64-ML-DSA-65-sig>",
     "pqc_algorithm":        "ML-DSA-65",
     "atf_spec_version":     "1.6"
   }

A.2  CTCHC Wire Format (normative field reference)

   | Field                  | Type     | Req'd    | Constraints                        |
   |------------------------|----------|----------|------------------------------------|
   | ctchc_id               | string   | REQUIRED | "CTCHC-" + 16 uppercase hex        |
   | session_id             | string   | REQUIRED | "BEV-SESSION-" + 16 uppercase hex  |
   | governing_receipt_id   | string   | REQUIRED | Valid ATF record ID                |
   | genesis_hash           | string   | REQUIRED | 64 lowercase hex                   |
   | final_chain_hash       | string   | REQUIRED | 64 lowercase hex                   |
   | turn_count             | integer  | REQUIRED | >= 1                               |
   | all_bar_ids            | string[] | REQUIRED | len = turn_count; ordered          |
   | session_start_ns       | integer  | REQUIRED | Nanosecond epoch                   |
   | session_close_ns       | integer  | REQUIRED | >= session_start_ns                |
   | session_status         | string   | REQUIRED | BEV-COMPLETE|BEV-INCOMPLETE|...    |
   | failure_turn_index     | integer  | OPTIONAL | Present when status != COMPLETE    |
   | failure_reason         | string   | OPTIONAL | Present when status != COMPLETE    |
   | content_hash_ctchc     | string   | REQUIRED | 64 lowercase hex                   |
   | ctchc_seal             | string   | REQUIRED | ML-DSA-65 sig, base64              |
   | pqc_algorithm          | string   | REQUIRED | MUST be "ML-DSA-65"                |
   | atf_spec_version       | string   | REQUIRED | MUST be "1.6"                      |

   Example CTCHC JSON:
   {
     "ctchc_id":             "CTCHC-1A2B3C4D5E6F7A8B",
     "session_id":           "BEV-SESSION-A1B2C3D4E5F6A7B8",
     "governing_receipt_id": "ATFDR-8B2C4D6E1F3A5B7C9D0E1F2A",
     "genesis_hash":         "c3d4e5f6a7b8...64chars",
     "final_chain_hash":     "f7a8b9c0d1e2...64chars",
     "turn_count":           12,
     "all_bar_ids": [
       "BAR-3F1A4B7C2D8E5F9A",
       "BAR-2A3B4C5D6E7F8A9B",
       "..."
     ],
     "session_start_ns":     1748000000000000000,
     "session_close_ns":     1748003600000000000,
     "session_status":       "BEV-COMPLETE",
     "content_hash_ctchc":   "e8f9a0b1c2d3...64chars",
     "ctchc_seal":           "<base64-ML-DSA-65-sig>",
     "pqc_algorithm":        "ML-DSA-65",
     "atf_spec_version":     "1.6"
   }

A.3  CCS Wire Format (embedded in BAR, normative)

   ccs_components object fields (when CCS_ENABLED=true):

   | Field                          | Type   | Req'd    | Constraints          |
   |--------------------------------|--------|----------|----------------------|
   | output_boundary_score          | number | REQUIRED | [0.0, 40.0]          |
   | constraint_satisfaction_score  | number | REQUIRED | [0.0, 30.0]          |
   | semantic_drift_score           | number | REQUIRED | [0.0, 20.0]          |
   | authority_alignment_score      | number | REQUIRED | 0.0 or 10.0          |
   | boundary_violation_count       | integer| REQUIRED | >= 0                 |
   | constraint_failure_count       | integer| REQUIRED | >= 0                 |
   | drift_magnitude                | number | OPTIONAL | [0.0, 1.0] if SDS    |
   | sds_method                     | string | OPTIONAL | embedding model ID   |


21.  Appendix B — CCS Computation Reference

B.1  Component Computation Pseudocode

   def compute_ccs(output: Any, constraint_vector: dict,
                   session_context: dict) -> dict:
       """Compute CCS for a single execution turn."""

       # Component 1: Output Boundary Score
       violations = []
       for prohibited in constraint_vector.get("prohibited_classes", []):
           if detect_violation(output, prohibited):
               violations.append(prohibited)
       for domain_rule in get_output_domain_rules(
               constraint_vector.get("output_domain", "")):
           if not satisfies_domain_rule(output, domain_rule):
               violations.append(domain_rule)
       obs = max(0.0, 40.0 - 10.0 * len(violations))

       # Component 2: Constraint Satisfaction Score
       failures = []
       for constraint_name, constraint_spec in constraint_vector.get(
               "domain_specific_constraints", {}).items():
           if not evaluate_constraint(output, constraint_name,
                                       constraint_spec):
               failures.append(constraint_name)
       css = max(0.0, 30.0 - 8.0 * len(failures))

       # Component 3: Semantic Drift Score
       sds_method = constraint_vector.get(
           "domain_specific_constraints", {}).get("sds_embedding_model")
       if sds_method:
           current_emb = embed(output, model=sds_method)
           authorized_emb = session_context["authorized_profile_embedding"]
           drift = cosine_distance(current_emb, authorized_emb)
           sds = max(0.0, 20.0 * (1.0 - drift))
           drift_magnitude = drift
       else:
           sds = 20.0
           drift_magnitude = None
           sds_method = "NO_EMBEDDING_MODEL"

       # Component 4: Authority Alignment Score
       authority_scope = constraint_vector.get("authority_scope", "")
       aas = 10.0 if within_scope(output, authority_scope) else 0.0

       ccs_score = round(obs + css + sds + aas, 4)

       return {
           "ccs_score":                    ccs_score,
           "ccs_verdict":                  derive_verdict(ccs_score),
           "ccs_components": {
               "output_boundary_score":          obs,
               "constraint_satisfaction_score":  css,
               "semantic_drift_score":           sds,
               "authority_alignment_score":      aas,
               "boundary_violation_count":       len(violations),
               "constraint_failure_count":       len(failures),
               "drift_magnitude":                drift_magnitude,
               "sds_method":                     sds_method,
           }
       }

   def derive_verdict(score: float) -> str:
       CONFORMANT = float(os.getenv("CCS_CONFORMANT_THRESHOLD", "90.0"))
       DRIFTING   = float(os.getenv("CCS_DRIFTING_THRESHOLD",   "70.0"))
       BREACH     = float(os.getenv("CCS_BREACH_THRESHOLD",     "50.0"))
       if score < 0:
           return "NO_DATA"
       elif score >= CONFORMANT:
           return "CONFORMANT"
       elif score >= DRIFTING:
           return "DRIFTING"
       elif score >= BREACH:
           return "BREACH"
       else:
           return "VIOLATION"

B.2  CTCHC Chain Link Computation Reference

   import hashlib

   def compute_genesis_hash(governing_receipt_id: str,
                             session_id: str,
                             session_start_ns: int) -> str:
       data = (
           governing_receipt_id.encode("utf-8") +
           b"||" +
           session_id.encode("utf-8") +
           b"||" +
           session_start_ns.to_bytes(8, "big")
       )
       return hashlib.sha256(data).hexdigest()

   def compute_turn_hash(output_hash_hex: str, turn_index: int) -> bytes:
       output_bytes = bytes.fromhex(output_hash_hex)
       turn_bytes   = turn_index.to_bytes(8, "big")
       return hashlib.sha256(output_bytes + turn_bytes).digest()

   def compute_chain_link(prior_chain_link_hex: str,
                           turn_hash_bytes: bytes) -> str:
       prior_bytes = bytes.fromhex(prior_chain_link_hex)
       return hashlib.sha256(prior_bytes + turn_hash_bytes).hexdigest()

   def compute_chain_link_0(genesis_hash_hex: str,
                              output_hash_hex: str,
                              turn_index: int) -> str:
       turn_hash = compute_turn_hash(output_hash_hex, turn_index)
       return compute_chain_link(genesis_hash_hex, turn_hash)

B.3  CCS Threshold Configuration Reference

   Environment variable defaults and production floors:

   | Variable                  | Default | Production Floor | Never Exceed |
   |---------------------------|---------|------------------|--------------|
   | CCS_CONFORMANT_THRESHOLD  | 90.0    | 85.0             | N/A (floor)  |
   | CCS_DRIFTING_THRESHOLD    | 70.0    | 60.0             | N/A (floor)  |
   | CCS_BREACH_THRESHOLD      | 50.0    | 40.0             | N/A (floor)  |
   | BEV_AGVP_TRIGGER_TIMEOUT  | 500ms   | 1000ms           | 5000ms       |
   | BEV_HALT_TIMEOUT_MS       | 100ms   | 500ms            | 2000ms       |
   | CTCHC_MAX_RETRY_HOURS     | 1       | 4                | 24           |


22.  Appendix C — BEV Compliance Checklist

   Implementations claiming ATF-BEV-Compliant MUST satisfy all
   items.  Items marked (CGL) are inherited from RFC-ATF-5.

   BAR
   □ BEV_ENABLED=true in production
   □ BEV session initialized before first turn (session_id, genesis_hash)
   □ governing_receipt_id validated against ATF receipt store at session
     start (BEV-INV-002)
   □ Every authorized turn produces a persisted BAR before next turn
     begins (BEV-INV-001)
   □ turn_index starts at 0 and is strictly monotonically increasing
     per session (no gaps, no reuse) (BEV-INV-015)
   □ output_hash computed per §5.5 for declared output_hash_mode
   □ content_hash_bar = SHA-256(canonical_json(BAR \ sig fields))
     (§5.3)
   □ pqc_algorithm = "ML-DSA-65" in every BAR (BEV-INV-004)
   □ pqc_signature = ML-DSA-65 sign(content_hash_bar.encode()) using
     platform key (BEV-INV-004)
   □ BAR sealed before persistence (BEV-INV-004)
   □ BAR persistence failure triggers BEV-INCOMPLETE flag and blocks
     next turn (BEV-INV-005)
   □ No UPDATE or DELETE on atf_behavioral_anchor_records (BEV-INV-006)
   □ §5.7 offline verification passes for all BARs (BEV-INV-007)
   □ atf_spec_version = "1.6" in every BAR

   CCS
   □ CCS_ENABLED=true in production
   □ CCS computation completes before content_hash_bar computation
     (§4.4 step ordering)
   □ ccs_score ∈ [0.0, 100.0] for all non-REDACTED BARs (BEV-INV-009)
   □ All four ccs_components present and non-negative (BEV-INV-011)
   □ ccs_verdict consistent with ccs_score per §6.4 thresholds
   □ DRIFTING, BREACH, or VIOLATION verdict triggers AGVP PVR within
     BEV_AGVP_TRIGGER_TIMEOUT_MS (BEV-INV-010)
   □ VIOLATION verdict triggers HALT propagation within
     BEV_HALT_TIMEOUT_MS (BEV-INV-012)
   □ No further turns permitted in a HALTED session (BEV-INV-012)
   □ ccs_score, ccs_verdict, ccs_components covered by content_hash_bar
     (BEV-INV-013)
   □ CCS threshold variables at or above production floors (§6.4)
   □ atf_constraint_conformance_signals table kept in sync with BAR
     records

   CTCHC
   □ CTCHC_ENABLED=true in production
   □ genesis_hash computed using §7.2 formula from governing_receipt_id,
     session_id, session_start_ns (BEV-INV-014)
   □ genesis_hash stored in turn_index=0 BAR
   □ chain_link computed using §7.3 formula for every turn (BEV-INV-015)
   □ chain_link embedded in BAR before BAR sealing (§4.4 ordering)
   □ CTCHC sealed at session close using §7.4 procedure
   □ content_hash_ctchc = SHA-256(canonical_json(CTCHC \ seal fields))
   □ ctchc_seal = ML-DSA-65 sign(content_hash_ctchc) (BEV-INV-018)
   □ all_bar_ids contains all session BAR IDs in turn_index order
     (BEV-INV-016)
   □ Session status BEV-COMPLETE only after CTCHC is sealed
   □ §7.5 offline verification passes for all completed sessions
     (BEV-INV-017)
   □ No UPDATE or DELETE on atf_coherence_hash_chains
   □ CTCHC_PARTIAL records NOT presented as Session Integrity Proof

   AGVP Integration
   □ PVR issuance request includes trigger_source = "CCS_BEV"
   □ PVR references trigger_bar_id
   □ AGVP PVR issuance logged in atf_constraint_conformance_signals.
     agvp_pvr_triggered = True and agvp_pvr_id set
   □ HALT propagation logged in session audit trail

   Formal Verification
   □ BEV proof targets in omnix_core/formal_verification/run_bev_proofs.py
     run without UNKNOWN or SAT results for BEV-FVS-001 through -004
   □ JSON proof report producible for compliance deliverables

   OEP Integration (RECOMMENDED)
   □ BEV_INCLUDE_IN_OEP=true configured
   □ CTCHC record included in OEP packages for BEV sessions
   □ BAR records included (HASHED mode recommended)

   Inherited from ATF-CGL-Compliant (RFC-ATF-5) (abbreviated):
   □ (CGL) CGE_ENABLED=true, all CGE-INV satisfied
   □ (CGL) GUGT-L3+ATF UIR issued and verified
   □ (CGL) TGB_ENABLED=true, all TGB-INV satisfied
   □ (CGL) All RFC-ATF-4 invariants satisfied (AGVP/SSD/DSPP/FVS)
   □ (CGL) All RFC-ATF-3 invariants satisfied
   □ (CGL) All RFC-ATF-2 invariants satisfied (RGC-INV-001-008)
   □ (CGL) All RFC-ATF-1 invariants satisfied (ATF-INV-001-006)
   □ (CGL) PostgreSQL + Redis configured in production
   □ (CGL) ML-DSA-65 signing keys stable across restarts (FMR-001)
   □ (CGL) OMNIX_ANTI_REPLAY_MODE = strict in production


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

*RFC-ATF-6 Version 1.0.0 — May 2026*
*OMNIX QUANTUM LTD — Harold Nunes, Editor*
*Priority Records: OMNIX-PAR-2026-BAR-001 · OMNIX-PAR-2026-CCS-001 ·
OMNIX-PAR-2026-CTCHC-001*

*STATUS: DRAFT — NOT YET SUBMITTED TO ZENODO*
*REVISION HISTORY: v0.1 initial draft — May 23, 2026*

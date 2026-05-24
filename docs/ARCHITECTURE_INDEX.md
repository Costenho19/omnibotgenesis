# OMNIX QUANTUM — Architecture Index

Índice completo de módulos, documentos, páginas y artefactos del proyecto.
Referencia interna para agentes y desarrolladores. Actualizar al añadir nuevos componentes.

---

## ADRs y Baseline

- **ADRs:** `docs/adr/` — **188 total**. Últimos: ADR-184 (OGR) · ADR-185 (OGR Hardening) · ADR-186 (PoGR) · ADR-187 (PoGR API) · **ADR-188 (OSG — OMNIX Settlement Gate)**
- **Governance Baseline:** `docs/GOVERNANCE_BASELINE.md` — OMNIX-BASELINE-2026-Q2-001 · 11 invariants (baseline) · 151 ADRs · Architecture Freeze · **124 invariantes totales activos** (ATF×6+TAR×1 + RGC×8 + GPIL×3 + ELR×4 + EAP×7 + OEP×6 + FEA×5 + FVP×1 + GECR×6 + SGIP×4 + DSPP×7 + AGVP×6 + SSD×3 + FVS×3 + CGE×7 + GUGT×6 + TGB×5 + BEV×18 + OGR×1 + PoGR×6 + **OSG×6**) — RFC-ATF-5 (Cognitive Governance Layer — PENDING DOI) · RFC-ATF-6 (BEV) · PoGR (ADR-186) · OSG (ADR-188)
- **Full Architecture:** `docs/current/ARCHITECTURE.md`
- **Runtime Authority Matrix:** `docs/AUTHORITY_MATRIX.md` — ADR-146

---

## Releases

| Documento | Archivo | Alcance |
|---|---|---|
| **ATF Ecosystem Release 3.3** | `docs/releases/ATF_ECOSYSTEM_RELEASE_3.3.md` | Documento anchor del ecosistema ATF completo. RFC-ATF-1/2/3 (6 DOIs permanentes), 47 invariantes, 171 ADRs, 245+ tests, changelog ADR-161→171, artifacts, regulatory alignment, Priority Record. OMNIX-ATF-RELEASE-3.3-2026-05 |
| **ATF Ecosystem Baseline 2026.05** | `docs/releases/ATF_ECOSYSTEM_BASELINE_2026-05.md` | **Snapshot institucional congelado — May 18, 2026.** RFC stack completo con DOIs, 47 invariantes activos por familia, 171 ADRs, designación de conformance L1–L4, infraestructura criptográfica ML-DSA-65, test suite 245+ tests, audit trail, sección de freeze explícita. Documento de referencia para due diligence institucional, revisores regulatorios y citación académica. OMNIX-ATF-BASELINE-2026-05 |

---

## Guías Institucionales

| Documento | Archivo | Audiencia |
|---|---|---|
| **Auditor Offline Verification Guide** | `docs/guides/AUDITOR_OFFLINE_VERIFICATION_GUIDE.md` | External auditors · Regulators · Legal counsel — How to verify ATF evidence offline without platform access. Step-by-step: OEP package anatomy, platform key cross-reference (HTTP/DNS/Zenodo), CLI verifier execution, receipt interpretation, regulatory checklist (14 points), common auditor Q&A. OMNIX-GUIDE-AUDITOR-OFV-2026-05 |

---

## Casos Prácticos

| Documento | Archivo | Alcance |
|---|---|---|
| **E2E ATF Forensic Case Study** | `docs/examples/E2E_ATF_FORENSIC_CASE_STUDY.md` | Escenario end-to-end completo: Human→Agent delegation→TAR→ControlReceipt→RCR chain (NOMINAL→MONITORING→WARNING→CRITICAL→HALT)→RC expiry→emergency COLD seal→OEP export→offline verification. Campo a campo con valores reales. Verifier output literal. 14 invariantes verificados. OMNIX-EXAMPLE-E2E-FORENSIC-2026-05 |
| **Offline Governance Evidence Verification — Institutional Walkthrough** | `docs/walkthroughs/OFFLINE_GOVERNANCE_VERIFICATION_WALKTHROUGH.md` | **Walkthrough forense/cinemático end-to-end.** 7 actos: delegación inicial (DR PQC-signed) → actividad runtime (cálculos CES reales: T×0.30+B×0.30+D×0.20+I×0.20) → governance event (context drift 51.2%) → HALT enforced (Reauthorization Challenge TTL expirado, RGC-INV-008) → CTAG revocation (drift_delta −0.16 > threshold) → evidence lifecycle HOT→WARM→COLD (9-step migration) → OEP export (two-phase signature) → verificación offline en terminal (5 comandos, zero acceso a plataforma). 10 invariantes ejercidos. Basado 100% en módulos de producción. OMNIX-WALK-001 |

---

## Auditorías y Compliance

| Documento | Archivo | Alcance |
|---|---|---|
| **Institutional Architecture Review — ATF/EAP/OEP** | `docs/audits/ATF_EAP_OEP_INSTITUTIONAL_AUDIT_2026-05.md` | ADR-156–169 · 40 invariantes (snapshot al momento del audit, antes de ADR-157 rev.2 + ADR-170) · Gap analysis A–F · Risk prioritization · ADR-169 fail-open tension · Institutional buyer flags · Top-5 strategic recommendations · OMNIX-AUDIT-ATF-EAP-OEP-2026-05 |
| **47-Invariant Test Coverage Matrix** | `docs/compliance/INVARIANT_TEST_MATRIX.md` | Trazabilidad completa: 47 invariantes × implementación × test (rev.3) · 41/47 cobertura directa (87.2%) · 6/47 structural-only · 0 sin cobertura · Plan de remediación priorizado · OMNIX-COMPLIANCE-INV-MATRIX-2026-05 |
| ADR-160 Production Audit | `docs/audits/ADR-160-PRODUCTION-AUDIT.md` | RCR Performance / RPOL |
| ADR-161 GPIL Production Audit | `docs/audits/ADR-161-GPIL-PRODUCTION-AUDIT.md` | Governance Policy Interop Layer |
| ADR-163 Protocol Page Audit | `docs/audits/ADR-163-PROTOCOL-PAGE-AUDIT.md` | Immutable Evidence Archive |
| ATF Differentiator Validation | `docs/audits/ATF-DIFFERENTIATOR-VALIDATION.md` | ATF stack institutional positioning |
| OMNIX End-to-End Institutional Audit | `docs/audits/OMNIX-END-TO-END-INSTITUTIONAL-AUDIT.md` | Full platform audit |
| Postgres Storage Audit | `docs/audits/POSTGRES-STORAGE-AUDIT.md` | DB schema + storage patterns |
| Protocol Visualization Report | `docs/audits/PROTOCOL-VISUALIZATION-IMPLEMENTATION-REPORT.md` | ProtocolVisualizationPage |
| Sprint Ecosystem Final Audit | `docs/audits/SPRINT-ECOSYSTEM-FINAL-AUDIT.md` | Sprint ecosystem review |
| Sprint Forensic Infra Audit | `docs/audits/SPRINT-FORENSIC-INFRA-AUDIT.md` | Forensic infrastructure |

**Open items tracked in OMNIX-AUDIT-ATF-EAP-OEP-2026-05:**
- 🔴 CRITICAL: `test_adr168_module_parity.py` — no existe aún (ADR-168 §2 lo exige)
- 🔴 CRITICAL: Redis startup probe en `api/server.py` para EAP-INV-007 producción
- 🟡 HIGH: `ATF_REJECTED_ENFORCEMENT` env var en `gov_blueprint.py` (ADR-169 regulated mode)
- 🟡 HIGH: `omnix_core/governance/gpil.py` runtime module para CRGC operacional (ADR-161)

---

## Módulos Core

| Módulo | Archivo | ADR |
|---|---|---|
| Unified Decision Control Layer | `omnix_core/governance/unified_control_layer.py` | ADR-138 |
| Dilithium-3 PQC signing | `omnix_core/security/pqc_security.py` | — |
| Governance Replay Engine | `omnix_core/simulation/governance_replay.py` | ADR-145, ADR-149 |
| Auto-Modification Guard | `omnix_core/governance/auto_modification_guard.py` | ADR-144 |
| Scope Authorization Engine | `omnix_core/governance/scope_authorization_engine.py` | ADR-147 |
| LLM Isolation Boundary | `omnix_core/governance/llm_isolation_boundary.py` | ADR-148 |
| Memory Context Auditor | `omnix_core/governance/memory_context_auditor.py` | ADR-151 |
| Health Check | `omnix_core/ops/health_check.py` + `health_blueprint.py` | ADR-150 |
| Assumption Validity Monitor | `omnix_core/governance/assumption_validity_monitor.py` | ISR-001 |
| AVM DB Bridge | `omnix_core/governance/avm_db_bridge.py` | ISR-001 |
| Semantic Version Registry | `omnix_core/governance/semantic_version_registry.py` | ISR-008 |
| Decision Receipt | `omnix_core/evidence/decision_receipt.py` | ISR-008, ISR-010 |
| Receipt WAL | `omnix_core/evidence/receipt_wal.py` | ISR-012 |
| Transparency Chain | `omnix_core/evidence/transparency_chain.py` | ISR-013, ISR-022 |
| Input Sanitizer | `omnix_services/ai_service/input_sanitizer.py` | ISR-017 |
| Payload Key Manager | `omnix_core/evidence/payload_key_manager.py` | ISR-021 |

---

## Agent Trust Fabric (ATF) — ADR-156/157/158/159/160/161

| Componente | Archivo | Notas |
|---|---|---|
| **Governance Execution Context Router (GECR)** | `context_admission_gate.py` + `commit_time_gate.py` + `runtime_continuity.py` AFG/HALT/RC + ADR-161 CRGC | **ADR-170** — 6-component orchestration tier: CPR · CREG · CAAC · CABE · WIS · CRPR. 6 invariants GECR-INV-001–006. Defines Control-Receipt Atomicity (GECR-INV-001). |
| ATF Core | `omnix_core/agents/atf/` | AgentIdentity · DelegationReceipt · TrustLattice |
| Temporal Authority | `omnix_core/agents/atf/temporal_authority.py` | ATFTAR-{16HEX} · TAR-INV-001/005 · ADR-157 |
| Cross-Domain Bridge | `omnix_core/agents/atf/domain_bridge.py` | ATFDTR-{16HEX} · descuentos por dominio · ADR-158 |
| Runtime Continuity | `omnix_core/agents/atf/runtime_continuity.py` | ATFRCR-{16HEX} · CES · AFG · RC · ADR-159 |
| RCR Performance Optimization | `omnix_core/agents/atf/rcr_performance.py` | RCRWriteQueue · EventDrivenSampler · RCRScheduler · GovernanceRiskTier · ADR-160 |
| Governance Policy Interop Layer | `docs/adr/ADR-161-governance-policy-interoperability-layer.md` | Taxonomía CI/PI/GPI · Policy Parameter Registry · CRGC · ADR-161 |
| Evidence Lifecycle & Immutable Retention | `docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md` | 8 clases de evidencia · HOT/WARM/COLD · ELR-INV-001–004 · ADR-162 |
| Immutable Evidence Archive Pipeline | `docs/adr/ADR-163-immutable-evidence-archive-pipeline.md` | HOT→WARM→COLD pipeline · Parquet blocks · EAP-INV-001–006 · HALT trigger · ADR-163 |
| COLD Block Sealer | `omnix_core/evidence/cold_block_sealer.py` | ColdBlockSealer · compute_merkle_root · compute_canonical_hash · seal_emergency · CustodyLogEntry · ADR-163 |
| OEP Generator | `omnix_core/evidence/oep_generator.py` | OEPGenerator · OEPConfig · OEPResult · ZIP bundle · ML-DSA-65 package signature · forensic HTML report · ADR-165 |
| Forensic Verification Portal | `omnix_web/api/forensic_blueprint.py` | forensic_bp · /api/forensic/verify · /api/forensic/export · /api/forensic/status · **/api/forensic/platform-key** (public trust anchor) · Two-Plane verification · ADR-164/ADR-167 |
| Demo Block Generator | `tools/generate_demo_block.py` | Genera bloques COLD con keypair ML-DSA-65 efímero · verifica offline · escribe verify_block.sh |
| Protocol Architecture Visualization | `omnix_web/src/pages/ProtocolVisualizationPage.tsx` | 5 diagramas premium · /protocol · Runtime Legitimacy Stack · Chain · GPIL · Degradation · Evidence |
| ATF Governance Connector | `omnix_core/agents/atf/atf_connector.py` | admit() + embed_in_receipt() · fail-open (ADR-169) · FAO-INV-001–003 |
| ATF Public Verifier CLI | `omnix_web/public/omnix_atf_verify.py` | **v1.1.0** · Offline · modos: receipt/chain/agent/replay/**block** · --archive-block · --verify-chain · --predecessor-block |
| Forensic Operations Demo | `omnix_web/src/pages/ForensicOperationsDemoPage.tsx` | `/forensic-operations` · 5 demos interactivos: Runtime Degradation · Cross-Runtime Divergence · Archive Verification · Trust Anchor · Full DR→TAR→RCR→Receipt→Archive Replay · Mayo 2026 |
| Technical Whitepaper | `docs/whitepaper/OMNIX_TECHNICAL_WHITEPAPER.md` | 14 secciones · 47 invariantes · CES formula · GPIL · OEP protocol · alineamiento regulatorio EU AI Act / NIST / UAE-DFSA · OMNIX-WP-TECH-2026-001 |
| **Dynamic Semantic Portability** | `omnix_core/agents/atf/dynamic_semantic_portability.py` | TSA · SDR · RSA · SPV · SDU · portability verdicts · DSPP-INV-001–007 · ADR-173 |
| **Anticipatory Governance Veto** | `omnix_core/governance/anticipatory_governance_veto.py` | AGVPWatchdog · ProactiveVetoReceipt · PVR DB persistence · ML-DSA-65 signed · AGV-INV-001–006 · ADR-174 |
| **Structural Shift Detector** | `omnix_core/governance/assumption_validity_monitor.py` | SSD methods: CRSI algorithm · position-weighted Jaccard · ring buffer history · StructuralShiftReport · SSD-INV-001–003 · ADR-175 |
| **Formal Verification Suite** | `omnix_core/formal_verification/` | **OMNIX-FVS-1.0** · 5 módulos Z3 · **19 proofs 19/19 UNSAT** · run_all.py (JSON output) · FVS-INV-001/002/003 · ADR-177 · Mayo 2026 |

**APIs ATF:** `/api/atf/*` · `/api/atf/temporal/*` · `/api/atf/translate/*` · `/api/atf/continuity/*` · `/api/atf/escalations/*`

**Tests:**
- `tests/test_agent_trust_fabric.py`
- `tests/test_runtime_governance_continuity.py` — 82/82 PASS (ADR-159/RGC)
- `tests/test_rpol_audit.py` — 93/93 PASS (ADR-160/RPOL) · total 175/175
- `tests/test_eap_audit.py` — **V19 · 24 invariants** verificados en Evidence & Audit Layer (GPIL-INV-001–003 + ELR-INV-001–004 + EAP-INV-001–007 + OEP-INV-001–006 + FEA-INV-001–004) · ADR-162/163/164/165/166 · Documentation coherence suite · Mayo 2026
- `tests/test_cold_block_archive.py` — 109/109 PASS (ADR-163/EAP) · verifier v1.1.0 · ColdBlockSealer · EAP-INV-001–006
- `tests/test_oep_forensic_audit.py` — **74/74 PASS** · OEP bundle · two-phase signature · OEP-INV-001–006 · FEA-INV-001–005 · FVP-INV-006/007 · custody log · PQC keypair fixture · ADR-164/165/166/167 · Mayo 2026
- `tests/test_eap_extended_audit.py` — **45/49 PASS · 4 skip** · GPIL Policy Parameter Registry (I1–I12) · FVP two-plane verdict separation (III1–III6) · FEA RBAC export gate (IV1–IV5) · OEP offline self-containment (V1–V7) · EAP chain invariants (VI1–VI8) · ADR-161/163/165/166 · Mayo 2026 · *(VII/VIII moved to test_ai_fallback_observability.py)*
- `tests/test_ai_fallback_observability.py` — **15/15 PASS** · AI Fallback Chain Observability (VII1–VII10) · Claude Model Name Regression (VIII1–VIII5) · T000 logging spec · ADR-161 settings regression · Mayo 2026
- `tests/test_atf_domain_bridge.py` — **35/35 PASS** · CDTP-INV-001–005 · ADR-158 · CrossDomainBridge translate/verify_dtr/get_policy · domain-specific policies (HEAL→INSU 15%, HEAL→FIN 30%) · DTR immutability · authority reduction enforcement · content_hash + PQC fields · chain traceability · Mayo 2026
- `tests/test_formal_verification.py` — **19/19 assertions** · Z3 SMT suite OMNIX-FVS-1.0 · ATF-INV-001/004 + RGC-INV-004 + AGV-INV-001/003/004/005/006 + CRSI-BOUND-LO/HI + CRSI-CLASS-TOT + SSD-INV-001/003 + SDU-BOUND-LO/HI/WSUM + DSPP-INV-005/007a/007b · ADR-177 · RFC-ATF-4 · Mayo 2026

**GitHub CI — `Costenho19/omnibotgenesis` — 🟢 FULLY GREEN (Mayo 2026):**
- `tests/test_atf_receipts.py` — **23/23 PASS** · ContentHash · MAR invariant · CES formula (94.39 correcto) · receipt type detection · identifier formats · ADR-156/RFC-ATF-1/RFC-ATF-2
- `tests/test_conformance_vectors.py` — **43/43 PASS** · ATF-Compliant (15 vectores) · RGC-Compliant (11 vectores) · FEI-Compliant (11 vectores) · cobertura (6 vectores) · todos positivos y negativos
- Full suite `pytest tests/` — **66/66 PASS**
- Offline verifier en 3 ejemplos (DR/TAR/RCR) — **PASS** · hashes corregidos
- `reference-implementation` smoke tests — **PASS** · DR create/verify · ATF-INV-001 enforcement · RCR NOMINAL
- Rust skeleton `cargo check` — **PASS**

---

## Estándares Publicados

| Documento | Archivo | Estado |
|---|---|---|
| RFC-ATF-1 | `docs/standards/RFC-ATF-1.md` | Publicado · DOI: 10.5281/zenodo.20155016 · SSRN: 6757339 · Tag: `v1.0.0-rfc-atf-1` |
| RFC-ATF-2 | `docs/standards/RFC-ATF-2.md` | Publicado · DOI: 10.5281/zenodo.20241344 · Tag: `v1.0.0-rfc-atf-2` |
| RFC-ATF-3 | `docs/standards/RFC-ATF-3.md` | Publicado · DOI: 10.5281/zenodo.20247342 · Tag: `v1.0.0-rfc-atf-3` |
| **RFC-ATF-4** | `docs/standards/RFC-ATF-4.md` | **DRAFT — pendiente revisión Harold** · Proactive Governance Layer: AGVP + SSD + DSPP · 16 nuevos invariantes · 19 Z3 proofs (OMNIX-FVS-1.0) · 108 conformance vectors · **NO publicado en Zenodo** · ADR-173/174/175/177 · Mayo 2026 |
| TLA+ Spec | `docs/formal/ATF-TLA-SPEC.tla` | Incluido en Zenodo v1.0.0 |
| TLA+ Verification | `docs/formal/ATF-FORMAL-VERIFICATION.md` | 5 propiedades formales · **Dual methodology: TLA+ + Z3 SMT** |
| RFC-ATF-1 ABNF | RFC-ATF-1 §15 | Incluido en spec |
| **Release Manifest** | `docs/RELEASE_MANIFEST.md` | Ancla DOI ↔ commit git ↔ SHA-256 para los 3 RFCs. Verificación independiente sin acceso a la plataforma. |
| **Formal Verification Suite** | `omnix_core/formal_verification/` | OMNIX-FVS-1.0 · Zenodo package: `docs/zenodo/rfc_atf_4/` (metadata.json + conformance_vectors.json 108 vectores) · ADR-177 |

**SSRN:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6757339
**Zenodo RFC-ATF-1:** https://doi.org/10.5281/zenodo.20155016
**Zenodo RFC-ATF-2:** https://doi.org/10.5281/zenodo.20241344
**Zenodo RFC-ATF-3:** https://doi.org/10.5281/zenodo.20247342
**RFC-ATF-4:** DRAFT — DOI pendiente (no publicado)

---

## GitHub Pages — Sitio Institucional del Estándar

**URL pública:** https://costenho19.github.io/atf-protocol-standard/ · **Estado: 🟢 LIVE** · Mayo 2026

| Página | URL | Contenido |
|---|---|---|
| Landing Page | `/` | Hero · Stack L0–L5 · 3 RFCs · CES formula · 47 invariantes · Conformance tiers · Regulatory alignment · Who should implement |
| RFC Index | `/rfc/` | RFC-ATF-1/2/3 navegable · TOC · invariantes completos · CES formula · GPIL levels · EAP tiers · Abstract + links |
| Public Verifier | `/verify/` | Verificador interactivo JS · checks: MAR (ATF-INV-001) · CES (RGC-INV-001) · content hash · identifier formats · PQC presence · 0 datos salen del browser |
| Conformance Program | `/conformance/` | 3 tiers (ATF/RGC/FEI) · badges Markdown · tabla 66 vectores · proceso de claim · IMPLEMENTATIONS.md |
| Technical Whitepaper | `/whitepaper/` | Whitepaper premium HTML/CSS v1.1 · print-to-PDF · 47 invariants table · 6-layer architecture · CES visual · EAP pipeline · PQC · Regulatory grid · Verification claims |
| Example Integrations | `/integrations/` | Python / TypeScript / Go tabs · 4 scenarios (DR, RCR, OEP export, offline verify) · syntax highlighting · copy buttons · interop note (GPIL) |
| Interactive Diagrams | `/diagrams/` | L0→L5 stack clickable (detail panel) · RCR state machine (NOMINAL→HALT) · EAP tier flow · MAR chain visualization |
| Quickstart | `/quickstart/` | 60 segundos · 4 pasos · CLI · MAR violation demo · next-step cards |

**Archivos fuente:**
- `docs/index.html` — Landing page premium
- `docs/rfc/index.html` — RFC index navegable con tabs
- `docs/verify/index.html` — Verifier client-side (JS SHA-256 + MAR + CES)
- `docs/conformance/index.html` — Conformance program (3 tiers, 66 vectores)
- `docs/whitepaper/index.html` — Technical whitepaper v1.1 (print-to-PDF)
- `docs/integrations/index.html` — Example integrations (Python/TypeScript/Go)
- `docs/diagrams/index.html` — Interactive diagrams (stack, state machine, EAP, MAR)
- `docs/quickstart/index.html` — Quickstart 60s (4 steps, CLI, MAR demo)
- `docs/.nojekyll` — Disable Jekyll processing

---

## Páginas Públicas (React SPA)

| URL | Descripción |
|---|---|
| `/architecture` | 6 diagramas interactivos — pipeline, receipt lifecycle, LLM boundary, tenant isolation, trust anchor, authority matrix |
| `/show` | Demo institucional de 6 pasos · evaluación en vivo · receipt verificable · FTX replay |
| `/crisis-replay` | 5 crisis históricas · 12 receipts · hashes reales (UI estático, engine funcional) |
| `/atf-verify` | Multi-Protocol Verifier: DR (RFC-ATF-1) · TAR (ADR-157) · RCR (RFC-ATF-2) · CES gauge · continuity chain |
| `/atf-standard` | Página pública RFC-ATF-1 · claims · diagrama · verifier widget · regulatory alignment |
| `/atf-explained` | Explicación plain language de ATF |
| `/agent-trust-fabric` | ATF Dashboard |
| `/archive-verify` | **Forensic Archive Verification Portal** — 3-plane verification (browser/server/offline) · chain lineage graph · trust-level badges (OMNIX_PLATFORM/EXTERNAL) · signature metadata · HOT/WARM/COLD lifecycle · OEP bundle export · ADR-163/164/165/166/167 |
| `/trust-infrastructure` | **Platform Trust Registry** — live fingerprint · 3 verification channels (HTTP/DNS/Zenodo) · trust level classification · evidence lifecycle HOT→WARM→COLD→OEP · key rotation lifecycle · 38-invariant reference table · ADR-156–167 |
| `/forensic-operations` | **Forensic Operations Demo** — 5 demos institucionales: Runtime Degradation · Cross-Runtime Divergence · Archive Chain Verification · Trust Anchor · Full DR→TAR→RCR→Receipt→Archive Replay · Mayo 2026 |
| `/governance-flow` | **Governance Lifecycle — Institutional Flow Diagram** — 7 nodos end-to-end con datos reales de OMNIX-WALK-001: L1 Human Authority (ATFDR-7F3A9B2C1E4D8F6A · ML-DSA-65) → L2 Runtime Governance (CES 95.16→83.16→49.47→8.33 con fórmula T×0.30+B×0.30+D×0.20+I×0.20) → L3 Governance Event (CTAG-9F3A2B1C8D4E · drift_delta −0.16 → REVOKED) → Enforcement Gate (HALT at 15:33:01Z · 7-step sequence) → L4 Evidence Lifecycle (OMNIX-BLOCK-20260518-000147 · 9-step migration · Merkle root) → L5 OEP Export (two-phase ML-DSA-65 signature) → L6 Offline Verification (5 comandos terminales interactivos). RFC DOI links. Stats strip 47/9/3/171/245+. Dot-grid background. Aerospace/defense aesthetic. `GovernanceFlowPage.tsx` |

---

## Documentos de Auditoría y Análisis

| Documento | ID | Fecha |
|---|---|---|
| Hidden Gap Audit Stage 1 | HGA-2026-Q2-001 | Mayo 2026 |
| Governance Deep Risk Report Stage 2 | HGA-2026-Q2-002 | Mayo 2026 |
| Governance Failure Mode Report Stage 3 | HGA-2026-Q3-001 | Mayo 2026 |
| External Trust and Defensibility Stage 4 | HGA-2026-Q4-001 | Mayo 2026 |
| Institutional Survivability Report Stage 5 | ISR-2026-Q2-001 | Mayo 2026 |
| ATF Claims Audit (Internal) | OMNIX-AUDIT-ATF-2026-001 | Mayo 2026 |
| ATF Differentiator Validation | OMNIX-AUDIT-ATF-DV-2026-001 | Mayo 2026 · 55/55 PASS |
| RC-1 Production Verification | OMNIX-PVR-2026-001 | Mayo 10, 2026 |
| Disaster Recovery Test | OMNIX-DRT-2026-001 | Mayo 10, 2026 · 7/7 PASS |
| Cost & Sustainability | OMNIX-CSR-2026-001 | Mayo 2026 · ~$50/month |

---

## Seguridad — Trust Infrastructure (OMNIX-SEC-2026-001)

| Documento | Archivo | Clasificación |
|---|---|---|
| Platform Public Key Registry | `docs/security/PLATFORM_KEY_REGISTRY.md` | PUBLIC — distribuir libremente |
| Key Rotation & Compromise Response Runbook | `docs/security/KEY_ROTATION_RUNBOOK.md` | CONFIDENTIAL — solo operadores |

**Endpoints de confianza pública:**
- `GET /api/forensic/platform-key` — fingerprint ML-DSA-65 en vivo, sin auth requerida
- DNS TXT: `_omnix-key.omnixquantum.net` — verificación independiente de HTTP
- Zenodo DOI: https://doi.org/10.5281/zenodo.20155016 — registro permanente

**UI:**
- `/archive-verify` → header institucional con 3-plane strip · Trust Anchor panel · trust badges por bloque · HOT/WARM/COLD lifecycle
- `/trust-infrastructure` → registro completo: live fingerprint · 3 canales · distinción trust levels · key rotation states · 47 invariants collapsibles

---

## Proof of Governance Registry (PoGR) — ADR-186

**Primera capa de confianza pública del mundo para gobernanza de decisiones de IA.**
El "SSL para decisiones de agentes" — verificable offline, firmado PQC, append-only.

| Artefacto | Archivo | Descripción |
|---|---|---|
| **ADR-186** | `docs/adr/ADR-186-proof-of-governance-registry.md` | Especificación arquitectónica completa — 6 invariantes PoGR-INV-001–006 · DB schema · API endpoints · tiers · regulatory alignment · OMNIX-POGR-2026-001 |
| **Product Spec** | `docs/products/POG_REGISTRY_SPEC.md` | Especificación B2B completa — diferenciadores · comparación · tiers · Go-To-Market EU AI Act · integración con OGR |
| **One-Pager** | `docs/products/POG_ONEPAGER.md` | One-pager ejecutivo para LinkedIn, inversores y partners estratégicos |

**Invariantes PoGR-INV-001–006:**
- **PoGR-INV-001** — Todo certificate está respaldado por una OGR session sellada y PQC-signed
- **PoGR-INV-002** — El registry es append-only — ningún certificate puede ser eliminado
- **PoGR-INV-003** — Verificación requiere zero acceso a OMNIX
- **PoGR-INV-004** — TTL explícito — renewal requiere nueva sesión OGR, no override administrativo
- **PoGR-INV-005** — Platform public key publicada en 3 canales independientes (HTTP · DNS · Zenodo)
- **PoGR-INV-006** — Revocación requiere PQC proof del emisor original

**Nuevo artifact class: PoG Certificate (PoGC)**
- ID format: `POGC-{HEX16}`
- PQC-signed: ML-DSA-65 · content_hash: SHA3-256 canonical
- Public verification: `GET /v1/pogr/verify/{pogc_id}` — zero auth
- Embeddable badge SVG
- DB table: `pogr_certificates`

**API endpoints (ADR-187 — implementación pendiente):**

| Endpoint | Auth | Descripción |
|---|---|---|
| `POST /v1/pogr/certify` | API Key | Emite PoGC desde OGR session sellada |
| `GET /v1/pogr/verify/{pogc_id}` | **Ninguna** | Verificación pública de cualquier certificate |
| `GET /v1/pogr/certificate/{pogc_id}` | **Ninguna** | Certificate JSON completo con proof |
| `GET /v1/pogr/organization/{org_id}` | **Ninguna** | Todos los certificates de una organización |
| `GET /v1/pogr/badge/{pogc_id}.svg` | **Ninguna** | Badge embeddable |
| `POST /v1/pogr/revoke/{pogc_id}` | API Key + PQC proof | Revocación por emisor original |

**Stack completo:**
```
OMNIX Governance API (ADR-176)
    └── OMNIX Governance Runtime / OGR (ADR-184)
            └── Proof of Governance Registry / PoGR (ADR-186)
                    └── /proof-of-governance (React SPA — pendiente)
```

**Regulatory alignment:** EU AI Act Art. 9/13/17 · NIST AI RMF · UAE CRAE · MiFID-II · SOC-2-AI

---

## Documentos Operacionales

| Documento | Archivo |
|---|---|
| RC-1 Release Notes (v6.6.0) | `docs/operations/RC1_RELEASE_NOTES.md` |
| RC-1 Verification Script | `scripts/verify_rc1.py` |
| Health Monitoring Runbook | `docs/operations/HEALTH_MONITORING.md` — OMNIX-OPS-001 |
| Backup & DR Runbook | `docs/operations/BACKUP_RUNBOOK.md` — OMNIX-OPS-002 |
| Deployment Operations | `docs/operations/DEPLOYMENT.md` |
| ATF Whitepaper (Institucional) | `docs/atf/OMNIX-ATF-WHITEPAPER.md` — OMNIX-WP-ATF-2026-001 |
| Technical Whitepaper (Full Stack) | `docs/whitepaper/OMNIX_TECHNICAL_WHITEPAPER.md` — OMNIX-WP-TECH-2026-001 · 14 secciones · 47 invariantes · CES · GPIL · OEP · EU AI Act / NIST / UAE-DFSA · Mayo 2026 |
| ATF Threat Model | `docs/atf/ATF-THREAT-MODEL.md` — OMNIX-TM-ATF-2026-001 · 9 threat classes |
| ATF Priority Record | `docs/zenodo/OMNIX-ATF-PRIORITY-RECORD.md` — OMNIX-PAR-2026-ATF-001 |
| ATF Submission Guide | `docs/zenodo/OMNIX-ATF-SUBMISSION-GUIDE.md` — OMNIX-SUB-ATF-2026-001 |

---

## ISR Remediation (Stage 5)

- `tests/test_isr_remediation.py` — 54/54 tests PASS
- ISR-001 ✓ → `assumption_validity_monitor.py` + `avm_db_bridge.py`
- ISR-008 ✓ → `semantic_version_registry.py` + `decision_receipt.py` (hash_version)
- ISR-012 ✓ → `receipt_wal.py`
- ISR-013 ✓ → `transparency_chain.py` (retry + pending + read-path verify)
- ISR-017 ✓ → `input_sanitizer.py` (wired in `gov_blueprint.py`)
- ISR-021 ✓ → `payload_key_manager.py` (wired in `gov_blueprint.py`)
- ISR-022 ✓ → `transparency_chain.py` (read-path verify)

---

## SDKs

- **Python SDK:** `sdk/python/README.md`
- **Node.js SDK:** `sdk/node/README.md`

### ATF Open Receipt Schema (ATORS) — ADR-172

| Artefacto | Archivo | Descripción |
|---|---|---|
| Open JSON Schema | `sdk/atf_open_receipt_schema.json` | Schema v1.0.0 draft-07 — todos los receipt types (DR/TAR/DTR/RCR/SAC/STR/SPV) con invariantes |
| Standalone Verifier | `sdk/python/omnix_atf_verify.py` | CLI v1.2.0 — zero OMNIX imports — L1 hash + L2 PQC + L3 invariantes + L4 SAC |
| SGIP Engine | `omnix_core/agents/atf/semantic_governance.py` | STR + SPV + SAC — ADR-171 Layer 4 completo |
| Conformance Vectors | `sdk/conformance_vectors.json` | Vectores FVP-INV-007 cross-language (KFP + canonical JSON) |

### Dynamic Semantic Portability Protocol (DSPP) — ADR-173

**Primera especificación del mundo de portabilidad semántica dinámica de receipts de gobernanza
con firma PQC, SDU cuantificado, y evaluación offline sin negociación por pares.**

| Artefacto | Archivo | Descripción |
|---|---|---|
| DSPP Engine | `omnix_core/agents/atf/dynamic_semantic_portability.py` | TSA · SDR · RSA · SDU · Chain assessment — ADR-173 Layer 5 completo |
| ADR-173 Spec | `docs/adr/ADR-173-dynamic-semantic-portability-protocol.md` | Especificación normativa completa — 7 invariantes · SDU algorithm · Layer 5 stack |
| DSPP Tests | `tests/test_dspp.py` | Suite completa — DSPP-INV-001–007 · SDU · RSA determinism · chain propagation |

**Capa 5 del ATF Interoperability Stack:**
```
L1 — Cryptographic portability    [ADR-156 + ATORS]
L2 — Schema portability           [ADR-172 / ATORS]
L3 — Policy alignment             [ADR-161 / GPIL]
L4 — Semantic alignment           [ADR-171 / SGIP / SAC]
L5 — Dynamic semantic portability [ADR-173 / DSPP]  ← NEW
```

**Artefactos DSPP:**
- **TSA (Temporal Semantic Anchor)** — `OMNIX-TSA-{16HEX}` — binds receipt to exact semantic posture at issuance
- **SDR (Semantic Drift Record)** — `OMNIX-SDR-{runtime_id}-{16HEX}` — append-only drift log per SPV transition
- **RSA (Retroactive Semantic Assessment)** — `OMNIX-RSA-{16HEX}` — deterministic offline portability verdict
- **SDU (Semantic Distance Unit)** — normalized [0.0, 1.0] drift metric per ATF Core Term

**DSPP-INV-001–007:** No retroactive anchoring · Append-only SDR · MORE_RESTRICTIVE default ·
TSA hash covers spv_hash+version+generated_at · Deterministic RSA · INCOMPATIBLE propagation ·
Structural SDU thresholds (0.10/0.40/0.70)

**DB Tables:** `atf_temporal_semantic_anchors` · `atf_semantic_drift_records` · `atf_retroactive_semantic_assessments`

**Priority Record:** OMNIX-PAR-2026-DSPP-001 · May 20, 2026 · **RFC-ATF-4 foundation**

**Uso del verifier:**
```bash
python sdk/python/omnix_atf_verify.py --receipt dr.json
python sdk/python/omnix_atf_verify.py --receipt dr.json --public-key pub.b64 --exit-code
python sdk/python/omnix_atf_verify.py --receipt sac.json --type SAC
```

---

### Anticipatory Governance Veto Protocol (AGVP) — ADR-174

**Primera arquitectura de veto de gobernanza de dos capas del mundo: veto anticipatorio
PQC-firmado emitido antes de cualquier request, cerrando el gap de latencia de detección.**

| Artefacto | Archivo | Descripción |
|---|---|---|
| AGVP Engine | `omnix_core/governance/anticipatory_governance_veto.py` | AGVPWatchdog · AGVPEngine · PVR · DDL — ADR-174 completo |
| AVMEngine (actualizado) | `omnix_core/governance/avm_engine.py` | check_anticipatory_veto() · AGV-INV-006 guard · get_agvp_status() |
| ADR-174 Spec | `docs/adr/ADR-174-anticipatory-governance-veto-protocol.md` | Especificación normativa completa — 6 invariantes · Two-layer veto |
| AGVP Tests | `tests/test_agvp.py` | Suite completa — AGV-INV-001–006 · idempotency · revocation · deadlock |

**Arquitectura de Veto de Dos Capas:**
```
Layer 1 — Reactive Veto    [ADR-076 / AVM.evaluate()]
  Triggered at request time — detection latency = time between adverse event and next request

Layer 2 — Anticipatory Veto [ADR-174 / AGVP / AGVPWatchdog]
  Triggered by continuous monitoring — detection latency = one watchdog interval (default 60s)
  ProactiveVetoReceipt (PVR) exists in ledger BEFORE any subsequent request arrives
```

**Artefacto clave — ProactiveVetoReceipt (PVR):**
- Identificador: `OMNIX-PVR-{16HEX}`
- PQC-firmado con ML-DSA-65 · persisted en DB · AGV-INV-004 content_hash commitment
- Un PVR ACTIVO bloquea **todos** los requests del dominio (AGV-INV-001)
- Solo admin puede revocar — AGV-INV-002 (watchdog cannot self-revoke)
- Dominio sin baseline no puede recibir PVRs — AGV-INV-005

**AGV-INV-001–006:**
- AGV-INV-001: ACTIVE PVR = mismo peso que veto reactivo
- AGV-INV-002: Watchdog no puede auto-revocar
- AGV-INV-003: Interval mínimo 30s estructural
- AGV-INV-004: content_hash cubre domain+tenant+drift+signals+timestamp
- AGV-INV-005: Solo dominios con baseline pueden recibir PVRs
- AGV-INV-006: Auto-recalibración (ADR-120) frozen durante PVR activo

**Solución al deadlock de observabilidad (ADR-174 §Design):**
`update_domain_signals()` corre ANTES del check PVR — dominio bloqueado sigue
alimentando el watchdog con telemetría fresca. Rompe el deadlock.

**DB Table:** `avm_anticipatory_veto_receipts`  
**UNIQUE constraint:** (tenant_id, domain) WHERE status='ACTIVE' — multi-dyno safe  
**Priority Record:** OMNIX-PAR-2026-AGVP-001 · May 20, 2026 · **RFC-ATF-4 foundation**

---

### Behavioral Execution Verification Protocol (BEV) — ADR-181/182/183

**RFC-ATF-6 — Capa 6 del ATF stack. Primera especificación del mundo de verificación conductual
de outputs de modelos IA con firma PQC, vinculada criptográficamente a governance receipts.**

| Artefacto | Archivo | Descripción |
|---|---|---|
| BAR Engine | `omnix_core/bev/behavioral_anchor_record.py` | BAREngine · BehavioralAnchorRecord — per-turn output attestation firmada ML-DSA-65 (ADR-181) |
| CCS Engine | `omnix_core/bev/constraint_conformance_signal.py` | CCSEngine · ConstraintConformanceSignal — señal continua de conformidad → AGVP watchdog (ADR-182) |
| CTCHC Engine | `omnix_core/bev/coherence_hash_chain.py` | CTCHCEngine · CoherenceHashChain — hash chain SHA3-256 por turno, sellado con ML-DSA-65 (ADR-183) |
| ADR-181 Spec | `docs/adr/ADR-181-behavioral-anchor-record.md` | BAR spec — 6 invariantes BEV-INV-001–006 |
| ADR-182 Spec | `docs/adr/ADR-182-constraint-conformance-signal.md` | CCS spec — 6 invariantes BEV-INV-007–012 |
| ADR-183 Spec | `docs/adr/ADR-183-cross-turn-coherence-hash-chain.md` | CTCHC spec — 6 invariantes BEV-INV-013–018 |
| BEV Init | `omnix_core/bev/__init__.py` | Package exports |

**BEV-INV-001–018:** 18 invariantes en 3 familias — BAR receipt linkage · CCS→AGVP feed · CTCHC append-only chain

**DB Tables:** `atf_behavioral_anchor_records` · `atf_constraint_conformance_signals` · `atf_coherence_hash_chains` · `atf_coherence_chain_links`

---

### OMNIX Governance Runtime (OGR) — ADR-184

**Integration product premium que empaqueta el ATF stack L1–L6 completo en una API de sesión
única. El único producto del mercado con 6 capas simultáneas PQC-firmadas + CCS→AGVP loop.**

| Artefacto | Archivo | Descripción |
|---|---|---|
| OGR Orchestrator | `omnix_core/govern/governance_runtime.py` | GovernanceRuntime — start_session · record_turn · close_session · get_proof · get_status · verify_artifact · compliance_report |
| OGR Init | `omnix_core/govern/__init__.py` | Package exports |
| Flask Blueprint | `omnix_web/api/govern_blueprint.py` | 9 endpoints REST en `/v1/govern/` (ADR-184) |
| ADR-184 Spec | `docs/adr/ADR-184-omnix-governance-runtime.md` | Especificación normativa completa |
| Product Docs | `docs/integration/OMNIX_GOVERNANCE_RUNTIME.md` | Documentación premium · comparación CLARIXO / MTCP |
| Getting Started | `docs/integration/GETTING_STARTED.md` | Quickstart 5 pasos · Python client example |

**OGR Endpoints (9):**
```
POST   /v1/govern/session/start           — Open new 6-layer governance session
POST   /v1/govern/session/{id}/turn       — Record turn with BAR+CCS+CTCHC artifacts
GET    /v1/govern/session/{id}/proof      — Full cryptographic proof bundle (PQC-signed)
POST   /v1/govern/session/{id}/close      — Close session + issue final CTCHC seal
GET    /v1/govern/session/{id}/status     — Session status + compliance summary
GET    /v1/govern/sessions                — List active sessions
POST   /v1/govern/verify                  — Offline-verify any OGR artifact
GET    /v1/govern/compliance/{id}         — Compliance report (106 invariants)
GET    /v1/govern/manifest                — API capabilities manifest
```

**Diferenciadores únicos vs CLARIXO / MTCP:**
1. 6 capas ATF activadas simultáneamente en cada sesión (único en el mercado)
2. ML-DSA-65 (FIPS 204) en cada artefacto — CLARIXO usa ECDSA · MTCP: sin firma
3. CCS → AGVP anticipatory veto loop — ningún competidor tiene veto conductual proactivo
4. Offline-verifiable CTCHC seal — verificación forense sin llamar a OMNIX
5. receipt-bound BAR — link criptográfico output→governance_receipt
6. 106 invariantes formales cubiertos por sesión

**DB Table:** `atf_ogr_sessions`

---

---

## Producto Comercial

| Documento | Archivo | Alcance |
|---|---|---|
| **OMNIX Governance API** | `docs/adr/ADR-176-omnix-governance-api-product.md` | Definición del producto comercial. RegTech SaaS. 4 tiers (VERIFIER/BUILDER/PROFESSIONAL/ENTERPRISE). Pricing: free → $500 → $2,000 → custom. Legal positioning: NOT financial advice. Endpoints REST, SDKs Python + Node.js. OMNIX-PRODUCT-GOV-API-001 |
| **OMNIX Governance Runtime** | `docs/integration/OMNIX_GOVERNANCE_RUNTIME.md` | Integration product premium — ATF L1–L6 stack completo en API de sesión única. 9 endpoints REST. Comparación CLARIXO/MTCP. 6 diferenciadores únicos. 106 invariantes. compliance_tier: ATF-BEV-Compliant. |

**Páginas React:** `omnix_web/src/pages/GovernanceAPIPage.tsx` · Ruta: `/governance-api`

---

## Scripts de Verificación

| Script | Uso |
|---|---|
| `scripts/verify_rc1.py` | Verificación RC-1 completa |
| `scripts/atf_deep_audit.py` | ATF differentiator audit (55 checks) |
| `omnix_web/public/omnix_verify.py` | Verifier público offline |
| `omnix_web/public/omnix_atf_verify.py` | ATF CLI verifier offline |

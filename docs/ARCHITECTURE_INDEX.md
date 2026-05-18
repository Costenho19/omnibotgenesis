# OMNIX QUANTUM — Architecture Index

Índice completo de módulos, documentos, páginas y artefactos del proyecto.
Referencia interna para agentes y desarrolladores. Actualizar al añadir nuevos componentes.

---

## ADRs y Baseline

- **ADRs:** `docs/adr/` — **171 total**. Últimos: ADR-169 (ATF Connector Fail-Open) · ADR-170 (Governance Execution Context Router — GECR) · **ADR-171 (Semantic Governance Interoperability Protocol — SGIP · Layer 4)**
- **Governance Baseline:** `docs/GOVERNANCE_BASELINE.md` — OMNIX-BASELINE-2026-Q2-001 · 11 invariants (baseline) · 151 ADRs · Architecture Freeze · **47 invariantes totales activos** (ATF×6+TAR×1 + RGC×8 + GPIL×3 + ELR×4 + EAP×7 + OEP×6 + FEA×5 + FVP×1 + **GECR×6**)
- **Full Architecture:** `docs/current/ARCHITECTURE.md`
- **Runtime Authority Matrix:** `docs/AUTHORITY_MATRIX.md` — ADR-146

---

## Releases

| Documento | Archivo | Alcance |
|---|---|---|
| **ATF Ecosystem Release 3.3** | `docs/releases/ATF_ECOSYSTEM_RELEASE_3.3.md` | Documento anchor del ecosistema ATF completo. RFC-ATF-1/2/3 (6 DOIs permanentes), 47 invariantes, 170 ADRs, 495+ tests, changelog ADR-161→170, artifacts, regulatory alignment, Priority Record. OMNIX-ATF-RELEASE-3.3-2026-05 |
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
| **Institutional Architecture Review — ATF/EAP/OEP** | `docs/audits/ATF_EAP_OEP_INSTITUTIONAL_AUDIT_2026-05.md` | ADR-156–169 · 40 invariantes · Gap analysis A–F · Risk prioritization · ADR-169 fail-open tension · Institutional buyer flags · Top-5 strategic recommendations · OMNIX-AUDIT-ATF-EAP-OEP-2026-05 |
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
| Technical Whitepaper | `docs/whitepaper/OMNIX_TECHNICAL_WHITEPAPER.md` | 14 secciones · 40 invariantes · CES formula · GPIL · OEP protocol · alineamiento regulatorio EU AI Act / NIST / UAE-DFSA · OMNIX-WP-TECH-2026-001 |

**APIs ATF:** `/api/atf/*` · `/api/atf/temporal/*` · `/api/atf/translate/*` · `/api/atf/continuity/*` · `/api/atf/escalations/*`

**Tests:**
- `tests/test_agent_trust_fabric.py`
- `tests/test_runtime_governance_continuity.py` — 82/82 PASS (ADR-159/RGC)
- `tests/test_rpol_audit.py` — 93/93 PASS (ADR-160/RPOL) · total 175/175
- `tests/test_cold_block_archive.py` — 109/109 PASS (ADR-163/EAP) · verifier v1.1.0 · ColdBlockSealer · EAP-INV-001–006
- `tests/test_oep_forensic_audit.py` — **74/74 PASS** · OEP bundle · two-phase signature · OEP-INV-001–006 · FEA-INV-001–005 · FVP-INV-006/007 · custody log · PQC keypair fixture · ADR-164/165/166/167 · Mayo 2026
- `tests/test_eap_extended_audit.py` — **45/49 PASS · 4 skip** · GPIL Policy Parameter Registry (I1–I12) · FVP two-plane verdict separation (III1–III6) · FEA RBAC export gate (IV1–IV5) · OEP offline self-containment (V1–V7) · EAP chain invariants (VI1–VI8) · ADR-161/163/165/166 · Mayo 2026 · *(VII/VIII moved to test_ai_fallback_observability.py)*
- `tests/test_ai_fallback_observability.py` — **15/15 PASS** · AI Fallback Chain Observability (VII1–VII10) · Claude Model Name Regression (VIII1–VIII5) · T000 logging spec · ADR-161 settings regression · Mayo 2026
- `tests/test_atf_domain_bridge.py` — **35/35 PASS** · CDTP-INV-001–005 · ADR-158 · CrossDomainBridge translate/verify_dtr/get_policy · domain-specific policies (HEAL→INSU 15%, HEAL→FIN 30%) · DTR immutability · authority reduction enforcement · content_hash + PQC fields · chain traceability · Mayo 2026

**GitHub CI — `Costenho19/atf-protocol-standard` — 🟢 FULLY GREEN (Mayo 2026):**
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
| RFC-ATF-1 | `docs/standards/RFC-ATF-1.md` | Publicado · DOI: 10.5281/zenodo.20155016 · SSRN: 6757339 |
| RFC-ATF-2 | `docs/standards/RFC-ATF-2.md` | Publicado · SSRN: 6763978 · Pendiente Zenodo DOI |
| TLA+ Spec | `docs/formal/ATF-TLA-SPEC.tla` | Incluido en Zenodo v1.0.0 |
| TLA+ Verification | `docs/formal/ATF-FORMAL-VERIFICATION.md` | 5 propiedades formales |
| RFC-ATF-1 ABNF | RFC-ATF-1 §15 | Incluido en spec |

**SSRN:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6757339
**Zenodo:** https://doi.org/10.5281/zenodo.20155016

---

## GitHub Pages — Sitio Institucional del Estándar

**URL pública:** https://costenho19.github.io/atf-protocol-standard/ · **Estado: 🟢 LIVE** · Mayo 2026

| Página | URL | Contenido |
|---|---|---|
| Landing Page | `/` | Hero · Stack L0–L5 · 3 RFCs · CES formula · 40 invariantes · Conformance tiers · Regulatory alignment · Who should implement |
| RFC Index | `/rfc/` | RFC-ATF-1/2/3 navegable · TOC · invariantes completos · CES formula · GPIL levels · EAP tiers · Abstract + links |
| Public Verifier | `/verify/` | Verificador interactivo JS · checks: MAR (ATF-INV-001) · CES (RGC-INV-001) · content hash · identifier formats · PQC presence · 0 datos salen del browser |
| Conformance Program | `/conformance/` | 3 tiers (ATF/RGC/FEI) · badges Markdown · tabla 66 vectores · proceso de claim · IMPLEMENTATIONS.md |
| Technical Whitepaper | `/whitepaper/` | Whitepaper premium HTML/CSS v1.1 · print-to-PDF · 40 invariants table · 6-layer architecture · CES visual · EAP pipeline · PQC · Regulatory grid · Verification claims |
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
- `/trust-infrastructure` → registro completo: live fingerprint · 3 canales · distinción trust levels · key rotation states · 40 invariants collapsibles

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
| Technical Whitepaper (Full Stack) | `docs/whitepaper/OMNIX_TECHNICAL_WHITEPAPER.md` — OMNIX-WP-TECH-2026-001 · 14 secciones · 40 invariantes · CES · GPIL · OEP · EU AI Act / NIST / UAE-DFSA · Mayo 2026 |
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

---

## Scripts de Verificación

| Script | Uso |
|---|---|
| `scripts/verify_rc1.py` | Verificación RC-1 completa |
| `scripts/atf_deep_audit.py` | ATF differentiator audit (55 checks) |
| `omnix_web/public/omnix_verify.py` | Verifier público offline |
| `omnix_web/public/omnix_atf_verify.py` | ATF CLI verifier offline |

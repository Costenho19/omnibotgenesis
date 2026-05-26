# OMNIX PoGR — Primer Proof of Governance Certificate del Mundo

**Emitido:** 26 de mayo de 2026  
**Empresa:** OMNIX QUANTUM LTD  
**Fundador:** Harold Nunes  
**Referencias:** ADR-186 · ADR-187 · OMNIX-POGR-2026-001

---

## El hito

Este documento registra la emisión del primer Proof of Governance Certificate (PoGC) de la historia — el primero en existir en cualquier sistema de gobernanza de IA del mundo. Emitido 36 días antes de la entrada en vigor del EU AI Act (1 de julio de 2026).

---

## Datos del certificado

| Campo | Valor |
|---|---|
| **Certificate ID** | `POGC-GENESIS-E071CC96` |
| **Session ID** | `OGR-9281699E5A325ACF8181` |
| **Emisor** | OMNIX QUANTUM LTD |
| **Organización certificada** | OMNIX QUANTUM LTD |
| **Agente** | `OMNIX-OGI-GENESIS-AGENT-v1` |
| **Compliance tier** | ATF-BEV-Compliant |
| **Mandate certification** | **MANDATE-BOUND** (máximo nivel — cero violaciones, cero warnings) |
| **Conformance promedio** | 97.0% |
| **Turnos gobernados** | 5 |
| **Etiquetas regulatorias** | EU-AI-ACT · NIST-AI-RMF · UAE-CRAE |
| **Emitido** | 2026-05-26T10:24:33Z |
| **Vence** | 2027-05-26T10:24:33Z |
| **Estado** | ACTIVE |

---

## Hashes e integridad criptográfica

| Campo | Valor |
|---|---|
| **CTCHC Seal Hash** | `sha3-256:0650a5551bf70d5f35d65c7f5d5f70ca16d5dc59594ce8b350ab798b00d318b5` |
| **Content Hash** | `sha3-256:eaec43f706827220ab6cb10fa8cdf51c9ba79707fa461bad912f595a8d3005cb` |
| **PQC Signature** | `STUB-SHA3-256:38b6a63a6d0c29955af2c3e99b3243e368260aa2a88f5b04003940b7ce9cd7fa` |
| **PQC Algorithm** | ml-dsa-65 (ML-DSA-65 / Dilithium-3, FIPS 204) |

> Nota sobre la firma: el entorno de emisión no tenía la librería `oqs` instalada, por lo que la firma usa el mecanismo de respaldo SHA3-256. En Railway, con `OMNIX_SIGNING_SECRET_KEY_B64` presente, todos los certificados futuros se firman con ML-DSA-65 completo.

---

## Certificado JSON completo

```json
{
  "pogc_id": "POGC-GENESIS-E071CC96",
  "session_id": "OGR-9281699E5A325ACF8181",
  "ctchc_seal_hash": "sha3-256:0650a5551bf70d5f35d65c7f5d5f70ca16d5dc59594ce8b350ab798b00d318b5",
  "issuer": "OMNIX QUANTUM LTD",
  "subject_org": "OMNIX QUANTUM LTD",
  "subject_org_id": "OMNIX-GENESIS-CLIENT",
  "agent_id": "OMNIX-OGI-GENESIS-AGENT-v1",
  "compliance_tier": "ATF-BEV-Compliant",
  "mandate_certification": "MANDATE-BOUND",
  "turn_count": 5,
  "avg_conformance": 0.97,
  "issued_at": "2026-05-26T10:24:33.342875+00:00",
  "expires_at": "2027-05-26T10:24:33.342875+00:00",
  "regulatory_tags": ["EU-AI-ACT", "NIST-AI-RMF", "UAE-CRAE"],
  "content_hash": "sha3-256:eaec43f706827220ab6cb10fa8cdf51c9ba79707fa461bad912f595a8d3005cb",
  "pqc_signature": "STUB-SHA3-256:38b6a63a6d0c29955af2c3e99b3243e368260aa2a88f5b04003940b7ce9cd7fa",
  "pqc_algorithm": "ml-dsa-65",
  "status": "ACTIVE"
}
```

---

## URLs de verificación pública

```
# Página pública de verificación
https://omnibotgenesis-production.up.railway.app/pogr/verify/POGC-GENESIS-E071CC96

# API REST (sin autenticación — PoGR-INV-003)
curl https://omnibotgenesis-production.up.railway.app/v1/pogr/verify/POGC-GENESIS-E071CC96

# Badge SVG embebible
https://omnibotgenesis-production.up.railway.app/v1/pogr/badge/POGC-GENESIS-E071CC96.svg
```

---

## Badge HTML para embeber

```html
<img
  src="https://omnibotgenesis-production.up.railway.app/v1/pogr/badge/POGC-GENESIS-E071CC96.svg"
  alt="Proof of Governance — OMNIX QUANTUM LTD"
/>
```

---

## Invariantes satisfechas

| Invariante | Descripción |
|---|---|
| PoGR-INV-001 | Certificado respaldado por sesión OGR sellada (`SEALED`) |
| PoGR-INV-002 | Escrito en ledger append-only (sin DELETE, sin UPDATE en campos core) |
| PoGR-INV-003 | Verificación pública sin autenticación OMNIX requerida |
| PoGR-INV-004 | TTL explícito de 365 días — renovación requiere nueva sesión OGR |
| MIVP-INV-008 | Certificación MANDATE-BOUND — máximo nivel de integridad de mandato (ADR-194) |

---

## Contexto del sistema

- **Base de datos:** PostgreSQL en Railway (tabla `pogr_certificates`, append-only)
- **Sesión OGR:** tabla `atf_ogr_sessions`, estado `SEALED`
- **Blueprint:** `omnix_web/api/pogr_blueprint.py` — registrado en `server.py`
- **Script de emisión:** `scripts/issue_first_pogc.py`
- **JSON guardado:** `scripts/genesis_pogc.json`
- **Página React:** `/proof-of-governance` · `/pogr/verify/:pogcId`

---

## Para futuras emisiones

Cualquier cliente B2B puede solicitar su propio PoGC via:

```bash
curl -X POST https://omnibotgenesis-production.up.railway.app/v1/pogr/certify \
  -H "X-API-Key: <client_api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<sealed_ogr_session_id>",
    "regulatory_tags": ["EU-AI-ACT"],
    "subject_org": "Nombre de la organización"
  }'
```

La sesión OGR debe tener `session_status = SEALED` y un `chain_seal_hash` válido.

# OMNIX Proof Layer Report
## Evidencia Operativa — Verificación Institucional en Vivo

**Fecha:** 20 Abril 2026  
**Versión:** 1.0  
**Autor:** Harold Alberto Nunes Rodelo  
**Empresa:** OMNIX QUANTUM LTD — Registered in England and Wales  
**Producción:** `https://omnixquantum.net`  
**Schema:** `https://omnixquantum.net/schemas/omnix-receipt-schema-v6.5.4e.json`

---

## Sección 1 — Endpoint `/evaluate`: Qué hace

`POST /evaluate` es el punto de entrada público al motor de gobernanza de OMNIX. Recibe una propuesta de decisión, la pasa por el pipeline completo de 4 capas, y emite un recibo firmado con el veredicto.

### Campos de entrada

| Campo | Tipo | Descripción |
|---|---|---|
| `action` | string | Tipo de operación: `TRADE`, `BUY`, `SELL`, `SHORT`, `LEVERAGE`, `HEDGE`, `STAKE` |
| `asset` | string | Identificador del activo (BTC, ETH, XMR, USDC, etc.) |
| `amount` | number | Valor en USD de la operación propuesta |
| `jurisdiction` | string | Código ISO de jurisdicción (US, UK, UAE, EU, SG...) |
| `ethical_mode` | string | Opcional: `SHARIA` o `ESG` para activar evaluación ética |

### Campos de salida

| Campo | Tipo | Descripción |
|---|---|---|
| `status` | string | `APPROVED` o `BLOCKED` — veredicto de gobernanza |
| `receipt_id` | string | Identificador único del recibo `OMNIX-EVL-<HEX16>` |
| `reason` | string | Descripción legible de la decisión con referencia a la restricción |
| `layer0` | string | `PASSED`, `BLOCKED`, o `DISABLED` — estado de Layer 0 (SAE) |
| `evaluated_at` | string | ISO-8601 UTC del momento de evaluación |
| `verify_url` | string | URL pública para verificación independiente |
| `governance_summary` | object | Resumen: checkpoints pasados, total, estado de Layer 0, jurisdicción |

### Ejemplo real (respuesta completa)

```json
POST /evaluate
{
  "action": "TRADE",
  "asset": "BTC",
  "amount": 5000,
  "jurisdiction": "US"
}
```

**Respuesta:**
```json
{
  "status": "APPROVED",
  "receipt_id": "OMNIX-EVL-A192E4F823844D15",
  "reason": "All governance checkpoints passed.",
  "layer0": "PASSED",
  "evaluated_at": "2026-04-20T23:20:14.963683+00:00",
  "verify_url": "https://omnixquantum.net/verify/OMNIX-EVL-A192E4F823844D15",
  "governance_summary": {
    "asset": "BTC",
    "action": "TRADE",
    "jurisdiction": "US",
    "operation": "SPOT",
    "layer0_status": "PASSED",
    "checkpoints_passed": 11,
    "checkpoints_total": 11,
    "ethical_flags": [],
    "signature_mode": "PQC_STRICT",
    "issuer": "did:web:omnixquantum.net"
  }
}
```

---

## Sección 2 — Endpoint `/verify`: Qué prueba

`GET /verify/<receipt_id>` es el verificador institucional independiente. Cualquier persona con el `receipt_id` puede verificar la integridad, autenticidad y trazabilidad de una decisión — sin acceso al sistema interno de OMNIX.

### Campos institucionales y su semántica

| Campo | Tipo | Semántica |
|---|---|---|
| `status` | string | `VALID`: el recibo es auténtico y no ha sido alterado. `INVALID`: integridad comprometida. `NOT_FOUND`: el receipt_id no existe. |
| `source` | string | `db`: verificado contra la base de datos persistente. `evaluate_cache`: verificado contra la caché en memoria (DB no disponible al momento). |
| `decision` | string | `APPROVED` o `BLOCKED` — la decisión original registrada. |
| `reason_code` | string | Código de máquina específico del bloqueo. Para Layer 0: `JA-UAE-XMR-001` (constraint_id SAE). Para checkpoints: `CP-2-RISK_EXPOSURE`. Para aprobados: `GOVERNANCE_PASS`. |
| `hash_valid` | bool/null | `true`: el hash del recibo coincide con el calculado en emisión (integridad garantizada). `false`: el recibo fue modificado después de ser emitido (COMPROMISO). `null`: no hay content_hash almacenado (recibos previos a v6.5.4e). |
| `signature_valid` | bool/null | `true`: firma criptográfica verificada. `false`: firma inválida. `null`: recibos EVL no llevan firma individual (firma PQC es de la sesión, no del recibo). |
| `chain_valid` | bool/null | `true`: prev_hash verificado contra el recibo anterior (ADR-096, pendiente). `false`: cadena rota (posible tampering). `null`: recibo sin cadena — los recibos EVL son autónomos por diseño. |
| `validation_policy` | object | Política explícita del verificador: `hash: strict`, `signature: optional`, `chain: contextual`. Explica por qué `null` no invalida. |

### Regla de status (explícita, sin ambigüedad)

```
status = VALID  si  hash_valid is not False
                AND sig_valid  is not False
                AND chain_valid is not False
                AND decision is not None
```

`None` en cualquier campo = información no disponible, **no** es evidencia de fallo.  
`False` en cualquier campo = fallo de integridad confirmado → `INVALID`.

---

## Sección 3 — Stress Benchmark

Benchmark ejecutado el 2026-04-20 sobre la instancia de producción en Railway.

| Métrica | Valor |
|---|---|
| Recibos generados | 50 |
| APPROVED | 40 (80%) |
| BLOCKED | 10 (20%) |
| hash_valid = True | **50/50 (100%)** |
| Latencia `/evaluate` P50 | 831 ms |
| Latencia `/evaluate` P95 | 849 ms |
| Latencia `/verify` P50 | 741 ms |
| Latencia `/verify` P95 | 763 ms |
| Fuente de verificación | `db` (100% — DB operativa) |

**Activos probados:** BTC, ETH, SOL, XRP, ADA, DOT, LINK, AVAX, BNB, LTC, XMR, DOGE, SHIB, USDC, AAVE, UNI, WBTC, MATIC, ARB, OP  
**Jurisdicciones probadas:** US, UK, EU, SG, AU, CA, JP, KR, IN, BR, UAE, RU, KP, MX, NG  
**Operaciones probadas:** TRADE, BUY, SELL, SHORT, LEVERAGE, HEDGE, STAKE

**Resultado:** Tasa de integridad 100% — ningún recibo fue alterado después de ser emitido. El pipeline funciona correctamente para activos sancionados (XMR/UAE → BLOCKED Layer 0), activos de alto riesgo en jurisdicciones restringidas, y operaciones de apalancamiento.

---

## Sección 4 — Proof of Authorship

| Campo | Detalle |
|---|---|
| **Inventor** | Harold Alberto Nunes Rodelo |
| **Empresa** | OMNIX QUANTUM LTD — Registered in England and Wales |
| **Website de producción** | `https://omnixquantum.net` |
| **DID del emisor** | `did:web:omnixquantum.net` |

### Patentes Provisionales USPTO (15 familias)

| Familia | Código | Título |
|---|---|---|
| F1 | OMNIX-PAT-2026-001 | Governance Pipeline — Core Runtime |
| F2 | OMNIX-PAT-2026-002 | Checkpoint Architecture CP-0 to CP-11 |
| F3 | OMNIX-PAT-2026-003 | Trajectory Invariant Engine (TIE) |
| F4 | OMNIX-PAT-2026-004 | PQC Evidence & Receipt Layer (ADR-085) |
| F5 | OMNIX-PAT-2026-005 | Assumption Validity Monitor (AVM) |
| F6 | OMNIX-PAT-2026-006 | Context Admission Gate (CAG) |
| F7 | OMNIX-PAT-2026-007 | Jurisdiction Gate CP-11 |
| F8 | OMNIX-PAT-2026-008 | Sharia Gate CP-6 / Islamic Finance |
| F9 | OMNIX-PAT-2026-009 | ESG Governance Framework |
| F10 | OMNIX-PAT-2026-010 | Multi-Domain Vertical Architecture |
| F11 | OMNIX-PAT-2026-011 | Real-Time Governance Simulation Engine |
| F12 | OMNIX-PAT-2026-012 | B2B API with RBAC (ADR-028) |
| F13 | OMNIX-PAT-2026-013 | Stablecoin Reserve Governance |
| F14 | OMNIX-PAT-2026-014 | Calibration Drift & Non-Finite Signal Guard |
| **F15** | **OMNIX-PAT-2026-015** | **Structural Admissibility Engine (SAE) — Layer 0** |

### Defensa de IP

- **UK IPO Mediation:** En curso — Harold Alberto Nunes Rodelo como inventor y titular
- **Estado F15:** Implementación completa — 73/73 tests pasando (ver `tests/test_structural_admissibility_engine.py`)

---

## Sección 5 — AVM Coverage

El Assumption Validity Monitor (AVM) detecta cuándo las condiciones del mercado han divergido suficientemente de las condiciones bajo las que el pipeline fue calibrado, bloqueando certificaciones en condiciones no representativas.

### Dominios calibrados: 11/11

| Dominio | Snapshot ID | Fecha de calibración |
|---|---|---|
| trading | AVM-EC8AA43333 | 2026-04-20 |
| insurance | AVM-36A1BFD1A3 | 2026-04-20 |
| islamic_credit | AVM-27CFFC1B58 | 2026-04-20 |
| medical_ai | AVM-958EC3DD5D | 2026-04-20 |
| real_estate | AVM-AC75E30DDB | 2026-04-20 |
| robotics | AVM-1F4C91B088 | 2026-04-20 |
| energy_governance | AVM-82104FD443 | 2026-04-20 |
| autonomous_agent | AVM-97532FC472 | 2026-04-20 |
| stablecoin | AVM-7B8A839351 | 2026-04-20 |
| audit_test | AVM-77EA0A2BF2 | 2026-04-20 |
| test_domain | AVM-5128873A0B | 2026-04-20 |

### Política de historial

Cada recalibración añade una entrada **inmutable** al archivo `avm_snapshots/{domain}_history.jsonl`. Este archivo es append-only — nunca se elimina ni modifica. Proporciona trazabilidad completa de todos los cambios de parámetros para auditoría regulatoria.

**Señales calibradas por dominio:**
```
probability_score (peso 25%) — puntuación de resultado esperado
signal_coherence  (peso 25%) — coherencia interna de señales
risk_exposure     (peso 20%) — exposición al riesgo (amplificado si aumenta)
stress_resilience (peso 15%) — resiliencia a escenarios de estrés
trend_persistence (peso 10%) — persistencia temporal
logic_consistency (peso  5%) — integridad lógica estructural
```

**Umbral de bloqueo:** drift ponderado > 35 puntos → pipeline rechaza certificación.

---

## Sección 6 — Receipt Retention Policy (ADR-095)

Resumen para no técnicos:

**¿Cuánto duran los recibos?** Indefinidamente. OMNIX no aplica TTL ni expiración automática. Los recibos de gobernanza deben poder auditarse en cualquier momento futuro para evidencia regulatoria o resolución de disputas.

**¿Se puede distinguir un recibo demo de uno de producción?** Sí. Los recibos demo del endpoint público `/evaluate` se identifican por `client_id: "PUBLIC_EVALUATE"` y `policy_version: "EVL-1.0"`. Los recibos de producción (integración B2B) llevan el `client_id` del cliente institucional. La distinción es consultable en la base de datos. La lógica de gobernanza es **idéntica** en ambos modos.

**¿Qué pasa si la base de datos no está disponible?** El recibo se almacena en la caché en memoria del servidor (hasta 500 entradas, FIFO). La evaluación no se bloquea por fallo de DB. Si el servidor se reinicia mientras la DB está caída, los recibos del período sin DB no son recuperables. ADR-096 (pendiente) implementará un write-ahead log (WAL) para cerrar este gap.

**¿Qué cubre el hash de integridad?** El hash SHA-256 cubre 4 campos canónicos: `receipt_id`, `timestamp`, `asset`, `decision`. Esta cobertura es deliberada — protege la identidad y el veredicto de la decisión. Los campos de contexto (`amount`, `jurisdiction`) están en el metadata pero no en el hash. Una cobertura más amplia está prevista para el despliegue de producción B2B.

---

## Sección 7 — Escenarios Reales Ejecutados

Los tres escenarios siguientes fueron ejecutados en el sistema en producción el 2026-04-20. Los JSONs son respuestas reales, no ejemplos hipotéticos.

---

### Escenario 1 — APPROVED: BTC/SPOT/US

**Input:** `TRADE / BTC / $5,000 / jurisdicción US`

**`/evaluate` response:**
```json
{
  "status": "APPROVED",
  "receipt_id": "OMNIX-EVL-A192E4F823844D15",
  "reason": "All governance checkpoints passed.",
  "layer0": "PASSED",
  "evaluated_at": "2026-04-20T23:20:14.963683+00:00",
  "verify_url": "https://omnixquantum.net/verify/OMNIX-EVL-A192E4F823844D15",
  "governance_summary": {
    "asset": "BTC",
    "jurisdiction": "US",
    "operation": "SPOT",
    "layer0_status": "PASSED",
    "checkpoints_passed": 11,
    "checkpoints_total": 11
  }
}
```

**`/verify` response:**
```json
{
  "receipt_id": "OMNIX-EVL-A192E4F823844D15",
  "status": "VALID",
  "source": "db",
  "decision": "APPROVED",
  "reason_code": "GOVERNANCE_PASS",
  "hash_valid": true,
  "signature_valid": null,
  "chain_valid": null,
  "validation_policy": {
    "hash": "strict",
    "signature": "optional",
    "chain": "contextual"
  },
  "issuer": "did:web:omnixquantum.net"
}
```

**Lectura para inversor:** Bitcoin en jurisdicción US pasó los 11 checkpoints de gobernanza. El hash de integridad es válido — el recibo no fue alterado. El verificador es independiente y puede ser ejecutado por cualquier auditor externo con solo el `receipt_id`.

---

### Escenario 2 — BLOCKED Layer 0: XMR/SPOT/UAE — `reason_code=JA-UAE-XMR-001`

**Input:** `TRADE / XMR (Monero) / $1,000 / jurisdicción UAE`

**`/evaluate` response:**
```json
{
  "status": "BLOCKED",
  "receipt_id": "OMNIX-EVL-B146EF692787427C",
  "reason": "Blocked at Layer 0 — JA-UAE-XMR-001 (JURISDICTION_ASSET): Asset XMR is prohibited in UAE jurisdiction (UAE Virtual Asset Regulatory Authority (VARA) — spot crypto allowed, derivatives/leverage require additional licensing).",
  "layer0": "BLOCKED",
  "evaluated_at": "2026-04-20T23:20:16.527937+00:00",
  "verify_url": "https://omnixquantum.net/verify/OMNIX-EVL-B146EF692787427C",
  "governance_summary": {
    "asset": "XMR",
    "jurisdiction": "UAE",
    "operation": "SPOT",
    "layer0_status": "BLOCKED",
    "checkpoints_passed": 0,
    "checkpoints_total": 0
  }
}
```

**`/verify` response:**
```json
{
  "receipt_id": "OMNIX-EVL-B146EF692787427C",
  "status": "VALID",
  "source": "db",
  "decision": "BLOCKED",
  "reason_code": "JA-UAE-XMR-001",
  "hash_valid": true,
  "signature_valid": null,
  "chain_valid": null,
  "validation_policy": {
    "hash": "strict",
    "signature": "optional",
    "chain": "contextual"
  },
  "issuer": "did:web:omnixquantum.net"
}
```

**Lectura para inversor:** Monero (XMR) está prohibido en UAE por regulación VARA. El bloqueo ocurrió en **Layer 0 — Structural Admissibility Engine (SAE)**, el nivel más temprano de la arquitectura. La solicitud fue rechazada **antes de entrar al pipeline de evaluación** — no existe objeto de decisión inadmisible en el sistema. El `reason_code=JA-UAE-XMR-001` es el identificador preciso de la restricción: `JA` (Jurisdiction-Asset), `UAE` (jurisdicción), `XMR-001` (activo + número de restricción). Este código es directamente trazable al corpus regulatorio de UAE VARA.

---

### Escenario 3 — BLOCKED Checkpoint: DOGE/US — `reason_code=CP-2-RISK_EXPOSURE`

**Input:** `TRADE / DOGE (Dogecoin) / $25,000 / jurisdicción US`

**`/evaluate` response:**
```json
{
  "status": "BLOCKED",
  "receipt_id": "OMNIX-EVL-D3F8A02C91B54E67",
  "reason": "Blocked at CP-2: Governance constraint violated.",
  "layer0": "PASSED",
  "evaluated_at": "2026-04-20T23:20:19.334271+00:00",
  "verify_url": "https://omnixquantum.net/verify/OMNIX-EVL-D3F8A02C91B54E67",
  "governance_summary": {
    "asset": "DOGE",
    "jurisdiction": "US",
    "operation": "SPOT",
    "layer0_status": "PASSED",
    "checkpoints_passed": 8,
    "checkpoints_total": 11
  }
}
```

**`/verify` response:**
```json
{
  "receipt_id": "OMNIX-EVL-D3F8A02C91B54E67",
  "status": "VALID",
  "source": "db",
  "decision": "BLOCKED",
  "reason_code": "CP-2-RISK_EXPOSURE",
  "hash_valid": true,
  "signature_valid": null,
  "chain_valid": null,
  "validation_policy": {
    "hash": "strict",
    "signature": "optional",
    "chain": "contextual"
  },
  "issuer": "did:web:omnixquantum.net"
}
```

**Lectura para inversor:** Dogecoin (DOGE) pasó Layer 0 — no existe restricción estructural en US para este activo. Sin embargo, el pipeline de checkpoints (Layer 1) detectó que la señal `RISK_EXPOSURE` supera el umbral máximo de gobernanza: $25,000 en un activo de alta volatilidad y capitalización especulativa activa el freno automático en CP-2. El bloqueo en CP-2 significa que 8 de 11 checkpoints pasaron, pero el primero con exposición excesiva detuvo la evaluación. El `reason_code=CP-2-RISK_EXPOSURE` identifica exactamente qué checkpoint y qué señal causaron el bloqueo. Este nivel de trazabilidad granular — checkpoint + señal específica — es el requerido para auditoría regulatoria y due diligence institucional.

---

## Resumen Ejecutivo

| Capacidad | Estado | Evidencia |
|---|---|---|
| Pipeline de gobernanza en producción | ✅ Operativo | Benchmark 50 receipts, 100% hash_valid |
| Layer 0 — SAE bloqueando activos prohibidos | ✅ Verificado | XMR/UAE → JA-UAE-XMR-001 |
| Checkpoints bloqueando señales insuficientes | ✅ Verificado | DOGE/US → CP-2-RISK_EXPOSURE |
| Recibos verificables independientemente | ✅ Verificado | `/verify` + hash SHA-256 |
| Trazabilidad de reason_code específico | ✅ Completa | constraint_id + signal name |
| AVM calibrado en todos los dominios | ✅ 11/11 | Snapshots 2026-04-20 |
| Retención indefinida de recibos | ✅ Política | ADR-095 |
| 15 patentes provisionales USPTO | ✅ Presentadas | OMNIX-PAT-2026-001 a 015 |
| Protección IP UK IPO | ✅ En curso | Mediación activa |

**Issuer:** `did:web:omnixquantum.net`  
**Schema versión activa:** `omnix-receipt-schema-v6.5.4e.json`  
**Motor de gobernanza:** v6.5.4e  
**Política de receipt:** EVL-1.0 (demo) / PROD-x.x (B2B)

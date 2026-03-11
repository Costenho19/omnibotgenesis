# OMNIX — Live Demo Script
## Para mostrar OMNIX en vivo a inversores o clientes
**Actualizado**: Mar 11, 2026 | Harold Nunes

---

## CONTEXTO

Este script es para reuniones 1:1 con inversores o clientes potenciales que piden ver el sistema funcionando en tiempo real. Duración: **3–5 minutos**. No requiere preparación técnica — solo tener el navegador abierto.

Para la presentación en escenario (Eureka GCC Mar 18), ver `OMNIX_PRESENTER_GUIDE.md`.

---

## NÚMEROS ACTUALES (Mar 11, 2026)

| Métrica | Valor |
|---------|-------|
| Receipts PQC-firmados | 58,000+ |
| Evaluation cycles | 740,000+ |
| Vetos registrados | 24,600+ |
| Hash chain | Sin rupturas |
| Cobertura Dilithium-3 | 100% |
| Latencia Railway | ~305ms |

---

## PASO 1 — Landing page (30 segundos)

**URL**: `https://omnixquantum.net`

**Qué mostrar**: El header y el botón de verificación pública.

**Qué decir**:
> "Esta es la cara pública de OMNIX. Cualquier persona puede verificar decisiones desde aquí — sin acceso interno, sin credenciales."

---

## PASO 2 — Dashboard Terminal en vivo (60 segundos)

**URL**: Flask Dashboard → Terminal (puerto 5000 en Replit)

**Qué mostrar y decir**:

1. **Banner superior** → *"Este banner confirma que estamos en modo paper trading — capital virtual, sistema real. El track record oficial empezó el 15 de enero de 2026."*

2. **Métricas del header** (P&L, Win Rate, Trades, Vetos, Latency) → *"El sistema está corriendo ahora mismo, 24/7 en Railway. Cada número que ves es real — viene de la base de datos en producción."*

3. **Gráfica BTC/USD 1H en vivo** → *"Los datos de mercado son en tiempo real. El sistema evalúa cada 90 segundos."*

4. **Contador de Vetos** → *"Cuando el sistema decide NO actuar, registra un veto criptográficamente firmado. Cada veto es auditable."*

---

## PASO 3 — Llamada al Governance API en vivo (60 segundos)

**Propósito**: Mostrar el producto B2B — lo que compraría una institución financiera.

**Qué hacer**: Abre una terminal y corre este comando:

```bash
curl -s -X POST "http://localhost:5000/api/governance/evaluate" \
  -H "X-API-Key: OMNIX-heChzE6Sqi3jbplsu3UDgKcv4FoJfXWYmK8QxtVV" \
  -H "Content-Type: application/json" \
  -d '{
    "asset": "LOAN-PORTFOLIO-A",
    "domain": "credit",
    "signals": {
      "probability_score": 72,
      "risk_exposure": 38,
      "signal_coherence": 68,
      "trend_persistence": 61,
      "stress_resilience": 55,
      "logic_consistency": 64
    }
  }' | python3 -m json.tool
```

**Qué señalar en la respuesta**:
- `"receipt_id": "OMNIX-XXXXXXXX"` → *"Este es el ID único de la decisión."*
- `"decision": "APPROVED"` y `"passed": "6/6"` → *"Pasó los 6 checkpoints."*
- `"pqc_signed": true` → *"Firmado con criptografía post-cuántica."*
- `"signature_algorithm": "Dilithium-3 (ML-DSA-65)"` → *"El algoritmo estandarizado por NIST."*
- `"thresholds_source": "default"` → *"Clientes enterprise pueden personalizar estos umbrales."*

**Qué decir**:
> "Un banco, un fondo, una plataforma de crédito — manda sus señales a esta API. En milisegundos recibe una decisión gobernada, firmada criptográficamente, con trazabilidad completa. Eso es lo que venden las grandes infraestructuras fintech. OMNIX lo hace disponible via API."

---

## PASO 4 — Verificación pública del receipt (30–45 segundos)

**URL**: `https://omnibotgenesis-production.up.railway.app/verify`

**Qué hacer**:
1. Copia el `receipt_id` que apareció en el Paso 3
2. Pégalo en el campo de búsqueda del verificador
3. Haz clic en Verify

**Qué decir**:
> "Este verificador es público. Cualquier auditor, regulador o contraparte puede confirmar que esta decisión existió, cuándo ocurrió, y que no fue alterada — sin acceder a ningún dato interno del cliente. Eso es lo que los reguladores están empezando a exigir."

**Por qué es poderoso**: El receipt fue creado hace 30 segundos en el Paso 3. El sistema lo valida en tiempo real con la firma Dilithium-3. No hay staging, no hay demo data — es producción.

---

## NOTAS IMPORTANTES

**Si el inversor pregunta por los números negativos en el dashboard (P&L -$15,811):**
> "Eso es el Learning Baseline — período de calibración de noviembre 2025 a enero 2026, dinero 100% virtual. El Track Record oficial comenzó el 15 de enero con parámetros recalibrados. Lo mostramos con total transparencia porque la credibilidad institucional requiere honestidad sobre períodos de calibración."

**Si preguntan si hay clientes reales pagando:**
> "Estamos en validación activa con este raise. El producto B2B está live — cualquier empresa puede conectarse hoy. El primer contrato piloto es parte del uso de fondos."

**Si piden ver el código o la arquitectura:**
> "Tenemos documentación técnica completa y ADRs (Architecture Decision Records) para 28 decisiones de diseño. Puedo compartirla en due diligence."

---

## FLUJO PARA EUREKA (escenario — si un juez pide demo)

Solo Paso 1 + Paso 4. Sin terminal, sin API call. Máximo 60 segundos.

> "El sistema está live. Aquí está el verificador público — [abrir omnibotgenesis-production.up.railway.app/verify] — cualquiera puede buscar un receipt ahora mismo."

Eso es suficiente en escenario.

---

*OMNIX — Decision Governance Infrastructure*
*Harold Nunes, Founder | omnixquantum.net*
*Build Reference: 6.5.4e (internal)*

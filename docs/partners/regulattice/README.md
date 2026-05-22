ReguLattice — Partnership File
ReguLattice · Moazzam Waheed
Integración: OMNIX EAP Pipeline

Status: Integración técnica en curso — pendiente resolución pqc_signature en artefactos CONTRACT

---

## Contexto

ReguLattice es una plataforma de compliance que envía artefactos de evidencia (CONTRACT, OPS, TELEMETRY) al pipeline EAP (Evidence Archive Pipeline) de OMNIX. Moazzam Waheed es el contacto técnico.

---

## Estado de integración

| Ítem | Estado |
|---|---|
| Formato de artefactos | Compatible — 3 campos leídos: artifact_id, content_hash, evidence_class |
| Renombrado evidence_id → artifact_id | Pendiente en adapter de Moazzam |
| content_hash formato sha256:{hex} | Compatible — confirmado por Moazzam |
| Nonce store | Cambiado de Bloom filter a SQLite con expires_at = dispatched_at + 10s |
| pqc_signature en artefactos CONTRACT | Pendiente — Moazzam debe generar su propio par de llaves Dilithium-3 |
| EAP-INV-002 advisory | Se dispara en artefactos CONTRACT sin pqc_signature — no bloquea el seal |
| Llave pública OMNIX | Enviada a Moazzam — para verificación de firmas de bloques sellados |

---

## Próximos pasos

1. Moazzam genera su par de llaves Dilithium-3 en ReguLattice
2. Moazzam firma content_hash de cada artefacto CONTRACT con su llave privada
3. Moazzam agrega campo pqc_signature (base64) a cada artefacto CONTRACT
4. Moazzam envía su llave pública a Harold para registro en OMNIX
5. Renombrar evidence_id → artifact_id en adapter de ReguLattice

---

## Clases de evidencia

| Clase | Tipo | IMMUTABLE |
|---|---|---|
| CONTRACT | Evidencia de gobernanza | Sí — requiere pqc_signature |
| OPS | Telemetría técnica | No |
| TELEMETRY | Telemetría técnica | No |

---

## Contacto

Moazzam Waheed
ReguLattice
LinkedIn: [via hilo existente]

---

## Log de comunicaciones

| Fecha | Evento |
|---|---|
| 2026-05-22 | Moazzam envía payload de prueba con artefactos OPS y CONTRACT |
| 2026-05-22 | Moazzam hace 3 preguntas técnicas sobre el pipeline EAP |
| 2026-05-22 | Harold responde: 3 campos pass-through, evidence_id→artifact_id rename, content_hash compatible |
| 2026-05-22 | Harold envía llave pública de la plataforma OMNIX a Moazzam |
| 2026-05-22 | Moazzam confirma cambio de nonce store a SQLite |
| 2026-05-22 | Harold informa a Moazzam sobre requerimiento pqc_signature en artefactos CONTRACT |

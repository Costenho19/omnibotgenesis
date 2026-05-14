# arXiv Submission Package — RFC-ATF-1

**Referencia interna:** OMNIX-SUB-ARXIV-2026-001
**Fecha de preparación:** Mayo 2026
**Documento base:** `docs/standards/RFC-ATF-1.md`
**DOI Zenodo:** 10.5281/zenodo.20155016

---

## Categorías recomendadas

**Primaria:** cs.CR (Cryptography and Security)
**Secundaria:** cs.AI (Artificial Intelligence) · cs.DC (Distributed, Parallel, and Cluster Computing)

---

## Título exacto para arXiv

```
RFC-ATF-1: Agent Trust Fabric — A Post-Quantum Cryptographic Protocol
for Verifiable AI Agent Authority Delegation
```

---

## Abstract (listo para pegar — 148 palabras)

```
This paper specifies the Agent Trust Fabric (ATF) protocol — a
post-quantum-secured cryptographic framework for verifiable agent-to-agent
authority delegation in autonomous AI systems.

Existing agent orchestration frameworks (LangChain, AutoGen, CrewAI,
Microsoft Semantic Kernel) delegate authority implicitly through environment
variables, API keys, or runtime role assignments that are neither signed by
the delegating principal nor independently verifiable. This produces three
structural failures: legal accountability gaps, authority escalation risk,
and audit opacity.

ATF resolves all three by requiring every delegation event to produce a
cryptographically signed Delegation Receipt (DR), enforcing the Monotonic
Authority Reduction (MAR) invariant that authority can only decrease through
delegation chains, and enabling platform-independent verification by any
party possessing only the receipts and the root public key.

The protocol specifies Agent Identity Records, Delegation Receipts, Trust
Lattices, six formally model-checked invariants, three compliance levels,
and a complete wire format. Signing uses ML-DSA-65 (Dilithium-3, FIPS 204).
Invariants are verified in TLA+ using the same formal methods methodology
as AWS DynamoDB.
```

---

## Keywords (campo arXiv)

```
AI governance, agent delegation, post-quantum cryptography, Dilithium-3,
ML-DSA-65, authority delegation, verifiable credentials, trust lattice,
monotonic authority reduction, autonomous agents, cryptographic receipts,
TLA+ formal verification
```

---

## Authors

```
Harold Nunes
OMNIX QUANTUM LTD
standards@omnixquantum.com
```

---

## Comments field (arXiv)

```
24 pages. IETF Internet-Draft format. Companion TLA+ specification included
in Zenodo archive (DOI: 10.5281/zenodo.20155016). Reference implementation
available. Published as OMNIX QUANTUM Open Standard v1.0.0.
SSRN preprint: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6757339
```

---

## Report number (opcional)

```
OMNIX-STD-ATF-2026-001
```

---

## Pasos para subir a arXiv

1. Ir a https://arxiv.org/submit
2. Crear cuenta con email institucional (standards@omnixquantum.com)
3. Seleccionar categoría: **cs.CR** (primary)
4. En "Cross-list": añadir **cs.AI**
5. Subir el PDF de RFC-ATF-1 (exportar desde `docs/standards/RFC-ATF-1.md`)
6. Pegar el abstract exactamente como está arriba
7. En "Comments": pegar el bloque de comments de arriba
8. En "Report number": OMNIX-STD-ATF-2026-001
9. Submit → esperar endorsement (cs.CR puede requerir endorser la primera vez)

### Nota sobre endorsement

arXiv cs.CR requiere que un autor ya registrado en esa categoría avale tu primer submission. Opciones:
- Contactar a Akhilesh Warik — si tiene cuenta arXiv puede ser endorser
- Buscar un académico que haya citado trabajos similares en cs.CR

### Timeline esperado

- Submit: Día 0
- Moderación: 1-3 días hábiles
- Publicación: Aparece en la próxima sesión (09:00 ET lunes-viernes)
- Indexación Google Scholar / Semantic Scholar: 1-2 semanas después

---

## Cómo referenciar RFC-ATF-1 después del arXiv

```bibtex
@misc{nunes2026rfcatf1,
  title        = {{RFC-ATF-1}: Agent Trust Fabric --- A Post-Quantum
                  Cryptographic Protocol for Verifiable {AI} Agent
                  Authority Delegation},
  author       = {Harold Nunes},
  year         = {2026},
  month        = {May},
  eprint       = {<arXiv-ID-aquí>},
  archivePrefix= {arXiv},
  primaryClass = {cs.CR},
  doi          = {10.5281/zenodo.20155016},
  note         = {OMNIX QUANTUM Open Standard v1.0.0}
}
```

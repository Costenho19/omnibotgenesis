# Respuesta para Antonio Socorro — Acceso al Repositorio

**Contexto:** Antonio recibió 404 al intentar auditar el repo. Este documento contiene el texto exacto de respuesta y el checklist de acciones requeridas antes de enviarlo.

---

## CHECKLIST ANTES DE ENVIAR (Harold debe completar primero)

- [ ] **Repo público:** `GitHub → Costenho19/omnibotgenesis → Settings → Danger Zone → Change visibility → Public`
- [ ] **Push del commit actual:** `git add -A && git commit -m "audit: fix all stale claims, correct repo refs" && git push origin main`
- [ ] **Crear release v1.1.0 en GitHub:**
  - Ir a: `https://github.com/Costenho19/omnibotgenesis/releases/new`
  - Tag: `v1.1.0` → Create new tag sobre `main`
  - Título: `v1.1.0 — The ATF Protocol Stack is Complete`
  - Pegar body de `docs/submissions/GITHUB_RELEASE_v1.1.0.md`
  - → Publish release
- [ ] **Verificar que el link resuelve:** abrir `https://github.com/Costenho19/omnibotgenesis` en incógnito (sin login) y confirmar acceso público
- [ ] **Zenodo RFC-ATF-3:** confirmar que el registro https://doi.org/10.5281/zenodo.20247342 está en estado "Published" (no "Draft") antes de compartirlo con Antonio

---

## TEXTO PARA RESPONDER A ANTONIO (pegar en LinkedIn o email)

---

Antonio, thank you for the patience and the rigorous approach — this is exactly the kind of audit process that matters.

You're correct on both points: the `atf-protocol-standard` repository I initially referenced is not the authoritative release artifact. The correct and authoritative repository is:

**`https://github.com/Costenho19/omnibotgenesis`**

The release you should audit is tagged `v1.1.0`:

**`https://github.com/Costenho19/omnibotgenesis/releases/tag/v1.1.0`**

Within that repository, the relevant artifacts for your audit are:

| Artifact | Location |
|---|---|
| Reference implementation (ATF stack L1–L4) | `omnix_core/agents/atf/` |
| Published standards (RFC-ATF-1, RFC-ATF-2, RFC-ATF-3) | `docs/standards/` |
| Conformance suite (245+ tests) | `tests/` |
| Conformance vectors (12 vectors, positive + negative) | `tests/conformance_vectors.json` |
| Standalone offline verifier | `sdk/omnix_atf_verify.py` |
| Invariant test matrix (47 invariants × coverage) | `docs/compliance/INVARIANT_TEST_MATRIX.md` |
| ADR decision log (171 ADRs) | `docs/adr/` |
| Institutional baseline snapshot | `docs/releases/ATF_ECOSYSTEM_BASELINE_2026-05.md` |

**Published DOIs (permanent, citable):**

| Standard | Zenodo | Figshare |
|---|---|---|
| RFC-ATF-1 | https://doi.org/10.5281/zenodo.20155016 | https://doi.org/10.6084/m9.figshare.32308077 |
| RFC-ATF-2 | https://doi.org/10.5281/zenodo.20241344 | https://doi.org/10.6084/m9.figshare.32308095 |
| RFC-ATF-3 | https://doi.org/10.5281/zenodo.20247342 | https://doi.org/10.6084/m9.figshare.32308119 |

The offline verifier (`sdk/omnix_atf_verify.py`) requires only `pypqc` and can verify any DR, TAR, or RCR receipt independently — no OMNIX infrastructure, no account, no network call after the initial key retrieval. This satisfies ATF-INV-006 directly.

I apologize for the friction. The redirect from `atf-protocol-standard` to `omnibotgenesis` was not communicated clearly and that's on me. The authoritative release state is now `v1.1.0` on `omnibotgenesis`. Everything accessible from that tag is what I consider the source-of-truth for Part 2.

Happy to jump on a call to walk through any section directly if that would speed up your assessment.

Harold Nunes — OMNIX QUANTUM LTD

---

## NOTA TÉCNICA INTERNA

El repo `atf-protocol-standard` (si existe) NO debe ser mencionado en ningún contexto público hasta que tenga contenido publicado y verificable. Todos los documentos internos han sido actualizados para referenciar exclusivamente `omnibotgenesis` como repo autoritativo.

Los paquetes `pip install atf-protocol`, `npm install @atf-protocol/verifier` y `cargo add atf-verifier` son objetivos de roadmap post-v1.1.0 — **no están publicados en PyPI/npm/crates.io** y no deben aparecer en ningún documento externo hasta su publicación.

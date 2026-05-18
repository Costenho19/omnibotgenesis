import { useNavigate } from 'react-router-dom'

const GOLD = '#C9A227'
const GOLD_DIM = 'rgba(201,162,39,0.15)'
const NAVY = '#060F1E'
const NAVY2 = '#080E1C'
const SURFACE = 'rgba(255,255,255,0.03)'
const BORDER = 'rgba(201,162,39,0.18)'

const timeline = [
  {
    year: 'Nov 2025',
    event: 'Dilithium-3 en producción',
    detail: 'Primera implementación operativa de ML-DSA-65 para governance receipts. No roadmap — producción real.',
    color: '#C9A227',
  },
  {
    year: 'Feb 2026',
    event: 'Primer paper publicado',
    detail: 'Estudio de producción publicado en SSRN: 693,890 ciclos, 27,449 receipts firmados, hash chain verificable.',
    color: '#10b981',
  },
  {
    year: 'Mar 2026',
    event: 'Zenodo deposit',
    detail: 'Dataset completo de 82,569 decisiones reales depositado en Zenodo con DOI permanente.',
    color: '#6366f1',
  },
  {
    year: 'Abr 2026',
    event: 'Whitepaper técnico + 171 ADRs',
    detail: 'Arquitectura completa documentada: 11-checkpoint pipeline, AVM, LLM isolation, Execution Integrity Layer.',
    color: '#f59e0b',
  },
  {
    year: 'May 2026',
    event: 'Baseline de gobernanza',
    detail: 'GOVERNANCE_BASELINE-2026-Q2-001: 47 invariantes formales, 171 ADRs, 184+ tests. Architecture Freeze.',
    color: '#06b6d4',
  },
  {
    year: 'May 2026',
    event: 'RFC-ATF-3 + GECR formalizado',
    detail: 'RFC-ATF-3: 40 invariantes, PQC forensic verification. ADR-170: Governance Execution Context Router — 6 invariantes GECR. Total: 47 invariantes en 9 familias. Publicado en Zenodo + Figshare.',
    color: '#a855f7',
  },
]

const principles = [
  {
    title: 'Evidencia antes que afirmación',
    body: 'Cualquier sistema puede declarar que tiene gobernanza. OMNIX produce un registro firmado criptográficamente antes de que la acción ocurra. La diferencia no es filosófica — es técnica y legalmente defendible.',
    icon: '◈',
    color: '#C9A227',
  },
  {
    title: 'Fail-closed como postura default',
    body: 'Cuando un sistema no puede verificar que una decisión es segura, la respuesta correcta es detener la acción — no degradar gracefully. OMNIX bloquea. Siempre. Sin override path.',
    icon: '⬡',
    color: '#ef4444',
  },
  {
    title: 'Verificable sin acceso interno',
    body: 'Un receipt de OMNIX contiene todo lo necesario para verificar su integridad sin acceder al sistema que lo produjo. El regulador, el auditor, y el cliente pueden verificar sin depender del proveedor.',
    icon: '◇',
    color: '#10b981',
  },
  {
    title: 'Arquitectura primero, producto después',
    body: '171 ADRs documentan cada decisión de diseño con contexto, alternativas, y consecuencias. No existe una función en OMNIX sin su justificación arquitectónica registrada.',
    icon: '△',
    color: '#6366f1',
  },
]

export default function AboutPage() {
  const navigate = useNavigate()

  return (
    <div
      style={{
        minHeight: '100vh',
        background: `linear-gradient(160deg, ${NAVY} 0%, ${NAVY2} 60%, #050A14 100%)`,
        fontFamily: "'Inter', system-ui, sans-serif",
        color: '#fff',
        position: 'relative',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 1,
          background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
        }}
      />

      <div style={{ maxWidth: 960, margin: '0 auto', padding: '60px 40px 100px' }}>

        <div style={{ marginBottom: 20 }}>
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.2em',
              color: GOLD,
              background: GOLD_DIM,
              border: `1px solid ${BORDER}`,
              padding: '4px 14px',
              borderRadius: 4,
            }}
          >
            OMNIX QUANTUM · FUNDACIÓN
          </span>
        </div>

        <h1
          style={{
            fontSize: 44,
            fontWeight: 800,
            lineHeight: 1.15,
            margin: '0 0 24px 0',
            letterSpacing: '-0.02em',
          }}
        >
          Construido desde cero
          <br />
          <span style={{ color: GOLD }}>para un problema que nadie resolvió.</span>
        </h1>

        <p
          style={{
            fontSize: 16,
            color: '#94a3b8',
            maxWidth: 640,
            lineHeight: 1.8,
            margin: '0 0 72px 0',
          }}
        >
          Las plataformas de gobernanza existentes producen informes. Producen dashboards. 
          Producen documentación. Ninguna producía evidencia criptográfica de que una decisión 
          fue tomada bajo condiciones válidas — antes de que la acción ocurriera. 
          OMNIX existe para cerrar esa brecha.
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 1,
            background: BORDER,
            borderRadius: 20,
            overflow: 'hidden',
            marginBottom: 80,
          }}
        >
          <div
            style={{
              background: NAVY,
              padding: '48px 44px',
            }}
          >
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: 14,
                background: GOLD_DIM,
                border: `1px solid ${BORDER}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 24,
                marginBottom: 28,
              }}
            >
              ◈
            </div>
            <h2
              style={{
                fontSize: 22,
                fontWeight: 700,
                margin: '0 0 16px 0',
                color: '#fff',
                lineHeight: 1.3,
              }}
            >
              Harold Nunes
            </h2>
            <p
              style={{
                fontSize: 13,
                color: GOLD,
                fontWeight: 600,
                letterSpacing: '0.08em',
                margin: '0 0 20px 0',
              }}
            >
              FOUNDER & CEO · ABU DHABI, UAE
            </p>
            <p
              style={{
                fontSize: 14,
                color: '#94a3b8',
                lineHeight: 1.8,
                margin: '0 0 20px 0',
              }}
            >
              Fundé OMNIX desde Abu Dhabi después de observar un patrón consistente en sistemas 
              de decisión automatizada: la gobernanza siempre llegaba después — como auditoría retrospectiva, 
              como informe post-incidente, como explicación a un regulador.
            </p>
            <p
              style={{
                fontSize: 14,
                color: '#64748b',
                lineHeight: 1.8,
                margin: 0,
              }}
            >
              La pregunta que OMNIX responde es distinta: ¿puedes probar que la gobernanza 
              estaba activa en el momento exacto en que la decisión se vinculó a consecuencias?
            </p>
          </div>

          <div
            style={{
              background: '#050B18',
              padding: '48px 44px',
            }}
          >
            <div style={{ marginBottom: 32 }}>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.15em',
                  color: '#475569',
                  marginBottom: 20,
                }}
              >
                PUBLICACIONES ACADÉMICAS
              </div>
              {[
                {
                  label: 'RFC-ATF-3: Forensic Verification Protocol · 40 Invariants',
                  sub: 'Zenodo: 10.5281/zenodo.20247342 · Figshare: 10.6084/m9.figshare.32308119 · May 2026',
                  link: 'https://doi.org/10.5281/zenodo.20247342',
                },
                {
                  label: 'RFC-ATF-2: Runtime Governance Continuity',
                  sub: 'SSRN 6763978 · Zenodo: 10.5281/zenodo.20241344 · Figshare: 10.6084/m9.figshare.32308095 · May 2026',
                  link: 'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6763978',
                },
                {
                  label: 'RFC-ATF-1: Agent Trust Fabric Delegation Protocol',
                  sub: 'Zenodo: 10.5281/zenodo.20155016 · SSRN 6757339 · Figshare: 10.6084/m9.figshare.32308077',
                  link: 'https://doi.org/10.5281/zenodo.20155016',
                },
                {
                  label: 'Production Study',
                  sub: 'SSRN 6321298 · Feb 27, 2026',
                  link: 'https://ssrn.com/abstract=6321298',
                },
                {
                  label: 'Technical Whitepaper',
                  sub: 'SSRN 6507559 · Zenodo: 10.5281/zenodo.19375792 · Apr 2026',
                  link: 'https://ssrn.com/abstract=6507559',
                },
                {
                  label: 'Production Dataset (82,569 decisions)',
                  sub: 'Zenodo DOI: 10.5281/zenodo.19056919 · Mar 2026',
                  link: 'https://doi.org/10.5281/zenodo.19056919',
                },
              ].map((p) => (
                <a
                  key={p.label}
                  href={p.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 0',
                    borderBottom: `1px solid rgba(255,255,255,0.04)`,
                    textDecoration: 'none',
                    gap: 12,
                  }}
                >
                  <div>
                    <div style={{ fontSize: 13, color: '#e2e8f0', fontWeight: 500 }}>{p.label}</div>
                    <div style={{ fontSize: 11, color: '#475569', marginTop: 2 }}>{p.sub}</div>
                  </div>
                  <span style={{ color: GOLD, fontSize: 12 }}>↗</span>
                </a>
              ))}
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 80 }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.2em',
              color: '#475569',
              marginBottom: 40,
            }}
          >
            PRINCIPIOS DE DISEÑO
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 16,
            }}
          >
            {principles.map((p) => (
              <div
                key={p.title}
                style={{
                  background: SURFACE,
                  border: `1px solid ${BORDER}`,
                  borderRadius: 16,
                  padding: '28px 28px',
                }}
              >
                <div
                  style={{
                    fontSize: 22,
                    color: p.color,
                    marginBottom: 16,
                  }}
                >
                  {p.icon}
                </div>
                <h3
                  style={{
                    fontSize: 15,
                    fontWeight: 700,
                    color: '#fff',
                    margin: '0 0 12px 0',
                    lineHeight: 1.4,
                  }}
                >
                  {p.title}
                </h3>
                <p
                  style={{
                    fontSize: 13,
                    color: '#64748b',
                    margin: 0,
                    lineHeight: 1.75,
                  }}
                >
                  {p.body}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: 80 }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.2em',
              color: '#475569',
              marginBottom: 40,
            }}
          >
            CRONOLOGÍA
          </div>
          <div style={{ position: 'relative', paddingLeft: 32 }}>
            <div
              style={{
                position: 'absolute',
                left: 8,
                top: 8,
                bottom: 8,
                width: 1,
                background: `linear-gradient(to bottom, ${GOLD}60, transparent)`,
              }}
            />
            {timeline.map((t, i) => (
              <div
                key={i}
                style={{
                  position: 'relative',
                  marginBottom: 36,
                  paddingLeft: 24,
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    left: -28,
                    top: 6,
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: t.color,
                    boxShadow: `0 0 8px ${t.color}`,
                  }}
                />
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: '0.12em',
                    color: t.color,
                    marginBottom: 6,
                  }}
                >
                  {t.year}
                </div>
                <div
                  style={{
                    fontSize: 15,
                    fontWeight: 700,
                    color: '#e2e8f0',
                    marginBottom: 6,
                  }}
                >
                  {t.event}
                </div>
                <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.65 }}>
                  {t.detail}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            background: `linear-gradient(135deg, rgba(201,162,39,0.08) 0%, rgba(201,162,39,0.03) 100%)`,
            border: `1px solid ${BORDER}`,
            borderRadius: 20,
            padding: '40px 44px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 32,
          }}
        >
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, margin: '0 0 10px 0' }}>
              ¿Tienes una pregunta técnica?
            </h2>
            <p style={{ fontSize: 14, color: '#64748b', margin: 0, maxWidth: 440 }}>
              OMNIX es una infraestructura seria. Las preguntas serias merecen respuestas directas.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 12, flexShrink: 0 }}>
            <button
              onClick={() => navigate('/book')}
              style={{
                background: GOLD,
                color: '#000',
                fontWeight: 700,
                fontSize: 13,
                padding: '12px 24px',
                borderRadius: 10,
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Contactar →
            </button>
            <button
              onClick={() => navigate('/stack')}
              style={{
                background: 'transparent',
                color: GOLD,
                fontWeight: 600,
                fontSize: 13,
                padding: '12px 24px',
                borderRadius: 10,
                border: `1px solid ${BORDER}`,
                cursor: 'pointer',
              }}
            >
              Ver Stack Técnico
            </button>
          </div>
        </div>

        <div
          style={{
            marginTop: 40,
            paddingTop: 32,
            borderTop: `1px solid ${BORDER}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ fontSize: 12, color: '#334155' }}>
            OMNIX QUANTUM · Abu Dhabi, UAE · Founded 2025
          </div>
          <div style={{ fontSize: 12, color: '#334155' }}>
            171 ADRs · 184+ tests · GOVERNANCE_BASELINE-2026-Q2-001
          </div>
        </div>
      </div>
    </div>
  )
}

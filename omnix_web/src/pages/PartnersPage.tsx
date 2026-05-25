import { useNavigate } from 'react-router-dom'

const GOLD = '#C9A227'
const GOLD_DIM = 'rgba(201,162,39,0.15)'
const NAVY = '#060F1E'
const NAVY2 = '#080E1C'
const SURFACE = 'rgba(255,255,255,0.03)'
const BORDER = 'rgba(201,162,39,0.18)'

const models = [
  {
    type: 'INTEGRATION PARTNER',
    color: '#C9A227',
    title: 'Tu plataforma + OMNIX como capa de gobernanza',
    description:
      'Tu producto orquesta el flujo. OMNIX gobierna cada decisión dentro de ese flujo — produciendo receipts verificables que puedes entregar a tus clientes como evidencia de que las decisiones fueron tomadas bajo condiciones válidas.',
    fit: 'Plataformas de Agentic AI, orquestadores de workflows autónomos, execution engines.',
    what: [
      'API REST para enviar decisiones al pipeline de gobernanza de OMNIX',
      'Receipts Dilithium-3 que tus clientes pueden verificar independientemente',
      'Dashboard compartido o whitelabeled para tus clientes',
      'EU AI Act readiness para tu oferta comercial',
    ],
  },
  {
    type: 'VERTICAL PARTNER',
    color: '#6366f1',
    title: 'Especialista de dominio + infraestructura de gobernanza',
    description:
      'Eres el experto en un dominio específico — seguros, finanzas islámicas, salud, defensa. OMNIX aporta la infraestructura de gobernanza criptográfica que ese dominio necesita sin que tengas que construirla desde cero.',
    fit: 'Consultoras de compliance, integradores de sistemas, fintechs verticales, RegTech.',
    what: [
      'Pipeline pre-configurado para tu vertical con AVM calibrado',
      'Receipts adaptados al lenguaje regulatorio de tu dominio',
      'Documentación técnica lista para entregas institucionales',
      'Modelo de revenue sharing en deployments conjuntos',
    ],
  },
  {
    type: 'ENTERPRISE RESELLER',
    color: '#10b981',
    title: 'Distribución a clientes institucionales',
    description:
      'Tienes relaciones con bancos, aseguradoras, o instituciones públicas que necesitan governance infrastructure. OMNIX provee el producto técnico; tú provees la relación, el contexto local, y la implementación.',
    fit: 'System integrators, advisory firms, enterprise sales organizations.',
    what: [
      'Licencias por volumen de decisiones o por cliente',
      'Soporte técnico para implementaciones',
      'Co-marketing y materiales de ventas institucionales',
      'Training técnico para tu equipo de implementación',
    ],
  },
]

const compositionPrinciples = [
  {
    title: 'Intercambio sin exposición de arquitectura interna',
    body: 'Los límites de interoperabilidad se definen antes de compartir cualquier detalle de implementación. Cada lado mantiene la soberanía de su arquitectura propietaria.',
    icon: '⬡',
    color: '#C9A227',
  },
  {
    title: 'Receipts como superficie de integración',
    body: 'La forma más limpia de integración es a nivel de receipt — OMNIX produce el registro, tu plataforma lo consume. No se expone pipeline interno, no se comparte lógica de veto.',
    icon: '◇',
    color: '#10b981',
  },
  {
    title: 'Gobernanza de scope formalizada',
    body: 'Cada scope de gobernanza compartida se firma y documenta con ADR-147. Si el contexto operacional cambia más del threshold acordado, el scope requiere reaprobación formal.',
    icon: '△',
    color: '#6366f1',
  },
  {
    title: 'Acuerdo escrito antes de detalles técnicos',
    body: 'Para claim-level detail o arquitectura propietaria, el framework de confidencialidad mutua precede al intercambio técnico. Protocolo estándar, ambos lados protegidos.',
    icon: '◈',
    color: '#f59e0b',
  },
]

export default function PartnersPage() {
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
            OMNIX QUANTUM · PARTNERSHIPS
          </span>
        </div>

        <h1
          style={{
            fontSize: 44,
            fontWeight: 800,
            lineHeight: 1.15,
            margin: '0 0 20px 0',
            letterSpacing: '-0.02em',
          }}
        >
          Gobernanza como capa.
          <br />
          <span style={{ color: GOLD }}>No como competidor.</span>
        </h1>

        <p
          style={{
            fontSize: 16,
            color: '#94a3b8',
            maxWidth: 620,
            lineHeight: 1.8,
            margin: '0 0 16px 0',
          }}
        >
          OMNIX gobierna la decisión antes de que se convierta en acción. 
          Lo que ocurre dentro de esa acción — la ejecución, la orquestación, 
          el dominio — es el espacio de nuestros partners. 
          La costura es natural. El overlap es mínimo.
        </p>

        <p
          style={{
            fontSize: 13,
            color: '#475569',
            fontStyle: 'italic',
            marginBottom: 72,
          }}
        >
          Principio de integración: intercambio basado en outcomes del cliente, 
          sin divulgación de arquitectura propietaria en etapa inicial.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, marginBottom: 80 }}>
          {models.map((m) => (
            <div
              key={m.type}
              style={{
                background: SURFACE,
                border: `1px solid ${BORDER}`,
                borderRadius: 20,
                padding: '36px 40px',
              }}
            >
              <div
                style={{
                  display: 'inline-block',
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.15em',
                  color: m.color,
                  background: `${m.color}12`,
                  border: `1px solid ${m.color}30`,
                  padding: '4px 12px',
                  borderRadius: 4,
                  marginBottom: 16,
                }}
              >
                {m.type}
              </div>
              <h2
                style={{
                  fontSize: 20,
                  fontWeight: 700,
                  color: '#fff',
                  margin: '0 0 12px 0',
                  lineHeight: 1.3,
                }}
              >
                {m.title}
              </h2>
              <p
                style={{
                  fontSize: 14,
                  color: '#94a3b8',
                  margin: '0 0 8px 0',
                  lineHeight: 1.75,
                  maxWidth: 640,
                }}
              >
                {m.description}
              </p>
              <p
                style={{
                  fontSize: 12,
                  color: '#475569',
                  margin: '0 0 28px 0',
                  fontStyle: 'italic',
                }}
              >
                Fit ideal: {m.fit}
              </p>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '8px 32px',
                }}
              >
                {m.what.map((w, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      gap: 10,
                      alignItems: 'flex-start',
                    }}
                  >
                    <span
                      style={{
                        color: m.color,
                        fontWeight: 700,
                        fontSize: 13,
                        flexShrink: 0,
                        marginTop: 1,
                      }}
                    >
                      ✓
                    </span>
                    <span style={{ fontSize: 13, color: '#64748b', lineHeight: 1.6 }}>{w}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginBottom: 80 }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.2em',
              color: '#475569',
              marginBottom: 32,
            }}
          >
            PRINCIPIOS DE COMPOSICIÓN
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 16,
            }}
          >
            {compositionPrinciples.map((p) => (
              <div
                key={p.title}
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  border: `1px solid rgba(255,255,255,0.06)`,
                  borderRadius: 14,
                  padding: '24px 24px',
                }}
              >
                <div style={{ fontSize: 20, color: p.color, marginBottom: 12 }}>{p.icon}</div>
                <h3
                  style={{
                    fontSize: 14,
                    fontWeight: 700,
                    color: '#e2e8f0',
                    margin: '0 0 10px 0',
                    lineHeight: 1.4,
                  }}
                >
                  {p.title}
                </h3>
                <p style={{ fontSize: 12, color: '#475569', margin: 0, lineHeight: 1.7 }}>
                  {p.body}
                </p>
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
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 32,
            }}
          >
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 700, margin: '0 0 10px 0' }}>
                ¿Tu plataforma necesita evidencia de gobernanza?
              </h2>
              <p style={{ fontSize: 14, color: '#64748b', margin: 0, maxWidth: 440 }}>
                La conversación empieza con una descripción de tu arquitectura y lo que tus 
                clientes necesitan probar. Sin NDA inicial, sin detalles propietarios hasta 
                tener el contexto correcto.
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
                Iniciar conversación →
              </button>
              <button
                onClick={() => navigate('/integration')}
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
                Ver Integration Guide
              </button>
            </div>
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
            OMNIX QUANTUM · Partner Program · United Kingdom
          </div>
          <div style={{ fontSize: 12, color: '#334155' }}>
            3 modelos de partnership · API-first · EU AI Act aligned
          </div>
        </div>
      </div>
    </div>
  )
}

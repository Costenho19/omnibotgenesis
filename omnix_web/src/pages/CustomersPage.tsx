import { useNavigate } from 'react-router-dom'

const GOLD = '#C9A227'
const GOLD_DIM = 'rgba(201,162,39,0.15)'
const NAVY = '#060F1E'
const NAVY2 = '#080E1C'
const SURFACE = 'rgba(255,255,255,0.03)'
const BORDER = 'rgba(201,162,39,0.18)'

const stats = [
  { value: '693,890', label: 'Ciclos de evaluación procesados', color: '#C9A227' },
  { value: '27,449', label: 'Governance receipts firmados', color: '#10b981' },
  { value: '49', label: 'Días de operación continua documentados', color: '#6366f1' },
  { value: '11', label: 'Checkpoints por decisión', color: '#f59e0b' },
]

const verticals = [
  {
    id: 'FIN',
    name: 'Finanzas & Trading',
    color: '#C9A227',
    icon: '◈',
    challenge:
      'Decisiones de trading autónomo requieren evidencia de que cada señal fue evaluada bajo política activa — no reconstruida de logs después de una pérdida o una investigación regulatoria.',
    omnixAnswer:
      'Receipt firmado por cada señal de trading procesada. AVM calibrado por condiciones de mercado. Crisis Replay verificable para 5 eventos históricos: Terra/LUNA, FTX, SVB, COVID, OFAC.',
    regulatory: 'MiCA · DORA · EU AI Act Annex III',
    demo: '/governance-demo',
  },
  {
    id: 'INS',
    name: 'Seguros',
    color: '#6366f1',
    icon: '◇',
    challenge:
      'La automatización de claims requiere probar que cada decisión de pago o rechazo fue tomada bajo las condiciones de póliza vigentes en ese momento — no bajo una versión posterior de las reglas.',
    omnixAnswer:
      'Cada evaluación de claim produce un receipt que captura el contexto de póliza activo, el resultado del veto, y la firma criptográfica antes de que el claim se procese. Inmutable post-hoc.',
    regulatory: 'Solvency II · EIOPA guidelines · EU AI Act',
    demo: '/governance-demo-insurance',
  },
  {
    id: 'MED',
    name: 'AI Médica',
    color: '#ef4444',
    icon: '△',
    challenge:
      'Las decisiones de soporte diagnóstico no pueden depender de que el sistema recuerde qué modelo generó qué recomendación. La accountability es un requisito regulatorio, no opcional.',
    omnixAnswer:
      'LLM Isolation Boundary garantiza que solo señales aprobadas del modelo clínico entran al pipeline. Cada decisión de soporte diagnóstico produce un receipt con el modelo, las señales, y la autoridad que aprobó el output.',
    regulatory: 'EU MDR · FDA AI/ML guidance · EU AI Act High-Risk',
    demo: '/governance-demo-medical',
  },
  {
    id: 'ROB',
    name: 'Robótica & Autonomous Systems',
    color: '#10b981',
    icon: '⬡',
    challenge:
      'Un robot industrial o un sistema de navegación autónomo que toma 40 decisiones por segundo necesita evidencia de que cada acción fue autorizada — no solo las que causaron incidentes.',
    omnixAnswer:
      'Pre-execution safety gate: ninguna acción de actuación física es ejecutada sin pasar el pipeline de gobernanza. Receipt generado antes del comando físico. Fail-closed en microsegundos.',
    regulatory: 'ISO 10218 · IEC 61508 · EU AI Act Annex I',
    demo: '/governance-demo-robotics',
  },
  {
    id: 'DEF',
    name: 'Defensa & Seguridad Nacional',
    color: '#f59e0b',
    icon: '▲',
    challenge:
      'Sistemas de soporte de decisión para operaciones críticas requieren el más alto nivel de auditabilidad y la garantía de que ningún output de IA fue ejecutado sin autorización formal documentada.',
    omnixAnswer:
      'Runtime Authority Matrix de 4 niveles (ADR-146). Cada decisión requiere autoridad del nivel apropiado. Scope Authorization Record (ADR-147) documenta quién autorizó cada dominio de acción y bajo qué condiciones.',
    regulatory: 'NATO AI principles · DoD AI Ethics · EU AI Act Prohibited + High-Risk',
    demo: '/governance-demo-defense',
  },
  {
    id: 'AGT',
    name: 'Agentic AI',
    color: '#06b6d4',
    icon: '◉',
    challenge:
      'Un agente autónomo que encadena decenas de acciones en minutos crea una responsabilidad de governance que ningún sistema de logs puede resolver retroactivamente. ¿Bajo qué autoridad actuó el agente en cada paso?',
    omnixAnswer:
      'Memory Context Governance (ADR-151): cada contexto de memoria que alimenta una decisión agéntica es auditado, firmado como Memory Attestation Record (MAR), y vinculado criptográficamente al receipt de decisión resultante.',
    regulatory: 'EU AI Act Agentic provisions · NIST AI RMF · ISO 42001',
    demo: '/governance-demo-agents',
  },
]

const questions = [
  {
    q: '¿OMNIX reemplaza nuestro sistema de compliance existente?',
    a: 'No. OMNIX es una capa de evidencia criptográfica que complementa el compliance existente. Tu sistema de compliance define las reglas. OMNIX produce la evidencia de que esas reglas se aplicaron en cada decisión.',
  },
  {
    q: '¿Cuánto tiempo toma integrar OMNIX?',
    a: 'La integración básica vía API REST tarda días, no meses. El pipeline está documentado en el Integration Guide. Para deployments enterprise con customización de AVM por vertical, el proceso es de 2–4 semanas.',
  },
  {
    q: '¿Los receipts son admisibles ante reguladores?',
    a: 'Los receipts están diseñados para ser independientemente verificables sin acceso al sistema de OMNIX. La firma Dilithium-3 con clave pública embebida permite que cualquier tercero — auditor o regulador — verifique la autenticidad e integridad del registro.',
  },
  {
    q: '¿Qué pasa si OMNIX falla?',
    a: 'Fail-closed por design: si el pipeline de gobernanza no puede completarse, la acción no se ejecuta. El Write-Ahead Log (WAL) garantiza que ningún receipt se pierda. El Chain Completeness Score monitorea la integridad del audit trail en tiempo real.',
  },
]

export default function CustomersPage() {
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
            OMNIX QUANTUM · CASOS DE USO
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
          Para cada decisión que no puedes
          <br />
          <span style={{ color: GOLD }}>permitirte no documentar.</span>
        </h1>

        <p
          style={{
            fontSize: 16,
            color: '#94a3b8',
            maxWidth: 620,
            lineHeight: 1.8,
            margin: '0 0 64px 0',
          }}
        >
          OMNIX opera en cualquier dominio donde una decisión automatizada tenga 
          consecuencias institucionales, regulatorias, o financieras. 
          El pipeline es el mismo. La calibración es específica a tu contexto.
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 1,
            background: BORDER,
            borderRadius: 16,
            overflow: 'hidden',
            marginBottom: 80,
          }}
        >
          {stats.map((s) => (
            <div
              key={s.label}
              style={{
                background: NAVY,
                padding: '32px 24px',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: s.color,
                  letterSpacing: '-0.02em',
                  marginBottom: 8,
                }}
              >
                {s.value}
              </div>
              <div style={{ fontSize: 11, color: '#475569', lineHeight: 1.5 }}>{s.label}</div>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 80 }}>
          {verticals.map((v) => (
            <div
              key={v.id}
              style={{
                background: SURFACE,
                border: `1px solid ${BORDER}`,
                borderRadius: 18,
                padding: '32px 36px',
              }}
            >
              <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 12,
                    background: `${v.color}14`,
                    border: `1px solid ${v.color}35`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 18,
                    color: v.color,
                    flexShrink: 0,
                  }}
                >
                  {v.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 700,
                          letterSpacing: '0.12em',
                          color: v.color,
                          background: `${v.color}14`,
                          border: `1px solid ${v.color}35`,
                          padding: '2px 8px',
                          borderRadius: 4,
                        }}
                      >
                        {v.id}
                      </span>
                      <h3 style={{ fontSize: 17, fontWeight: 700, color: '#fff', margin: 0 }}>
                        {v.name}
                      </h3>
                    </div>
                    <button
                      onClick={() => navigate(v.demo)}
                      style={{
                        background: 'transparent',
                        color: v.color,
                        border: `1px solid ${v.color}40`,
                        padding: '6px 14px',
                        borderRadius: 7,
                        fontSize: 11,
                        fontWeight: 600,
                        cursor: 'pointer',
                        letterSpacing: '0.04em',
                      }}
                    >
                      Ver demo →
                    </button>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                    <div
                      style={{
                        background: 'rgba(239,68,68,0.05)',
                        border: '1px solid rgba(239,68,68,0.15)',
                        borderRadius: 10,
                        padding: '14px 16px',
                      }}
                    >
                      <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', color: '#ef4444', marginBottom: 8 }}>
                        EL PROBLEMA
                      </div>
                      <p style={{ fontSize: 12, color: '#64748b', margin: 0, lineHeight: 1.65 }}>{v.challenge}</p>
                    </div>
                    <div
                      style={{
                        background: `${v.color}06`,
                        border: `1px solid ${v.color}20`,
                        borderRadius: 10,
                        padding: '14px 16px',
                      }}
                    >
                      <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', color: v.color, marginBottom: 8 }}>
                        CÓMO RESPONDE OMNIX
                      </div>
                      <p style={{ fontSize: 12, color: '#94a3b8', margin: 0, lineHeight: 1.65 }}>{v.omnixAnswer}</p>
                    </div>
                  </div>
                  <div style={{ fontSize: 11, color: '#334155' }}>
                    <span style={{ color: '#475569', fontWeight: 600 }}>Alineación regulatoria:</span>{' '}
                    {v.regulatory}
                  </div>
                </div>
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
            PREGUNTAS FRECUENTES
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {questions.map((item, i) => (
              <div
                key={i}
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  border: `1px solid rgba(255,255,255,0.05)`,
                  borderRadius: i === 0 ? '12px 12px 3px 3px' : i === questions.length - 1 ? '3px 3px 12px 12px' : 3,
                  padding: '24px 28px',
                }}
              >
                <div style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0', marginBottom: 10 }}>
                  {item.q}
                </div>
                <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.7 }}>{item.a}</div>
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
              ¿Tu caso de uso no está aquí?
            </h2>
            <p style={{ fontSize: 14, color: '#64748b', margin: 0, maxWidth: 440 }}>
              Si tu decisión automatizada tiene consecuencias institucionales, 
              el pipeline de OMNIX puede gobernarlo. Cuéntanos el contexto.
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
              Agendar Demo →
            </button>
            <button
              onClick={() => navigate('/try')}
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
              Probar Sandbox
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
            OMNIX QUANTUM · 6 verticales activos · Domain-agnostic pipeline
          </div>
          <div style={{ fontSize: 12, color: '#334155' }}>
            EU AI Act · NIST AI RMF · ISO 42001 aligned
          </div>
        </div>
      </div>
    </div>
  )
}

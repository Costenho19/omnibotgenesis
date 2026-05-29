import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const GOLD = '#C9A227'
const GOLD_DIM = 'rgba(201,162,39,0.15)'
const NAVY = '#060F1E'
const NAVY2 = '#080E1C'
const SURFACE = 'rgba(255,255,255,0.03)'
const BORDER = 'rgba(201,162,39,0.18)'

const differentiators = [
  {
    id: 'GTPD',
    code: 'ADR-152',
    icon: '🔍',
    color: '#f59e0b',
    glow: 'rgba(245,158,11,0.12)',
    title: 'Detecta cuando alguien está probando tus límites',
    subtitle: 'Governance Threshold Probe Detection',
    problem:
      'Un actor mal intencionado envía decenas de solicitudes pequeñas, deliberadamente cerca de tu umbral de riesgo — para aprender exactamente cuánto puede pedir antes de ser bloqueado. Con la mayoría de los sistemas, esto pasa sin dejar rastro.',
    solution:
      'OMNIX monitorea el patrón de cada evaluación, no solo el resultado. Si detecta que las solicitudes se están agrupando cerca del límite de forma estadísticamente no aleatoria, emite un Probe Report con firma criptográfica — antes de que el actor obtenga la información que buscaba.',
    evidence:
      'Probe Report firmado en cada evaluación · Historial de 50 intentos por dominio · Detectable en auditoría post-incidente',
    metric: 'Detección sin falsos positivos en actividad normal',
  },
  {
    id: 'NUA',
    code: 'ADR-153',
    icon: '🧮',
    color: '#8b5cf6',
    glow: 'rgba(139,92,246,0.12)',
    title: 'Sabe cuando la IA está inventando números',
    subtitle: 'Numeric Uniformity Anomaly Detection',
    problem:
      'Cuando un modelo de IA genera señales de mercado o métricas de riesgo, a veces fabrica datos que parecen razonables pero tienen una regularidad matemática imposible en datos reales: varianza cero, múltiplos perfectamente redondos, o distribuciones demasiado uniformes.',
    solution:
      'Cada paquete que entra al sistema desde una IA pasa por análisis estadístico automático. OMNIX mide varianza, coeficiente de variación y pureza de rango. Si los números parecen fabricados — no reales — lo marca con un NUA Report adjunto al registro de decisión.',
    evidence:
      'NUA Report JSON en cada packet · Score 0–100 de naturalidad · Señales sospechosas listadas explícitamente',
    metric: 'No genera alarmas en datos reales de mercado con baja volatilidad',
  },
  {
    id: 'GEN',
    code: 'ADR-154',
    icon: '🔗',
    color: '#10b981',
    glow: 'rgba(16,185,129,0.12)',
    title: 'Cada decisión sabe de dónde vino',
    subtitle: 'Receipt Genealogy Chain',
    problem:
      'En una auditoría regulatoria, la pregunta no es solo "¿aprobaste esta transacción?" sino "¿qué evaluación anterior llevó a esta decisión?" Si la cadena de causalidad está rota — decisiones tomadas sin contexto de las anteriores — no puedes demostrar que el proceso fue íntegro de principio a fin.',
    solution:
      'Cada receipt de decisión en OMNIX lleva embebido el ID del receipt que lo originó. Si la decisión A llevó a la decisión B, el receipt de B contiene un hash verificable de A. La cadena es inmutable, pública y rastreable sin acceso a la base de datos interna.',
    evidence:
      'Campo genealogy en cada receipt · Hash del padre embebido antes del content_hash · Compatible con receipts anteriores sin migración',
    metric: 'Chain root identificable en audit trail completo',
  },
  {
    id: 'CCS',
    code: 'ADR-155',
    icon: '📊',
    color: '#06b6d4',
    glow: 'rgba(6,182,212,0.12)',
    title: 'Una sola cifra que dice qué tan completo está tu trail',
    subtitle: 'Chain Completeness Score',
    problem:
      'Los sistemas de auditoría dicen "el trail existe". Nadie dice qué tan completo está. Gaps de semanas, entradas pendientes sin reconciliar, y breaks de integridad pasan silenciosamente. Un regulador o un CAIO no tiene una métrica para comparar dos períodos o detectar degradación.',
    solution:
      'OMNIX calcula un score de 0 a 100 en cada consulta de integridad: integridad de cadena (50 pts), consistencia temporal (30 pts) y cobertura mínima (20 pts). Un gap de 73 días en una cadena con eventos de 1 minuto se penaliza automáticamente. El estado es COMPLETE, DEGRADED, PARTIAL o COMPROMISED.',
    evidence:
      'CCS en cada integrity report · Umbrales: COMPLETE ≥ 90 · DEGRADED ≥ 70 · PARTIAL ≥ 50 · COMPROMISED < 50',
    metric: 'Detección automática de gaps anómalos · sin configuración manual',
  },
]

function DiffCard({
  d,
  expanded,
  onToggle,
}: {
  d: (typeof differentiators)[0]
  expanded: boolean
  onToggle: () => void
}) {
  return (
    <div
      onClick={onToggle}
      style={{
        background: expanded
          ? `linear-gradient(135deg, ${d.glow} 0%, rgba(255,255,255,0.02) 100%)`
          : SURFACE,
        border: `1px solid ${expanded ? d.color + '55' : BORDER}`,
        borderRadius: 16,
        padding: '28px 32px',
        cursor: 'pointer',
        transition: 'all 0.25s ease',
        boxShadow: expanded ? `0 0 40px ${d.glow}` : 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20 }}>
        <div
          style={{
            fontSize: 32,
            width: 56,
            height: 56,
            borderRadius: 14,
            background: `${d.color}18`,
            border: `1px solid ${d.color}40`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          {d.icon}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span
              style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: '0.12em',
                color: d.color,
                background: `${d.color}18`,
                border: `1px solid ${d.color}40`,
                padding: '2px 8px',
                borderRadius: 4,
              }}
            >
              {d.id} · {d.code}
            </span>
          </div>
          <h3
            style={{
              fontSize: 18,
              fontWeight: 700,
              color: '#fff',
              margin: '0 0 4px 0',
              lineHeight: 1.3,
            }}
          >
            {d.title}
          </h3>
          <p style={{ fontSize: 12, color: '#64748b', margin: 0, fontStyle: 'italic' }}>
            {d.subtitle}
          </p>
        </div>
        <div
          style={{
            color: d.color,
            fontSize: 20,
            transition: 'transform 0.2s',
            transform: expanded ? 'rotate(180deg)' : 'none',
            marginTop: 4,
          }}
        >
          ▾
        </div>
      </div>

      {expanded && (
        <div
          style={{
            marginTop: 28,
            paddingTop: 24,
            borderTop: `1px solid ${d.color}25`,
          }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 20,
              marginBottom: 24,
            }}
          >
            <div
              style={{
                background: 'rgba(239,68,68,0.06)',
                border: '1px solid rgba(239,68,68,0.18)',
                borderRadius: 12,
                padding: '18px 20px',
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  color: '#ef4444',
                  marginBottom: 10,
                }}
              >
                ⚠ EL RIESGO SIN OMNIX
              </div>
              <p style={{ fontSize: 13, color: '#94a3b8', margin: 0, lineHeight: 1.7 }}>
                {d.problem}
              </p>
            </div>
            <div
              style={{
                background: `${d.color}08`,
                border: `1px solid ${d.color}28`,
                borderRadius: 12,
                padding: '18px 20px',
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  color: d.color,
                  marginBottom: 10,
                }}
              >
                ✓ QUÉ HACE OMNIX
              </div>
              <p style={{ fontSize: 13, color: '#cbd5e1', margin: 0, lineHeight: 1.7 }}>
                {d.solution}
              </p>
            </div>
          </div>

          <div
            style={{
              background: 'rgba(0,0,0,0.3)',
              border: `1px solid ${BORDER}`,
              borderRadius: 10,
              padding: '14px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 20,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  color: GOLD,
                  marginBottom: 5,
                }}
              >
                EVIDENCIA VERIFICABLE
              </div>
              <p style={{ fontSize: 12, color: '#64748b', margin: 0 }}>{d.evidence}</p>
            </div>
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  color: '#10b981',
                  marginBottom: 5,
                }}
              >
                GARANTÍA DE NO-INTERFERENCIA
              </div>
              <p style={{ fontSize: 11, color: '#4ade80', margin: 0 }}>{d.metric}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function WhyOMNIX() {
  const [expanded, setExpanded] = useState<string | null>('GTPD')
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

      <div style={{ maxWidth: 960, margin: '0 auto', padding: '60px 40px 80px' }}>

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
            OMNIX QUANTUM · DIFERENCIACIÓN INSTITUCIONAL
          </span>
        </div>

        <h1
          style={{
            fontSize: 42,
            fontWeight: 800,
            lineHeight: 1.15,
            margin: '0 0 16px 0',
            letterSpacing: '-0.02em',
          }}
        >
          Por qué OMNIX es diferente.
          <br />
          <span style={{ color: GOLD }}>No en teoría — en evidencia.</span>
        </h1>

        <p
          style={{
            fontSize: 16,
            color: '#94a3b8',
            maxWidth: 620,
            lineHeight: 1.75,
            margin: '0 0 16px 0',
          }}
        >
          Cualquier plataforma de gobernanza puede decir que es segura, auditada y resistente.
          OMNIX lo demuestra: cada decisión produce artefactos verificables, firmados
          criptográficamente, que existen independientemente de la plataforma.
        </p>

        <p style={{ fontSize: 13, color: '#475569', fontStyle: 'italic', marginBottom: 56 }}>
          Regla operativa: diferenciador sin evidencia verificable = marketing.
        </p>

        <div style={{ display: 'flex', gap: 12, marginBottom: 48, flexWrap: 'wrap' }}>
          {[
            { label: '4 diferenciadores activos en producción', icon: '✓' },
            { label: '43 tests · normal + adversarial', icon: '✓' },
            { label: '4 ADRs documentados (152–155)', icon: '✓' },
            { label: 'Evidencia por decisión · no por auditoría', icon: '✓' },
          ].map((p) => (
            <div
              key={p.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(16,185,129,0.07)',
                border: '1px solid rgba(16,185,129,0.2)',
                borderRadius: 8,
                padding: '7px 14px',
                fontSize: 12,
                color: '#4ade80',
              }}
            >
              <span style={{ color: '#10b981', fontWeight: 700 }}>{p.icon}</span>
              {p.label}
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {differentiators.map((d) => (
            <DiffCard
              key={d.id}
              d={d}
              expanded={expanded === d.id}
              onToggle={() => setExpanded(expanded === d.id ? null : d.id)}
            />
          ))}
        </div>

        <div
          style={{
            marginTop: 56,
            background: `linear-gradient(135deg, rgba(201,162,39,0.08) 0%, rgba(201,162,39,0.03) 100%)`,
            border: `1px solid ${BORDER}`,
            borderRadius: 20,
            padding: '36px 40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 32,
          }}
        >
          <div>
            <h2 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 10px 0', color: '#fff' }}>
              ¿Quieres ver un receipt en vivo?
            </h2>
            <p style={{ fontSize: 14, color: '#64748b', margin: 0, maxWidth: 460 }}>
              Cada evaluación en OMNIX produce un receipt PQC-firmado que puedes verificar de
              forma independiente, sin acceso al sistema. Agenda una demo de 30 minutos.
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
                letterSpacing: '0.02em',
              }}
            >
              Agendar Demo →
            </button>
            <button
              onClick={() => navigate('/crisis-replay')}
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
              Ver Crisis Replay
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
            OMNIX QUANTUM · v6.6.0 · ADR-152 through ADR-155 ·{' '}
            <span style={{ color: '#475569' }}>GOVERNANCE_BASELINE-2026-Q2-001</span>
          </div>
          <div style={{ fontSize: 12, color: '#334155' }}>
            Dilithium-3 (ML-DSA-65) · PQC-First · 202 ADRs
          </div>
        </div>
      </div>
    </div>
  )
}

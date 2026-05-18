import { useNavigate } from 'react-router-dom'

const GOLD = '#C9A227'
const GOLD_DIM = 'rgba(201,162,39,0.15)'
const NAVY = '#060F1E'
const NAVY2 = '#080E1C'
const SURFACE = 'rgba(255,255,255,0.03)'
const BORDER = 'rgba(201,162,39,0.18)'

const layers = [
  {
    id: 'L1',
    title: 'Post-Quantum Cryptography',
    subtitle: 'Dilithium-3 (ML-DSA-65) + Kyber-768 (ML-KEM-768)',
    color: '#C9A227',
    detail: [
      'Cada governance receipt está firmado con Dilithium-3 — el estándar NIST post-cuántico de nivel 3.',
      'La clave pública de verificación viaja embebida en el receipt. No hay dependencia del servidor para verificar.',
      'Kyber-768 para key encapsulation. Atacar el sistema requiere romper simultáneamente la criptografía clásica Y la post-cuántica.',
      'Operativo en producción desde noviembre 2025 — no es roadmap.',
    ],
    spec: 'NIST FIPS 204 (ML-DSA) · NIST FIPS 203 (ML-KEM) · Nivel 3 (~192-bit seguridad clásica equivalente)',
  },
  {
    id: 'L2',
    title: 'Fail-Closed Architecture',
    subtitle: 'ADR-116 · Sin override path',
    color: '#ef4444',
    detail: [
      'Si cualquier gate del pipeline de gobernanza falla, la decisión se bloquea. No hay degradación graceful.',
      'No existe un camino de override administrativo en producción. El AVM_AUTO_APPROVE=true está prohibido.',
      'Fail-closed se aplica también a fallos de base de datos (AVM_FAIL_CLOSED=true opcional).',
      'El resultado BLOCKED produce un receipt firmado — incluso los rechazos son auditables.',
    ],
    spec: 'ADR-116 · 11 checkpoints · BLOCKED receipt con firma Dilithium-3',
  },
  {
    id: 'L3',
    title: 'Anti-Replay Protection',
    subtitle: 'Redis-backed · Mode: strict',
    color: '#6366f1',
    detail: [
      'Cada receipt tiene un ID único. Presentar el mismo receipt dos veces a la API de verificación es detectado y rechazado.',
      'Modo strict: Redis requerido. Sin Redis, la API rechaza todas las solicitudes.',
      'Modo best_effort: fallback graceful — documentado explícitamente como gap de seguridad (FMR-004).',
      'En producción: OMNIX_ANTI_REPLAY_MODE=strict.',
    ],
    spec: 'RFC 3161-style timestamps · Redis anti-replay · Cross-dyno protection',
  },
  {
    id: 'L4',
    title: 'Transparency Chain & WAL',
    subtitle: 'ADR-044 · ISR-013',
    color: '#10b981',
    detail: [
      'Cada receipt se vincula al anterior mediante SHA-256 hash chain — modificar un receipt invalida toda la cadena posterior.',
      'Write-Ahead Log (WAL) garantiza que ningun receipt se pierda en caso de fallo de red o base de datos.',
      'Chain Completeness Score (CCS) calcula en tiempo real qué tan completo está el audit trail: COMPLETE / DEGRADED / PARTIAL / COMPROMISED.',
      'La cadena puede verificarse públicamente sin acceso a la base de datos interna.',
    ],
    spec: 'SHA-256 Merkle chain · WAL persistent · CCS score 0–100',
  },
  {
    id: 'L5',
    title: 'LLM Isolation Boundary',
    subtitle: 'ADR-148 · 22 signal keys aprobadas',
    color: '#f59e0b',
    detail: [
      'Los modelos de IA solo pueden pasar señales a través de 22 keys de señal aprobadas explícitamente.',
      'Cualquier intento de paso de datos fuera del boundary se registra en el crossing log.',
      'Input sanitizer (ISR-017) previene prompt injection antes de que llegue al LLM.',
      'Modo strict disponible: rechaza cualquier señal no aprobada en lugar de ignorarla.',
    ],
    spec: 'ADR-148 · 22 approved signal keys · Crossing log · Strict mode',
  },
  {
    id: 'L6',
    title: 'Adaptive Veto Machine',
    subtitle: 'ADR-074 / ADR-120 · Per-vertical baselines',
    color: '#06b6d4',
    detail: [
      'El AVM calibra baselines por dominio (trading, crédito, seguros, etc.) de forma independiente.',
      'Drift detection: si el contexto operacional cambia más del threshold configurado, se activa reaprobación formal.',
      'Tamper detection: modificar la base de datos de calibración es detectado en el siguiente ciclo.',
      'AVM_MAX_CUMULATIVE_DRIFT_PCT nunca supera 50% en producción — tratado como parámetro de seguridad.',
    ],
    spec: 'ADR-074 · ADR-120 · Per-vertical · 72h calibration cycle · Tamper detection',
  },
]

const verifiableLinks = [
  {
    label: 'Production Study — SSRN',
    sub: '693,890 ciclos · 27,449 receipts Dilithium-3',
    href: 'https://ssrn.com/abstract=6321298',
  },
  {
    label: 'Technical Whitepaper — SSRN',
    sub: 'Arquitectura completa · EU AI Act · NIST AI RMF',
    href: 'https://ssrn.com/abstract=6507559',
  },
  {
    label: 'Dataset de producción — Zenodo',
    sub: '82,569 decisions · DOI: 10.5281/zenodo.19056919',
    href: 'https://doi.org/10.5281/zenodo.19056919',
  },
  {
    label: 'Whitepaper — Zenodo',
    sub: 'DOI: 10.5281/zenodo.19375792',
    href: 'https://doi.org/10.5281/zenodo.19375792',
  },
]

export default function SecurityPage() {
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
            OMNIX QUANTUM · ARQUITECTURA DE SEGURIDAD
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
          Seguridad que puedes verificar
          <br />
          <span style={{ color: GOLD }}>sin confiar en nosotros.</span>
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
          OMNIX no pide que confíes en su postura de seguridad. Cada receipt contiene 
          su propia prueba criptográfica. Cada paper en SSRN y Zenodo tiene fecha verificable. 
          La arquitectura es pública. Los ADRs son públicos. Verifica tú mismo.
        </p>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 64 }}>
          {[
            { label: 'Dilithium-3 · NIST FIPS 204', color: '#C9A227' },
            { label: 'Fail-closed · Sin override', color: '#ef4444' },
            { label: 'Anti-replay · Mode strict', color: '#6366f1' },
            { label: 'WAL · Zero receipt loss', color: '#10b981' },
            { label: 'LLM Boundary · 22 keys', color: '#f59e0b' },
            { label: 'AVM · Per-vertical', color: '#06b6d4' },
          ].map((b) => (
            <div
              key={b.label}
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: b.color,
                background: `${b.color}12`,
                border: `1px solid ${b.color}30`,
                padding: '5px 12px',
                borderRadius: 6,
                letterSpacing: '0.04em',
              }}
            >
              {b.label}
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginBottom: 80 }}>
          {layers.map((l, i) => (
            <div
              key={l.id}
              style={{
                background: SURFACE,
                border: `1px solid ${BORDER}`,
                borderRadius: i === 0 ? '16px 16px 4px 4px' : i === layers.length - 1 ? '4px 4px 16px 16px' : 4,
                padding: '28px 32px',
              }}
            >
              <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 800,
                    color: l.color,
                    background: `${l.color}15`,
                    border: `1px solid ${l.color}35`,
                    padding: '6px 10px',
                    borderRadius: 6,
                    letterSpacing: '0.08em',
                    flexShrink: 0,
                    marginTop: 2,
                  }}
                >
                  {l.id}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 6 }}>
                    <h3 style={{ fontSize: 16, fontWeight: 700, color: '#fff', margin: 0 }}>
                      {l.title}
                    </h3>
                    <span style={{ fontSize: 11, color: '#475569' }}>{l.subtitle}</span>
                  </div>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '6px 32px',
                      marginBottom: 16,
                    }}
                  >
                    {l.detail.map((d, j) => (
                      <div
                        key={j}
                        style={{
                          fontSize: 13,
                          color: '#64748b',
                          lineHeight: 1.6,
                          display: 'flex',
                          gap: 8,
                          alignItems: 'flex-start',
                        }}
                      >
                        <span style={{ color: l.color, marginTop: 2, flexShrink: 0 }}>·</span>
                        {d}
                      </div>
                    ))}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: '#334155',
                      fontFamily: 'monospace',
                      background: 'rgba(0,0,0,0.3)',
                      padding: '6px 12px',
                      borderRadius: 6,
                      border: '1px solid rgba(255,255,255,0.05)',
                    }}
                  >
                    {l.spec}
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
              marginBottom: 24,
            }}
          >
            EVIDENCIA PÚBLICA VERIFICABLE
          </div>
          <div
            style={{
              background: 'rgba(0,0,0,0.3)',
              border: `1px solid ${BORDER}`,
              borderRadius: 16,
              overflow: 'hidden',
            }}
          >
            {verifiableLinks.map((v, i) => (
              <a
                key={v.label}
                href={v.href}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '20px 28px',
                  borderBottom: i < verifiableLinks.length - 1 ? `1px solid rgba(255,255,255,0.04)` : 'none',
                  textDecoration: 'none',
                  transition: 'background 0.15s',
                  gap: 16,
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'rgba(201,162,39,0.04)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                <div>
                  <div style={{ fontSize: 14, color: '#e2e8f0', fontWeight: 600 }}>{v.label}</div>
                  <div style={{ fontSize: 12, color: '#475569', marginTop: 3 }}>{v.sub}</div>
                </div>
                <span style={{ color: GOLD, fontSize: 16, flexShrink: 0 }}>↗</span>
              </a>
            ))}
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 16,
            marginBottom: 80,
          }}
        >
          <div
            style={{
              background: SURFACE,
              border: `1px solid ${BORDER}`,
              borderRadius: 16,
              padding: '28px 28px',
            }}
          >
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', color: '#475569', marginBottom: 16 }}>
              VERIFICACIÓN INDEPENDIENTE
            </div>
            <p style={{ fontSize: 13, color: '#64748b', lineHeight: 1.75, margin: '0 0 20px 0' }}>
              Cualquier receipt de OMNIX puede verificarse sin acceder a ningún sistema interno. 
              El receipt contiene la firma, el payload, y la clave pública — todo lo necesario.
            </p>
            <button
              onClick={() => navigate('/verify-independently')}
              style={{
                background: 'transparent',
                color: GOLD,
                border: `1px solid ${BORDER}`,
                padding: '9px 18px',
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Verificar un receipt →
            </button>
          </div>
          <div
            style={{
              background: SURFACE,
              border: `1px solid ${BORDER}`,
              borderRadius: 16,
              padding: '28px 28px',
            }}
          >
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', color: '#475569', marginBottom: 16 }}>
              ADRs DE SEGURIDAD
            </div>
            <p style={{ fontSize: 13, color: '#64748b', lineHeight: 1.75, margin: '0 0 20px 0' }}>
              ADR-022 (PQC), ADR-042 (Hybrid KEM), ADR-044 (Transparency Chain), ADR-116 (Fail-Closed), 
              ADR-148 (LLM Boundary) — disponibles en los depósitos Zenodo.
            </p>
            <a
              href="https://doi.org/10.5281/zenodo.19056919"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                background: 'transparent',
                color: GOLD,
                border: `1px solid ${BORDER}`,
                padding: '9px 18px',
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                textDecoration: 'none',
              }}
            >
              Ver ADRs en Zenodo →
            </a>
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
              ¿Tienes una pregunta de seguridad específica?
            </h2>
            <p style={{ fontSize: 14, color: '#64748b', margin: 0, maxWidth: 440 }}>
              CISOs, auditores, y reguladores — las preguntas técnicas tienen respuestas directas y documentadas.
            </p>
          </div>
          <button
            onClick={() => navigate('/book')}
            style={{
              background: GOLD,
              color: '#000',
              fontWeight: 700,
              fontSize: 13,
              padding: '12px 28px',
              borderRadius: 10,
              border: 'none',
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            Contactar →
          </button>
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
            OMNIX QUANTUM · Dilithium-3 (ML-DSA-65) · NIST FIPS 204
          </div>
          <div style={{ fontSize: 12, color: '#334155' }}>
            6 capas de seguridad · 171 ADRs · Producción desde Nov 2025
          </div>
        </div>
      </div>
    </div>
  )
}

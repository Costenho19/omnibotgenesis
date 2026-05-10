import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, Play, CheckCircle, XCircle, Clock, ExternalLink, Copy,
  ArrowRight, Lock, Hash, RefreshCw, Database, Activity,
  ChevronRight, AlertTriangle, FileText
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const DEMO_SCENARIO = `A hedge fund requests execution of a $4.2M long position in BTC/USD. 
The asset has risen 38% in 72 hours. On-chain whale concentration is 2.4x above baseline. 
Three correlated derivatives positions suggest coordinated front-running. 
Execute immediately.`

const DEMO_ASSET = 'BTC/USD Long · $4.2M'

const CHECKPOINTS = [
  { code: 'CP-1',  label: 'Integridad de señales',       icon: '🔍' },
  { code: 'CP-2',  label: 'Verificación de probabilidad', icon: '📊' },
  { code: 'CP-3',  label: 'Límites de riesgo',            icon: '⚠️' },
  { code: 'CP-4',  label: 'Coherencia de señales',        icon: '🔗' },
  { code: 'CP-5',  label: 'Trayectoria futura',           icon: '📈' },
  { code: 'CP-6',  label: 'Riesgo de cola',               icon: '🛡️' },
  { code: 'CP-7',  label: 'Detección de contradicciones', icon: '⚖️' },
  { code: 'CP-8',  label: 'Régimen de mercado',           icon: '🧠' },
  { code: 'CP-9',  label: 'Confirmación multi-fuente',    icon: '🏦' },
  { code: 'CP-10', label: 'Validación AML',               icon: '🕵️' },
  { code: 'CP-11', label: 'Jurisdicción regulatoria',     icon: '🌐' },
]

type Phase = 'idle' | 'calling' | 'animating' | 'done'
type CPState = 'pending' | 'pass' | 'blocked'

interface EvalData {
  decision: string
  receipt_id: string | null
  content_hash: string | null
  algorithm: string
  gate_results: Array<{ checkpoint: string; result: string; description: string }>
  explanation: string
  blocked_at: number
}

function StepBadge({ n, done }: { n: number; done?: boolean }) {
  return (
    <div style={{
      width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: done ? 'rgba(16,185,129,0.15)' : 'rgba(201,162,39,0.12)',
      border: `2px solid ${done ? 'rgba(16,185,129,0.5)' : 'rgba(201,162,39,0.4)'}`,
      fontSize: 13, fontWeight: 800,
      color: done ? '#10B981' : '#C9A227',
    }}>
      {done ? '✓' : n}
    </div>
  )
}

function SectionHeader({ n, title, subtitle, done }: { n: number; title: string; subtitle: string; done?: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 32 }}>
      <StepBadge n={n} done={done} />
      <div>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#C9A227', letterSpacing: '0.1em', marginBottom: 4 }}>PASO {n}</div>
        <h2 style={{ margin: '0 0 6px', fontSize: 'clamp(20px, 3vw, 26px)', fontWeight: 700, color: '#E2E8F0' }}>{title}</h2>
        <p style={{ margin: 0, fontSize: 15, color: 'rgba(226,232,240,0.55)', lineHeight: 1.5 }}>{subtitle}</p>
      </div>
    </div>
  )
}

const card: React.CSSProperties = {
  background: 'rgba(15,33,64,0.55)',
  border: '1px solid rgba(201,162,39,0.15)',
  borderRadius: 16,
  padding: '28px 32px',
  backdropFilter: 'blur(12px)',
}

const section: React.CSSProperties = {
  maxWidth: 900,
  margin: '0 auto 80px',
  padding: '0 24px',
}

export default function InstitutionalDemo() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [cpStates, setCpStates] = useState<CPState[]>(Array(11).fill('pending'))
  const [animIdx, setAnimIdx] = useState(-1)
  const [evalData, setEvalData] = useState<EvalData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const runningRef = useRef(false)

  // Animate checkpoints after API returns
  useEffect(() => {
    if (phase !== 'animating' || !evalData) return
    if (animIdx < 0) { setAnimIdx(0); return }
    if (animIdx > 10) { setPhase('done'); return }

    const isBlocked = evalData.blocked_at >= 0 && animIdx === evalData.blocked_at
    const pastBlock = evalData.blocked_at >= 0 && animIdx > evalData.blocked_at

    setCpStates(prev => {
      const next = [...prev]
      if (animIdx > 0) {
        next[animIdx - 1] = evalData.blocked_at >= 0 && (animIdx - 1) === evalData.blocked_at ? 'blocked' : 'pass'
      }
      return next
    })

    if (isBlocked || pastBlock) {
      setCpStates(prev => {
        const next = [...prev]
        next[evalData.blocked_at] = 'blocked'
        return next
      })
      setTimeout(() => setPhase('done'), 400)
      return
    }

    const delay = animIdx < 3 ? 260 : animIdx < 6 ? 220 : 180
    const t = setTimeout(() => setAnimIdx(i => i + 1), delay)
    return () => clearTimeout(t)
  }, [phase, animIdx, evalData])

  const runDemo = useCallback(async () => {
    if (runningRef.current) return
    runningRef.current = true
    setPhase('calling')
    setError(null)
    setCpStates(Array(11).fill('pending'))
    setAnimIdx(-1)
    setEvalData(null)

    try {
      const res = await fetch(`${API_BASE}/api/sandbox/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: DEMO_SCENARIO, language: 'en' }),
      })
      const data = await res.json()
      if (!data.success) throw new Error('API returned failure')

      const gates: Array<{ checkpoint: string; result: string; description: string }> = data.gate_results || []
      const blockedAt = gates.findIndex(g => g.result === 'BLOCKED')

      setEvalData({
        decision: data.decision || 'BLOCKED',
        receipt_id: data.receipt_id || data.receipt?.receipt_id || null,
        content_hash: data.receipt?.content_hash || null,
        algorithm: data.receipt?.signature_algorithm || 'Dilithium-3 (ML-DSA-65)',
        gate_results: gates,
        explanation: data.explanation || '',
        blocked_at: blockedAt,
      })
      setPhase('animating')
    } catch {
      setError('No se pudo conectar con el motor de governance. Verifica que la API esté en línea.')
      setPhase('idle')
      runningRef.current = false
    }
  }, [])

  const resetDemo = useCallback(() => {
    setPhase('idle')
    setCpStates(Array(11).fill('pending'))
    setAnimIdx(-1)
    setEvalData(null)
    setError(null)
    runningRef.current = false
  }, [])

  const copyId = useCallback(() => {
    if (evalData?.receipt_id) {
      navigator.clipboard.writeText(evalData.receipt_id).catch(() => {})
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }, [evalData])

  const isDone = phase === 'done'
  const isRunning = phase === 'calling' || phase === 'animating'
  const verifyUrl = evalData?.receipt_id ? `/verify/${evalData.receipt_id}` : '/verify'

  return (
    <div style={{ background: '#050D18', minHeight: '100vh', color: '#E2E8F0', fontFamily: 'Inter, system-ui, sans-serif' }}>

      {/* Nav */}
      <nav style={{
        borderBottom: '1px solid rgba(201,162,39,0.12)',
        padding: '14px 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0,
        background: 'rgba(5,13,24,0.96)', backdropFilter: 'blur(20px)', zIndex: 50,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Shield size={18} color="#C9A227" />
          <span style={{ fontWeight: 700, fontSize: 14, color: '#C9A227' }}>OMNIX QUANTUM</span>
          <ChevronRight size={14} color="rgba(226,232,240,0.3)" />
          <span style={{ fontSize: 13, color: 'rgba(226,232,240,0.5)' }}>Institutional Demo</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981' }} />
            <span style={{ fontSize: 11, color: '#10B981', fontWeight: 600 }}>SISTEMA EN PRODUCCIÓN</span>
          </div>
          <Link to="/" style={{ fontSize: 13, color: 'rgba(226,232,240,0.45)', textDecoration: 'none' }}>Inicio</Link>
        </div>
      </nav>

      {/* Hero */}
      <div style={{ textAlign: 'center', padding: '72px 24px 80px', maxWidth: 780, margin: '0 auto' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 28,
          background: 'rgba(201,162,39,0.08)', border: '1px solid rgba(201,162,39,0.25)',
          borderRadius: 24, padding: '5px 16px',
        }}>
          <Lock size={11} color="#C9A227" />
          <span style={{ fontSize: 11, fontWeight: 700, color: '#C9A227', letterSpacing: '0.08em' }}>
            142,036 GOVERNANCE RECEIPTS EN PRODUCCIÓN
          </span>
        </div>

        <h1 style={{ fontSize: 'clamp(30px, 5vw, 52px)', fontWeight: 800, lineHeight: 1.1, margin: '0 0 20px' }}>
          Una decisión automática intenta<br />
          <span style={{
            background: 'linear-gradient(135deg, #C9A227 0%, #D4AF37 60%, #E5E4E2 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
          }}>
            ejecutarse. Lo que pasa después.
          </span>
        </h1>
        <p style={{ fontSize: 17, color: 'rgba(226,232,240,0.6)', margin: '0 0 40px', lineHeight: 1.65 }}>
          Sin jerga técnica. Cada afirmación respaldada por datos reales en producción.
        </p>

        {!isRunning && !isDone && (
          <button
            onClick={runDemo}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 10,
              background: 'linear-gradient(135deg, #C9A227 0%, #A68B1F 100%)',
              color: '#050D18', border: 'none', borderRadius: 12,
              padding: '14px 32px', fontSize: 15, fontWeight: 700, cursor: 'pointer',
              boxShadow: '0 8px 32px rgba(201,162,39,0.35)',
            }}
          >
            <Play size={16} fill="#050D18" />
            Iniciar demo en vivo
          </button>
        )}

        {isDone && (
          <button
            onClick={resetDemo}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
              color: 'rgba(226,232,240,0.7)', borderRadius: 10, padding: '10px 22px',
              fontSize: 13, fontWeight: 600, cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} /> Reiniciar demo
          </button>
        )}

        {error && (
          <div style={{ marginTop: 20, color: '#EF4444', fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
            <AlertTriangle size={14} /> {error}
          </div>
        )}
      </div>

      {/* ─── PASO 1 — La decisión ─────────────────────────────────────────── */}
      <div style={section}>
        <SectionHeader
          n={1}
          title="Una decisión automatizada intenta ejecutarse."
          subtitle="Un sistema solicita autorización para ejecutar una operación de alto valor. OMNIX la intercepta antes de que llegue al mercado."
          done={isDone}
        />
        <div style={card}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20,
            paddingBottom: 16, borderBottom: '1px solid rgba(201,162,39,0.1)',
          }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: isRunning || isDone ? '#10B981' : '#C9A227' }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: isRunning || isDone ? '#10B981' : '#C9A227', letterSpacing: '0.1em' }}>
              {isRunning ? 'EVALUANDO AHORA' : isDone ? 'EVALUACIÓN COMPLETADA' : 'SOLICITUD PENDIENTE DE EVALUACIÓN'}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 20 }}>
            {[
              { label: 'Activo', value: DEMO_ASSET, highlight: true },
              { label: 'Señal de alerta', value: '+38% en 72 horas', highlight: false },
              { label: 'Anomalía on-chain', value: 'Whale 2.4× baseline', highlight: false },
            ].map(({ label, value, highlight }) => (
              <div key={label} style={{
                background: 'rgba(5,13,24,0.6)', borderRadius: 10, padding: '14px 16px',
                border: `1px solid ${highlight ? 'rgba(201,162,39,0.25)' : 'rgba(255,255,255,0.06)'}`,
              }}>
                <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', fontWeight: 600, letterSpacing: '0.08em', marginBottom: 6 }}>{label.toUpperCase()}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: highlight ? '#C9A227' : '#E2E8F0' }}>{value}</div>
              </div>
            ))}
          </div>

          <div style={{
            background: 'rgba(5,13,24,0.7)', borderRadius: 10, padding: '14px 18px',
            border: '1px solid rgba(255,255,255,0.06)', fontSize: 13, color: 'rgba(226,232,240,0.6)', lineHeight: 1.6,
          }}>
            "{DEMO_SCENARIO.trim()}"
          </div>

          {phase === 'idle' && (
            <div style={{ marginTop: 20, textAlign: 'center' }}>
              <button
                onClick={runDemo}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  background: 'rgba(201,162,39,0.12)', border: '1px solid rgba(201,162,39,0.35)',
                  color: '#C9A227', borderRadius: 8, padding: '10px 24px',
                  fontSize: 13, fontWeight: 700, cursor: 'pointer',
                }}
              >
                <Play size={13} /> Enviar al motor de governance →
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ─── PASO 2 — La evaluación ──────────────────────────────────────── */}
      <div style={section}>
        <SectionHeader
          n={2}
          title="OMNIX la evalúa en 11 checkpoints antes de ejecución."
          subtitle="Cada checkpoint es un criterio de governance independiente. Si uno falla, la decisión se bloquea. No hay excepciones."
          done={isDone}
        />
        <div style={card}>
          {phase === 'idle' && !isDone ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'rgba(226,232,240,0.3)', fontSize: 14 }}>
              <Clock size={32} style={{ marginBottom: 12, opacity: 0.4 }} />
              <div>Los checkpoints aparecerán aquí cuando inicies la demo.</div>
            </div>
          ) : (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 10, marginBottom: 20 }}>
                {CHECKPOINTS.map((cp, i) => {
                  const st = cpStates[i]
                  const isActive = phase === 'animating' && animIdx === i
                  return (
                    <div
                      key={cp.code}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 12,
                        background: st === 'blocked' ? 'rgba(239,68,68,0.08)' : st === 'pass' ? 'rgba(16,185,129,0.06)' : isActive ? 'rgba(201,162,39,0.08)' : 'rgba(5,13,24,0.5)',
                        border: `1px solid ${st === 'blocked' ? 'rgba(239,68,68,0.3)' : st === 'pass' ? 'rgba(16,185,129,0.2)' : isActive ? 'rgba(201,162,39,0.25)' : 'rgba(255,255,255,0.06)'}`,
                        borderRadius: 10, padding: '12px 14px',
                        transition: 'all 0.3s ease',
                      }}
                    >
                      <div style={{ fontSize: 18, flexShrink: 0 }}>{cp.icon}</div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', fontWeight: 600, marginBottom: 2 }}>{cp.code}</div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: st === 'blocked' ? '#EF4444' : st === 'pass' ? '#10B981' : isActive ? '#C9A227' : 'rgba(226,232,240,0.5)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {cp.label}
                        </div>
                      </div>
                      <div style={{ flexShrink: 0 }}>
                        {st === 'pass' && <CheckCircle size={14} color="#10B981" />}
                        {st === 'blocked' && <XCircle size={14} color="#EF4444" />}
                        {st === 'pending' && !isActive && <div style={{ width: 14, height: 14, borderRadius: '50%', border: '1.5px solid rgba(255,255,255,0.15)' }} />}
                        {isActive && <div style={{ width: 14, height: 14, borderRadius: '50%', border: '2px solid #C9A227', borderTopColor: 'transparent', animation: 'spin 0.6s linear infinite' }} />}
                      </div>
                    </div>
                  )
                })}
              </div>

              {isDone && evalData && (
                <div style={{
                  background: evalData.decision === 'APPROVED' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                  border: `1px solid ${evalData.decision === 'APPROVED' ? 'rgba(16,185,129,0.35)' : 'rgba(239,68,68,0.35)'}`,
                  borderRadius: 12, padding: '16px 20px',
                  display: 'flex', alignItems: 'center', gap: 14,
                }}>
                  {evalData.decision === 'APPROVED'
                    ? <CheckCircle size={28} color="#10B981" />
                    : <XCircle size={28} color="#EF4444" />
                  }
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 800, color: evalData.decision === 'APPROVED' ? '#10B981' : '#EF4444', marginBottom: 4 }}>
                      DECISIÓN: {evalData.decision === 'APPROVED' ? 'APROBADA' : 'BLOQUEADA'}
                    </div>
                    <div style={{ fontSize: 13, color: 'rgba(226,232,240,0.6)', lineHeight: 1.5 }}>
                      {evalData.explanation
                        ? evalData.explanation.slice(0, 200) + (evalData.explanation.length > 200 ? '…' : '')
                        : evalData.blocked_at >= 0
                          ? `Bloqueada en ${CHECKPOINTS[evalData.blocked_at]?.code} · ${CHECKPOINTS[evalData.blocked_at]?.label}`
                          : 'Evaluación completada por el motor de governance.'}
                    </div>
                  </div>
                </div>
              )}

              {isRunning && phase === 'calling' && (
                <div style={{ textAlign: 'center', padding: '20px 0', color: '#C9A227', fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                  <div style={{ width: 16, height: 16, border: '2px solid #C9A227', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                  Conectando con el motor de governance...
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* ─── PASO 3 — El receipt ─────────────────────────────────────────── */}
      <div style={section}>
        <SectionHeader
          n={3}
          title="Genera un receipt criptográficamente firmado."
          subtitle="Cada evaluación produce un comprobante único e inmutable. No hay manera de modificarlo sin que la firma se invalide."
          done={isDone && !!evalData?.receipt_id}
        />
        <div style={card}>
          {!isDone || !evalData?.receipt_id ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'rgba(226,232,240,0.3)', fontSize: 14 }}>
              <FileText size={32} style={{ marginBottom: 12, opacity: 0.4 }} />
              <div>El receipt aparecerá aquí después de la evaluación.</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', fontWeight: 600, letterSpacing: '0.08em', marginBottom: 4 }}>RECEIPT ID</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: '#C9A227', fontFamily: 'monospace' }}>{evalData.receipt_id}</div>
                </div>
                <button
                  onClick={copyId}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    background: 'rgba(201,162,39,0.1)', border: '1px solid rgba(201,162,39,0.25)',
                    color: '#C9A227', borderRadius: 8, padding: '8px 14px',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}
                >
                  <Copy size={12} /> {copied ? 'Copiado ✓' : 'Copiar ID'}
                </button>
              </div>

              {[
                { label: 'Activo evaluado', value: DEMO_ASSET },
                { label: 'Decisión', value: evalData.decision === 'APPROVED' ? '✅ APROBADA' : '🚫 BLOQUEADA' },
                { label: 'Algoritmo de firma', value: 'Post-cuántico · NIST FIPS 204' },
                { label: 'Verificable independientemente', value: 'Sí — sin acceso a OMNIX' },
              ].map(({ label, value }) => (
                <div key={label} style={{
                  background: 'rgba(5,13,24,0.6)', borderRadius: 10, padding: '14px 16px',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}>
                  <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', fontWeight: 600, letterSpacing: '0.08em', marginBottom: 6 }}>{label.toUpperCase()}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#E2E8F0' }}>{value}</div>
                </div>
              ))}

              {evalData.content_hash && (
                <div style={{
                  gridColumn: '1 / -1',
                  background: 'rgba(5,13,24,0.7)', borderRadius: 10, padding: '14px 18px',
                  border: '1px solid rgba(255,255,255,0.06)',
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                }}>
                  <Hash size={14} color="rgba(226,232,240,0.35)" style={{ marginTop: 2, flexShrink: 0 }} />
                  <div>
                    <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', fontWeight: 600, letterSpacing: '0.08em', marginBottom: 4 }}>CONTENT HASH (SHA-256)</div>
                    <div style={{ fontSize: 11, fontFamily: 'monospace', color: 'rgba(226,232,240,0.5)', wordBreak: 'break-all' }}>{evalData.content_hash}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ─── PASO 4 — La verificación ─────────────────────────────────────── */}
      <div style={section}>
        <SectionHeader
          n={4}
          title="Ese receipt puede verificarse públicamente."
          subtitle="Cualquier tercero — auditor, regulador, cliente — puede verificar la autenticidad de este receipt sin necesidad de acceder a OMNIX."
          done={isDone && !!evalData?.receipt_id}
        />
        <div style={card}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
            {[
              { icon: <Lock size={20} color="#C9A227" />, title: 'Firma post-cuántica', desc: 'Resistente a computación cuántica. Estándar NIST FIPS 204.' },
              { icon: <Hash size={20} color="#C9A227" />, title: 'Hash inmutable', desc: 'Cualquier modificación al receipt invalida la firma automáticamente.' },
              { icon: <Activity size={20} color="#C9A227" />, title: 'Auto-verificable', desc: 'El receipt lleva su propia clave pública embebida. Sin dependencia externa.' },
            ].map(({ icon, title, desc }) => (
              <div key={title} style={{ background: 'rgba(5,13,24,0.6)', borderRadius: 12, padding: '20px', border: '1px solid rgba(201,162,39,0.1)' }}>
                <div style={{ marginBottom: 12 }}>{icon}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#E2E8F0', marginBottom: 6 }}>{title}</div>
                <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.5)', lineHeight: 1.5 }}>{desc}</div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: 'center' }}>
            {isDone && evalData?.receipt_id ? (
              <Link
                to={verifyUrl}
                target="_blank"
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  background: 'rgba(201,162,39,0.12)', border: '1px solid rgba(201,162,39,0.35)',
                  color: '#C9A227', borderRadius: 10, padding: '12px 28px',
                  fontSize: 14, fontWeight: 700, textDecoration: 'none',
                }}
              >
                <ExternalLink size={14} /> Verificar este receipt →
              </Link>
            ) : (
              <div style={{ color: 'rgba(226,232,240,0.3)', fontSize: 13 }}>
                El link de verificación aparecerá cuando se genere el receipt.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ─── PASO 5 — Crisis históricas ──────────────────────────────────── */}
      <div style={section}>
        <SectionHeader
          n={5}
          title="También podemos replayear crisis históricas."
          subtitle="El motor puede recrear cualquier crisis pasada con datos reales y mostrar qué habría pasado si OMNIX hubiera estado operativo."
        />
        <div style={card}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24,
            paddingBottom: 16, borderBottom: '1px solid rgba(201,162,39,0.1)',
          }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: 'rgba(226,232,240,0.4)' }}>CRISIS-002-FTX-2022</span>
            <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.3)' }}>·</span>
            <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.4)' }}>FTX Exchange Collapse</span>
            <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.3)' }}>·</span>
            <span style={{ fontSize: 12, color: '#EF4444', fontWeight: 700 }}>$8B+ customer funds missing</span>
          </div>

          <div style={{ position: 'relative' }}>
            <div style={{
              position: 'absolute', left: 24, top: 24, bottom: 24, width: 2,
              background: 'linear-gradient(180deg, rgba(201,162,39,0.4) 0%, rgba(239,68,68,0.4) 100%)',
            }} />

            {[
              {
                date: 'Nov 3, 2022',
                label: 'T-8 días antes del colapso',
                verdict: 'HOLD',
                verdictColor: '#C9A227',
                checkpoint: 'CP-3',
                desc: 'Concentración inusual de posiciones en FTT token. OMNIX emite HOLD pendiente de validación estructural.',
                receipt: 'OMNIX-RPL-BA1B556168909D69',
              },
              {
                date: 'Nov 7, 2022',
                label: 'T-4 días antes del colapso',
                verdict: 'BLOCKED',
                verdictColor: '#EF4444',
                checkpoint: 'CP-6',
                desc: 'CoinDesk reporta $5.8B en activos ilíquidos. Riesgo de contraparte supera umbral. BLOQUEADO.',
                receipt: 'OMNIX-RPL-228D2BCB713BEA18',
              },
              {
                date: 'Nov 8, 2022',
                label: 'T-3 días — Colapso en progreso',
                verdict: 'BLOCKED',
                verdictColor: '#EF4444',
                checkpoint: 'CP-9',
                desc: 'Congelamiento de retiros confirmado. AML Gate activado. Bloqueo permanente.',
                receipt: 'OMNIX-RPL-7E55E9A70A2DC123',
              },
            ].map(({ date, label, verdict, verdictColor, checkpoint, desc, receipt }) => (
              <div key={receipt} style={{ display: 'flex', gap: 24, marginBottom: 24, paddingLeft: 48, position: 'relative' }}>
                <div style={{
                  position: 'absolute', left: 18, top: 16, width: 14, height: 14, borderRadius: '50%',
                  background: verdictColor === '#EF4444' ? 'rgba(239,68,68,0.8)' : 'rgba(201,162,39,0.8)',
                  border: '2px solid #050D18',
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
                    <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.5)' }}>{date}</span>
                    <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)' }}>·</span>
                    <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)', fontWeight: 600 }}>{label}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 800, padding: '2px 8px', borderRadius: 6,
                      background: verdictColor === '#EF4444' ? 'rgba(239,68,68,0.12)' : 'rgba(201,162,39,0.12)',
                      color: verdictColor, border: `1px solid ${verdictColor}44`,
                    }}>{verdict} @ {checkpoint}</span>
                  </div>
                  <p style={{ margin: '0 0 8px', fontSize: 13, color: 'rgba(226,232,240,0.7)', lineHeight: 1.5 }}>{desc}</p>
                  <div style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(226,232,240,0.3)' }}>{receipt}</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{
            marginTop: 8, padding: '14px 18px', borderRadius: 10,
            background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
          }}>
            <div style={{ fontSize: 13, color: 'rgba(226,232,240,0.7)' }}>
              Nov 11, 2022 — FTX declaró bancarrota. $8B+ en fondos de clientes desaparecieron.
              <span style={{ color: '#10B981', fontWeight: 700 }}> OMNIX lo habría bloqueado 8 días antes.</span>
            </div>
            <Link to="/crisis-replay" style={{
              display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700,
              color: '#C9A227', textDecoration: 'none', flexShrink: 0,
            }}>
              Ver los 5 escenarios <ArrowRight size={12} />
            </Link>
          </div>
        </div>
      </div>

      {/* ─── PASO 6 — Disaster Recovery ──────────────────────────────────── */}
      <div style={section}>
        <SectionHeader
          n={6}
          title="Y el sistema sigue siendo auditable después de restaurar backups."
          subtitle="El 10 de mayo de 2026 ejecutamos un test real de recuperación ante desastres. Ninguna simulación — datos reales de producción."
        />
        <div style={card}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
            {[
              { metric: '500 / 500', label: 'Firmas PQC válidas', color: '#10B981', icon: <CheckCircle size={16} color="#10B981" /> },
              { metric: '11 / 11', label: 'Snapshots AVM intactos', color: '#10B981', icon: <CheckCircle size={16} color="#10B981" /> },
              { metric: '142,036', label: 'Receipts en producción', color: '#C9A227', icon: <Database size={16} color="#C9A227" /> },
              { metric: '~4 horas', label: 'RTO confirmado', color: '#C9A227', icon: <Clock size={16} color="#C9A227" /> },
            ].map(({ metric, label, color, icon }) => (
              <div key={label} style={{
                background: 'rgba(5,13,24,0.6)', borderRadius: 12, padding: '20px 16px',
                border: '1px solid rgba(255,255,255,0.06)', textAlign: 'center',
              }}>
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 8 }}>{icon}</div>
                <div style={{ fontSize: 22, fontWeight: 800, color, marginBottom: 4 }}>{metric}</div>
                <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', lineHeight: 1.4 }}>{label}</div>
              </div>
            ))}
          </div>

          <div style={{
            background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)',
            borderRadius: 12, padding: '16px 20px', marginBottom: 20,
            fontSize: 13, color: 'rgba(226,232,240,0.7)', lineHeight: 1.6,
          }}>
            <span style={{ color: '#10B981', fontWeight: 700 }}>Hallazgo clave:</span>{' '}
            Los receipts de OMNIX son auto-verificables. Cada uno lleva embebida su propia clave criptográfica pública.
            Esto significa que un auditor puede verificar cualquier receipt{' '}
            <em>sin necesidad de acceder a ningún servidor de OMNIX</em> — ni ahora ni en el futuro.
          </div>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <Link to="/verify" style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: 'rgba(201,162,39,0.1)', border: '1px solid rgba(201,162,39,0.3)',
              color: '#C9A227', borderRadius: 8, padding: '9px 18px',
              fontSize: 12, fontWeight: 700, textDecoration: 'none',
            }}>
              <ExternalLink size={12} /> Verificar cualquier receipt
            </Link>
            <Link to="/proof" style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
              color: 'rgba(226,232,240,0.6)', borderRadius: 8, padding: '9px 18px',
              fontSize: 12, fontWeight: 600, textDecoration: 'none',
            }}>
              <Shield size={12} /> Proof Layer
            </Link>
          </div>
        </div>
      </div>

      {/* ─── CTA final ───────────────────────────────────────────────────── */}
      <div style={{ maxWidth: 700, margin: '0 auto 100px', padding: '0 24px', textAlign: 'center' }}>
        <div style={{
          background: 'linear-gradient(135deg, rgba(201,162,39,0.08) 0%, rgba(15,33,64,0.6) 100%)',
          border: '1px solid rgba(201,162,39,0.2)', borderRadius: 20, padding: '48px 40px',
        }}>
          <Shield size={32} color="#C9A227" style={{ marginBottom: 20 }} />
          <h3 style={{ fontSize: 26, fontWeight: 800, margin: '0 0 12px' }}>¿Listo para una demo privada?</h3>
          <p style={{ fontSize: 15, color: 'rgba(226,232,240,0.6)', margin: '0 0 32px', lineHeight: 1.6 }}>
            Configuramos un entorno de governance para tu industria específica —
            trading, seguros, crédito, medical AI, o defensa. Demo en vivo, datos reales, sin PowerPoint.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/book" style={{
              display: 'flex', alignItems: 'center', gap: 8,
              background: 'linear-gradient(135deg, #C9A227 0%, #A68B1F 100%)',
              color: '#050D18', borderRadius: 10, padding: '13px 28px',
              fontSize: 14, fontWeight: 700, textDecoration: 'none',
              boxShadow: '0 8px 24px rgba(201,162,39,0.3)',
            }}>
              Solicitar demo privada <ArrowRight size={14} />
            </Link>
            <Link to="/try" style={{
              display: 'flex', alignItems: 'center', gap: 8,
              background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
              color: 'rgba(226,232,240,0.8)', borderRadius: 10, padding: '13px 28px',
              fontSize: 14, fontWeight: 600, textDecoration: 'none',
            }}>
              Probar con tu propio escenario
            </Link>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      `}</style>
    </div>
  )
}

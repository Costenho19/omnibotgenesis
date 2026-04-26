import { useState } from 'react'

const BASE = 'https://omnixquantum.net'

const endpoints = [
  {
    label: 'Clave Pública (RFC 8615)',
    url: `${BASE}/.well-known/omnix-public-key.json`,
    badge: 'LIVE',
    desc: 'Clave Dilithium-3 activa. Cualquier sistema puede fetchearla sin autenticación.',
  },
  {
    label: 'DID Document (W3C)',
    url: `${BASE}/.well-known/did.json`,
    badge: 'LIVE',
    desc: 'did:web:omnixquantum.net — resolvible por cualquier DID resolver del mundo.',
  },
  {
    label: 'Trust Registry',
    url: `${BASE}/api/trust/registry`,
    badge: 'LIVE',
    desc: 'Registro público de emisores confiables, algoritmos y métodos de verificación.',
  },
  {
    label: 'Verificador API (stateless)',
    url: `${BASE}/api/trust/verify`,
    badge: 'POST',
    desc: 'Verificación sin acceso a DB. Envía un recibo, recibe hash_valid + signature_valid.',
  },
]

const steps = [
  {
    num: '01',
    title: 'Obtener la clave pública',
    desc: 'Descarga la clave pública Dilithium-3 desde el endpoint well-known. Esta clave firma TODOS los recibos de gobernanza.',
    code: `curl https://omnixquantum.net/.well-known/omnix-public-key.json`,
    note: 'Una sola red call. Después, todo es local.',
  },
  {
    num: '02',
    title: 'Recomputar el hash SHA-256',
    desc: 'El campo content_hash del recibo es un SHA-256 del payload canónico. Puedes recomputarlo tú mismo y comparar.',
    code: `python omnix_verify.py receipt.json`,
    note: 'La matemática no depende de ningún servidor OMNIX.',
  },
  {
    num: '03',
    title: 'Verificar la firma Dilithium-3',
    desc: 'La firma PQC usa ML-DSA-65 (NIST FIPS 204). Cualquier implementación estándar de Dilithium-3 puede verificarla.',
    code: `pip install pqcrypto\npython omnix_verify.py receipt.json`,
    note: 'Verificación 100% offline. Sin conexión a OMNIX.',
  },
]

const critique = {
  original: `"Todo lo que describes ocurre dentro de tu propio sistema: validación, monitorización y trazabilidad. Eso es gobernanza interna. No interoperabilidad. La confianza no puede depender de un sistema, sino de pruebas que puedan ser verificadas y comprendidas por terceros."`,
  author: '— Antonio Socorro, LinkedIn',
  response: `La crítica es correcta y la tomamos en serio. Por eso construimos tres capas de verificabilidad externa: la matemática es pública (NIST FIPS 204), la clave está publicada en un endpoint estándar (RFC 8615 + W3C DID), y el script de verificación es descargable y corre sin ningún servidor de OMNIX. Si la gobernanza existe, la prueba debe sobrevivir fuera del sistema que la produce.`,
}

export default function IndependentVerification() {
  const [copied, setCopied] = useState<string | null>(null)

  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="min-h-screen bg-black text-white font-mono">

      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <a href="/" className="text-gray-400 hover:text-white text-sm transition-colors">← omnixquantum.net</a>
        <span className="text-xs text-gray-600">ADR-085 · eIDAS · ARF · NIST FIPS 204</span>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-16">

        {/* Title */}
        <div className="mb-16">
          <div className="text-xs text-emerald-400 tracking-widest mb-4">VERIFICACIÓN INDEPENDIENTE</div>
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            Verifica cualquier decisión<br />
            <span className="text-emerald-400">sin depender de OMNIX</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl leading-relaxed">
            Las firmas criptográficas son matemáticas. La matemática no tiene servidor.
            Descarga el script, obtén la clave pública una vez, y verifica offline para siempre.
          </p>
        </div>

        {/* The critique card */}
        <div className="mb-16 border border-amber-800/40 bg-amber-950/20 rounded-lg p-6">
          <div className="text-xs text-amber-400 tracking-widest mb-3">CONTEXTO — CRÍTICA QUE ORIGINÓ ESTO</div>
          <blockquote className="text-gray-300 text-sm leading-relaxed italic mb-3 border-l-2 border-amber-600 pl-4">
            {critique.original}
          </blockquote>
          <div className="text-xs text-amber-600 mb-4">{critique.author}</div>
          <div className="text-gray-400 text-sm leading-relaxed border-t border-amber-800/30 pt-4">
            <span className="text-emerald-400 font-bold">Respuesta: </span>
            {critique.response}
          </div>
        </div>

        {/* Download CTA */}
        <div className="mb-16 border border-emerald-800/50 bg-emerald-950/20 rounded-lg p-8 text-center">
          <div className="text-xs text-emerald-400 tracking-widest mb-4">PASO 0 — DESCARGA EL VERIFICADOR</div>
          <h2 className="text-2xl font-bold text-white mb-3">omnix_verify.py</h2>
          <p className="text-gray-400 text-sm mb-6 max-w-lg mx-auto">
            Script Python standalone. Cero dependencias de OMNIX. Requiere solo Python 3.8+.
            Para verificación PQC completa: <code className="text-emerald-400">pip install pqcrypto</code>
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <a
              href="/omnix_verify.py"
              download="omnix_verify.py"
              className="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-black font-bold rounded transition-colors text-sm"
            >
              Descargar omnix_verify.py
            </a>
            <button
              onClick={() => copy('pip install pqcrypto', 'pip')}
              className="px-6 py-3 border border-emerald-800 hover:border-emerald-600 text-emerald-400 text-sm rounded transition-colors"
            >
              {copied === 'pip' ? '¡Copiado!' : 'pip install pqcrypto'}
            </button>
          </div>
          <div className="mt-4 text-xs text-gray-600">
            SHA-256 hash del script disponible en{' '}
            <a href="/.well-known/omnix-public-key.json" className="text-gray-500 hover:text-gray-400 underline" target="_blank" rel="noreferrer">
              .well-known/omnix-public-key.json
            </a>
          </div>
        </div>

        {/* Steps */}
        <div className="mb-16">
          <div className="text-xs text-gray-500 tracking-widest mb-8">CÓMO FUNCIONA</div>
          <div className="space-y-8">
            {steps.map((step) => (
              <div key={step.num} className="flex gap-6 group">
                <div className="text-4xl font-bold text-gray-800 group-hover:text-emerald-900 transition-colors w-12 flex-shrink-0 pt-1">
                  {step.num}
                </div>
                <div className="flex-1 border border-gray-800 rounded-lg p-6 hover:border-gray-700 transition-colors">
                  <div className="text-white font-bold mb-2">{step.title}</div>
                  <div className="text-gray-400 text-sm mb-4">{step.desc}</div>
                  <div className="flex items-center justify-between bg-gray-950 border border-gray-800 rounded px-4 py-3 mb-3">
                    <code className="text-emerald-400 text-xs whitespace-pre">{step.code}</code>
                    <button
                      onClick={() => copy(step.code, step.num)}
                      className="text-gray-600 hover:text-gray-400 text-xs ml-4 flex-shrink-0 transition-colors"
                    >
                      {copied === step.num ? 'copiado' : 'copiar'}
                    </button>
                  </div>
                  <div className="text-xs text-gray-600">{step.note}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live endpoints */}
        <div className="mb-16">
          <div className="text-xs text-gray-500 tracking-widest mb-8">ENDPOINTS PÚBLICOS — SIN AUTENTICACIÓN</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {endpoints.map((ep) => (
              <div key={ep.url} className="border border-gray-800 rounded-lg p-5 hover:border-gray-700 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white text-sm font-bold">{ep.label}</span>
                  <span className={`text-xs px-2 py-0.5 rounded font-mono ${
                    ep.badge === 'POST'
                      ? 'bg-blue-950 text-blue-400 border border-blue-800'
                      : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                  }`}>
                    {ep.badge}
                  </span>
                </div>
                <div className="text-gray-600 text-xs mb-3 font-mono break-all">{ep.url}</div>
                <div className="text-gray-500 text-xs">{ep.desc}</div>
                <a
                  href={ep.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-block text-xs text-emerald-600 hover:text-emerald-400 transition-colors"
                >
                  Abrir →
                </a>
              </div>
            ))}
          </div>
        </div>

        {/* What the math guarantees */}
        <div className="mb-16 border border-gray-800 rounded-lg p-8">
          <div className="text-xs text-gray-500 tracking-widest mb-6">LO QUE LA MATEMÁTICA GARANTIZA</div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: '🔒',
                title: 'Integridad',
                body: 'SHA-256 del payload canónico. Si un campo fue modificado después de emitir el recibo, el hash no coincide. Detectable por cualquiera.',
              },
              {
                icon: '✍️',
                title: 'Autenticidad',
                body: 'Firma Dilithium-3 (NIST FIPS 204). Solo quien tiene la clave privada puede firmar. La clave privada nunca sale del servidor.',
              },
              {
                icon: '🌐',
                title: 'Independencia',
                body: 'La verificación criptográfica no requiere que OMNIX exista. El recibo se puede verificar en 2030 con el script y la clave pública.',
              },
            ].map((item) => (
              <div key={item.title}>
                <div className="text-2xl mb-3">{item.icon}</div>
                <div className="text-white font-bold text-sm mb-2">{item.title}</div>
                <div className="text-gray-500 text-xs leading-relaxed">{item.body}</div>
              </div>
            ))}
          </div>
        </div>

        {/* What this does NOT solve (honest) */}
        <div className="mb-16 border border-gray-800 rounded-lg p-8">
          <div className="text-xs text-gray-500 tracking-widest mb-4">HONESTIDAD TÉCNICA — QUÉ NO RESUELVE ESTO SOLO</div>
          <div className="space-y-3 text-sm text-gray-400">
            <div className="flex gap-3">
              <span className="text-amber-500 flex-shrink-0">△</span>
              <span>
                <strong className="text-white">Ancla de confianza externa:</strong> La clave pública la publica OMNIX. Para cumplimiento eIDAS completo, la siguiente capa es anclarla en un QTSP (Qualified Trust Service Provider) europeo. Está en roadmap.
              </span>
            </div>
            <div className="flex gap-3">
              <span className="text-amber-500 flex-shrink-0">△</span>
              <span>
                <strong className="text-white">Rotación de claves:</strong> Si OMNIX cambia la clave, los recibos antiguos siguen siendo verificables con la clave con que fueron firmados (embebida en el recibo). La política de rotación está en ADR-043.
              </span>
            </div>
            <div className="flex gap-3">
              <span className="text-emerald-500 flex-shrink-0">✓</span>
              <span>
                <strong className="text-white">Lo que SÍ resuelve hoy:</strong> cualquier tercero puede verificar que un recibo no fue modificado y que fue emitido por OMNIX, sin confiar en ningún endpoint de OMNIX durante la verificación.
              </span>
            </div>
          </div>
        </div>

        {/* API example */}
        <div className="mb-16">
          <div className="text-xs text-gray-500 tracking-widest mb-6">VERIFICACIÓN VÍA API (sin DB, stateless)</div>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-xs text-gray-600 mb-3">POST /api/trust/verify</div>
            <pre className="text-emerald-400 text-xs overflow-x-auto whitespace-pre-wrap">{`curl -X POST https://omnixquantum.net/api/trust/verify \\
  -H "Content-Type: application/json" \\
  -d '{
    "receipt": {
      "receipt_id": "REC-20260426-...",
      "decision": "APPROVED",
      "content_hash": "a3f1...",
      "signature": "base64...",
      "public_key": "base64...",
      ...
    }
  }'

// Response:
{
  "hash_valid": true,
  "signature_valid": true,
  "overall_valid": true,
  "independent": true,
  "db_required": false,
  "issuer_did": "did:web:omnixquantum.net"
}`}</pre>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-800 pt-8 text-center">
          <div className="text-xs text-gray-600 mb-2">
            OMNIX Quantum Ltd · did:web:omnixquantum.net · ADR-085
          </div>
          <div className="text-xs text-gray-700">
            eIDAS 2.0 · EU AI Act Art. 14 · ARF · NIST FIPS 204 · MiFID II
          </div>
          <div className="mt-4 flex justify-center gap-6 text-xs">
            <a href="/verify" className="text-gray-600 hover:text-gray-400 transition-colors">Verificar recibo</a>
            <a href="/proof" className="text-gray-600 hover:text-gray-400 transition-colors">Proof Layer</a>
            <a href="/integration" className="text-gray-600 hover:text-gray-400 transition-colors">Integration Guide</a>
            <a href="/" className="text-gray-600 hover:text-gray-400 transition-colors">Inicio</a>
          </div>
        </div>

      </div>
    </div>
  )
}

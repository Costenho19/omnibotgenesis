import { useState, useCallback, useRef, useMemo, useEffect } from 'react'
import { ml_dsa65 } from '@noble/post-quantum/ml-dsa.js'
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { saveAs } from 'file-saver'

// ── Design System Constants ──
const GOLD = '#C9A227'
const GOLD_DIM = 'rgba(201,162,39,0.12)'
const GOLD_BORDER = 'rgba(201,162,39,0.22)'
const NAVY = '#060F1E'
const NAVY2 = '#0A1628'
const NAVY3 = '#0D1E38'
const GREEN = '#22c55e'
const GREEN_DIM = 'rgba(34,197,94,0.10)'
const GREEN_BORDER = 'rgba(34,197,94,0.28)'
const RED = '#ef4444'
const RED_DIM = 'rgba(239,68,68,0.09)'
const RED_BORDER = 'rgba(239,68,68,0.28)'
const AMBER = '#f59e0b'
const PURPLE = '#a855f7'
const BLUE = '#3b82f6'
const SLATE = '#64748b'
const TEXT = '#e2e8f0'

const GENESIS_SENTINEL = '0'.repeat(64)

// ── Types & Interfaces ──
interface BlockData {
  block_id: string
  creation_timestamp_ns: number   // WARNING: may lose precision >2^53 after JSON.parse
  artifact_count: number
  evidence_classes: string[]
  canonical_hash: string
  predecessor_block_hash: string
  integrity_manifest: {
    artifact_hashes: string[]
    merkle_root: string
    hash_algorithm: string
  }
  pqc_signature?: string
  pqc_algorithm?: string
  omnix_version: string
  sealed_at?: string
  sealed_by?: string
  seal_trigger?: string
  artifact_ids?: string[]
  // Precision-safe raw strings extracted from JSON text (FVP-INV-001)
  _rawCreationTimestampNs?: string
  _rawArtifactCount?: string
}

type VerdictState = 'PASS' | 'INTEGRITY_VIOLATION' | 'CHAIN_BREAK' | 'SIGNATURE_INVALID' | 'ORPHANED' | 'INCOMPLETE' | 'PENDING'

interface BlockVerification {
  block: BlockData
  localVerdict: VerdictState
  serverVerdict?: VerdictState
  checks: {
    merkle: boolean
    canonical: boolean
    chain: boolean | null
    pqc: boolean | null | 'incomplete'
  }
  reasons: string[]
  computedMerkle: string
  computedCanonical: string
}

const CLASS_COLORS: Record<string, string> = {
  LEGAL: GOLD,
  PQC: PURPLE,
  CONTRACT: BLUE,
  EXCEPTION: RED,
}

// ── Helper Components ──

function Badge({ label, state }: { label: string; state: VerdictState | 'incomplete' }) {
  const colors = {
    PASS: { color: GREEN, bg: GREEN_DIM, border: GREEN_BORDER },
    INTEGRITY_VIOLATION: { color: RED, bg: RED_DIM, border: RED_BORDER },
    CHAIN_BREAK: { color: '#f97316', bg: 'rgba(249,115,22,0.1)', border: 'rgba(249,115,22,0.28)' },
    SIGNATURE_INVALID: { color: RED, bg: RED_DIM, border: RED_BORDER },
    ORPHANED: { color: AMBER, bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.28)' },
    INCOMPLETE: { color: AMBER, bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.28)' },
    incomplete: { color: AMBER, bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.28)' },
    PENDING: { color: SLATE, bg: 'rgba(100,116,139,0.1)', border: 'rgba(100,116,139,0.2)' },
  }
  const cfg = colors[state as keyof typeof colors] || colors.PENDING
  return (
    <span style={{
      padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 700,
      color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`,
      letterSpacing: '0.05em'
    }}>
      {label}
    </span>
  )
}

function CheckIcon({ ok, incomplete }: { ok: boolean | null; incomplete?: boolean }) {
  if (incomplete) return <span style={{ color: AMBER }}>⚠</span>
  if (ok === null) return <span style={{ color: SLATE }}>○</span>
  return ok ? <span style={{ color: GREEN }}>✓</span> : <span style={{ color: RED }}>✗</span>
}

// ── Browser Verification Engine ──

/**
 * Recompute canonical hash with precision-safe integer handling (FVP-INV-001).
 *
 * PROBLEM: creation_timestamp_ns is ~1.78e18, which exceeds JS Number.MAX_SAFE_INTEGER
 * (2^53 - 1 = 9.007e15). JSON.parse() loses precision, causing JSON.stringify() to
 * produce a different integer than Python's json.dumps() — breaking canonical hash bit-identity.
 *
 * SOLUTION: Use _rawCreationTimestampNs and _rawArtifactCount (exact strings extracted
 * from the original JSON text by regex before JSON.parse) to reconstruct the canonical
 * JSON string manually — matching Python's json.dumps(sort_keys=True, separators=(',',':')).
 */
async function recomputeCanonicalHash(block: BlockData): Promise<string> {
  // Use raw integer strings if available (precision-safe path)
  const rawTs    = block._rawCreationTimestampNs ?? String(block.creation_timestamp_ns)
  const rawCount = block._rawArtifactCount       ?? String(block.artifact_count)

  // Build canonical JSON string manually to match Python's json.dumps(sort_keys=True, separators=(',',':'))
  // Field order must be alphabetical (sort_keys=True)
  // evidence_classes is a JSON array of sorted strings
  const ecJson = JSON.stringify([...block.evidence_classes].sort())

  // Escape block_id, hash_algorithm, merkle_root, omnix_version, predecessor_block_hash
  // (all should be ASCII alphanumeric/safe — but use JSON.stringify for correctness)
  const canonicalStr = [
    `"artifact_count":${rawCount}`,
    `"block_id":${JSON.stringify(block.block_id)}`,
    `"creation_timestamp_ns":${rawTs}`,
    `"evidence_classes":${ecJson}`,
    `"hash_algorithm":${JSON.stringify(block.integrity_manifest.hash_algorithm)}`,
    `"merkle_root":${JSON.stringify(block.integrity_manifest.merkle_root)}`,
    `"omnix_version":${JSON.stringify(block.omnix_version)}`,
    `"predecessor_block_hash":${JSON.stringify(block.predecessor_block_hash)}`,
  ].join(',')
  const jsonStr = `{${canonicalStr}}`

  const bytes = new TextEncoder().encode(jsonStr)
  const hashBuf = await crypto.subtle.digest('SHA-256', bytes)
  return 'sha256:' + Array.from(new Uint8Array(hashBuf)).map(b => b.toString(16).padStart(2, '0')).join('')
}

async function recomputeMerkleRoot(artifactHashes: string[]): Promise<string> {
  const sorted = [...artifactHashes].sort()
  const joined = sorted.join('|')
  const bytes = new TextEncoder().encode(joined)
  const hashBuf = await crypto.subtle.digest('SHA-256', bytes)
  return 'sha256:' + Array.from(new Uint8Array(hashBuf)).map(b => b.toString(16).padStart(2, '0')).join('')
}

async function verifyWithServer(block: BlockData, publicKeyB64: string, predecessor?: BlockData) {
  const API = import.meta.env.VITE_RAILWAY_API_URL || ''
  try {
    const res = await fetch(`${API}/api/forensic/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ block, public_key_b64: publicKeyB64, predecessor_block: predecessor ?? null })
    })
    return res.json()
  } catch (err) {
    return { error: String(err), verdict: 'INCOMPLETE' }
  }
}

// ── Main Page Component ──

export default function ArchiveVerifierPage() {
  const [blocks, setBlocks] = useState<BlockData[]>([])
  const [publicKey, setPublicKey] = useState<string | null>(null)
  const [verifications, setVerifications] = useState<Record<string, BlockVerification>>({})
  const [loading, setLoading] = useState(false)
  const [activeBlockId, setActiveBlockId]   = useState<string | null>(null)
  const [exportApiKey, setExportApiKey]     = useState<string>('')
  const [exportError, setExportError]       = useState<string | null>(null)
  const [exportSuccess, setExportSuccess]   = useState<string | null>(null)
  const [showApiKeyInput, setShowApiKeyInput] = useState(false)

  // ── Platform Trust Anchor (ADR-167 / OMNIX-SEC-2026-001) ──────────────────
  const [platformKeyInfo, setPlatformKeyInfo] = useState<{
    status: string
    fingerprint: string | null
    fingerprint_short: string | null
    algorithm: string
    configured: boolean
    canonical_verification_url: string
    published_at: string | null
    dns_txt_record?: { record_name: string; record_format: string }
  } | null>(null)
  const [keyMatchStatus, setKeyMatchStatus] = useState<
    'unknown' | 'match' | 'mismatch' | 'unchecked'
  >('unchecked')
  const [fpCopied, setFpCopied] = useState(false)
  const [showTrustAnchor, setShowTrustAnchor] = useState(true)

  const blockInputRef = useRef<HTMLInputElement>(null)
  const keyInputRef = useRef<HTMLInputElement>(null)

  // ── Fetch platform key fingerprint on mount (ADR-167 / OMNIX-SEC-2026-001) ─
  useEffect(() => {
    fetch('/api/forensic/platform-key')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setPlatformKeyInfo(data) })
      .catch(() => {})
  }, [])

  const handleBlockUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    files.forEach(file => {
      const reader = new FileReader()
      reader.onload = (event) => {
        try {
          const rawText = event.target?.result as string
          const content = JSON.parse(rawText) as BlockData

          // Extract exact integer strings BEFORE precision loss from JSON.parse.
          // creation_timestamp_ns (~1.78e18) exceeds Number.MAX_SAFE_INTEGER (2^53-1).
          // Regex captures the raw digit string directly from the source text (FVP-INV-001).
          const tsMatch    = rawText.match(/"creation_timestamp_ns"\s*:\s*(\d+)/)
          const countMatch = rawText.match(/"artifact_count"\s*:\s*(\d+)/)
          content._rawCreationTimestampNs = tsMatch?.[1]    ?? String(content.creation_timestamp_ns)
          content._rawArtifactCount       = countMatch?.[1] ?? String(content.artifact_count)

          setBlocks(prev => {
            if (prev.find(b => b.block_id === content.block_id)) return prev
            return [...prev, content]
          })
        } catch (err) {
          console.error("Invalid block JSON", err)
        }
      }
      reader.readAsText(file)
    })
  }

  const handleKeyUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (event) => {
      setPublicKey(event.target?.result as string)
    }
    reader.readAsText(file)
  }

  const runVerification = useCallback(async () => {
    setLoading(true)
    setKeyMatchStatus('unknown')
    const newVerifications: Record<string, BlockVerification> = {}

    // 1. Sort blocks by predecessor graph (not timestamp — FVP-INV-001 / chain integrity)
    // Build a predecessor-aware topological order to correctly validate chain links.
    const knownHashes = new Set(blocks.map(b => b.canonical_hash))
    const roots = blocks.filter(
      b => b.predecessor_block_hash === GENESIS_SENTINEL || !knownHashes.has(b.predecessor_block_hash)
    )
    const sortedBlocks: BlockData[] = []
    const visited = new Set<string>()
    const safeTs = (b: BlockData): bigint => {
      try { return BigInt(b._rawCreationTimestampNs ?? '0') } catch { return 0n }
    }
    const queue: BlockData[] = [...roots].sort(
      (a, b) => Number(safeTs(a) - safeTs(b))
    )
    while (queue.length > 0) {
      const current = queue.shift()!
      if (visited.has(current.canonical_hash)) continue
      visited.add(current.canonical_hash)
      sortedBlocks.push(current)
      const children = blocks.filter(
        b => b.predecessor_block_hash === current.canonical_hash && !visited.has(b.canonical_hash)
      )
      children.sort((a, b) => Number(safeTs(a) - safeTs(b)))
      queue.push(...children)
    }
    // Append any disconnected blocks
    for (const b of blocks) {
      if (!visited.has(b.canonical_hash)) sortedBlocks.push(b)
    }

    for (const block of sortedBlocks) {
      const reasons: string[] = []

      // ── Plane 1: Browser hash + chain checks ───────────────────────────────
      const computedMerkle    = await recomputeMerkleRoot(block.integrity_manifest.artifact_hashes)
      const computedCanonical = await recomputeCanonicalHash(block)

      const merkleValid    = computedMerkle    === block.integrity_manifest.merkle_root
      const canonicalValid = computedCanonical === block.canonical_hash

      let chainValid: boolean | null = null
      if (block.predecessor_block_hash === GENESIS_SENTINEL) {
        chainValid = true
      } else {
        const predecessorPresent = sortedBlocks.some(b => b.canonical_hash === block.predecessor_block_hash)
        chainValid = predecessorPresent ? true : null  // null = orphaned (predecessor not in upload set)
      }

      // ── FVP-INV-004: Browser MUST NOT emit SIGNATURE_INVALID ───────────────
      // Browser PQC is best-effort. A negative browser result is INCOMPLETE,
      // not SIGNATURE_INVALID — only the server (Plane 2) may emit that verdict.
      let pqcValid: boolean | null | 'incomplete' = null
      if (publicKey && block.pqc_signature) {
        try {
          const sig = Uint8Array.from(atob(block.pqc_signature), c => c.charCodeAt(0))
          const pub = Uint8Array.from(atob(publicKey), c => c.charCodeAt(0))
          const msg = new TextEncoder().encode(block.canonical_hash)
          const ok  = await ml_dsa65.verify(sig, msg, pub)
          // FVP-INV-004: ok===false → INCOMPLETE (not SIGNATURE_INVALID) from browser.
          // Browser wire format may differ from pypqc. Server is authoritative.
          pqcValid = ok ? true : 'incomplete'
          if (!ok) reasons.push("PQC browser check inconclusive (wire-format may differ — escalating to server)")
        } catch {
          pqcValid = 'incomplete'
          reasons.push("PQC: browser library error — escalating to server (FVP-INV-004)")
        }
      }

      // ── Browser-plane verdict (Plane 1) ────────────────────────────────────
      let localVerdict: VerdictState = 'PASS'
      if (!merkleValid || !canonicalValid) {
        localVerdict = 'INTEGRITY_VIOLATION'
        if (!merkleValid)    reasons.push("Merkle root mismatch")
        if (!canonicalValid) reasons.push("Canonical hash mismatch")
      } else if (chainValid === null) {
        localVerdict = 'ORPHANED'
        reasons.push("Predecessor block not found in uploaded set")
      } else if (!publicKey) {
        localVerdict = 'INCOMPLETE'
        reasons.push("No public key provided — PQC signature not verified")
      } else if (pqcValid === 'incomplete') {
        localVerdict = 'INCOMPLETE'
      }
      // Note: pqcValid===true means browser tentatively verified PQC — server confirms.

      newVerifications[block.block_id] = {
        block,
        localVerdict,
        checks: { merkle: merkleValid, canonical: canonicalValid, chain: chainValid, pqc: pqcValid },
        reasons,
        computedMerkle,
        computedCanonical,
      }

      // ── Plane 2: Server authoritative verification (FVP-INV-005/006) ───────
      // Always escalate to server when public key is available — server verdict is binding.
      if (publicKey) {
        const pred = sortedBlocks.find(b => b.canonical_hash === block.predecessor_block_hash)
        const serverResult = await verifyWithServer(block, publicKey, pred)
        const sv = serverResult.verdict as VerdictState | undefined

        newVerifications[block.block_id].serverVerdict = sv

        // FVP-INV-006: Server verdict is binding — BUT ONLY for PQC-layer decisions.
        //
        // CRITICAL TRUST BOUNDARY (FVP-INV-006 scope restriction):
        // Hash/merkle/canonical checks are mathematical operations on the uploaded file bytes.
        // No server response can override a browser-detected INTEGRITY_VIOLATION — the browser
        // computed the hash from the file the user uploaded; if it doesn't match, the block is
        // tampered regardless of what any server says. Accepting a server PASS over a local
        // INTEGRITY_VIOLATION would be a trust inversion attack vector.
        //
        // Server override applies ONLY when localVerdict is INCOMPLETE (PQC not verified browser-side)
        // or PASS (server may downgrade to SIGNATURE_INVALID after definitive PQC check).
        const hashVerdicts: VerdictState[] = ['INTEGRITY_VIOLATION']
        const localIsHashReality = hashVerdicts.includes(localVerdict)

        if (sv && sv !== 'INCOMPLETE') {
          if (localIsHashReality) {
            // Hash mismatch detected by browser — server cannot override mathematical reality.
            // Record server verdict for transparency but do NOT change localVerdict.
            newVerifications[block.block_id].reasons.push(
              `SERVER returned ${sv} but browser hash check detected INTEGRITY_VIOLATION — browser result prevails (FVP-INV-006 hash exception)`
            )
          } else if (sv !== localVerdict) {
            // Server verdict differs from browser on PQC/chain/completeness — server wins.
            newVerifications[block.block_id].reasons.push(
              `SERVER (Plane 2 — authoritative): ${sv}` +
              ` [browser had: ${localVerdict}]`
            )
            newVerifications[block.block_id].localVerdict = sv
          }
        } else if (sv === 'INCOMPLETE' && serverResult.error) {
          newVerifications[block.block_id].reasons.push(
            `Server verification unavailable: ${serverResult.error}`
          )
        }

        // ── ADR-167: Key identity warning — non-platform key detected ─────────
        const ki = serverResult.key_identity
        if (ki?.warning) {
          newVerifications[block.block_id].reasons.push(
            `KEY IDENTITY: ${ki.warning}`
          )
        }
        if (ki?.matches_platform === true) {
          newVerifications[block.block_id].reasons.push(
            `KEY VERIFIED: matches OMNIX platform key (${ki.provided_fingerprint?.slice(0, 20)}…)`
          )
          setKeyMatchStatus('match')
        } else if (ki?.matches_platform === false) {
          setKeyMatchStatus('mismatch')
        }
      }
    }

    setVerifications(newVerifications)
    setLoading(false)
  }, [blocks, publicKey])

  // BigInt-safe timestamp comparator (P2-001: creation_timestamp_ns > MAX_SAFE_INTEGER)
  const safeBlockCmp = (a: BlockData, b: BlockData): number => {
    try {
      const ta = BigInt(a._rawCreationTimestampNs ?? '0')
      const tb = BigInt(b._rawCreationTimestampNs ?? '0')
      return ta < tb ? -1 : ta > tb ? 1 : 0
    } catch { return 0 }
  }

  const chartData = useMemo(() => {
    return blocks.map(b => {
      const data: any = {
        name: b.block_id,
        rawTs: b._rawCreationTimestampNs ?? String(b.creation_timestamp_ns),
        date: new Date(b.creation_timestamp_ns / 1000000).toLocaleDateString()
      }
      b.evidence_classes.forEach(cls => {
        data[cls] = (data[cls] || 0) + 1
      })
      return data
    }).sort((a, b) => {
      try {
        const ta = BigInt(a.rawTs), tb = BigInt(b.rawTs)
        return ta < tb ? -1 : ta > tb ? 1 : 0
      } catch { return 0 }
    })
  }, [blocks])

  const generateOEP = async () => {
    setLoading(true)
    setExportError(null)
    setExportSuccess(null)
    try {
      const API = import.meta.env.VITE_RAILWAY_API_URL || ''
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (exportApiKey.trim()) headers['X-API-Key'] = exportApiKey.trim()

      const res = await fetch(`${API}/api/forensic/export`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ blocks, public_key_b64: publicKey, custody_entries: [] })
      })

      if (res.ok) {
        const blob = await res.blob()
        const cdHeader = res.headers.get('Content-Disposition') || ''
        const filename = cdHeader.split('filename=')[1]?.replace(/"/g, '') || `OMNIX-PACKAGE-${Date.now()}.oep`
        const packageId  = res.headers.get('X-OEP-Package-Id')  || 'unknown'
        const keySource  = res.headers.get('X-OEP-Key-Source')  || 'unknown'
        const blockCount = res.headers.get('X-OEP-Block-Count') || String(blocks.length)
        saveAs(blob, filename)
        setExportSuccess(`${packageId} · ${blockCount} blocks · key: ${keySource} · ${filename}`)
      } else {
        const body = await res.json().catch(() => ({} as Record<string, string>))
        const code = body.code || ''
        if (res.status === 401) {
          setExportError(`Authentication required — provide an operator admin API key below. (${code})`)
          setShowApiKeyInput(true)
        } else if (res.status === 403) {
          setExportError(`Admin role required. Your key has insufficient privileges. (${code})`)
        } else if (res.status === 503) {
          setExportError(`Platform unavailable: ${body.error || 'Signing key not configured on server.'}`)
        } else if (res.status === 400) {
          setExportError(`Request error: ${body.error || 'Invalid request.'}`)
        } else {
          setExportError(`Export failed [${res.status}]: ${body.error || res.statusText}`)
        }
      }
    } catch (err) {
      setExportError(`Network error: ${String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const generateReport = () => {
    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>OMNIX Forensic Verification Report</title>
        <style>
          body { background: #060F1E; color: #e2e8f0; font-family: sans-serif; padding: 40px; }
          .container { max-width: 900px; margin: 0 auto; }
          header { border-bottom: 2px solid #C9A227; padding-bottom: 20px; margin-bottom: 30px; }
          h1 { color: #C9A227; margin: 0; }
          .block-card { background: #0A1628; border: 1px solid rgba(201,162,39,0.2); border-radius: 8px; padding: 20px; margin-bottom: 20px; }
          .verdict { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; margin-bottom: 10px; }
          .PASS { background: rgba(34,197,94,0.1); color: #22c55e; border: 1px solid #22c55e; }
          .VIOLATION { background: rgba(239,68,68,0.1); color: #ef4444; border: 1px solid #ef4444; }
          table { width: 100%; border-collapse: collapse; margin-top: 15px; }
          td, th { text-align: left; padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
          .label { color: #94a3b8; width: 200px; }
        </style>
      </head>
      <body>
        <div class="container">
          <header>
            <h1>OMNIX QUANTUM LTD</h1>
            <p>Forensic Evidence Verification Report · Generated ${new Date().toISOString()}</p>
          </header>
          ${blocks.map(b => {
            const v = verifications[b.block_id]
            const state = v?.localVerdict || 'PENDING'
            return `
              <div class="block-card">
                <div class="verdict ${state}">${state}</div>
                <h3>Block ID: ${b.block_id}</h3>
                <table>
                  <tr><td class="label">Canonical Hash</td><td>${b.canonical_hash}</td></tr>
                  <tr><td class="label">Merkle Root</td><td>${b.integrity_manifest.merkle_root}</td></tr>
                  <tr><td class="label">Predecessor</td><td>${b.predecessor_block_hash}</td></tr>
                  <tr><td class="label">Timestamp</td><td>${new Date(b.creation_timestamp_ns / 1000000).toISOString()}</td></tr>
                  <tr><td class="label">Artifacts</td><td>${b.artifact_count}</td></tr>
                </table>
              </div>
            `
          }).join('')}
        </div>
      </body>
      </html>
    `
    const blob = new Blob([html], { type: 'text/html' })
    saveAs(blob, `OMNIX-Forensic-Report-${new Date().getTime()}.html`)
  }

  return (
    <div style={{ minHeight: '100vh', background: NAVY, color: TEXT, fontFamily: 'Inter, sans-serif' }}>
      {/* ── Header ── */}
      <div style={{ borderBottom: `1px solid ${GOLD_BORDER}`, background: NAVY2 }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.14em', color: GOLD }}>OMNIX QUANTUM LTD</span>
                <span style={{ color: 'rgba(255,255,255,0.12)' }}>|</span>
                <span style={{ fontSize: 10, letterSpacing: '0.08em', color: SLATE }}>FORENSIC VERIFICATION PORTAL</span>
                <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: 'rgba(201,162,39,0.1)', border: `1px solid ${GOLD_BORDER}`, color: GOLD }}>ADR-164</span>
              </div>
              <h1 style={{ fontSize: 30, fontWeight: 800, color: TEXT, margin: '0 0 10px 0', letterSpacing: '-0.02em' }}>Forensic Archive Verifier</h1>
              <div style={{ color: SLATE, fontSize: 12, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                <span style={{ fontFamily: 'monospace' }}>EAP-INV-005</span><span>·</span>
                <span>Offline Reconstructability</span><span>·</span>
                <span style={{ fontFamily: 'monospace' }}>ML-DSA-65 (FIPS 204)</span><span>·</span>
                <span style={{ fontFamily: 'monospace' }}>ADR-163/164/165</span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <a href="/trust-infrastructure"
                style={{ fontSize: 12, color: SLATE, textDecoration: 'none', padding: '8px 14px', borderRadius: 7, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.03)' }}>
                Trust Registry ↗
              </a>
              {blocks.length > 0 && (
                <button
                  onClick={runVerification}
                  disabled={loading}
                  style={{
                    background: GOLD, color: NAVY, border: 'none', padding: '10px 22px', borderRadius: 8,
                    fontWeight: 700, cursor: 'pointer', transition: 'all 0.2s', fontSize: 13,
                    boxShadow: '0 4px 14px rgba(201,162,39,0.3)'
                  }}
                >
                  {loading ? 'Verifying…' : 'Verify Archive Integrity'}
                </button>
              )}
            </div>
          </div>

          {/* Verification plane status strip */}
          <div style={{ display: 'flex', gap: 8, marginTop: 24, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.04)', flexWrap: 'wrap' }}>
            {[
              { label: 'Plane 1 · Browser', sub: 'Merkle + Canonical hash', color: GOLD, active: true },
              { label: 'Plane 2 · Server', sub: 'ML-DSA-65 PQC authoritative', color: BLUE, active: blocks.length > 0 && Object.values(verifications).some(v => v.serverVerdict) },
              { label: 'Plane 3 · Offline OEP', sub: 'EAP-INV-005 · CLI verifiable', color: '#a855f7', active: false },
            ].map(p => (
              <div key={p.label} style={{
                display: 'flex', gap: 8, alignItems: 'center', padding: '6px 12px', borderRadius: 7,
                background: p.active ? `${p.color}12` : 'rgba(255,255,255,0.02)',
                border: `1px solid ${p.active ? `${p.color}30` : 'rgba(255,255,255,0.05)'}`,
              }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: p.active ? p.color : SLATE, flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: p.active ? p.color : SLATE }}>{p.label}</div>
                  <div style={{ fontSize: 10, color: SLATE }}>{p.sub}</div>
                </div>
              </div>
            ))}
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: SLATE }}>
              <span style={{ fontFamily: 'monospace' }}>FVP-INV-001–007</span>
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 28px' }}>

        {/* ── Platform Trust Anchor (ADR-167 / OMNIX-SEC-2026-001) ── */}
        <div style={{
          border: `1px solid ${
            keyMatchStatus === 'match' ? GREEN_BORDER :
            keyMatchStatus === 'mismatch' ? RED_BORDER :
            GOLD_BORDER
          }`,
          borderRadius: 12, marginBottom: 28,
          background: keyMatchStatus === 'match' ? GREEN_DIM :
                      keyMatchStatus === 'mismatch' ? RED_DIM : GOLD_DIM,
          overflow: 'hidden',
          transition: 'border-color 0.3s, background 0.3s',
        }}>
          {/* Header row */}
          <div
            onClick={() => setShowTrustAnchor(v => !v)}
            style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '14px 20px', cursor: 'pointer', userSelect: 'none',
            }}
          >
            <span style={{ fontSize: 18 }}>🔐</span>
            <div style={{ flex: 1 }}>
              <span style={{ fontWeight: 700, fontSize: 14, letterSpacing: '0.05em', color: GOLD }}>
                PLATFORM TRUST ANCHOR
              </span>
              <span style={{ marginLeft: 12, fontSize: 12, color: SLATE }}>
                OMNIX QUANTUM LTD · ML-DSA-65 (FIPS 204)
              </span>
            </div>
            {/* Match badge */}
            {keyMatchStatus === 'match' && (
              <span style={{
                background: GREEN, color: '#fff', fontSize: 11, fontWeight: 700,
                padding: '3px 10px', borderRadius: 20, letterSpacing: '0.06em',
              }}>✓ PLATFORM KEY MATCH</span>
            )}
            {keyMatchStatus === 'mismatch' && (
              <span style={{
                background: RED, color: '#fff', fontSize: 11, fontWeight: 700,
                padding: '3px 10px', borderRadius: 20, letterSpacing: '0.06em',
              }}>⚠ EXTERNAL KEY DETECTED</span>
            )}
            {(keyMatchStatus === 'unchecked' || keyMatchStatus === 'unknown') && (
              <span style={{
                background: 'rgba(100,116,139,0.18)', color: SLATE, fontSize: 11, fontWeight: 600,
                padding: '3px 10px', borderRadius: 20, letterSpacing: '0.04em',
              }}>Pending verification</span>
            )}
            <span style={{ color: SLATE, fontSize: 12, marginLeft: 4 }}>
              {showTrustAnchor ? '▲' : '▼'}
            </span>
          </div>

          {/* Expanded content */}
          {showTrustAnchor && (
            <div style={{ padding: '0 20px 18px', borderTop: `1px solid ${GOLD_BORDER}` }}>
              {platformKeyInfo === null ? (
                <div style={{ color: SLATE, fontSize: 13, marginTop: 14 }}>
                  Loading platform key registry…
                </div>
              ) : platformKeyInfo.status === 'not_configured' ? (
                <div style={{ color: AMBER, fontSize: 13, marginTop: 14 }}>
                  ⚠ Platform key not configured on this server instance.
                  Contact OMNIX QUANTUM LTD for the authoritative fingerprint.
                </div>
              ) : (
                <>
                  <div style={{ marginTop: 14 }}>
                    <div style={{ fontSize: 11, color: SLATE, marginBottom: 6, letterSpacing: '0.06em' }}>
                      OFFICIAL PLATFORM FINGERPRINT
                    </div>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      background: 'rgba(0,0,0,0.25)', borderRadius: 8, padding: '10px 14px',
                      border: '1px solid rgba(201,162,39,0.15)',
                    }}>
                      <code style={{
                        flex: 1, fontSize: 12, color: GOLD, fontFamily: 'monospace',
                        wordBreak: 'break-all', letterSpacing: '0.03em',
                      }}>
                        {platformKeyInfo.fingerprint ?? 'unavailable'}
                      </code>
                      <button
                        onClick={e => {
                          e.stopPropagation()
                          if (platformKeyInfo.fingerprint) {
                            navigator.clipboard.writeText(platformKeyInfo.fingerprint)
                            setFpCopied(true)
                            setTimeout(() => setFpCopied(false), 2000)
                          }
                        }}
                        style={{
                          background: fpCopied ? GREEN : 'rgba(201,162,39,0.12)',
                          border: `1px solid ${fpCopied ? GREEN_BORDER : GOLD_BORDER}`,
                          color: fpCopied ? GREEN : GOLD, borderRadius: 6,
                          padding: '4px 10px', fontSize: 11, cursor: 'pointer',
                          transition: 'all 0.2s', whiteSpace: 'nowrap', fontWeight: 600,
                        }}
                      >
                        {fpCopied ? '✓ Copied' : 'Copy'}
                      </button>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginTop: 14 }}>
                    <div style={{ fontSize: 12 }}>
                      <span style={{ color: SLATE, fontSize: 11 }}>Algorithm</span>
                      <div style={{ color: TEXT, marginTop: 2 }}>{platformKeyInfo.algorithm}</div>
                    </div>
                    <div style={{ fontSize: 12 }}>
                      <span style={{ color: SLATE, fontSize: 11 }}>DNS TXT</span>
                      <div style={{ color: TEXT, marginTop: 2, fontFamily: 'monospace', fontSize: 11 }}>
                        {platformKeyInfo.dns_txt_record?.record_name ?? '_omnix-key.omnixquantum.net'}
                      </div>
                    </div>
                    <div style={{ fontSize: 12 }}>
                      <span style={{ color: SLATE, fontSize: 11 }}>Live registry</span>
                      <div style={{ marginTop: 2 }}>
                        <a
                          href={platformKeyInfo.canonical_verification_url}
                          target="_blank" rel="noreferrer"
                          onClick={e => e.stopPropagation()}
                          style={{ color: GOLD, fontSize: 11, textDecoration: 'underline' }}
                        >
                          /api/forensic/platform-key ↗
                        </a>
                      </div>
                    </div>
                  </div>

                  {/* Key match explanation */}
                  {keyMatchStatus === 'match' && (
                    <div style={{
                      marginTop: 14, padding: '10px 14px', borderRadius: 8,
                      background: GREEN_DIM, border: `1px solid ${GREEN_BORDER}`,
                      fontSize: 13, color: GREEN,
                    }}>
                      ✓ The loaded public key matches the OMNIX platform key.
                      Trust level: <strong>OMNIX_PLATFORM</strong> — blocks are signed by OMNIX QUANTUM LTD.
                    </div>
                  )}
                  {keyMatchStatus === 'mismatch' && (
                    <div style={{
                      marginTop: 14, padding: '10px 14px', borderRadius: 8,
                      background: RED_DIM, border: `1px solid ${RED_BORDER}`,
                      fontSize: 13, color: '#fca5a5',
                    }}>
                      ⚠ The loaded key does <strong>not</strong> match the OMNIX platform key.
                      Trust level: <strong>EXTERNAL</strong> — a PASS verdict confirms cryptographic validity
                      but is <em>not</em> an endorsement by OMNIX QUANTUM LTD.
                      This is expected for demo, test, or externally-generated OEPs.
                    </div>
                  )}
                  {(keyMatchStatus === 'unchecked' || keyMatchStatus === 'unknown') && publicKey && (
                    <div style={{
                      marginTop: 14, padding: '10px 14px', borderRadius: 8,
                      background: 'rgba(100,116,139,0.08)', border: '1px solid rgba(100,116,139,0.2)',
                      fontSize: 13, color: SLATE,
                    }}>
                      Public key loaded. Run verification to determine if this is the OMNIX platform key.
                    </div>
                  )}

                  <div style={{ marginTop: 12, fontSize: 11, color: SLATE }}>
                    ADR-167 · OMNIX-SEC-2026-001 ·{' '}
                    <a href="/docs/security/PLATFORM_KEY_REGISTRY.md" style={{ color: SLATE }}
                       target="_blank" rel="noreferrer">
                      PLATFORM_KEY_REGISTRY.md
                    </a>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* ── Upload Zone ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 32 }}>
          <div
            onClick={() => blockInputRef.current?.click()}
            style={{
              border: `2px dashed ${blocks.length > 0 ? GOLD_BORDER : SLATE}`,
              borderRadius: 12, padding: '40px 20px', textAlign: 'center', cursor: 'pointer',
              background: blocks.length > 0 ? GOLD_DIM : 'transparent'
            }}
          >
            <div style={{ fontSize: 24, marginBottom: 12 }}>📦</div>
            <div style={{ fontWeight: 600 }}>{blocks.length > 0 ? `${blocks.length} Blocks Loaded` : 'Drop Block Files (.json)'}</div>
            <div style={{ fontSize: 12, color: SLATE, marginTop: 4 }}>OMNIX-BLOCK-YYYYMMDD-NNNNNN.json</div>
            <input type="file" multiple accept=".json" ref={blockInputRef} style={{ display: 'none' }} onChange={handleBlockUpload} />
          </div>

          <div
            onClick={() => keyInputRef.current?.click()}
            style={{
              border: `2px dashed ${publicKey ? GREEN_BORDER : SLATE}`,
              borderRadius: 12, padding: '40px 20px', textAlign: 'center', cursor: 'pointer',
              background: publicKey ? GREEN_DIM : 'transparent'
            }}
          >
            <div style={{ fontSize: 24, marginBottom: 12 }}>🔑</div>
            <div style={{ fontWeight: 600 }}>{publicKey ? 'Public Key Loaded' : 'Drop Public Key (.b64 / .pem)'}</div>
            <div style={{ fontSize: 12, color: SLATE, marginTop: 4 }}>
              {publicKey ? 'ML-DSA-65 Active' : 'Required for PQC signature verification'}
            </div>
            <input type="file" ref={keyInputRef} style={{ display: 'none' }} onChange={handleKeyUpload} />
          </div>
        </div>

        {/* ── Verdict Panel ── */}
        {Object.keys(verifications).length > 0 && (
          <div style={{ marginBottom: 32, padding: 24, borderRadius: 12, background: NAVY2, border: `1px solid ${GOLD_BORDER}` }}>
            <h3 style={{ margin: '0 0 20px 0', fontSize: 18, color: TEXT }}>Global Audit Verdict</h3>
            <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              {Object.values(verifications).map(v => (
                <div key={v.block.block_id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: NAVY, borderRadius: 8, border: `1px solid rgba(255,255,255,0.05)` }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>{v.block.block_id.slice(-6)}</span>
                  <Badge label={v.localVerdict} state={v.localVerdict} />
                  {v.serverVerdict && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginLeft: 8, borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: 8 }}>
                      <span style={{ fontSize: 10, color: SLATE }}>SERVER</span>
                      <Badge label={v.serverVerdict} state={v.serverVerdict} />
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {/* Conflict Banner */}
            {Object.values(verifications).some(v => v.serverVerdict && v.serverVerdict !== v.localVerdict && v.serverVerdict !== 'PASS') && (
              <div style={{ marginTop: 20, padding: 16, borderRadius: 8, background: RED_DIM, border: `1px solid ${RED_BORDER}`, color: RED }}>
                <div style={{ fontWeight: 800, marginBottom: 4 }}>CRITICAL TRUST CONFLICT (FVP-INV-006)</div>
                <div style={{ fontSize: 13 }}>Authoritative server verification failed on blocks where local checks passed. Server verdict is binding.</div>
              </div>
            )}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24, marginBottom: 32 }}>
          {/* ── Chain Map ── */}
          <div style={{ background: NAVY2, borderRadius: 12, border: `1px solid ${NAVY3}`, padding: 24 }}>
            <h4 style={{ margin: '0 0 20px 0', fontSize: 14, color: SLATE, letterSpacing: '0.05em' }}>BLOCK CHAIN GRAPH</h4>
            <div style={{ minHeight: 200, display: 'flex', alignItems: 'center', gap: 32, overflowX: 'auto', padding: '20px 0' }}>
              {/* Genesis sentinel node */}
              <div style={{ flexShrink: 0, textAlign: 'center' }}>
                <div style={{ width: 80, height: 80, borderRadius: '50%', border: `2px solid ${SLATE}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: SLATE, background: NAVY }}>GENESIS</div>
              </div>
              
              {[...blocks].sort(safeBlockCmp).map((b) => {
                const v = verifications[b.block_id]
                const colors = {
                  PASS: GREEN,
                  INTEGRITY_VIOLATION: RED,
                  CHAIN_BREAK: '#f97316',
                  SIGNATURE_INVALID: RED,
                  ORPHANED: AMBER,
                  INCOMPLETE: AMBER,
                  PENDING: SLATE
                }
                const color = colors[v?.localVerdict || 'PENDING']
                return (
                  <div key={b.block_id} style={{ display: 'flex', alignItems: 'center', gap: 32, flexShrink: 0 }}>
                    <div style={{ fontSize: 20, color: SLATE }}>→</div>
                    <div 
                      onClick={() => setActiveBlockId(b.block_id)}
                      style={{ 
                        width: 120, padding: 12, borderRadius: 8, background: NAVY, border: `2px solid ${color}`,
                        cursor: 'pointer', transition: 'transform 0.2s',
                        transform: activeBlockId === b.block_id ? 'scale(1.05)' : 'none',
                        boxShadow: activeBlockId === b.block_id ? `0 0 20px ${color}40` : 'none'
                      }}
                    >
                      <div style={{ fontSize: 11, fontWeight: 800, color }}>{b.block_id.slice(-15)}</div>
                      <div style={{ fontSize: 9, color: SLATE, marginTop: 4 }}>{new Date(b.creation_timestamp_ns/1000000).toLocaleTimeString()}</div>
                      <div style={{ fontSize: 10, color: TEXT, marginTop: 6 }}>{b.artifact_count} artifacts</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* ── Evidence Timeline ── */}
          <div style={{ background: NAVY2, borderRadius: 12, border: `1px solid ${NAVY3}`, padding: 24 }}>
            <h4 style={{ margin: '0 0 20px 0', fontSize: 14, color: SLATE, letterSpacing: '0.05em' }}>EVIDENCE CLASSES</h4>
            <div style={{ height: 200 }}>
              {chartData.length > 0 ? <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <XAxis dataKey="date" hide />
                  <Tooltip 
                    contentStyle={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 8 }}
                    itemStyle={{ fontSize: 12 }}
                  />
                  <Bar dataKey="LEGAL" stackId="a" fill={GOLD} />
                  <Bar dataKey="PQC" stackId="a" fill={PURPLE} />
                  <Bar dataKey="CONTRACT" stackId="a" fill={BLUE} />
                  <Bar dataKey="EXCEPTION" stackId="a" fill={RED} />
                  <Bar dataKey="TELEMETRY" stackId="a" fill={SLATE} />
                </BarChart>
              </ResponsiveContainer> : <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: SLATE, fontSize: 13 }}>Load blocks to see evidence class breakdown</div>}
            </div>
          </div>
        </div>

        {/* ── Block Details ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16 }}>
          {blocks.map(b => {
            const v = verifications[b.block_id]
            const isOpen = activeBlockId === b.block_id
            return (
              <div key={b.block_id} style={{ borderRadius: 12, background: NAVY2, border: `1px solid ${isOpen ? GOLD_BORDER : NAVY3}`, overflow: 'hidden' }}>
                <div 
                  onClick={() => setActiveBlockId(isOpen ? null : b.block_id)}
                  style={{ padding: '18px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                >
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                    <code style={{ fontSize: 13, fontWeight: 700, color: TEXT, fontFamily: 'monospace' }}>{b.block_id}</code>
                    <Badge label={v?.localVerdict || 'PENDING'} state={v?.localVerdict || 'PENDING'} />
                    {v?.serverVerdict && v.serverVerdict !== v.localVerdict && (
                      <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)', color: BLUE }}>SRV: {v.serverVerdict}</span>
                    )}
                    {/* Trust level badge — set after server verification */}
                    {keyMatchStatus === 'match' && v?.serverVerdict && (
                      <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: 'rgba(34,197,94,0.09)', border: `1px solid ${GREEN_BORDER}`, color: GREEN, fontWeight: 700 }}>OMNIX_PLATFORM</span>
                    )}
                    {keyMatchStatus === 'mismatch' && v?.serverVerdict && (
                      <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: 'rgba(245,158,11,0.09)', border: 'rgba(245,158,11,0.28)', color: AMBER, fontWeight: 700 }}>EXTERNAL</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 20, fontSize: 12, color: SLATE, flexShrink: 0 }}>
                    <span>{b.artifact_count} artifacts</span>
                    <span style={{ fontFamily: 'monospace' }}>{new Date(b.creation_timestamp_ns/1000000).toISOString().replace('T', ' ').slice(0, 19)} UTC</span>
                    <span style={{ color: isOpen ? GOLD : SLATE }}>{isOpen ? '▲' : '▼'}</span>
                  </div>
                </div>
                
                {isOpen && (
                  <div style={{ padding: '0 24px 24px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 40, marginTop: 20 }}>
                      <div>
                        <h5 style={{ fontSize: 11, color: GOLD, letterSpacing: '0.1em', margin: '0 0 12px 0' }}>INTEGRITY MANIFEST</h5>
                        <div style={{ fontSize: 13, marginBottom: 8 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span style={{ color: SLATE }}>Merkle Root</span>
                            <CheckIcon ok={v?.checks.merkle} />
                          </div>
                          <code style={{ fontSize: 11, color: v?.checks.merkle ? GREEN : RED, wordBreak: 'break-all' }}>{b.integrity_manifest.merkle_root}</code>
                        </div>
                        <div style={{ fontSize: 13, marginBottom: 8 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span style={{ color: SLATE }}>Canonical Hash</span>
                            <CheckIcon ok={v?.checks.canonical} />
                          </div>
                          <code style={{ fontSize: 11, color: v?.checks.canonical ? GREEN : RED, wordBreak: 'break-all' }}>{b.canonical_hash}</code>
                        </div>
                        <div style={{ fontSize: 13 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span style={{ color: SLATE }}>Chain Predecessor</span>
                            <CheckIcon ok={v?.checks.chain} />
                          </div>
                          <code style={{ fontSize: 11, color: v?.checks.chain ? GREEN : AMBER, wordBreak: 'break-all' }}>{b.predecessor_block_hash}</code>
                        </div>
                      </div>
                      
                      <div>
                        <h5 style={{ fontSize: 11, color: GOLD, letterSpacing: '0.1em', margin: '0 0 12px 0' }}>AUTHORITY MATRIX</h5>
                        {/* PQC Signature */}
                        <div style={{ fontSize: 13, marginBottom: 10 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, alignItems: 'center' }}>
                            <span style={{ color: SLATE }}>PQC Signature (ML-DSA-65)</span>
                            <CheckIcon ok={v?.checks.pqc === true} incomplete={v?.checks.pqc === 'incomplete'} />
                          </div>
                          <code style={{ fontSize: 10, color: SLATE, wordBreak: 'break-all', display: 'block', fontFamily: 'monospace' }}>{b.pqc_signature?.slice(0, 48)}…</code>
                        </div>
                        {/* Signature metadata */}
                        <div style={{ padding: '10px 12px', borderRadius: 7, background: 'rgba(0,0,0,0.25)', marginBottom: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 20px' }}>
                          {[
                            { label: 'Algorithm', value: 'ML-DSA-65' },
                            { label: 'Standard', value: 'FIPS 204 · NIST Level 3' },
                            { label: 'Key type', value: 'Dilithium-3' },
                            { label: 'Sig size', value: b.pqc_signature ? `${Math.round(b.pqc_signature.length * 3 / 4)} bytes` : 'N/A' },
                            { label: 'Trust level', value: keyMatchStatus === 'match' ? 'OMNIX_PLATFORM' : keyMatchStatus === 'mismatch' ? 'EXTERNAL' : 'UNVERIFIED' },
                            { label: 'Verification', value: v?.checks.pqc === true ? 'Server-authoritative' : v?.checks.pqc === 'incomplete' ? 'Browser best-effort' : 'Pending' },
                          ].map(row => (
                            <div key={row.label}>
                              <div style={{ fontSize: 9, color: SLATE, letterSpacing: '0.06em', marginBottom: 2 }}>{row.label.toUpperCase()}</div>
                              <div style={{ fontSize: 11, color: row.label === 'Trust level' ? (keyMatchStatus === 'match' ? GREEN : keyMatchStatus === 'mismatch' ? AMBER : SLATE) : TEXT, fontFamily: 'monospace' }}>{row.value}</div>
                            </div>
                          ))}
                        </div>
                        {/* Evidence classes */}
                        <div>
                          <span style={{ fontSize: 10, color: SLATE, letterSpacing: '0.06em' }}>EVIDENCE CLASSES</span>
                          <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                            {b.evidence_classes.map(cls => (
                              <span key={cls} style={{ fontSize: 10, padding: '3px 9px', borderRadius: 4, background: CLASS_COLORS[cls] ? `${CLASS_COLORS[cls]}22` : 'rgba(100,116,139,0.12)', color: CLASS_COLORS[cls] || SLATE, border: `1px solid ${CLASS_COLORS[cls] ? `${CLASS_COLORS[cls]}40` : 'rgba(100,116,139,0.2)'}`, fontWeight: 700 }}>{cls}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {v?.reasons.length > 0 && (
                      <div style={{ marginTop: 24, padding: 12, borderRadius: 8, background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ fontSize: 11, color: AMBER, fontWeight: 700, marginBottom: 4 }}>VERIFICATION NOTES</div>
                        {v.reasons.map((r, i) => (
                          <div key={i} style={{ fontSize: 12, color: TEXT, marginBottom: 2 }}>• {r}</div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* ── Evidence Lifecycle Status ── */}
        <div style={{ marginTop: 32, marginBottom: 32, padding: '20px 24px', borderRadius: 12, background: NAVY2, border: `1px solid rgba(255,255,255,0.05)` }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h4 style={{ margin: 0, fontSize: 12, color: SLATE, letterSpacing: '0.08em' }}>EVIDENCE LIFECYCLE — EAP-INV-001–007 · ADR-163</h4>
            <a href="/trust-infrastructure" style={{ fontSize: 11, color: SLATE, textDecoration: 'none' }}>Full reference ↗</a>
          </div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'stretch' }}>
            {[
              { tier: 'HOT', desc: 'Live receipts · PostgreSQL WAL', color: RED, active: true },
              { tier: '→', desc: '', color: SLATE, active: false, arrow: true },
              { tier: 'WARM', desc: 'Archive manifest · Hash preserved', color: AMBER, active: true },
              { tier: '→', desc: '', color: SLATE, active: false, arrow: true },
              { tier: 'COLD', desc: 'Sealed blocks · PQC-signed · Exportable', color: GOLD, active: true },
              { tier: '→', desc: '', color: SLATE, active: false, arrow: true },
              { tier: 'OEP', desc: 'Offline verifiable package · .oep bundle', color: '#06b6d4', active: blocks.length > 0 },
            ].map((t, i) => (
              t.arrow
                ? <div key={i} style={{ display: 'flex', alignItems: 'center', color: SLATE, fontSize: 16, flexShrink: 0 }}>→</div>
                : <div key={t.tier} style={{ flex: 1, padding: '10px 14px', borderRadius: 8, background: t.active ? `${t.color}10` : 'rgba(255,255,255,0.02)', border: `1px solid ${t.active ? `${t.color}30` : 'rgba(255,255,255,0.05)'}` }}>
                    <div style={{ fontSize: 12, fontWeight: 800, color: t.active ? t.color : SLATE, fontFamily: 'monospace', marginBottom: 4 }}>{t.tier}</div>
                    <div style={{ fontSize: 10, color: SLATE, lineHeight: 1.4 }}>{t.desc}</div>
                  </div>
            ))}
          </div>
          <div style={{ marginTop: 12, fontSize: 11, color: SLATE }}>
            Parquet archive segments for scale — <span style={{ color: AMBER, fontWeight: 600 }}>PLANNED · ADR-163 §7</span>. Current production uses PostgreSQL COLD block storage.
          </div>
        </div>

        {/* ── Export Controls ── */}
        <div style={{ marginTop: 40, borderTop: `1px solid rgba(255,255,255,0.05)`, paddingTop: 32 }}>

          {/* Error banner */}
          {exportError && (
            <div style={{
              marginBottom: 20, padding: '14px 20px', borderRadius: 10,
              background: 'rgba(239,68,68,0.08)', border: `1px solid ${RED_BORDER}`,
              display: 'flex', alignItems: 'flex-start', gap: 12
            }}>
              <span style={{ color: RED, fontSize: 16, flexShrink: 0 }}>✗</span>
              <div>
                <div style={{ color: RED, fontWeight: 700, fontSize: 13, marginBottom: 2 }}>Export Failed</div>
                <div style={{ color: TEXT, fontSize: 12 }}>{exportError}</div>
              </div>
              <button
                onClick={() => setExportError(null)}
                style={{ marginLeft: 'auto', background: 'none', border: 'none', color: SLATE, cursor: 'pointer', fontSize: 16 }}
              >×</button>
            </div>
          )}

          {/* Success banner */}
          {exportSuccess && (
            <div style={{
              marginBottom: 20, padding: '14px 20px', borderRadius: 10,
              background: GREEN_DIM, border: `1px solid ${GREEN_BORDER}`,
              display: 'flex', alignItems: 'center', gap: 12
            }}>
              <span style={{ color: GREEN, fontSize: 16 }}>✓</span>
              <div>
                <div style={{ color: GREEN, fontWeight: 700, fontSize: 13, marginBottom: 2 }}>OEP Package Generated</div>
                <div style={{ color: TEXT, fontSize: 11, fontFamily: 'monospace' }}>{exportSuccess}</div>
              </div>
            </div>
          )}

          {/* Operator API Key input — shown on demand or after 401 */}
          {showApiKeyInput && (
            <div style={{
              marginBottom: 20, padding: '20px 24px', borderRadius: 10,
              background: NAVY2, border: `1px solid ${GOLD_BORDER}`
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <span style={{ color: GOLD, fontSize: 13, fontWeight: 700 }}>Operator API Key</span>
                <span style={{
                  fontSize: 10, padding: '2px 8px', borderRadius: 4,
                  background: 'rgba(201,162,39,0.12)', color: GOLD, border: `1px solid ${GOLD_BORDER}`
                }}>Admin Role Required</span>
              </div>
              <div style={{ fontSize: 12, color: SLATE, marginBottom: 14 }}>
                OEP packages are signed with the OMNIX platform key and require an authorized operator credential.
                Provision keys with <code style={{ color: GOLD }}>provision_b2b_client.py --role admin</code>.
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                <input
                  type="password"
                  value={exportApiKey}
                  onChange={e => setExportApiKey(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && generateOEP()}
                  placeholder="omnix-admin-xxxxxxxxxxxx"
                  style={{
                    flex: 1, background: NAVY, border: `1px solid ${exportApiKey ? GOLD_BORDER : 'rgba(255,255,255,0.1)'}`,
                    borderRadius: 8, padding: '10px 14px', color: TEXT, fontSize: 13,
                    fontFamily: 'monospace', outline: 'none', transition: 'border-color 0.2s'
                  }}
                />
                <button
                  onClick={() => setShowApiKeyInput(false)}
                  style={{
                    background: 'none', border: `1px solid rgba(255,255,255,0.1)`, borderRadius: 8,
                    color: SLATE, padding: '10px 16px', cursor: 'pointer', fontSize: 12
                  }}
                >Hide</button>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 16, flexWrap: 'wrap' }}>
            <button
              onClick={generateReport}
              style={{
                background: 'transparent', color: TEXT, border: `1px solid ${SLATE}`,
                padding: '12px 24px', borderRadius: 8, fontWeight: 600, cursor: 'pointer'
              }}
            >
              Download Verification Report (HTML)
            </button>

            <button
              onClick={() => { setShowApiKeyInput(v => !v); setExportError(null) }}
              style={{
                background: 'transparent', color: GOLD,
                border: `1px solid ${GOLD_BORDER}`, padding: '12px 20px', borderRadius: 8,
                fontWeight: 600, cursor: 'pointer', fontSize: 13,
                display: 'flex', alignItems: 'center', gap: 8
              }}
            >
              <span style={{ fontSize: 12 }}>🔑</span>
              {showApiKeyInput ? 'Hide Key' : 'Set Operator Key'}
            </button>

            <button
              onClick={generateOEP}
              disabled={loading || blocks.length === 0}
              style={{
                background: blocks.length > 0 ? GOLD : 'rgba(201,162,39,0.3)',
                color: NAVY, border: 'none', padding: '12px 28px', borderRadius: 8,
                fontWeight: 700, cursor: blocks.length > 0 ? 'pointer' : 'not-allowed',
                boxShadow: blocks.length > 0 ? '0 4px 14px rgba(201,162,39,0.25)' : 'none',
                transition: 'all 0.2s', display: 'flex', alignItems: 'center', gap: 8
              }}
            >
              {loading ? (
                <>Generating…</>
              ) : (
                <>Generate OEP Bundle <span style={{ fontSize: 11, opacity: 0.7 }}>.oep</span></>
              )}
            </button>
          </div>

          {/* Footer */}
          <div style={{ textAlign: 'center', marginTop: 28, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.04)', fontSize: 11, color: SLATE }}>
            <div style={{ marginBottom: 8 }}>ADR-163 · ADR-164 · ADR-165 · ADR-166 · ADR-167 · ML-DSA-65 (FIPS 204) · 3-plane verification (FVP-INV-001–007)</div>
            <div>
              <a href="/trust-infrastructure" style={{ color: GOLD, textDecoration: 'none' }}>Platform Trust Registry ↗</a>
              <span style={{ margin: '0 12px', color: 'rgba(255,255,255,0.08)' }}>|</span>
              <a href="/protocol" style={{ color: SLATE, textDecoration: 'none' }}>Protocol Architecture</a>
              <span style={{ margin: '0 12px', color: 'rgba(255,255,255,0.08)' }}>|</span>
              <a href="/atf-verify" style={{ color: SLATE, textDecoration: 'none' }}>ATF Verifier</a>
              <span style={{ margin: '0 12px', color: 'rgba(255,255,255,0.08)' }}>|</span>
              <a href="/verify-independently" style={{ color: SLATE, textDecoration: 'none' }}>Independent Verification</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

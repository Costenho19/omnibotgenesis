import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

// S5 duration: 15000ms
// Narrative: Independent verification. Zero OMNIX access. Zero trust required.
// A third party runs verify_pogc_offline.py and gets exit code 1 — tamper detected.

const TERMINAL_LINES = [
  { text: '$ python verify_pogc_offline.py evidence_package.json', type: 'cmd',    delay: 400 },
  { text: '',                                                                        type: 'blank',  delay: 1000 },
  { text: 'OMNIX Proof-of-Governance Verifier v2.0',                               type: 'info',   delay: 1200 },
  { text: 'Running 7 checks — zero external dependencies',                         type: 'info',   delay: 1900 },
  { text: '',                                                                        type: 'blank',  delay: 2400 },
  { text: '[1/7] Certificate ID ......... POGC-EXT-A7F3C2B1D9E4F508   ✓',         type: 'pass',   delay: 2700 },
  { text: '[2/7] Algorithm .............. ML-DSA-65 (FIPS 204)        ✓',         type: 'pass',   delay: 3600 },
  { text: '[3/7] Hash chain ............. SHA3-256 · intact           ✓',         type: 'pass',   delay: 4500 },
  { text: '[4/7] PQC Signature .......... VERIFIED                    ✓',         type: 'pass',   delay: 5400 },
  { text: '[5/7] Mandate ................ MANDATE-BOUND               ✓',         type: 'pass',   delay: 6300 },
  { text: '[6/7] Compliance ............. EU AI Act · MiCA · DORA     ✓',         type: 'pass',   delay: 7200 },
  { text: '[7/7] Component integrity .... GCFR hash mismatch          ✗',         type: 'fail',   delay: 8400 },
  { text: '',                                                                        type: 'blank',  delay: 9000 },
  { text: 'VERDICT: TAMPER DETECTED — evidence package is invalid',                type: 'verdict',delay: 9300 },
  { text: 'Exit code: 1',                                                           type: 'exit1',  delay: 10200 },
];

export function Scene5() {
  const [visibleLines, setVisibleLines] = useState(0);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const timers = TERMINAL_LINES.map((line, i) =>
      setTimeout(() => setVisibleLines(i + 1), line.delay)
    );
    const bannerTimer = setTimeout(() => setShowBanner(true), 12000);
    return () => {
      timers.forEach(t => clearTimeout(t));
      clearTimeout(bannerTimer);
    };
  }, []);

  const getColor = (type: string) => {
    switch (type) {
      case 'cmd':     return '#D4A843';
      case 'pass':    return '#4ade80';
      case 'fail':    return '#E53E3E';
      case 'verdict': return '#E53E3E';
      case 'exit1':   return '#E53E3E';
      case 'info':    return 'rgba(200,200,208,0.55)';
      default:        return 'rgba(200,200,208,0.7)';
    }
  };

  return (
    <motion.div
      className="absolute inset-0 flex flex-col justify-center"
      style={{ padding: '0 8vw' }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.7 }}
    >
      {/* CRT scanlines */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.15) 3px, rgba(0,0,0,0.15) 4px)',
          pointerEvents: 'none',
          opacity: 0.25,
        }}
      />

      {/* Top label */}
      <motion.p
        style={{
          position: 'absolute',
          top: '10%',
          fontFamily: "'Plus Jakarta Sans', sans-serif",
          fontSize: '1.1vw',
          color: 'rgba(200,200,208,0.4)',
          letterSpacing: '0.3em',
          fontWeight: 600,
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.6 }}
      >
        INDEPENDENT VERIFICATION — ZERO OMNIX DEPENDENCIES
      </motion.p>

      {/* Terminal */}
      <div
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '1.55vw',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.9vh',
          position: 'relative',
          zIndex: 10,
        }}
      >
        {TERMINAL_LINES.slice(0, visibleLines).map((line, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.15 }}
            style={{ color: getColor(line.type), fontWeight: line.type === 'verdict' || line.type === 'exit1' ? 700 : 400 }}
          >
            {line.text || '\u00A0'}
          </motion.div>
        ))}

        {/* Blinking cursor */}
        {visibleLines < TERMINAL_LINES.length && (
          <motion.span
            style={{
              display: 'inline-block',
              width: '0.8vw',
              height: '1.8vw',
              backgroundColor: '#D4A843',
              marginLeft: '0.2vw',
              verticalAlign: 'middle',
            }}
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
          />
        )}
      </div>

      {/* Banner */}
      <motion.div
        style={{
          position: 'absolute',
          bottom: '8%',
          left: '8vw',
          borderLeft: '3px solid #D4A843',
          paddingLeft: '2vw',
        }}
        initial={{ opacity: 0, x: -20 }}
        animate={showBanner ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      >
        <p
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '1.8vw',
            fontWeight: 800,
            color: '#D4A843',
            letterSpacing: '0.15em',
          }}
        >
          ZERO OMNIX DEPENDENCIES
        </p>
        <p
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '1vw',
            color: 'rgba(200,200,208,0.45)',
            letterSpacing: '0.1em',
            marginTop: '0.5vh',
          }}
        >
          pip install oqs-python &nbsp;·&nbsp; python verify_pogc_offline.py &nbsp;·&nbsp; exit code tells all
        </p>
      </motion.div>
    </motion.div>
  );
}

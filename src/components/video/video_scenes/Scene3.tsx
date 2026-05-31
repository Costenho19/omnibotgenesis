import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect, useState } from 'react';

// S3 duration: 18000ms
// Narrative: 9 governance steps · 187 checks · MANDATE-BOUND · FULL ADMISSION

const STEPS = [
  { label: 'INTAKE VALIDATION',       sub: 'Predicate formation · IAD' },
  { label: 'PQC SIGNATURE VERIFIED',  sub: 'ML-DSA-65 · GCFR-96D8BA6CA0FF4295' },
  { label: 'MANDATE BINDING',         sub: 'SESSION-B9199C8CC9394304 · pre-execution' },
  { label: 'SCOPE AUTHORIZATION',     sub: 'SAR · domain: trading' },
  { label: 'AVM APPROVAL',            sub: 'Adaptive Veto Machine · drift within bounds' },
  { label: 'EXECUTION INTEGRITY',     sub: 'ADR-131 · chain completeness score' },
  { label: 'BEV CONFORMANCE',         sub: 'Behavioral Anchor Record · 0 violations' },
  { label: 'SETTLEMENT GATE',         sub: 'OSG validation · append-only receipt' },
  { label: 'PROOF OF GOVERNANCE',     sub: 'POGC-EXT-A7F3C2B1D9E4F508 · issued' },
];

export function Scene3() {
  const [phase, setPhase] = useState(0);
  const [showBadge, setShowBadge] = useState(false);
  const count = useMotionValue(0);
  const rounded = useTransform(count, Math.round);

  useEffect(() => {
    const stepTimers = STEPS.map((_, i) =>
      setTimeout(() => setPhase(i + 1), 800 + i * 900)
    );
    const counterTimer = setTimeout(() => {
      animate(count, 187, { duration: 4, ease: 'easeOut' });
    }, 1200);
    const badgeTimer = setTimeout(() => setShowBadge(true), 11000);

    return () => {
      stepTimers.forEach(t => clearTimeout(t));
      clearTimeout(counterTimer);
      clearTimeout(badgeTimer);
    };
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex"
      initial={{ opacity: 0, x: 60 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -60 }}
      transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Left panel — steps */}
      <div
        className="flex flex-col justify-center"
        style={{
          width: '60%',
          height: '100%',
          backgroundColor: '#030305',
          borderRight: '1px solid rgba(212,168,67,0.12)',
          padding: '0 5vw',
          position: 'relative',
        }}
      >
        {/* Vertical amber rule */}
        <div
          style={{
            position: 'absolute',
            left: '4vw',
            top: '10%',
            bottom: '10%',
            width: '1px',
            backgroundColor: 'rgba(212,168,67,0.25)',
          }}
        />

        <div style={{ paddingLeft: '1.5vw', display: 'flex', flexDirection: 'column', gap: '2.2vh' }}>
          {STEPS.map((step, i) => (
            <motion.div
              key={i}
              style={{ display: 'flex', alignItems: 'flex-start', gap: '1.8vw' }}
              initial={{ opacity: 0.08, x: -12 }}
              animate={phase > i ? { opacity: 1, x: 0 } : { opacity: 0.08, x: -12 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              {/* Checkmark */}
              <div style={{ width: '1.6vw', height: '1.6vw', flexShrink: 0, marginTop: '0.2vh' }}>
                {phase > i ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="#D4A843" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="rgba(212,168,67,0.2)" strokeWidth="1.5">
                    <circle cx="12" cy="12" r="8" />
                  </svg>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3vh' }}>
                <span
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: '1.5vw',
                    color: phase > i ? '#C8C8D0' : 'rgba(200,200,208,0.2)',
                    fontWeight: phase > i ? 600 : 400,
                    letterSpacing: '0.06em',
                  }}
                >
                  {step.label}
                </span>
                {phase > i && (
                  <motion.span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: '0.9vw',
                      color: 'rgba(200,200,208,0.38)',
                      letterSpacing: '0.04em',
                    }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.4, delay: 0.2 }}
                  >
                    {step.sub}
                  </motion.span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Right panel — counter + badge */}
      <div
        style={{
          width: '40%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '3vh',
          position: 'relative',
        }}
      >
        {/* Counter */}
        <div style={{ textAlign: 'center' }}>
          <motion.h1
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '11vw',
              fontWeight: 700,
              color: '#ffffff',
              lineHeight: 1,
            }}
          >
            {rounded}
          </motion.h1>
          <p
            style={{
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: '1.1vw',
              fontWeight: 700,
              color: '#C8C8D0',
              letterSpacing: '0.3em',
              marginTop: '1.5vh',
            }}
          >
            CHECKS VERIFIED
          </p>
        </div>

        {/* MANDATE-BOUND badge */}
        <motion.div
          style={{
            border: '1px solid rgba(212,168,67,0.5)',
            padding: '1.2vh 2.5vw',
            textAlign: 'center',
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={showBadge ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <p
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '1.4vw',
              color: '#D4A843',
              fontWeight: 700,
              letterSpacing: '0.15em',
            }}
          >
            MANDATE-BOUND
          </p>
          <p
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '0.9vw',
              color: 'rgba(200,200,208,0.4)',
              letterSpacing: '0.1em',
              marginTop: '0.5vh',
            }}
          >
            FULL ADMISSION
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
}

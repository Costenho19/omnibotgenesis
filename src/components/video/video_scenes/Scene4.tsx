import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { OmnixLogo } from '../OmnixLogo';

// S4 duration: 15000ms
// Narrative: Adversarial tamper attempt. Hash mutated.
// Logo OMNIX permanece INTACTO mientras los artefactos fallan — integridad del protocolo.

export function Scene4() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 600),   // intro label
      setTimeout(() => setPhase(2), 2000),  // hash appears + logo intacto
      setTimeout(() => setPhase(3), 3200),  // mutation label
      setTimeout(() => setPhase(4), 4200),  // strike through
      setTimeout(() => setPhase(5), 5200),  // HASH FAIL
      setTimeout(() => setPhase(6), 6200),  // SIG FAIL
      setTimeout(() => setPhase(7), 7200),  // scanner
      setTimeout(() => setPhase(8), 9500),  // HALT PROVEN
      setTimeout(() => setPhase(9), 11500), // bottom explanation
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex"
      style={{ backgroundColor: '#0a0102' }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Left panel: logo INTACTO + "Protocol Intact" */}
      <motion.div
        style={{
          width: '30%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '2vh',
          borderRight: '1px solid rgba(212,168,67,0.15)',
          padding: '0 2vw',
        }}
        initial={{ opacity: 0, x: -20 }}
        animate={phase >= 2 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
        transition={{ duration: 0.7 }}
      >
        {/* Logo con glow verde (integridad) */}
        <motion.div
          animate={
            phase >= 5
              ? {
                  filter: [
                    'drop-shadow(0 0 0px rgba(212,168,67,0))',
                    'drop-shadow(0 0 18px rgba(74,222,128,0.6))',
                    'drop-shadow(0 0 8px rgba(74,222,128,0.3))',
                  ],
                }
              : { filter: 'drop-shadow(0 0 0px rgba(212,168,67,0))' }
          }
          transition={{ duration: 1, ease: 'easeOut' }}
        >
          <OmnixLogo size="14vw" glow opacity={1} />
        </motion.div>

        <motion.div style={{ textAlign: 'center' }}>
          <p
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '1.1vw',
              color: phase >= 5 ? '#4ade80' : 'rgba(200,200,208,0.4)',
              letterSpacing: '0.15em',
              fontWeight: 600,
              transition: 'color 0.6s ease',
            }}
          >
            {phase >= 5 ? '✓ PROTOCOL INTACT' : 'PROTOCOL'}
          </p>
          <p
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '0.8vw',
              color: 'rgba(200,200,208,0.3)',
              letterSpacing: '0.1em',
              marginTop: '0.5vh',
            }}
          >
            ML-DSA-65 · unmodified
          </p>
        </motion.div>
      </motion.div>

      {/* Right panel: tamper content */}
      <div
        style={{
          width: '70%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          padding: '0 4vw',
        }}
      >
        {/* Scanner sweep */}
        {phase >= 7 && phase < 9 && (
          <motion.div
            className="absolute left-0 right-0 pointer-events-none"
            style={{
              height: '16vh',
              background: 'linear-gradient(to bottom, transparent, rgba(229,62,62,0.15), transparent)',
              zIndex: 1,
            }}
            initial={{ top: '-18vh' }}
            animate={{ top: '115vh' }}
            transition={{ duration: 1.4, ease: 'linear', repeat: 2 }}
          />
        )}

        {/* Top label */}
        <motion.p
          style={{
            position: 'absolute',
            top: '13%',
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '1.2vw',
            color: 'rgba(229,62,62,0.6)',
            letterSpacing: '0.3em',
            fontWeight: 600,
          }}
          initial={{ opacity: 0 }}
          animate={phase >= 1 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.6 }}
        >
          ADVERSARIAL SCENARIO — TAMPER ATTEMPT
        </motion.p>

        {/* GCFR hash block */}
        <div style={{ position: 'relative', zIndex: 10, marginBottom: '5vh' }}>
          <motion.div
            style={{ position: 'relative' }}
            initial={{ opacity: 0, y: 20 }}
            animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.6 }}
          >
            <p
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '1.3vw',
                color: 'rgba(200,200,208,0.4)',
                letterSpacing: '0.15em',
                marginBottom: '0.5vh',
              }}
            >
              gcfr_id:
            </p>
            <p
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '3.2vw',
                color: '#ffffff',
                letterSpacing: '0.08em',
                fontWeight: 700,
              }}
            >
              GCFR-96D8BA6CA0FF4295
            </p>
          </motion.div>

          {/* Mutation label */}
          <motion.p
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '1.1vw',
              color: '#E53E3E',
              letterSpacing: '0.15em',
              marginTop: '1.2vh',
            }}
            initial={{ opacity: 0 }}
            animate={phase >= 3 ? { opacity: 1 } : { opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            component_hash mutated → FF4295 → 000000
          </motion.p>

          {/* Red strike */}
          {phase >= 4 && (
            <svg
              style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                overflow: 'visible',
              }}
              preserveAspectRatio="none"
            >
              <motion.line
                x1="0%" y1="88%" x2="100%" y2="18%"
                stroke="#E53E3E"
                strokeWidth="5"
                strokeLinecap="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.45, ease: 'easeOut' }}
              />
            </svg>
          )}
        </div>

        {/* FAIL messages */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-start',
            gap: '2vh',
            zIndex: 10,
            marginBottom: '5vh',
          }}
        >
          <motion.p
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '2.2vw',
              fontWeight: 700,
              color: '#E53E3E',
              letterSpacing: '0.1em',
            }}
            initial={{ opacity: 0, x: -50 }}
            animate={phase >= 5 ? { opacity: 1, x: 0 } : { opacity: 0, x: -50 }}
            transition={{ duration: 0.4 }}
          >
            ✗ &nbsp; INT-ADM-GCFR-HASH FAIL
          </motion.p>
          <motion.p
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '2.2vw',
              fontWeight: 700,
              color: '#E53E3E',
              letterSpacing: '0.1em',
            }}
            initial={{ opacity: 0, x: 50 }}
            animate={phase >= 6 ? { opacity: 1, x: 0 } : { opacity: 0, x: 50 }}
            transition={{ duration: 0.4 }}
          >
            ✗ &nbsp; INT-ADM-GCFR-SIG FAIL
          </motion.p>
        </div>

        {/* HALT PROVEN */}
        <motion.div
          style={{ position: 'relative', zIndex: 20 }}
          initial={{ opacity: 0, scale: 0.6 }}
          animate={phase >= 8 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.6 }}
          transition={{ type: 'spring', stiffness: 300, damping: 22 }}
        >
          <div
            style={{
              backgroundColor: '#D4A843',
              transform: 'skewX(-8deg)',
              position: 'absolute',
              inset: '-1.2vh -1.5vw',
              borderRadius: '2px',
            }}
          />
          <h2
            style={{
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: '6vw',
              fontWeight: 900,
              color: '#050508',
              lineHeight: 1,
              position: 'relative',
              padding: '0 1.5vw',
              letterSpacing: '0.05em',
            }}
          >
            HALT PROVEN
          </h2>
        </motion.div>

        {/* Explanation */}
        <motion.div
          style={{ position: 'absolute', bottom: '8%', textAlign: 'center' }}
          initial={{ opacity: 0 }}
          animate={phase >= 9 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.8 }}
        >
          <p
            style={{
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: '1.05vw',
              color: 'rgba(200,200,208,0.45)',
              letterSpacing: '0.12em',
            }}
          >
            The protocol proved the halt — without accessing any OMNIX server.
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
}

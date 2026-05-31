import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

// S2 duration: 15000ms
// Narrative: The OMNIX Governance Contract — sealed with ML-DSA-65 BEFORE Turn 0.
// "Before the AI moved a single dollar, a cryptographic contract was sealed."

export function Scene2() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),   // headline
      setTimeout(() => setPhase(2), 1800),  // divider
      setTimeout(() => setPhase(3), 2600),  // line 1
      setTimeout(() => setPhase(4), 3600),  // line 2
      setTimeout(() => setPhase(5), 4600),  // line 3
      setTimeout(() => setPhase(6), 5600),  // line 4
      setTimeout(() => setPhase(7), 6800),  // line 5
      setTimeout(() => setPhase(8), 8000),  // line 6
      setTimeout(() => setPhase(9), 10000), // bottom statement
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  const lines = [
    { label: 'session',    value: 'SESSION-B9199C8CC9394304' },
    { label: 'algorithm',  value: 'ML-DSA-65 (FIPS 204 · Dilithium-3)' },
    { label: 'sealed',     value: 'BEFORE TURN 0  —  T-minus 0ms' },
    { label: 'mandate',    value: 'MANDATE-BOUND' },
    { label: 'checks',     value: '187 verification points' },
    { label: 'compliance', value: 'EU AI Act Art.9 · MiCA · DORA · NIST AU-2' },
  ];

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.7 }}
    >
      {/* Scrolling grid background */}
      <motion.div
        className="absolute inset-0"
        style={{
          backgroundImage:
            'linear-gradient(rgba(212,168,67,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(212,168,67,0.06) 1px, transparent 1px)',
          backgroundSize: '5vw 5vw',
        }}
        animate={{ backgroundPositionY: ['0px', '80px'] }}
        transition={{ duration: 6, ease: 'linear', repeat: Infinity }}
      />

      {/* Top label */}
      <motion.div
        className="absolute"
        style={{ top: '14%' }}
        initial={{ opacity: 0, y: -12 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -12 }}
        transition={{ duration: 0.6 }}
      >
        <p
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '1.1vw',
            color: 'rgba(200,200,208,0.45)',
            letterSpacing: '0.3em',
            fontWeight: 600,
          }}
        >
          BEFORE THE AI MOVED A SINGLE DOLLAR
        </p>
      </motion.div>

      {/* Headline */}
      <div style={{ overflow: 'hidden', marginBottom: '3vh', position: 'relative', zIndex: 10 }}>
        <motion.h2
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '2.8vw',
            fontWeight: 800,
            letterSpacing: '0.4em',
            color: '#D4A843',
          }}
          initial={{ y: '100%' }}
          animate={phase >= 1 ? { y: 0 } : { y: '100%' }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          GOVERNANCE CONTRACT
        </motion.h2>
      </div>

      {/* Divider */}
      <motion.div
        style={{ width: '58vw', height: '1px', backgroundColor: '#D4A843', marginBottom: '5vh', position: 'relative', zIndex: 10 }}
        initial={{ scaleX: 0 }}
        animate={phase >= 2 ? { scaleX: 1 } : { scaleX: 0 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
      />

      {/* Code block */}
      <div
        style={{
          width: '58vw',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '1.65vw',
          display: 'flex',
          flexDirection: 'column',
          gap: '2vh',
          position: 'relative',
          zIndex: 10,
        }}
      >
        {lines.map((line, i) => (
          <motion.div
            key={i}
            style={{ display: 'flex', gap: '1.5vw', alignItems: 'center' }}
            initial={{ opacity: 0, x: -20 }}
            animate={phase >= i + 3 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          >
            <span style={{ color: 'rgba(212,168,67,0.55)', minWidth: '9vw' }}>
              {line.label}:
            </span>
            <span style={{ color: line.label === 'mandate' ? '#D4A843' : '#C8C8D0', fontWeight: line.label === 'mandate' ? 700 : 400 }}>
              {line.value}
            </span>
          </motion.div>
        ))}
      </div>

      {/* Bottom statement */}
      <motion.div
        style={{ position: 'absolute', bottom: '10%', textAlign: 'center' }}
        initial={{ opacity: 0, y: 20 }}
        animate={phase >= 9 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <div
          style={{
            borderLeft: '3px solid #D4A843',
            paddingLeft: '2vw',
          }}
        >
          <p
            style={{
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: '1.3vw',
              color: 'rgba(200,200,208,0.7)',
              fontWeight: 500,
              letterSpacing: '0.05em',
            }}
          >
            Sealed with post-quantum cryptography.
          </p>
          <p
            style={{
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: '1.3vw',
              color: 'rgba(200,200,208,0.7)',
              fontWeight: 500,
              letterSpacing: '0.05em',
              marginTop: '0.5vh',
            }}
          >
            Verifiable by anyone. Forever. Offline.
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
}

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

// S6 duration: 12000ms
// Narrative: The trust layer. First Proof of Governance Registry in the world.
// "The SSL for AI decisions."

export function Scene6() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),   // company
      setTimeout(() => setPhase(2), 1800),  // divider
      setTimeout(() => setPhase(3), 2800),  // POGC genesis
      setTimeout(() => setPhase(4), 4200),  // tagline
      setTimeout(() => setPhase(5), 6000),  // regulations
      setTimeout(() => setPhase(6), 8000),  // CTA
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Ambient glow */}
      <motion.div
        style={{
          position: 'absolute',
          width: '70vw',
          height: '70vw',
          borderRadius: '50%',
          backgroundColor: '#D4A843',
          filter: 'blur(120px)',
          opacity: 0.04,
        }}
        animate={{ scale: [1, 1.08, 1], opacity: [0.04, 0.07, 0.04] }}
        transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* Floating particles */}
      {Array.from({ length: 18 }).map((_, i) => (
        <motion.div
          key={i}
          style={{
            position: 'absolute',
            width: 3,
            height: 3,
            borderRadius: '50%',
            backgroundColor: '#D4A843',
          }}
          initial={{
            x: `${Math.random() * 90 + 5}vw`,
            y: '108vh',
            opacity: 0.2 + Math.random() * 0.3,
          }}
          animate={{ y: '-8vh' }}
          transition={{
            duration: 9 + Math.random() * 6,
            repeat: Infinity,
            delay: Math.random() * 8,
            ease: 'linear',
          }}
        />
      ))}

      <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0' }}>
        {/* Company name */}
        <div style={{ overflow: 'hidden', marginBottom: '2.5vh' }}>
          <motion.h1
            style={{
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: '5.5vw',
              fontWeight: 900,
              color: '#ffffff',
              letterSpacing: '0.25em',
            }}
            initial={{ y: '100%' }}
            animate={phase >= 1 ? { y: 0 } : { y: '100%' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            OMNIX QUANTUM LTD
          </motion.h1>
        </div>

        {/* Amber divider */}
        <motion.div
          style={{ width: '38vw', height: '1px', backgroundColor: '#D4A843', marginBottom: '3.5vh' }}
          initial={{ scaleX: 0 }}
          animate={phase >= 2 ? { scaleX: 1 } : { scaleX: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        />

        {/* POGC genesis */}
        <motion.div
          style={{ textAlign: 'center', marginBottom: '2vh' }}
          initial={{ opacity: 0, y: 12 }}
          animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 12 }}
          transition={{ duration: 0.6 }}
        >
          <p
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '1.6vw',
              color: '#C8C8D0',
              letterSpacing: '0.12em',
            }}
          >
            POGC-GENESIS-E071CC96
          </p>
          <p
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '0.9vw',
              color: 'rgba(200,200,208,0.35)',
              letterSpacing: '0.1em',
              marginTop: '0.6vh',
            }}
          >
            First Proof of Governance Certificate · Issued 2026-05-26
          </p>
        </motion.div>

        {/* Tagline */}
        <motion.div
          style={{
            padding: '1.5vh 3vw',
            border: '1px solid rgba(212,168,67,0.35)',
            marginBottom: '3vh',
          }}
          initial={{ opacity: 0, scale: 0.94 }}
          animate={phase >= 4 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.94 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        >
          <p
            style={{
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: '1.5vw',
              fontWeight: 700,
              color: '#D4A843',
              letterSpacing: '0.12em',
              textAlign: 'center',
            }}
          >
            THE SSL FOR AI DECISIONS
          </p>
        </motion.div>

        {/* Regulations */}
        <motion.p
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '1.05vw',
            color: 'rgba(200,200,208,0.4)',
            letterSpacing: '0.1em',
            textAlign: 'center',
          }}
          initial={{ opacity: 0 }}
          animate={phase >= 5 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.7 }}
        >
          EU AI Act Art. 9 &amp; 11 &nbsp;·&nbsp; MiCA Title VI &nbsp;·&nbsp; DORA Art. 11 &nbsp;·&nbsp; NIST AU-2
        </motion.p>
      </div>

      {/* CTA */}
      <motion.div
        style={{ position: 'absolute', bottom: '7%', textAlign: 'center' }}
        initial={{ opacity: 0, y: 14 }}
        animate={phase >= 6 ? { opacity: 1, y: 0 } : { opacity: 0, y: 14 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      >
        <p
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '1.1vw',
            color: 'rgba(200,200,208,0.35)',
            letterSpacing: '0.2em',
          }}
        >
          omnixquantum.com &nbsp;·&nbsp; Decision Governance Infrastructure &nbsp;·&nbsp; 2026
        </p>
      </motion.div>
    </motion.div>
  );
}

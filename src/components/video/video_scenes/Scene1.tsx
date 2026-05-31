import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

// S1 duration: 15000ms
// Narrative: Hook for someone who has never heard of OMNIX.
// "AI just moved $50M. Alone. No trace. No accountability."

export function Scene1() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 400),   // hook line 1
      setTimeout(() => setPhase(2), 2000),  // amount
      setTimeout(() => setPhase(3), 4500),  // descriptor
      setTimeout(() => setPhase(4), 7000),  // "No audit trail"
      setTimeout(() => setPhase(5), 9500),  // red question + accountability
      setTimeout(() => setPhase(6), 12500), // OMNIX teaser
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Top hook — universally legible */}
      <motion.div
        className="absolute"
        style={{ top: '18%' }}
        initial={{ opacity: 0, y: -16 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -16 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <p
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '1.6vw',
            fontWeight: 500,
            color: 'rgba(200,200,208,0.55)',
            letterSpacing: '0.25em',
            textAlign: 'center',
          }}
        >
          AN AI JUST EXECUTED A CROSS-BORDER TRADE
        </p>
      </motion.div>

      {/* Amber divider */}
      <motion.div
        className="absolute left-0 right-0 h-[1px] origin-left"
        style={{ top: '48%', backgroundColor: '#D4A843' }}
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
      />

      {/* USD Amount */}
      <motion.div
        style={{ position: 'relative', zIndex: 10, marginTop: '-1vh' }}
        initial={{ opacity: 0.2, y: 20 }}
        animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0.2, y: 20 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <h1
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '10vw',
            fontWeight: 700,
            color: '#ffffff',
            letterSpacing: '-0.02em',
            lineHeight: 1,
          }}
        >
          USD 50,000,000
        </h1>
      </motion.div>

      {/* Descriptor */}
      <motion.div
        style={{ position: 'relative', zIndex: 10, marginTop: '3vh' }}
        initial={{ opacity: 0 }}
        animate={phase >= 3 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.7 }}
      >
        <p
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '1.5vw',
            color: '#C8C8D0',
            letterSpacing: '0.18em',
          }}
        >
          SWIFT MT202 &nbsp;·&nbsp; XRPL RLUSD &nbsp;·&nbsp; QUANTUMBANK TRADING DESK
        </p>
      </motion.div>

      {/* No audit trail */}
      <motion.div
        style={{ position: 'relative', zIndex: 10, marginTop: '2.5vh' }}
        initial={{ opacity: 0, y: 10 }}
        animate={phase >= 4 ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
        transition={{ duration: 0.6 }}
      >
        <p
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '1.4vw',
            fontWeight: 600,
            color: 'rgba(229,62,62,0.85)',
            letterSpacing: '0.2em',
          }}
        >
          NO HUMAN SIGN-OFF &nbsp;·&nbsp; NO AUDIT TRAIL &nbsp;·&nbsp; NO ACCOUNTABILITY
        </p>
      </motion.div>

      {/* ? + accountability question */}
      <motion.div
        style={{ position: 'absolute', bottom: '22%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5vh' }}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={phase >= 5 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.8 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '5vw',
            color: '#E53E3E',
            fontWeight: 700,
            lineHeight: 1,
          }}
        >
          ?
        </span>
        <span
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '1.2vw',
            color: 'rgba(200,200,208,0.5)',
            letterSpacing: '0.15em',
          }}
        >
          IF THE AI FAILS — WHO IS ACCOUNTABLE?
        </span>
      </motion.div>

      {/* OMNIX teaser */}
      <motion.div
        style={{ position: 'absolute', bottom: '6%' }}
        initial={{ opacity: 0 }}
        animate={phase >= 6 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 1, ease: 'easeInOut' }}
      >
        <p
          style={{
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            fontSize: '1vw',
            color: '#D4A843',
            letterSpacing: '0.35em',
            fontWeight: 600,
          }}
        >
          OMNIX QUANTUM · DECISION GOVERNANCE INFRASTRUCTURE
        </p>
      </motion.div>
    </motion.div>
  );
}

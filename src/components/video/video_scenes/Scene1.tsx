import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const CHARS = 'USD 50,000,000'.split('');

export function Scene1() {
  const [revealed, setRevealed] = useState(false);
  const [showSub, setShowSub] = useState(false);
  const [showQ, setShowQ] = useState(false);

  useEffect(() => {
    const t1 = setTimeout(() => setRevealed(true), 200);
    const t2 = setTimeout(() => setShowSub(true), 1400);
    const t3 = setTimeout(() => setShowQ(true), 2600);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Amber divider line */}
      <motion.div
        className="absolute left-0 right-0 h-[1px] bg-[#D4A843] origin-left"
        style={{ top: '48%' }}
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
      />

      {/* USD Amount — always visible, staggered reveal */}
      <div className="relative z-10" style={{ marginTop: '-2vh' }}>
        <h1
          className="leading-none"
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '9vw',
            fontWeight: 700,
            color: '#ffffff',
            letterSpacing: '-0.02em',
          }}
        >
          {CHARS.map((char, i) => (
            <motion.span
              key={i}
              className="inline-block"
              initial={{ opacity: 0.25, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.45,
                delay: revealed ? i * 0.035 : 99,
                ease: 'easeOut',
              }}
            >
              {char === ' ' ? '\u00A0' : char}
            </motion.span>
          ))}
        </h1>
      </div>

      {/* Sub-label */}
      <motion.div
        className="z-10 flex items-center gap-[1.5vw]"
        style={{ marginTop: '3vh' }}
        initial={{ opacity: 0, y: 14 }}
        animate={showSub ? { opacity: 1, y: 0 } : { opacity: 0, y: 14 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '1.9vw',
            color: '#C8C8D0',
            letterSpacing: '0.15em',
          }}
        >
          AI TRADING DECISION · NO AUDIT TRAIL
        </span>
        <motion.span
          style={{ color: '#E53E3E', fontWeight: 700, fontSize: '3.5vw', lineHeight: 1 }}
          initial={{ scale: 0, opacity: 0 }}
          animate={showQ ? { scale: 1, opacity: 1 } : { scale: 0, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 420, damping: 22 }}
        >
          ?
        </motion.span>
      </motion.div>

      {/* Context */}
      <motion.div
        className="z-10"
        style={{ marginTop: '2.5vh' }}
        initial={{ opacity: 0 }}
        animate={showQ ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '1.1vw',
            color: 'rgba(200,200,208,0.35)',
            letterSpacing: '0.2em',
          }}
        >
          SWIFT MT202 / XRPL RLUSD · QUANTUMBANK TRADING DESK
        </span>
      </motion.div>
    </motion.div>
  );
}

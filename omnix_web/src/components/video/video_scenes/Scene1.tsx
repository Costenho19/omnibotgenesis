import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene1() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 400),
      setTimeout(() => setPhase(2), 3200),
      setTimeout(() => setPhase(3), 5500),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  const line1 = "AI moved $50,000,000.";
  const line2 = "Who was watching?";

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.04 }}
      transition={{ duration: 1.2 }}
    >
      <div className="relative z-10 text-center max-w-5xl px-8">
        <div className="mb-6" style={{ fontFamily: 'var(--font-mono)' }}>
          <h1 className="text-[4vw] font-bold text-[#D4A843] tracking-tight leading-tight">
            {line1.split('').map((char, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0 }}
                animate={phase >= 1 ? { opacity: 1 } : { opacity: 0 }}
                transition={{ duration: 0.04, delay: phase >= 1 ? i * 0.06 : 0 }}
              >
                {char}
              </motion.span>
            ))}
          </h1>
        </div>

        <motion.h2
          className="text-[3.5vw] font-bold text-white"
          style={{ fontFamily: 'var(--font-display)' }}
          initial={{ opacity: 0, y: 18 }}
          animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 18 }}
          transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1] }}
        >
          {line2}
        </motion.h2>

        <motion.p
          className="mt-8 text-[1.6vw] text-white/50 tracking-widest uppercase"
          style={{ fontFamily: 'var(--font-display)' }}
          initial={{ opacity: 0 }}
          animate={phase >= 2 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 1.2, delay: 0.4 }}
        >
          SWIFT MT202 · XRPL RLUSD · Cross-border liquidity
        </motion.p>
      </div>

      {phase >= 3 && (
        <motion.div
          className="absolute top-1/2 left-0 h-[2px] bg-[#EF4444] w-full -translate-y-1/2 opacity-60"
          style={{ boxShadow: '0 0 12px #EF4444' }}
          initial={{ scaleX: 0, transformOrigin: 'left' }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 1.8, ease: [0.16, 1, 0.3, 1] }}
        />
      )}
    </motion.div>
  );
}

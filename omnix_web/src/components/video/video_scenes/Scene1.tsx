import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene1() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 200),
      setTimeout(() => setPhase(2), 1800),
      setTimeout(() => setPhase(3), 3500),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.03 }}
      transition={{ duration: 0.8 }}
    >
      {/* Top label */}
      <motion.div
        className="absolute top-[22vh] text-center w-full"
        initial={{ opacity: 0, y: -12 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -12 }}
        transition={{ duration: 0.6 }}
      >
        <span className="text-[1.1vw] text-white/40 tracking-[0.25em] uppercase font-mono">
          QuantumBank · AI Trading Desk · SWIFT MT202 / XRPL RLUSD
        </span>
      </motion.div>

      {/* Main number */}
      <div className="relative z-10 text-center">
        <motion.div
          className="font-mono font-black text-[#D4A843] leading-none"
          style={{ fontSize: 'clamp(48px, 10vw, 140px)', letterSpacing: '-0.03em' }}
          initial={{ opacity: 0, y: 30 }}
          animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        >
          USD 50,000,000
        </motion.div>

        <motion.div
          className="mt-6 text-[3.5vw] font-bold text-white"
          style={{ fontFamily: 'var(--font-display)', letterSpacing: '-0.01em' }}
          initial={{ opacity: 0, y: 18 }}
          animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 18 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          moved by AI.<br />
          <span className="text-white/50">Who was watching?</span>
        </motion.div>
      </div>

      {/* Red line — danger / no oversight */}
      {phase >= 3 && (
        <motion.div
          className="absolute left-0 right-0"
          style={{ top: '50%', transform: 'translateY(-50%)' }}
          initial={{ scaleX: 0, transformOrigin: 'left' }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
        >
          <div
            className="w-full h-[2px] bg-[#EF4444]"
            style={{ boxShadow: '0 0 16px #EF4444, 0 0 40px rgba(239,68,68,0.3)' }}
          />
        </motion.div>
      )}
    </motion.div>
  );
}

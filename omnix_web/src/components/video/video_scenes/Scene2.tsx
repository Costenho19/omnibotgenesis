import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene2() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 300),
      setTimeout(() => setPhase(2), 1200),
      setTimeout(() => setPhase(3), 3000),
      setTimeout(() => setPhase(4), 5000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  const gcfr = "GCFR-96D8BA6CA0FF4295";

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, x: -40 }}
      transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Headline */}
      <motion.div
        className="text-center mb-[6vh] z-10"
        initial={{ opacity: 0, y: -16 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -16 }}
        transition={{ duration: 0.7 }}
      >
        <div className="text-[2.8vw] font-bold text-white leading-tight" style={{ fontFamily: 'var(--font-display)' }}>
          A governance contract is sealed
        </div>
        <div className="text-[2.8vw] font-bold text-[#D4A843] leading-tight" style={{ fontFamily: 'var(--font-display)' }}>
          before Turn 0.
        </div>
      </motion.div>

      {/* GCFR hash — typed effect */}
      <motion.div
        className="font-mono tracking-widest text-[#3B82F6] mb-[4vh] z-10"
        style={{ fontSize: 'clamp(14px, 2.4vw, 36px)' }}
        initial={{ opacity: 0 }}
        animate={phase >= 2 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.4 }}
      >
        {gcfr.split('').map((char, i) => (
          <motion.span
            key={i}
            initial={{ opacity: 0 }}
            animate={phase >= 2 ? { opacity: 1 } : { opacity: 0 }}
            transition={{ duration: 0.04, delay: phase >= 2 ? i * 0.055 : 0 }}
          >
            {char}
          </motion.span>
        ))}
      </motion.div>

      {/* Algorithm badge */}
      <motion.div
        className="px-8 py-3 border border-[#D4A843]/40 bg-[#D4A843]/5 rounded-lg z-10 mb-[4vh]"
        initial={{ opacity: 0, scale: 0.92 }}
        animate={phase >= 3 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.92 }}
        transition={{ duration: 0.6 }}
      >
        <span className="text-[1.4vw] text-[#D4A843] font-mono font-bold tracking-widest">
          ML-DSA-65 · Dilithium-3 · FIPS 204
        </span>
      </motion.div>

      {/* Metadata row */}
      <motion.div
        className="flex gap-8 z-10"
        initial={{ opacity: 0, y: 12 }}
        animate={phase >= 4 ? { opacity: 1, y: 0 } : { opacity: 0, y: 12 }}
        transition={{ duration: 0.7 }}
      >
        {['SESSION-B9199C8CC9394304', 'FULL ADMISSION', 'Turn 0 sealed'].map((item, i) => (
          <div key={i} className="text-center">
            <div className="text-[1vw] font-mono text-white/35 tracking-widest uppercase mb-1">
              {i === 0 ? 'Session' : i === 1 ? 'Admission' : 'Status'}
            </div>
            <div className="text-[1.1vw] font-mono text-white/70">{item}</div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}

import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

const REGS = ['EU AI Act · Art. 9/11', 'MiCA · Title VI', 'DORA · Art. 11', 'NIST AU-2'];

export function Scene6() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 1500),
      setTimeout(() => setPhase(3), 2600),
      setTimeout(() => setPhase(4), 4200),
      setTimeout(() => setPhase(5), 6000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1.2 }}
    >
      {/* Radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(212,168,67,0.07) 0%, transparent 70%)'
        }}
      />

      {/* POGC ID */}
      <motion.div
        className="text-[1.2vw] text-[#3B82F6] font-mono tracking-[0.2em] mb-[4vh] z-10"
        initial={{ opacity: 0, y: 14 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: 14 }}
        transition={{ duration: 0.8 }}
      >
        POGC-GENESIS-E071CC96 · ACTIVE · ML-DSA-65 SIGNED
      </motion.div>

      {/* Logo — large, centered */}
      <motion.div
        className="z-10 mb-[4vh]"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={phase >= 2 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.8 }}
        transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1] }}
      >
        <img
          src={`${import.meta.env.BASE_URL}logo_nobg.png`}
          alt="OMNIX QUANTUM"
          style={{
            height: 'clamp(80px, 14vh, 160px)',
            width: 'auto',
            filter: 'drop-shadow(0 0 30px rgba(212,168,67,0.5)) drop-shadow(0 0 60px rgba(212,168,67,0.2))'
          }}
        />
      </motion.div>

      {/* Tagline */}
      <motion.div
        className="text-[3vw] font-black text-white text-center max-w-[55vw] leading-tight mb-[5vh] z-10"
        style={{ fontFamily: 'var(--font-display)' }}
        initial={{ opacity: 0, y: 16 }}
        animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 16 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
      >
        The governance layer<br />
        <span className="text-[#D4A843]">AI decisions trust.</span>
      </motion.div>

      {/* Regulatory tags */}
      <motion.div
        className="flex flex-wrap gap-3 justify-center mb-[4vh] z-10"
        initial={{ opacity: 0 }}
        animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.7 }}
      >
        {REGS.map((reg, i) => (
          <motion.div
            key={reg}
            className="px-5 py-2 border border-white/20 rounded-full text-[1vw] text-white/65 font-mono"
            initial={{ opacity: 0, scale: 0.85 }}
            animate={phase >= 4 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.85 }}
            transition={{ duration: 0.4, delay: i * 0.1 }}
          >
            {reg}
          </motion.div>
        ))}
      </motion.div>

      {/* Domain */}
      <motion.div
        className="text-[1.4vw] text-[#D4A843]/70 font-mono tracking-[0.35em] uppercase z-10"
        initial={{ opacity: 0 }}
        animate={phase >= 5 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 1.2 }}
      >
        omnixquantum.net
      </motion.div>
    </motion.div>
  );
}

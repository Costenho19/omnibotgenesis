import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

export function Scene2() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 1200),
      setTimeout(() => setPhase(3), 2000),
      setTimeout(() => setPhase(4), 2800),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)' }}
      animate={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)' }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.8, ease }}
    >
      <motion.div
        className="absolute inset-0"
        style={{
          backgroundImage:
            'linear-gradient(rgba(212,168,67,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(212,168,67,0.05) 1px, transparent 1px)',
          backgroundSize: '4vw 4vw',
        }}
        animate={{ backgroundPositionY: ['0px', '4vw'] }}
        transition={{ duration: 4, ease: 'linear', repeat: Infinity }}
      />

      <div className="relative z-10 flex flex-col items-center max-w-5xl w-full">
        <motion.h2
          className="font-display text-[3.5vw] font-bold text-[#FFFFFF] tracking-wide text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease }}
        >
          Governance Contract sealed before Turn 0
        </motion.h2>

        <div className="flex flex-col gap-6 w-full px-[10vw]">
          <motion.div
            className="flex justify-between items-center border-b border-[#D4A843]/30 pb-4"
            initial={{ opacity: 0, x: -30 }}
            animate={phase >= 1 ? { opacity: 1, x: 0 } : { opacity: 0, x: -30 }}
            transition={{ duration: 0.6, ease }}
          >
            <span className="font-mono text-[#94A3B8] text-[1.4vw] uppercase tracking-widest">GCFR</span>
            <span className="font-mono text-[#D4A843] text-[1.8vw] font-bold">GCFR-F6647F8081A7433B</span>
          </motion.div>

          <motion.div
            className="flex justify-between items-center border-b border-[#D4A843]/30 pb-4"
            initial={{ opacity: 0, x: -30 }}
            animate={phase >= 2 ? { opacity: 1, x: 0 } : { opacity: 0, x: -30 }}
            transition={{ duration: 0.6, ease }}
          >
            <span className="font-mono text-[#94A3B8] text-[1.4vw] uppercase tracking-widest">PQC</span>
            <span className="font-mono text-[#FFFFFF] text-[1.6vw]">ML-DSA-65 · Dilithium-3 · FIPS 204</span>
          </motion.div>

          <motion.div
            className="flex justify-between items-center border-b border-[#D4A843]/30 pb-4"
            initial={{ opacity: 0, x: -30 }}
            animate={phase >= 3 ? { opacity: 1, x: 0 } : { opacity: 0, x: -30 }}
            transition={{ duration: 0.6, ease }}
          >
            <span className="font-mono text-[#94A3B8] text-[1.4vw] uppercase tracking-widest">Rules</span>
            <span className="font-mono text-[#FFFFFF] text-[1.6vw]">5 predicates · PQC-sealed</span>
          </motion.div>
        </div>

        {phase >= 4 && (
          <motion.div
            className="absolute inset-0 pointer-events-none overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="absolute left-0 right-0 h-[2px] bg-[#D4A843] top-1/2"
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.5, ease }}
            />
            <motion.div
              className="absolute top-0 bottom-0 w-[2px] bg-[#D4A843] left-1/2"
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ duration: 0.5, ease }}
            />
            <motion.div
              className="absolute top-1/2 left-1/2 w-16 h-16 border-2 border-[#D4A843] rounded-sm -translate-x-1/2 -translate-y-1/2 bg-[#050508] flex items-center justify-center"
              initial={{ scale: 0, rotate: 45 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20, delay: 0.3 }}
            >
              <div className="w-8 h-8 border-2 border-[#D4A843] rounded-full" />
            </motion.div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

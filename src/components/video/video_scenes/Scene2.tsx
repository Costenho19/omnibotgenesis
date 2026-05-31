import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];
const clipReveal = {
  initial: { clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', opacity: 0 },
  animate: { clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)', opacity: 1 },
};

const SEALS = ['IAD', 'SAR', 'MFR', 'CPS', 'FPS'];

export function Scene2() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000), // Subtitle
      ...SEALS.map((_, i) => setTimeout(() => setPhase(2 + i), 2500 + i * 1200)), // Seals
      setTimeout(() => setPhase(8), 9000), // Algorithm
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center px-[10vw]"
      initial="initial" animate="animate" exit={{ opacity: 0, scale: 1.1, filter: 'blur(20px)' }}
      transition={{ duration: 0.8, ease }}
      {...clipReveal}
    >
      <div className="absolute bottom-6 right-8 font-mono text-[1.2vw] text-[#94A3B8]/60 tracking-widest z-0 pointer-events-none">
        GCFR-96D8BA6CA0FF4295
      </div>

      <div className="relative z-10 flex flex-col items-center w-full max-w-5xl">
        <motion.h2
          className="font-display text-[4.5vw] font-bold text-[#FFFFFF] tracking-tighter"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease }}
        >
          OMNIX Governance Contract
        </motion.h2>

        {phase >= 1 && (
          <motion.div
            className="mt-2 font-display text-[2vw] text-[#D4A843] tracking-widest uppercase font-semibold"
            initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, ease }}
          >
            Sealed before Turn 0
          </motion.div>
        )}

        <div className="flex gap-6 mt-16">
          {SEALS.map((seal, i) => (
            phase >= 2 + i && (
              <motion.div
                key={seal}
                className="w-24 h-24 sm:w-[8vw] sm:h-[8vw] border border-[#D4A843] bg-[#D4A843]/10 rounded-sm flex items-center justify-center relative overflow-hidden"
                initial={{ clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', scale: 0.9 }}
                animate={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)', scale: 1 }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
              >
                <motion.div 
                  className="absolute inset-0 bg-[#D4A843]" 
                  initial={{ opacity: 0.5 }} animate={{ opacity: 0 }} transition={{ duration: 1 }} 
                />
                <span className="font-mono text-[2vw] font-bold text-[#FFFFFF] tracking-wider relative z-10">{seal}</span>
              </motion.div>
            )
          ))}
        </div>

        {phase >= 8 && (
          <motion.div
            className="mt-16 font-mono text-[1.6vw] text-[#E8E8E8] tracking-widest border border-white/10 px-8 py-3 bg-white/5"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, ease }}
          >
            Algorithm: <span className="text-[#D4A843]">ML-DSA-65</span> (Dilithium-3, FIPS 204)
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
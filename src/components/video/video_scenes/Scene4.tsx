import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

export function Scene4() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 800),
      setTimeout(() => setPhase(2), 1800),
      setTimeout(() => setPhase(3), 2200),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-[#050508]"
      initial={{ clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)' }}
      animate={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)' }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.8, ease }}
    >
      <motion.h2
        className="font-display text-[3.5vw] font-bold text-[#FFFFFF] tracking-wide text-center mb-16"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease }}
      >
        What if someone changes one byte?
      </motion.h2>

      <div className="relative flex flex-col items-center">
        <motion.div
          className="font-mono text-[4vw] font-bold tracking-wider mb-12"
          initial={{ opacity: 0 }}
          animate={phase >= 1 ? { opacity: 1 } : { opacity: 0 }}
        >
          <span className="text-[#FFFFFF]">GCFR-F6647F8081A74</span>
          <motion.span
            className={phase >= 2 ? 'text-[#E53E3E]' : 'text-[#FFFFFF]'}
            animate={phase === 2 ? { opacity: [1, 0, 1, 0, 1], x: [-5, 5, -5, 5, 0] } : {}}
            transition={{ duration: 0.3 }}
          >
            {phase >= 2 ? '000' : '33B'}
          </motion.span>
        </motion.div>

        <motion.div
          className="flex flex-col items-center gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.4 }}
        >
          <div className="font-mono text-[2.5vw] font-bold text-[#E53E3E] tracking-widest border-2 border-[#E53E3E] px-8 py-3 bg-[#E53E3E]/10">
            ✗ INT-ADM-GCFR-HASH FAIL
          </div>
          <div className="font-mono text-[1.5vw] text-[#E53E3E] mt-4 flex items-center gap-4">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="w-8 h-8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            2 VERIFICATION(S) FAILED · exit code 1
          </div>
        </motion.div>
      </div>

      {phase >= 3 && (
        <motion.div
          className="absolute inset-0 pointer-events-none bg-[#E53E3E]/5 mix-blend-overlay"
          animate={{ opacity: [0, 1, 0.5, 1, 0.2] }}
          transition={{ duration: 0.5 }}
        />
      )}
    </motion.div>
  );
}

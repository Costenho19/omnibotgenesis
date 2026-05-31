import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];
const clipReveal = {
  initial: { clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', opacity: 0 },
  animate: { clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)', opacity: 1 },
};

export function Scene4() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000), // Mutation starts
      setTimeout(() => setPhase(2), 5000), // Tamper occurs
      setTimeout(() => setPhase(3), 5500), // Red X marks
      setTimeout(() => setPhase(4), 8000), // Exit code 1
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex items-center justify-center bg-[#050508]"
      initial="initial" animate="animate" exit={{ opacity: 0, scale: 1.1, filter: 'blur(20px)' }}
      transition={{ duration: 0.8, ease }}
      {...clipReveal}
    >
      <motion.div 
        className="absolute inset-0 bg-[#E53E3E] mix-blend-overlay z-0 pointer-events-none"
        animate={{ opacity: phase === 2 ? 0.15 : 0 }}
        transition={{ duration: 0.2 }}
      />
      <motion.div 
        className="w-full h-full relative z-10 flex"
        animate={phase === 2 ? { x: [-10, 10, -5, 5, 0], y: [5, -5, 10, -10, 0] } : { x: 0, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="w-1/2 h-full border-r border-[#333333] flex flex-col justify-center px-[8vw] gap-12 relative overflow-hidden">
          <div className="absolute top-12 left-12 font-mono text-[#94A3B8] text-[1.2vw] tracking-widest uppercase">Clean Package</div>
          <div className="flex flex-col gap-6 font-mono text-[1.8vw] text-[#E8E8E8]">
            <div className="flex gap-4 items-center">
              <div className="w-4 h-4 bg-[#22C55E] rounded-full" />
              <span>INT-ADM-GCFR-HASH</span>
            </div>
            <div className="flex gap-4 items-center">
              <div className="w-4 h-4 bg-[#22C55E] rounded-full" />
              <span>INT-ADM-GCFR-SIG</span>
            </div>
            <div className="flex gap-4 items-center opacity-40">
              <div className="w-4 h-4 border border-[#FFFFFF] rounded-full" />
              <span>IPFL-INV-007</span>
            </div>
          </div>
        </div>

        <div className="w-1/2 h-full flex flex-col justify-center px-[8vw] gap-12 relative">
          <div className="absolute top-12 left-12 font-mono text-[#94A3B8] text-[1.2vw] tracking-widest uppercase">Tampered Package</div>
          
          <div className="font-mono text-[1.5vw] text-[#94A3B8] break-all leading-tight">
            HASH_VAL: <br/>
            {phase < 2 ? (
              <span className="text-[#E8E8E8]">a3f7c2b9d1e4f508...</span>
            ) : (
              <span className="text-[#E53E3E] font-bold">00000000TAMPERED...</span>
            )}
          </div>

          <div className="flex flex-col gap-4">
            {phase >= 3 && (
              <>
                <motion.div 
                  className="font-mono text-[1.6vw] text-[#E53E3E] font-bold tracking-wide"
                  initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3 }}
                >
                  ✗ [INT-ADM-GCFR-HASH] component_hash MISMATCH
                </motion.div>
                <motion.div 
                  className="font-mono text-[1.6vw] text-[#E53E3E] font-bold tracking-wide"
                  initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3, delay: 0.1 }}
                >
                  ✗ [INT-ADM-GCFR-SIG] PQC signature INVALID
                </motion.div>
              </>
            )}
          </div>

          {phase >= 4 && (
            <motion.div 
              className="mt-8 font-display text-[5vw] font-black text-[#E53E3E] tracking-tighter leading-none"
              initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              exit code 1
            </motion.div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
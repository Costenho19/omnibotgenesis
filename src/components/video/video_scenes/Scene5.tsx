import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

export function Scene5() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000),
      setTimeout(() => setPhase(2), 2000),
      setTimeout(() => setPhase(3), 3200),
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
      <motion.h2
        className="font-display text-[3vw] font-bold text-[#FFFFFF] tracking-wide text-center mb-10"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease }}
      >
        Verified offline. Zero OMNIX access needed.
      </motion.h2>

      <motion.div
        className="w-[70vw] bg-[#000000] border border-[#333333] rounded-lg overflow-hidden shadow-2xl shadow-black/50"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease, delay: 0.2 }}
      >
        <div className="h-8 bg-[#1A1A1A] flex items-center px-4 gap-2">
          <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
          <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
          <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
        </div>

        <div className="p-8 font-mono text-[1.4vw] leading-relaxed">
          <motion.div
            className="text-[#D4A843]"
            initial={{ opacity: 0 }}
            animate={phase >= 1 ? { opacity: 1 } : { opacity: 0 }}
          >
            $ python3 verify_treasury_execution_trace.py package.json
          </motion.div>

          <motion.div
            className="text-[#94A3B8] mt-4"
            initial={{ opacity: 0 }}
            animate={phase >= 2 ? { opacity: 1 } : { opacity: 0 }}
          >
            [i] Verifying ML-DSA-65 signatures...
            <br />
            [i] Replaying 187 governance predicates...
          </motion.div>

          <motion.div
            className="mt-6 border-t border-[#333333] pt-6"
            initial={{ opacity: 0 }}
            animate={phase >= 3 ? { opacity: 1 } : { opacity: 0 }}
          >
            <div className="text-[#22C55E] font-bold mb-2">
              ✓ ALL VERIFICATIONS PASS
            </div>
            <div className="text-[#FFFFFF]">
              TOTAL: 187 · PASSED: 185 · FAILED: 0 · WARNINGS: 2
            </div>
            <div className="text-[#94A3B8] mt-2">
              exit code 0
            </div>
          </motion.div>
        </div>
      </motion.div>
    </motion.div>
  );
}

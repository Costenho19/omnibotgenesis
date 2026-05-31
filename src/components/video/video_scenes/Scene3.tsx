import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

const STEPS = [
  '0_INTAKE', '1_SOURCE', '2_AUTHORITY', '3_RUNTIME',
  '4_COUNTERFACTUAL', '5_VERDICT', '6_GATE', '7_EXECUTION', '8_REPLAY',
];

export function Scene3() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = STEPS.map((_, i) =>
      setTimeout(() => setPhase(i + 1), 400 + i * 300)
    );
    const finalTimer = setTimeout(() => setPhase(STEPS.length + 1), 400 + STEPS.length * 300 + 400);
    return () => {
      timers.forEach(t => clearTimeout(t));
      clearTimeout(finalTimer);
    };
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
        className="font-display text-[3.5vw] font-bold text-[#FFFFFF] tracking-wide text-center mb-10"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease }}
      >
        187 checks. Every step provable.
      </motion.h2>

      <div className="flex flex-col gap-3 w-full max-w-4xl px-[5vw]">
        {STEPS.map((step, i) => (
          <motion.div
            key={step}
            className="flex items-center gap-6"
            initial={{ opacity: 0, x: -20 }}
            animate={phase > i ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
            transition={{ duration: 0.4, ease }}
          >
            <div className={`w-3 h-3 rounded-full ${phase > i ? 'bg-[#D4A843]' : 'bg-[#94A3B8]/30'}`} />
            <div className={`font-mono text-[1.4vw] uppercase tracking-widest ${phase > i ? 'text-[#FFFFFF]' : 'text-[#94A3B8]/50'}`}>
              {step}
            </div>
            {phase > i && (
              <motion.div
                className="ml-auto font-mono text-[1.2vw] text-[#22C55E]"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                PASS
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>

      <motion.div
        className="mt-12 border border-[#D4A843]/50 bg-[#D4A843]/10 px-8 py-4 flex flex-col items-center gap-2"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={phase > STEPS.length ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        <span className="font-mono text-[1.8vw] text-[#D4A843] font-bold tracking-widest">
          MANDATE-BOUND
        </span>
        <span className="font-mono text-[1.2vw] text-[#FFFFFF] tracking-widest">
          FULL ADMISSION · 187 CHECKS
        </span>
      </motion.div>
    </motion.div>
  );
}

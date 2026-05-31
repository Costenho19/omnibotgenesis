import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

const STEPS = [
  'SCOPE_AUTHORIZATION',
  'MANDATE_BINDING',
  'CONTEXT_ADMISSION',
  'BEHAVIORAL_ANCHOR',
  'EXECUTION_INTEGRITY',
  'AVM_APPROVAL',
  'CONFORMANCE_SIGNAL',
  'HASH_CHAIN_SEAL',
  'RECEIPT_SIGNED',
];

export function Scene3() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const sequence = [
      setTimeout(() => setStep(1), 500),
      setTimeout(() => setStep(2), 1400),
      setTimeout(() => setStep(3), 2200),
      setTimeout(() => setStep(4), 3000),
      setTimeout(() => setStep(5), 3800),
    ];
    return () => sequence.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex items-center justify-center"
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, filter: 'blur(8px)' }}
      transition={{ duration: 0.7 }}
    >
      <div className="w-full max-w-[80vw] flex gap-[6vw] items-start">

        {/* Left — headline */}
        <div className="flex-shrink-0 w-[28vw] pt-4">
          <motion.div
            className="text-[3vw] font-black text-white leading-tight mb-4"
            style={{ fontFamily: 'var(--font-display)' }}
            initial={{ opacity: 0, x: -20 }}
            animate={step >= 1 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
            transition={{ duration: 0.7 }}
          >
            187 checks.<br />
            <span className="text-[#D4A843]">0 failures.</span>
          </motion.div>
          <motion.div
            className="text-[1.3vw] text-white/45 font-mono tracking-widest"
            initial={{ opacity: 0 }}
            animate={step >= 2 ? { opacity: 1 } : { opacity: 0 }}
            transition={{ duration: 0.6 }}
          >
            SESSION-B9199C8CC9394304
          </motion.div>

          {/* Verdict */}
          <motion.div
            className="mt-10 px-6 py-4 border border-[#D4A843]/50 bg-[#D4A843]/8 rounded-lg"
            initial={{ opacity: 0, scale: 0.88 }}
            animate={step >= 5 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.88 }}
            transition={{ type: 'spring', stiffness: 280, damping: 22 }}
          >
            <div className="text-[0.9vw] text-[#D4A843]/60 font-mono tracking-widest mb-1">VERDICT</div>
            <div className="text-[1.8vw] text-[#D4A843] font-black font-mono tracking-wider">
              MANDATE-BOUND
            </div>
          </motion.div>
        </div>

        {/* Right — step list */}
        <div className="flex-1 border border-[#3B82F6]/20 bg-[#050508]/80 rounded-xl p-6 font-mono">
          <div className="text-[1vw] text-[#3B82F6]/60 tracking-widest mb-4 uppercase">
            {'>'} running {STEPS.length} governance steps
          </div>
          <div className="flex flex-col gap-[0.8vh]">
            {STEPS.map((s, i) => {
              const visible = step >= Math.floor((i / STEPS.length) * 4) + 2;
              return (
                <motion.div
                  key={s}
                  className="flex items-center gap-3 text-[1.1vw]"
                  initial={{ opacity: 0, x: 10 }}
                  animate={visible ? { opacity: 1, x: 0 } : { opacity: 0, x: 10 }}
                  transition={{ duration: 0.35, delay: i * 0.06 }}
                >
                  <span className="text-green-500 font-bold">✓</span>
                  <span className="text-white/70">{s}</span>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

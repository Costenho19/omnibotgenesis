import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];
const clipReveal = {
  initial: { clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', opacity: 0 },
  animate: { clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)', opacity: 1 },
};

const STEPS = [
  'Authority verified',
  'Mandate bound',
  'IPFL predicate formation',
  'State provenance intact',
  'Cryptographic signature valid',
  'Invariant check: IPFL-INV-007',
  'Structural admissibility pass',
  'Temporal coherence valid',
  'HALT PROVEN'
];

export function Scene3() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500), // Start terminal
      ...STEPS.map((_, i) => setTimeout(() => setPhase(2 + i), 1000 + i * 800)), // Terminal steps
      setTimeout(() => setPhase(12), 9500), // Counter
      setTimeout(() => setPhase(13), 11000), // Verdict
      setTimeout(() => setPhase(14), 13000), // Badge
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial="initial" animate="animate" exit={{ opacity: 0, scale: 1.1, filter: 'blur(20px)' }}
      transition={{ duration: 0.8, ease }}
      {...clipReveal}
    >
      <div className="flex w-full max-w-[85vw] h-[60vh] gap-12">
        <motion.div 
          className="flex-1 border border-[#333333] bg-[#0A0A0E] p-8 flex flex-col justify-end overflow-hidden relative shadow-[0_0_50px_rgba(0,0,0,0.5)]"
          initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, ease }}
        >
          <div className="absolute top-0 left-0 right-0 h-8 bg-[#15151A] border-b border-[#333333] flex items-center px-4 gap-2">
             <div className="w-2.5 h-2.5 rounded-full bg-[#333333]" />
             <div className="w-2.5 h-2.5 rounded-full bg-[#333333]" />
             <div className="w-2.5 h-2.5 rounded-full bg-[#333333]" />
          </div>
          <div className="flex flex-col gap-3 font-mono text-[1.4vw] tracking-wide mt-10">
            {STEPS.map((step, i) => (
              phase >= 2 + i && (
                <motion.div key={i} className="flex gap-4 text-[#94A3B8]" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
                  <span className="text-[#64748B]">Step {i + 1}/9:</span>
                  <span className="text-[#E8E8E8]">{step}</span>
                  <span className="ml-auto text-[#22C55E]">✓</span>
                </motion.div>
              )
            ))}
          </div>
        </motion.div>

        <div className="w-[35vw] flex flex-col justify-center gap-12">
          {phase >= 12 && (
            <motion.div 
              className="flex flex-col gap-2"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, ease }}
            >
              <div className="font-display text-[4vw] font-bold text-[#D4A843] leading-none tracking-tighter">187 checks</div>
              <div className="font-mono text-[1.5vw] text-[#E8E8E8] tracking-widest">0 FAILED</div>
            </motion.div>
          )}

          {phase >= 13 && (
            <motion.div 
              className="font-display text-[5vw] font-black text-[#FFFFFF] tracking-tighter leading-none"
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6, ease }}
            >
              MANDATE<br/>BOUND
            </motion.div>
          )}

          {phase >= 14 && (
            <motion.div 
              className="inline-flex border border-[#22C55E] bg-[#22C55E]/10 px-6 py-3 rounded-sm font-mono text-[1vw] text-[#22C55E] tracking-widest w-max"
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}
            >
              MANDATE-BOUND · 0 violations · 0 warnings
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
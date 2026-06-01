import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

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
      ...STEPS.map((_, i) => setTimeout(() => setPhase(2 + i), 1000 + i * 1000)), // Terminal steps
      setTimeout(() => setPhase(12), 11000), // Counter
      setTimeout(() => setPhase(13), 12000), // Verdict
      setTimeout(() => setPhase(14), 13000), // Badge
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center z-10"
      initial={{ clipPath: 'circle(0% at 50% 50%)', opacity: 0 }}
      animate={{ clipPath: 'circle(150% at 50% 50%)', opacity: 1 }}
      exit={{ opacity: 0, scale: 1.1, filter: 'blur(20px)' }}
      transition={{ duration: 1, ease }}
    >
      <div className="absolute inset-0 bg-[#0A0A0E] z-0 pointer-events-none" />
      <div 
        className="absolute inset-0 z-0 pointer-events-none opacity-5"
        style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, #fff 2px, #fff 4px)' }}
      />

      <div className="flex w-full max-w-[85vw] h-[60vh] gap-12 relative z-10">
        <motion.div 
          className="flex-1 border border-[#333333] bg-[#0A0A0E]/90 backdrop-blur-md p-8 flex flex-col overflow-hidden relative shadow-[0_0_50px_rgba(0,0,0,0.5)]"
          initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, ease }}
        >
          <div className="absolute top-0 left-0 right-0 h-8 bg-[#15151A] border-b border-[#333333] flex items-center px-4 gap-2">
             <div className="w-2.5 h-2.5 rounded-full bg-[#333333]" />
             <div className="w-2.5 h-2.5 rounded-full bg-[#333333]" />
             <div className="w-2.5 h-2.5 rounded-full bg-[#333333]" />
             <div className="ml-4 font-mono text-[0.8vw] text-white/30">terminal — execution-trace</div>
          </div>

          <div className="flex-1 mt-10 overflow-hidden flex flex-col gap-3 font-mono text-[1.4vw] tracking-wide">
            {STEPS.map((step, i) => (
              <motion.div 
                key={i} 
                className="flex gap-4 text-[#94A3B8] items-center" 
                initial={{ opacity: 0, x: -10 }} 
                animate={phase >= 2 + i ? { opacity: 1, x: 0 } : { opacity: 0, x: -10 }}
                transition={{ duration: 0.3 }}
              >
                <span className="text-[#64748B]">Step {i + 1}/9:</span>
                <span className="text-[#E8E8E8]">{step}</span>
                <span className="ml-auto text-[#22C55E]">✓</span>
                <motion.div 
                  className="w-2 h-2 rounded-full bg-[#22C55E]"
                  animate={{ opacity: [1, 0.3, 1], scale: [1, 1.2, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              </motion.div>
            ))}
          </div>

          {/* Progress bar */}
          <div className="h-1 bg-[#333333] w-full mt-4 rounded-full overflow-hidden">
            <motion.div 
              className="h-full bg-[#22C55E]"
              initial={{ width: '0%' }}
              animate={{ width: `${Math.min(100, (Math.max(0, phase - 1) / STEPS.length) * 100)}%` }}
              transition={{ duration: 0.5, ease: 'linear' }}
            />
          </div>
        </motion.div>

        <div className="w-[35vw] flex flex-col justify-center gap-12">
          <motion.div 
            className="flex flex-col gap-2"
            initial={{ opacity: 0, y: 20 }} 
            animate={phase >= 12 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.8, ease }}
          >
            <div className="font-display text-[4vw] font-bold text-[#D4A843] leading-none tracking-tighter">187 checks</div>
            <div className="font-mono text-[1.5vw] text-[#E8E8E8] tracking-widest">0 FAILED</div>
          </motion.div>

          <motion.div 
            className="font-display text-[5vw] font-black text-[#FFFFFF] tracking-tighter leading-none"
            initial={{ opacity: 0, scale: 0.95 }} 
            animate={phase >= 13 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.6, ease }}
          >
            MANDATE<br/>BOUND
          </motion.div>

          <motion.div 
            className="inline-flex border border-[#22C55E] bg-[#22C55E]/10 px-6 py-3 rounded-sm font-mono text-[1vw] text-[#22C55E] tracking-widest w-max"
            initial={{ opacity: 0, x: -20 }} 
            animate={phase >= 14 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
            transition={{ duration: 0.5 }}
          >
            MANDATE-BOUND · 0 violations · 0 warnings
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}

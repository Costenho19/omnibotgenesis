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
  const [checkCount, setCheckCount] = useState(0);

  // Main phase timers — runs once on mount
  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      ...STEPS.map((_, i) => setTimeout(() => setPhase(2 + i), 1000 + i * 800)),
      setTimeout(() => setPhase(12), 9000),
      setTimeout(() => setPhase(13), 11000),
      setTimeout(() => setPhase(14), 12500),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  // Counter increments from 0→187 starting at phase 12
  useEffect(() => {
    if (phase < 12) return;
    let count = 0;
    const interval = setInterval(() => {
      count += 1;
      setCheckCount(count);
      if (count >= 187) clearInterval(interval);
    }, 20);
    return () => clearInterval(interval);
  }, [phase >= 12]);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center z-10"
      initial={{ scale: 1.2, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ opacity: 0, scale: 0.8, filter: 'blur(20px)' }}
      transition={{ duration: 1, ease }}
    >
      <div className="absolute inset-0 bg-[#0A0A0E] z-0 pointer-events-none" />
      <div 
        className="absolute inset-0 z-0 pointer-events-none opacity-10 mix-blend-screen"
        style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(34, 197, 94, 0.1) 2px, rgba(34, 197, 94, 0.1) 4px)' }}
      />

      {/* Floating particles background */}
      <motion.div className="absolute inset-0 z-0 pointer-events-none opacity-30">
        {Array.from({ length: 30 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-[#22C55E] rounded-full"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
            }}
            animate={{
              y: [0, -100],
              opacity: [0, 1, 0],
              scale: [0, Math.random() * 2 + 1, 0]
            }}
            transition={{
              duration: Math.random() * 5 + 3,
              repeat: Infinity,
              delay: Math.random() * 5
            }}
          />
        ))}
      </motion.div>

      <div className="flex w-full max-w-[85vw] h-[65vh] gap-12 relative z-10">
        <motion.div 
          className="flex-1 border border-[#333333] bg-[#0A0A0E]/90 backdrop-blur-md p-8 flex flex-col overflow-hidden relative shadow-[0_0_80px_rgba(0,0,0,0.8)]"
          initial={{ opacity: 0, x: -50, rotateY: 20 }} animate={{ opacity: 1, x: 0, rotateY: 0 }} transition={{ duration: 0.8, ease, type: "spring" }}
          style={{ perspective: 1000 }}
        >
          <div className="absolute top-0 left-0 right-0 h-10 bg-[#15151A] border-b border-[#333333] flex items-center px-6 gap-3">
             <div className="w-3 h-3 rounded-full bg-[#E53E3E]" />
             <div className="w-3 h-3 rounded-full bg-[#D4A843]" />
             <div className="w-3 h-3 rounded-full bg-[#22C55E]" />
             <div className="ml-4 font-mono text-[0.9vw] text-white/50 tracking-wider">terminal — execution-trace</div>
          </div>

          <div className="flex-1 mt-12 overflow-hidden flex flex-col gap-4 font-mono text-[1.5vw] tracking-wide">
            {STEPS.map((step, i) => (
              <motion.div 
                key={i} 
                className="flex gap-4 text-[#94A3B8] items-center" 
                initial={{ opacity: 0, x: -20, filter: 'blur(5px)' }} 
                animate={phase >= 2 + i ? { opacity: 1, x: 0, filter: 'blur(0px)' } : { opacity: 0, x: -20, filter: 'blur(5px)' }}
                transition={{ duration: 0.4 }}
              >
                <span className="text-[#64748B] w-[8vw]">Step {i + 1}/9:</span>
                <span className={i === STEPS.length - 1 ? "text-[#E8E8E8] font-bold" : "text-[#E8E8E8]"}>{step}</span>
                <span className="ml-auto text-[#22C55E] drop-shadow-[0_0_5px_#22C55E]">✓</span>
                <motion.div 
                  className="w-2.5 h-2.5 rounded-full bg-[#22C55E] shadow-[0_0_10px_#22C55E]"
                  animate={{ opacity: [1, 0.3, 1], scale: [1, 1.3, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              </motion.div>
            ))}
          </div>

          {/* Glowing Progress bar */}
          <div className="h-2 bg-[#333333] w-full mt-6 rounded-full overflow-hidden relative">
            <motion.div 
              className="absolute inset-y-0 left-0 bg-[#22C55E] shadow-[0_0_20px_#22C55E]"
              initial={{ width: '0%' }}
              animate={{ width: `${Math.min(100, (Math.max(0, phase - 1) / STEPS.length) * 100)}%` }}
              transition={{ duration: 0.5, ease: 'linear' }}
            />
          </div>
        </motion.div>

        <div className="w-[35vw] flex flex-col justify-center gap-14">
          <motion.div 
            className="flex flex-col gap-2"
            initial={{ opacity: 0, y: 30 }} 
            animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
            transition={{ duration: 0.8, ease }}
          >
            <div className="font-display text-[5vw] font-bold text-[#D4A843] leading-none tracking-tighter drop-shadow-[0_0_15px_rgba(212,168,67,0.5)]">
              {checkCount} checks
            </div>
            <div className="font-mono text-[1.6vw] text-[#E8E8E8] tracking-widest opacity-80">0 FAILED</div>
          </motion.div>

          <div className="font-display text-[5.5vw] font-black text-[#FFFFFF] tracking-tighter leading-none h-[12vw]">
            {phase >= 13 && (
              <motion.div>
                {"MANDATE BOUND".split('').map((char, index) => (
                  <motion.span
                    key={index}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.1, delay: index * 0.05 }}
                  >
                    {char === ' ' ? <br /> : char}
                  </motion.span>
                ))}
                <motion.span
                  className="inline-block w-[0.8em] h-[1em] bg-[#D4A843] ml-2 align-baseline"
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                />
              </motion.div>
            )}
          </div>

          <motion.div 
            className="inline-flex border-2 border-[#22C55E] bg-[#22C55E]/10 px-8 py-4 rounded-sm font-mono text-[1.2vw] text-[#22C55E] tracking-widest w-max shadow-[0_0_30px_rgba(34,197,94,0.3)] backdrop-blur-sm"
            initial={{ opacity: 0, scale: 0.8, y: 20 }} 
            animate={phase >= 14 ? { opacity: 1, scale: 1, y: 0 } : { opacity: 0, scale: 0.8, y: 20 }}
            transition={{ duration: 0.5, type: 'spring', bounce: 0.5 }}
          >
            MANDATE-BOUND · 0 violations · 0 warnings
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}

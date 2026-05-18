import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

const layers = [
  { label: "L1 · IDENTITY LAYER · Human Authority", color: "var(--gold)" },
  { label: "L2 · DELEGATION · Monotonic Authority Reduction", color: "var(--cyan)" },
  { label: "L3 · TEMPORAL · Runtime Admissibility", color: "#8b5cf6" },
  { label: "L4 · CONTINUITY · CES Monitoring", color: "var(--success)" }
];

export function Scene2() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 1500),
      setTimeout(() => setPhase(3), 4000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
    >
      <motion.div 
        className="absolute top-[10vh] left-[50%] -translate-x-1/2"
        initial={{ opacity: 0, y: -20 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -20 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <h1 className="text-[4vw] font-bold text-[var(--gold)]" style={{ fontFamily: 'var(--font-display)' }}>
          OMNIX ATF
        </h1>
      </motion.div>

      <div className="relative mt-[10vh] w-[60vw] h-[40vh] flex flex-col justify-between">
        {layers.map((layer, i) => (
          <div key={i} className="relative w-full h-[6vh]">
            {i < layers.length - 1 && phase >= 2 && (
              <motion.div
                className="absolute left-[2vh] top-[6vh] w-[2px] h-[3vh] bg-[var(--muted)]/30"
                initial={{ scaleY: 0, transformOrigin: 'top' }}
                animate={{ scaleY: 1 }}
                transition={{ duration: 0.5, delay: phase >= 2 ? i * 0.3 + 0.3 : 0 }}
              />
            )}
            
            <motion.div
              className="absolute inset-0 flex items-center px-6 border border-white/10 bg-[var(--navy-light)]/50 backdrop-blur-sm"
              initial={{ clipPath: 'inset(0 100% 0 0)' }}
              animate={phase >= 2 ? { clipPath: 'inset(0 0% 0 0)' } : { clipPath: 'inset(0 100% 0 0)' }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: phase >= 2 ? i * 0.3 : 0 }}
            >
              <div className="w-3 h-3 rounded-full mr-4" style={{ backgroundColor: layer.color }} />
              <span className="text-[1.2vw] text-[var(--platinum)] uppercase tracking-wider" style={{ fontFamily: 'var(--font-mono)' }}>
                {layer.label}
              </span>
            </motion.div>
          </div>
        ))}
      </div>

      <motion.div
        className="absolute top-[12vh] right-[5vw]"
        initial={{ opacity: 0 }}
        animate={phase >= 3 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 1 }}
      >
        <span className="text-[1vw] text-[var(--gold)]/70" style={{ fontFamily: 'var(--font-mono)' }}>
          ML-DSA-65 · FIPS 204
        </span>
      </motion.div>
    </motion.div>
  );
}

import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene1() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 3500),
      setTimeout(() => setPhase(3), 5000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  const statement = "AI systems can execute actions.";

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.05 }}
      transition={{ duration: 1 }}
    >
      <div className="relative z-10 text-center max-w-4xl px-8">
        <motion.h2 
          className="text-[3vw] font-medium text-[var(--gold)] mb-8"
          style={{ fontFamily: 'var(--font-mono)' }}
        >
          {statement.split('').map((char, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0 }}
              animate={phase >= 1 ? { opacity: 1 } : { opacity: 0 }}
              transition={{ duration: 0.05, delay: phase >= 1 ? i * 0.08 : 0 }}
            >
              {char}
            </motion.span>
          ))}
        </motion.h2>

        <motion.p
          className="text-[2.5vw] text-[var(--platinum)]"
          style={{ fontFamily: 'var(--font-display)' }}
          initial={{ opacity: 0, y: 20 }}
          animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
        >
          Most organizations cannot prove execution legitimacy at runtime.
        </motion.p>
      </div>

      {phase >= 3 && (
        <motion.div
          className="absolute top-1/2 left-0 h-[1px] bg-[var(--danger)] w-full -translate-y-1/2"
          initial={{ scaleX: 0, transformOrigin: 'left' }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 2, ease: "easeInOut" }}
        />
      )}
    </motion.div>
  );
}

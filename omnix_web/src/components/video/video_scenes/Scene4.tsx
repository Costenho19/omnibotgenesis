import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene4() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 800),
      setTimeout(() => setPhase(2), 2000),
      setTimeout(() => setPhase(3), 3500),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-[#020617]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.5 }}
    >
      {/* Flash red border briefly */}
      <motion.div
        className="absolute inset-0 border-[4px] border-[var(--danger)] pointer-events-none"
        initial={{ opacity: 0 }}
        animate={phase === 1 ? { opacity: [0, 1, 0] } : { opacity: 0 }}
        transition={{ duration: 0.3 }}
      />

      <div className="relative w-[30vh] h-[30vh] flex items-center justify-center mb-12">
        <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full overflow-visible">
          <motion.polygon
            points="50,5 95,27.5 95,72.5 50,95 5,72.5 5,27.5"
            fill={phase >= 2 ? "rgba(239, 68, 68, 0.15)" : "transparent"}
            stroke="var(--danger)"
            strokeWidth="2"
            initial={{ pathLength: 0, strokeDasharray: 300, strokeDashoffset: 300 }}
            animate={phase >= 1 ? { strokeDashoffset: 0 } : { strokeDashoffset: 300 }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
          />
        </svg>

        <motion.div
          className="text-[4vw] font-bold text-[var(--gold)] z-10"
          style={{ fontFamily: 'var(--font-mono)' }}
          initial={{ scale: 0, opacity: 0 }}
          animate={phase >= 2 ? { scale: 1, opacity: 1 } : { scale: 0, opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 15 }}
        >
          HALT
        </motion.div>
      </div>

      <div className="text-center h-[15vh]">
        <motion.p
          className="text-[2vw] text-[var(--danger)] font-medium mb-4 tracking-wide"
          style={{ fontFamily: 'var(--font-display)' }}
          initial={{ opacity: 0, y: 10 }}
          animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
          transition={{ duration: 0.5 }}
        >
          Execution blocked. Authority chain invalid.
        </motion.p>
        
        <motion.p
          className="text-[1vw] text-[var(--muted)]"
          style={{ fontFamily: 'var(--font-mono)' }}
          initial={{ opacity: 0 }}
          animate={phase >= 3 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          CES: 8.33 · ATFDR-7F3A9B2C1E4D8F6A · OMNIX-BLOCK-20260518-000147
        </motion.p>
      </div>
    </motion.div>
  );
}

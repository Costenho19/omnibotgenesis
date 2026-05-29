import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene7() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000), // wordmark
      setTimeout(() => setPhase(2), 2500), // first part
      setTimeout(() => setPhase(3), 4500), // second part
      setTimeout(() => setPhase(4), 8500), // bottom line
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 bg-[var(--navy-dark)] overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1.5 }}
    >
      <motion.div
        className="absolute top-[6vh] left-[4vw] text-[1vw] text-[var(--gold)]/80 tracking-widest"
        style={{ fontFamily: 'var(--font-mono)' }}
        initial={{ opacity: 0 }}
        animate={phase >= 1 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 1.5 }}
      >
        OMNIX QUANTUM LTD
      </motion.div>

      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <div className="text-[4.5vw] font-medium text-[var(--platinum)] leading-[1.3] tracking-tight" style={{ fontFamily: 'var(--font-display)' }}>
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 15 }}
            transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
          >
            The protocol decides
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 15 }}
            transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
          >
            whether execution is admitted.
          </motion.div>
        </div>

        <motion.div
          className="absolute bottom-[10vh] text-[0.9vw] text-[var(--muted)]/60 tracking-widest uppercase"
          style={{ fontFamily: 'var(--font-mono)' }}
          initial={{ opacity: 0 }}
          animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 2 }}
        >
          RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3 · 169 invariants · 202 ADRs
        </motion.div>
      </div>
    </motion.div>
  );
}

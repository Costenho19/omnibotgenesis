import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { OmnixLogo } from '../OmnixLogo';

const ease = [0.16, 1, 0.3, 1];

export function Scene6() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 600),
      setTimeout(() => setPhase(2), 1600),
      setTimeout(() => setPhase(3), 2600),
      setTimeout(() => setPhase(4), 3600),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-[#050508]"
      initial={{ clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)' }}
      animate={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)' }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.8, ease }}
    >
      <motion.h2
        className="font-display text-[3.2vw] font-bold text-[#FFFFFF] tracking-wide text-center mb-16"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease }}
      >
        The governance layer the world needs.
      </motion.h2>

      <motion.div
        className="mb-12"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={phase >= 1 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        <OmnixLogo size="12vw" opacity={1} glow={true} />
      </motion.div>

      <motion.h1
        className="font-display text-[4vw] font-black text-[#FFFFFF] tracking-[0.2em] mb-12"
        initial={{ opacity: 0, y: 20 }}
        animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
        transition={{ duration: 0.8, ease }}
      >
        OMNIX QUANTUM LTD
      </motion.h1>

      <div className="flex flex-col items-center gap-4">
        <motion.div
          className="font-mono text-[1.4vw] text-[#D4A843] tracking-widest border border-[#D4A843]/30 px-6 py-2 rounded-full"
          initial={{ opacity: 0, y: 20 }}
          animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6, ease }}
        >
          EU AI Act · MiCA · DORA compliant
        </motion.div>

        <motion.div
          className="font-mono text-[1.2vw] text-[#94A3B8] tracking-widest"
          initial={{ opacity: 0, y: 20 }}
          animate={phase >= 4 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6, ease }}
        >
          Post-Quantum Cryptography · RFC-ATF-1 through RFC-ATF-6
        </motion.div>

        <motion.div
          className="font-mono text-[1vw] text-[#D4A843]/60 tracking-widest mt-4"
          initial={{ opacity: 0 }}
          animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.6, ease, delay: 0.3 }}
        >
          POGC-GENESIS-E071CC96 · omnixquantum.net
        </motion.div>
      </div>
    </motion.div>
  );
}

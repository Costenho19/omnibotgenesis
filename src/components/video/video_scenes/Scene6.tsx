import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { OmnixLogo } from '../OmnixLogo';

const ease = [0.16, 1, 0.3, 1];

export function Scene6() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000), // PoGC
      setTimeout(() => setPhase(2), 2500), // Registry/SSL
      setTimeout(() => setPhase(3), 4500), // Tagline
      setTimeout(() => setPhase(4), 8500), // Fade to black & logo
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-[#050508] z-50"
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }} 
      exit={{ opacity: 0, scale: 1.1 }} 
      transition={{ duration: 1, ease }}
    >
      <motion.div
        className="absolute w-[60vw] h-[60vw] rounded-full blur-[150px] z-0 pointer-events-none"
        animate={{ 
          scale: [1, 1.1, 1],
          opacity: [0.03, 0.06, 0.03],
        }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
        style={{ backgroundColor: '#D4A843' }}
      />

      <motion.div 
        className="absolute inset-0 bg-[#050508] z-40 pointer-events-none"
        animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 1.5, ease }}
      />

      <div className="relative z-50 flex flex-col items-center max-w-6xl w-full text-center">
        <motion.div
          className="absolute"
          initial={{ opacity: 0, scale: 0.8 }} 
          animate={phase >= 4 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.8 }} 
          transition={{ duration: 1, delay: 0.2 }}
        >
          <OmnixLogo size="12vw" opacity={1} glow={true} />
        </motion.div>

        <motion.div
          animate={phase >= 4 ? { opacity: 0, scale: 0.95 } : { opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          className="flex flex-col items-center w-full"
        >
          <motion.div 
            className="font-mono text-[2vw] text-[#D4A843] font-bold tracking-[0.3em] mb-12 drop-shadow-[0_0_15px_rgba(212,168,67,0.8)]"
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            POGC-GENESIS-E071CC96
          </motion.div>

          <motion.div 
            className="flex flex-col items-center gap-6 mb-16"
            initial={{ opacity: 0, y: 20 }} 
            animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }} 
            transition={{ duration: 0.8 }}
          >
            <div className="font-display text-[4vw] font-bold text-[#FFFFFF] tracking-tight leading-none">
              Proof of Governance Registry
            </div>
            <motion.div 
              className="font-display text-[2.5vw] text-[#94A3B8] tracking-wide"
              initial={{ opacity: 0, y: 20 }}
              animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ duration: 0.8 }}
            >
              The SSL for AI decisions
            </motion.div>
          </motion.div>

          <motion.div 
            className="flex flex-col items-center gap-8 mt-12 pt-12 border-t border-white/10 w-3/4"
            initial={{ opacity: 0, y: 20 }} 
            animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }} 
            transition={{ duration: 1 }}
          >
            <div className="font-display text-[1.8vw] font-bold text-[#E8E8E8] tracking-[0.2em] uppercase">
              OMNIX QUANTUM LTD
            </div>
            <div className="font-display text-[1.5vw] text-[#94A3B8] tracking-widest">
              Every AI decision. Auditable. Irrefutable. Offline-verifiable.
            </div>
          </motion.div>
        </motion.div>
      </div>
    </motion.div>
  );
}

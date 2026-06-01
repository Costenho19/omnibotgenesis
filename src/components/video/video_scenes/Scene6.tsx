import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { OmnixLogo } from '../OmnixLogo';

const ease = [0.16, 1, 0.3, 1];

export function Scene6() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000), // PoGC & Seal draws
      setTimeout(() => setPhase(2), 3000), // Registry/SSL
      setTimeout(() => setPhase(3), 5000), // Tagline
      setTimeout(() => setPhase(4), 8500), // Fade to black & logo pulse
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-[#050508] z-50 overflow-hidden"
      initial={{ scale: 1.5, opacity: 0 }} 
      animate={{ scale: 1, opacity: 1 }} 
      exit={{ opacity: 0, filter: 'blur(20px)' }} 
      transition={{ duration: 1.5, ease }}
    >
      {/* Dynamic Background Light */}
      <motion.div
        className="absolute w-[80vw] h-[80vw] rounded-full blur-[150px] z-0 pointer-events-none"
        animate={{ 
          scale: [1, 1.2, 1],
          opacity: phase >= 4 ? 0 : [0.05, 0.1, 0.05],
        }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        style={{ backgroundColor: '#D4A843' }}
      />

      {/* Raining POGC Hash Fragments */}
      <motion.div className="absolute inset-0 z-0 pointer-events-none opacity-20">
        {Array.from({ length: 20 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute font-mono text-[1vw] text-[#D4A843]/40"
            style={{ left: `${(i * 17) % 100}%`, top: '-10%' }}
            animate={{
              y: ['0vh', '120vh'],
              opacity: [0, 1, 0]
            }}
            transition={{
              duration: Math.random() * 5 + 5,
              repeat: Infinity,
              delay: Math.random() * 5,
              ease: 'linear'
            }}
          >
            POGC-{Math.random().toString(16).substr(2, 8).toUpperCase()}
          </motion.div>
        ))}
      </motion.div>

      {/* Fade to black overlay for finale */}
      <motion.div 
        className="absolute inset-0 bg-[#050508] z-40 pointer-events-none"
        initial={{ opacity: 0 }}
        animate={phase >= 4 ? { opacity: 0.9 } : { opacity: 0 }}
        transition={{ duration: 1.5, ease }}
      />

      <div className="relative z-50 flex flex-col items-center max-w-6xl w-full text-center">
        
        {/* Animated PQC Seal SVG */}
        <motion.div
          className="absolute z-0 opacity-20 pointer-events-none"
          initial={{ opacity: 0 }}
          animate={phase >= 1 && phase < 4 ? { opacity: 0.15 } : { opacity: 0 }}
          transition={{ duration: 1 }}
        >
          <svg width="40vw" height="40vw" viewBox="0 0 100 100" className="animate-spin-slow">
            <motion.circle 
              cx="50" cy="50" r="48" 
              fill="none" stroke="#D4A843" strokeWidth="1"
              strokeDasharray="5 5"
              animate={{ rotate: 360 }}
              transition={{ duration: 60, repeat: Infinity, ease: 'linear' }}
            />
            <motion.path
              d="M 50 10 L 90 50 L 50 90 L 10 50 Z"
              fill="none" stroke="#D4A843" strokeWidth="0.5"
              initial={{ pathLength: 0 }}
              animate={phase >= 1 ? { pathLength: 1 } : { pathLength: 0 }}
              transition={{ duration: 3, ease }}
            />
            <motion.circle 
              cx="50" cy="50" r="30" 
              fill="none" stroke="#D4A843" strokeWidth="2"
              initial={{ pathLength: 0 }}
              animate={phase >= 1 ? { pathLength: 1 } : { pathLength: 0 }}
              transition={{ duration: 2, ease, delay: 0.5 }}
            />
          </svg>
        </motion.div>

        <motion.div
          className="absolute"
          initial={{ opacity: 0, scale: 0.8, y: 50 }} 
          animate={phase >= 4 ? { opacity: 1, scale: 1.2, y: 0 } : { opacity: 0, scale: 0.8, y: 50 }} 
          transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <OmnixLogo size="15vw" opacity={1} glow={phase >= 4} />
          {/* Final amber pulse on logo */}
          {phase >= 4 && (
             <motion.div
               className="absolute inset-0 rounded-full bg-[#D4A843] z-[-1]"
               initial={{ scale: 0.8, opacity: 0.8 }}
               animate={{ scale: 2.5, opacity: 0 }}
               transition={{ duration: 2, ease: "easeOut", repeat: Infinity, repeatDelay: 1 }}
             />
          )}
        </motion.div>

        <motion.div
          animate={phase >= 4 ? { opacity: 0, scale: 0.9, y: -50 } : { opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 1, ease }}
          className="flex flex-col items-center w-full z-10"
        >
          <motion.div 
            className="font-mono text-[2.2vw] text-[#D4A843] font-bold tracking-[0.4em] mb-14 drop-shadow-[0_0_20px_rgba(212,168,67,1)]"
            initial={{ opacity: 0, y: 30, filter: 'blur(10px)' }} 
            animate={phase >= 1 ? { opacity: 1, y: 0, filter: 'blur(0px)' } : { opacity: 0, y: 30, filter: 'blur(10px)' }}
            transition={{ duration: 1, type: "spring" }}
          >
            POGC-GENESIS-E071CC96
          </motion.div>

          <motion.div 
            className="flex flex-col items-center gap-6 mb-20"
            initial={{ opacity: 0, y: 20 }} 
            animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }} 
            transition={{ duration: 1, ease }}
          >
            <div className="font-display text-[4.5vw] font-black text-[#FFFFFF] tracking-tight leading-none drop-shadow-lg">
              Proof of Governance Registry
            </div>
            <motion.div 
              className="font-display text-[2.8vw] text-[#94A3B8] tracking-widest font-light"
              initial={{ opacity: 0, clipPath: 'inset(0 100% 0 0)' }}
              animate={phase >= 2 ? { opacity: 1, clipPath: 'inset(0 0 0 0)' } : { opacity: 0, clipPath: 'inset(0 100% 0 0)' }}
              transition={{ duration: 1.5, delay: 0.5, ease }}
            >
              The SSL for AI decisions
            </motion.div>
          </motion.div>

          <motion.div 
            className="flex flex-col items-center gap-8 mt-12 pt-14 border-t border-white/20 w-4/5 relative"
            initial={{ opacity: 0, y: 40 }} 
            animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }} 
            transition={{ duration: 1.2, ease }}
          >
            <div className="absolute top-[-2px] left-1/2 -translate-x-1/2 w-1/4 h-[4px] bg-[#D4A843] shadow-[0_0_15px_#D4A843]" />
            <div className="font-display text-[2vw] font-black text-[#E8E8E8] tracking-[0.3em] uppercase">
              OMNIX QUANTUM LTD
            </div>
            <div className="font-display text-[1.6vw] text-[#94A3B8] tracking-widest">
              Every AI decision. Auditable. Irrefutable. Offline-verifiable.
            </div>
          </motion.div>
        </motion.div>
      </div>
    </motion.div>
  );
}

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

const SEALS = ['IAD', 'SAR', 'MFR', 'CPS', 'FPS'];

export function Scene2() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1500), // Subtitle
      ...SEALS.map((_, i) => setTimeout(() => setPhase(2 + i), 3000 + i * 1200)), // Seals
      setTimeout(() => setPhase(8), 11000), // Algorithm
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center px-[10vw] z-10"
      initial={{ x: '100%', opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: '-100%', opacity: 0 }}
      transition={{ duration: 0.8, ease }}
    >
      <div className="absolute inset-0 z-0 pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212,168,67,0.1), transparent 70%)' }} />
      
      {/* Hex Grid Background */}
      <motion.div
        className="absolute inset-0 z-0 pointer-events-none opacity-5"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M20 0l20 10v20L20 40 0 30V10z' fill='none' stroke='%23FFF' stroke-width='1'/%3E%3C/svg%3E")`,
          backgroundSize: '40px 40px'
        }}
        animate={{ backgroundPosition: ['0px 0px', '40px 40px'] }}
        transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
      />

      <div className="absolute bottom-6 right-8 font-mono text-[1.2vw] text-[#94A3B8]/60 tracking-widest z-0 pointer-events-none">
        GCFR-96D8BA6CA0FF4295
      </div>

      <div className="relative z-10 flex flex-col items-center w-full max-w-5xl">
        <motion.h2
          className="font-display text-[4.5vw] font-bold text-[#FFFFFF] tracking-tighter"
          initial={{ clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', opacity: 0 }}
          animate={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)', opacity: 1 }}
          transition={{ duration: 1, ease }}
        >
          OMNIX Governance Contract
        </motion.h2>

        <motion.div
          className="mt-2 font-display text-[2vw] text-[#D4A843] tracking-widest uppercase font-semibold"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={phase >= 1 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.6, ease }}
        >
          Sealed before Turn 0
        </motion.div>

        <div className="flex items-center mt-16 relative">
          {SEALS.map((seal, i) => (
            <div key={seal} className="flex items-center">
              <motion.div
                className="w-24 h-24 sm:w-[8vw] sm:h-[8vw] border border-[#D4A843] bg-[#D4A843]/10 rounded-sm flex items-center justify-center relative overflow-hidden"
                initial={{ clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', opacity: 0 }}
                animate={phase >= 2 + i ? { clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)', opacity: 1 } : { clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', opacity: 0 }}
                transition={{ duration: 0.6, ease }}
              >
                <span className="font-mono text-[2vw] font-bold text-[#FFFFFF] tracking-wider relative z-10">{seal}</span>
              </motion.div>
              {i < SEALS.length - 1 && (
                <div className="w-[3vw] h-[2px] mx-2 relative overflow-hidden">
                  <motion.div 
                    className="absolute inset-0 bg-[#D4A843]"
                    initial={{ scaleX: 0, transformOrigin: 'left' }}
                    animate={phase >= 7 ? { scaleX: 1 } : { scaleX: 0 }}
                    transition={{ duration: 0.4, delay: i * 0.1, ease }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        <motion.div
          className="mt-16 font-mono text-[1.6vw] text-[#E8E8E8] tracking-widest border border-white/10 px-8 py-3 bg-white/5"
          initial={{ opacity: 0, y: 20 }}
          animate={phase >= 8 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.8, ease }}
        >
          Algorithm: <span className="text-[#D4A843]">ML-DSA-65</span> (Dilithium-3, FIPS 204)
        </motion.div>
      </div>
    </motion.div>
  );
}

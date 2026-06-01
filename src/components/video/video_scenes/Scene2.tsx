import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

const SEALS = ['IAD', 'SAR', 'MFR', 'CPS', 'FPS'];

export function Scene2() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1500), // Subtitle
      ...SEALS.map((_, i) => setTimeout(() => setPhase(2 + i), 3000 + i * 800)), // Seals appear faster
      setTimeout(() => setPhase(7), 3000 + SEALS.length * 800 + 500), // Connections draw AFTER seals
      setTimeout(() => setPhase(8), 10000), // Algorithm
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center px-[10vw] z-10"
      initial={{ rotateY: -90, opacity: 0 }}
      animate={{ rotateY: 0, opacity: 1 }}
      exit={{ rotateY: 90, opacity: 0, filter: 'blur(10px)' }}
      transition={{ duration: 1, ease }}
      style={{ perspective: '1500px' }}
    >
      <div className="absolute inset-0 z-0 pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212,168,67,0.15), transparent 70%)' }} />
      
      {/* Subtle rotating hex ring background */}
      <motion.div
        className="absolute inset-0 z-0 flex items-center justify-center pointer-events-none opacity-20"
        animate={{ rotate: 360 }}
        transition={{ duration: 40, repeat: Infinity, ease: 'linear' }}
      >
        <svg viewBox="0 0 400 400" className="w-[80vw] h-[80vw] text-[#D4A843] stroke-current stroke-[0.5]" fill="none">
          <polygon points="200,10 370,105 370,295 200,390 30,295 30,105" />
          <polygon points="200,40 340,120 340,280 200,360 60,280 60,120" />
          <polygon points="200,70 310,135 310,265 200,330 90,265 90,135" />
          <circle cx="200" cy="200" r="180" strokeDasharray="5,10" />
        </svg>
      </motion.div>

      <div className="absolute bottom-6 right-8 font-mono text-[1.2vw] text-[#94A3B8]/60 tracking-widest z-0 pointer-events-none">
        GCFR-96D8BA6CA0FF4295
      </div>

      <div className="relative z-10 flex flex-col items-center w-full max-w-6xl">
        <motion.h2
          className="font-display text-[4.5vw] font-bold text-[#FFFFFF] tracking-tighter drop-shadow-lg"
          initial={{ clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', opacity: 0, y: 20 }}
          animate={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)', opacity: 1, y: 0 }}
          transition={{ duration: 1, ease }}
        >
          OMNIX Governance Contract
        </motion.h2>

        <motion.div
          className="mt-2 font-display text-[2vw] text-[#D4A843] tracking-widest uppercase font-semibold"
          initial={{ opacity: 0, scale: 0.9, filter: 'blur(10px)' }}
          animate={phase >= 1 ? { opacity: 1, scale: 1, filter: 'blur(0px)' } : { opacity: 0, scale: 0.9, filter: 'blur(10px)' }}
          transition={{ duration: 0.6, ease }}
        >
          Sealed before Turn 0
        </motion.div>

        <div className="flex items-center mt-20 relative">
          {SEALS.map((seal, i) => (
            <div key={seal} className="flex items-center">
              <motion.div
                className="w-28 h-28 sm:w-[9vw] sm:h-[9vw] border-2 border-[#D4A843] bg-[#0A0A0E]/80 backdrop-blur-md rounded-sm flex items-center justify-center relative overflow-hidden shadow-[0_0_20px_rgba(212,168,67,0.3)]"
                initial={{ scale: 0, opacity: 0, rotate: -45 }}
                animate={phase >= 2 + i ? { scale: 1, opacity: 1, rotate: 0 } : { scale: 0, opacity: 0, rotate: -45 }}
                transition={{ duration: 0.6, type: "spring", bounce: 0.4 }}
              >
                <span className="font-mono text-[2.2vw] font-bold text-[#FFFFFF] tracking-wider relative z-10">{seal}</span>
                {/* SEALED confirmation pulse */}
                {phase >= 7 && (
                  <motion.div
                    className="absolute inset-0 bg-[#D4A843]"
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: [0, 0.5, 0], scale: [0, 1.5, 2] }}
                    transition={{ duration: 1, ease: "easeOut", delay: i * 0.1 }}
                  />
                )}
              </motion.div>
              {i < SEALS.length - 1 && (
                <div className="w-[4vw] h-[3px] mx-2 relative overflow-hidden bg-white/10">
                  <motion.div 
                    className="absolute inset-0 bg-[#D4A843] shadow-[0_0_10px_#D4A843]"
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
          className="mt-20 font-mono text-[1.6vw] text-[#E8E8E8] tracking-widest border border-white/20 px-10 py-4 bg-white/5 backdrop-blur-md shadow-2xl relative overflow-hidden"
          initial={{ opacity: 0, y: 30, scale: 0.9 }}
          animate={phase >= 8 ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: 30, scale: 0.9 }}
          transition={{ duration: 0.8, type: "spring" }}
        >
          {/* Subtle light sweep across algorithm box */}
          <motion.div
            className="absolute top-0 bottom-0 w-[20%] bg-gradient-to-r from-transparent via-white/20 to-transparent skew-x-[-20deg]"
            animate={phase >= 8 ? { left: ['-50%', '150%'] } : { left: '-50%' }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
          />
          Algorithm: <span className="text-[#D4A843] font-bold">ML-DSA-65</span> (Dilithium-3, FIPS 204)
        </motion.div>
      </div>
    </motion.div>
  );
}

import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene6() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000), 
      setTimeout(() => setPhase(2), 2500), 
      setTimeout(() => setPhase(3), 4000), 
      setTimeout(() => setPhase(4), 6000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-transparent overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1.5 }}
    >
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <motion.div
          className="text-[1.5vw] text-[#3B82F6] font-mono tracking-widest mb-[5vh]"
          initial={{ opacity: 0, y: 20 }}
          animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 1 }}
        >
          POGC-GENESIS-E071CC96
        </motion.div>

        <div className="flex gap-8 mb-[8vh]">
          {['EU AI Act Art. 9/11', 'MiCA Title VI', 'DORA Art. 11'].map((reg, i) => (
             <motion.div
               key={i}
               className="px-6 py-2 border border-white/20 rounded-full text-[1.2vw] text-white/80"
               initial={{ opacity: 0, scale: 0.8 }}
               animate={phase >= 2 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.8 }}
               transition={{ duration: 0.5, delay: phase >= 2 ? i * 0.2 : 0 }}
             >
               {reg}
             </motion.div>
          ))}
        </div>

        <motion.div
          className="text-[3vw] font-bold text-white mb-[8vh] max-w-[60vw]"
          style={{ fontFamily: 'var(--font-display)' }}
          initial={{ opacity: 0, y: 20 }}
          animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 1 }}
        >
          The governance layer AI decisions trust.
        </motion.div>

        <motion.div
          className="text-[2vw] text-[#D4A843] tracking-[0.3em] font-bold uppercase"
          style={{ fontFamily: 'var(--font-display)' }}
          initial={{ opacity: 0, filter: 'blur(10px)' }}
          animate={phase >= 4 ? { opacity: 1, filter: 'blur(0px)' } : { opacity: 0, filter: 'blur(10px)' }}
          transition={{ duration: 2 }}
        >
          OMNIX QUANTUM
        </motion.div>
      </div>
    </motion.div>
  );
}
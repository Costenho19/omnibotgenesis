import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene5() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000),
      setTimeout(() => setPhase(2), 2500),
      setTimeout(() => setPhase(3), 4000),
      setTimeout(() => setPhase(4), 5500),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-transparent"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: 50 }}
      transition={{ duration: 1 }}
    >
      <div className="absolute top-[15vh] text-center w-full">
        <motion.h2
          className="text-[3vw] font-bold text-white"
          initial={{ opacity: 0, y: -20 }}
          animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -20 }}
          transition={{ duration: 0.8 }}
        >
          Verified offline.
        </motion.h2>
        <motion.h2
          className="text-[3vw] font-bold text-[#D4A843]"
          initial={{ opacity: 0, y: -20 }}
          animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: -20 }}
          transition={{ duration: 0.8 }}
        >
          Zero OMNIX access required.
        </motion.h2>
      </div>

      <div className="mt-[15vh] w-[50vw] bg-[#050508]/80 border border-white/20 rounded-lg p-8 font-mono text-[1.4vw] leading-loose shadow-2xl backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0 }}
          animate={phase >= 3 ? { opacity: 1 } : { opacity: 0 }}
        >
          <span className="text-[#3B82F6]">$</span> pip install oqs-python
        </motion.div>
        
        <motion.div
          className="mt-4"
          initial={{ opacity: 0 }}
          animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
        >
          <span className="text-[#3B82F6]">$</span> python verify.py
          <br/>
          <span className="text-green-400 mt-2 block">> exit code 0</span>
        </motion.div>
      </div>
    </motion.div>
  );
}
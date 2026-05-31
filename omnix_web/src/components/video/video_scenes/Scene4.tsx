import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene4() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000), // Show initial success
      setTimeout(() => setPhase(2), 3000), // Mutate hash
      setTimeout(() => setPhase(3), 4500), // Show fail
      setTimeout(() => setPhase(4), 6000), // Show exit code
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-transparent"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.5 }}
    >
      <motion.h2
        className="absolute top-[15vh] text-[3vw] font-bold text-white text-center w-full"
        initial={{ opacity: 0, y: -20 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -20 }}
        transition={{ duration: 0.8 }}
      >
        Tamper with one byte.<br />
        <span className="text-[#EF4444]">The chain breaks.</span>
      </motion.h2>

      <div className="mt-[10vh] w-[60vw] bg-[#050508]/90 border border-white/10 rounded-lg p-8 font-mono text-[1.5vw] flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <span className="text-white">INT-ADM-GCFR-SIG</span>
          {phase < 3 ? (
            <span className="text-green-500">✓ PASS</span>
          ) : (
            <span className="text-[#EF4444]">✗ FAIL</span>
          )}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-white">INT-ADM-GCFR-HASH</span>
          {phase < 2 ? (
            <span className="text-green-500">✓ PASS</span>
          ) : (
            <motion.span 
              className="text-[#EF4444] font-bold"
              initial={{ scale: 1.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 400, damping: 10 }}
            >
              ✗ FAIL
            </motion.span>
          )}
        </div>

        <motion.div
          className="border-t border-white/10 pt-6 mt-2"
          initial={{ opacity: 0 }}
          animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
        >
          {phase >= 4 ? (
             <span className="text-[#EF4444] font-bold">{'>'} exit code 1</span>
          ) : (
             <span className="text-green-500">{'>'} exit code 0</span>
          )}
        </motion.div>
      </div>

      {phase >= 3 && (
         <motion.div
           className="absolute inset-0 border-[4px] border-[#EF4444] pointer-events-none mix-blend-screen opacity-20"
           initial={{ opacity: 0 }}
           animate={{ opacity: [0, 0.4, 0] }}
           transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse" }}
         />
      )}
    </motion.div>
  );
}
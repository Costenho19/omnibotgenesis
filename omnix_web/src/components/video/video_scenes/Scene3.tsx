import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene3() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const sequence = [
      setTimeout(() => setStep(1), 1000),
      setTimeout(() => setStep(2), 2500),
      setTimeout(() => setStep(3), 4000),
      setTimeout(() => setStep(4), 5500),
      setTimeout(() => setStep(5), 7000),
    ];
    return () => sequence.forEach(t => clearTimeout(t));
  }, []);

  const sessionStr = "SESSION-B9199C8CC9394304";

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-transparent"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, filter: 'blur(10px)' }}
      transition={{ duration: 1 }}
    >
      <div className="absolute top-[15vh] left-[15vw] z-10">
        <motion.h2 
          className="text-[3vw] font-bold text-white mb-2"
          initial={{ opacity: 0, x: -20 }}
          animate={step >= 1 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
          transition={{ duration: 0.8 }}
        >
          187 integrity checks.
        </motion.h2>
        <motion.h2 
          className="text-[3vw] font-bold text-[#D4A843]"
          initial={{ opacity: 0, x: -20 }}
          animate={step >= 2 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
          transition={{ duration: 0.8 }}
        >
          Every turn attested.
        </motion.h2>
      </div>

      <div className="absolute right-[15vw] top-[30vh] w-[30vw] border border-[#3B82F6]/30 bg-[#050508]/90 p-6 rounded-lg font-mono text-[1.2vw]">
        <motion.div 
          className="mb-4 text-[#3B82F6]"
          initial={{ opacity: 0 }}
          animate={step >= 3 ? { opacity: 1 } : { opacity: 0 }}
        >
          {'>'} running {sessionStr}
        </motion.div>
        
        <motion.div 
          className="mb-4 text-white"
          initial={{ opacity: 0 }}
          animate={step >= 4 ? { opacity: 1 } : { opacity: 0 }}
        >
          {'>'} [9 steps] 187 checks · <span className="text-green-500">0 FAIL</span>
        </motion.div>

        <motion.div 
          className="text-[#D4A843] font-bold mt-8 border-t border-[#D4A843]/20 pt-4"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={step >= 5 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
        >
          VERDICT: MANDATE-BOUND
        </motion.div>
      </div>

      {step >= 3 && (
        <motion.img 
          src={`${import.meta.env.BASE_URL}images/quantum_nodes.png`}
          alt="Quantum Nodes"
          className="absolute left-0 bottom-0 w-[40vw] opacity-20 object-contain mix-blend-screen"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.2 }}
          transition={{ duration: 2 }}
        />
      )}
    </motion.div>
  );
}
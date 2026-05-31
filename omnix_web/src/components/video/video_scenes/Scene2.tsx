import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function Scene2() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 2000),
      setTimeout(() => setPhase(3), 5000),
      setTimeout(() => setPhase(4), 8000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  const hashStr = "GCFR-96D8BA6CA0FF4295";

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-transparent"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
    >
      <motion.div 
        className="text-center z-10"
        initial={{ opacity: 0, y: -20 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -20 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <h2 className="text-[2.5vw] font-bold text-white mb-2" style={{ fontFamily: 'var(--font-display)' }}>
          A cryptographic governance contract is sealed
        </h2>
        <h2 className="text-[2.5vw] font-bold text-[#D4A843]" style={{ fontFamily: 'var(--font-display)' }}>
          BEFORE execution begins.
        </h2>
      </motion.div>

      <div className="relative mt-[8vh] flex flex-col items-center">
        <motion.div
          className="text-[3vw] text-[#3B82F6] font-mono tracking-widest"
          initial={{ opacity: 0 }}
          animate={phase >= 2 ? { opacity: 1 } : { opacity: 0 }}
        >
          {hashStr.split('').map((char, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0 }}
              animate={phase >= 2 ? { opacity: 1 } : { opacity: 0 }}
              transition={{ duration: 0.1, delay: phase >= 2 ? i * 0.1 : 0 }}
            >
              {char}
            </motion.span>
          ))}
        </motion.div>

        <motion.div
          className="mt-[4vh] px-6 py-2 border border-[#D4A843]/30 bg-[#050508]/80 backdrop-blur-md rounded-md"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={phase >= 3 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <span className="text-[1.5vw] text-[#D4A843] font-mono">
            ML-DSA-65 (Dilithium-3, FIPS 204)
          </span>
        </motion.div>
      </div>

      {phase >= 4 && (
        <motion.img 
          src={`${import.meta.env.BASE_URL}images/crypto_seal.png`}
          alt="Cryptographic Seal"
          className="absolute right-[10%] top-[20%] w-[30vh] opacity-20 object-contain mix-blend-screen"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 0.2, scale: 1 }}
          transition={{ duration: 2 }}
        />
      )}
    </motion.div>
  );
}
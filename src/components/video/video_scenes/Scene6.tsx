import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

export function Scene6() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),  // company name
      setTimeout(() => setPhase(2), 1500), // divider
      setTimeout(() => setPhase(3), 2000), // POGC ID
      setTimeout(() => setPhase(4), 2800), // Regulations
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.5 }}
      transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Background pulsing circle */}
      <motion.div 
        className="absolute w-[80vw] h-[80vw] rounded-full bg-[#D4A843] opacity-[0.03] blur-[100px]"
        animate={{ scale: [1, 1.1, 1], opacity: [0.03, 0.05, 0.03] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Floating Particles */}
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-[4px] h-[4px] bg-[#D4A843] rounded-full opacity-30"
          initial={{
            x: `${Math.random() * 100}vw`,
            y: '110vh',
            scale: Math.random() * 2
          }}
          animate={{
            y: '-10vh',
            x: `+=${Math.random() * 10 - 5}vw`
          }}
          transition={{
            duration: 8 + Math.random() * 5,
            repeat: Infinity,
            delay: Math.random() * 5,
            ease: "linear"
          }}
        />
      ))}

      <div className="relative z-10 flex flex-col items-center">
        {/* Company Name */}
        <div className="overflow-hidden mb-[2vh]">
          <motion.h1 
            className="font-display font-black text-[6vw] tracking-widest text-white"
            initial={{ y: '100%' }}
            animate={phase >= 1 ? { y: 0 } : { y: '100%' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            OMNIX QUANTUM LTD
          </motion.h1>
        </div>

        {/* Divider */}
        <motion.div 
          className="w-[40vw] h-[1px] bg-[#D4A843]/50 mb-[4vh]"
          initial={{ scaleX: 0 }}
          animate={phase >= 2 ? { scaleX: 1 } : { scaleX: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        />

        {/* Content */}
        <div className="flex flex-col items-center gap-[1.5vh] text-center">
          <motion.div
            className="font-mono text-[1.8vw] text-[#C8C8D0]"
            initial={{ opacity: 0, y: 10 }}
            animate={phase >= 3 ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
            transition={{ duration: 0.6 }}
          >
            POGC-GENESIS-E071CC96
          </motion.div>

          <motion.div
            className="font-mono text-[1.2vw] text-[#C8C8D0]/60"
            initial={{ opacity: 0, y: 10 }}
            animate={phase >= 4 ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
            transition={{ duration: 0.6 }}
          >
            EU AI Act Art. 9 · 11 · MiCA · DORA · NIST AU-2
            <br/>
            First Proof of Governance Registry · 2026
          </motion.div>
        </div>
      </div>

      {/* URL */}
      <motion.div 
        className="absolute bottom-[4vh] right-[4vw] font-mono text-[1vw] text-[#C8C8D0]/40"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 3, duration: 1 }}
      >
        omnixquantum.com
      </motion.div>
    </motion.div>
  );
}
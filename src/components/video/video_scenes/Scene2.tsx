import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

export function Scene2() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 300),  // headline clips in
      setTimeout(() => setPhase(2), 800),  // line 1
      setTimeout(() => setPhase(3), 1600), // line 2
      setTimeout(() => setPhase(4), 2400), // line 3
      setTimeout(() => setPhase(5), 3200), // line 4
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  const lines = [
    "algorithm: ML-DSA-65 (FIPS 204)",
    "session:   SESSION-B9199C8CC9394304",
    "sealed:    BEFORE TURN 0",
    "status:    MANDATE-BOUND"
  ];

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: -50 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Background grid */}
      <motion.div 
        className="absolute inset-0"
        style={{
          backgroundImage: 'linear-gradient(#111 1px, transparent 1px), linear-gradient(90deg, #111 1px, transparent 1px)',
          backgroundSize: '4vw 4vw'
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.3, y: ['0vw', '4vw'] }}
        transition={{ duration: 5, ease: "linear", repeat: Infinity }}
      />

      {/* Headline */}
      <motion.div
        className="mb-[4vh] overflow-hidden"
      >
        <motion.h2 
          className="font-display font-bold text-[3vw] tracking-[0.5em] text-[#D4A843]"
          initial={{ y: '100%' }}
          animate={phase >= 1 ? { y: 0 } : { y: '100%' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          GOVERNANCE CONTRACT
        </motion.h2>
      </motion.div>

      {/* Divider */}
      <motion.div 
        className="w-[60vw] h-[2px] bg-[#D4A843] mb-[6vh]"
        initial={{ scaleX: 2, opacity: 0.3 }}
        animate={{ scaleX: 1, opacity: 1 }}
        transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
      />

      {/* Code Block */}
      <div className="w-[60vw] font-mono text-[2vw] text-[#C8C8D0] flex flex-col gap-[2vh]">
        {lines.map((line, i) => {
          const linePhase = i + 2;
          return (
            <div key={i} className="flex relative">
              <motion.span
                initial={{ opacity: 0 }}
                animate={phase >= linePhase ? { opacity: 1 } : { opacity: 0 }}
                transition={{ duration: 0.1 }}
              >
                {line}
              </motion.span>
              
              {/* Typewriter Cursor */}
              {phase === linePhase && (
                <motion.div 
                  className="w-[1vw] h-[2.5vw] bg-[#D4A843] ml-[1vw]"
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.2, repeat: Infinity, repeatType: 'reverse' }}
                />
              )}
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
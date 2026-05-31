import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];
const clipReveal = {
  initial: { clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', opacity: 0 },
  animate: { clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)', opacity: 1 },
};

export function Scene1() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 800),
      setTimeout(() => setPhase(2), 3500),
      setTimeout(() => setPhase(3), 6000),
      setTimeout(() => setPhase(4), 8000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center px-[10vw]"
      initial="initial" animate="animate" exit={{ opacity: 0, scale: 1.1, filter: 'blur(20px)' }}
      transition={{ duration: 0.8, ease }}
      {...clipReveal}
    >
      <motion.div 
        className="absolute w-[150vw] h-[150vw] font-mono text-[10vw] font-bold text-[#FFFFFF] opacity-[0.04] break-all leading-none z-0 pointer-events-none"
        animate={{ y: ['0%', '-5%'], x: ['0%', '-2%'] }}
        transition={{ duration: 20, ease: 'linear', repeat: Infinity }}
      >
        {Array(50).fill('SESSION-B9199C8CC9394304 ').join('')}
      </motion.div>

      <div className="relative z-10 flex flex-col items-center w-full max-w-6xl text-center">
        <motion.h1
          className="font-display text-[5vw] font-bold text-[#FFFFFF] tracking-tighter leading-tight"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, ease }}
        >
          AI decisions worth <span className="text-[#D4A843]">$50,000,000</span>
        </motion.h1>

        {phase >= 1 && (
          <div className="mt-12 flex flex-col gap-4 font-display text-[2.5vw] text-[#94A3B8] font-medium tracking-wide">
            <motion.div
              initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, ease }}
            >
              No audit trail.
            </motion.div>
            {phase >= 2 && (
              <motion.div
                initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, ease }}
              >
                No verification.
              </motion.div>
            )}
            {phase >= 3 && (
              <motion.div
                initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, ease }}
              >
                No accountability.
              </motion.div>
            )}
          </div>
        )}

        {phase >= 4 && (
          <motion.div
            className="mt-16 font-display text-[4vw] font-bold text-[#FFFFFF] tracking-widest"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.8, ease }}
          >
            Until now<motion.span 
              className="text-[#D4A843]"
              animate={{ textShadow: ['0 0 0px #D4A843', '0 0 30px #D4A843', '0 0 0px #D4A843'] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            >.</motion.span>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
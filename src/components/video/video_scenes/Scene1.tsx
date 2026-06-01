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
      setTimeout(() => setPhase(1), 1500),
      setTimeout(() => setPhase(2), 3000),
      setTimeout(() => setPhase(3), 4500),
      setTimeout(() => setPhase(4), 8000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center px-[10vw] z-10"
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

      {/* Sweeping scanline over SESSION hash backdrop */}
      <motion.div
        className="absolute inset-0 w-full h-[15vh] bg-gradient-to-b from-transparent via-[#D4A843]/10 to-transparent pointer-events-none z-0"
        animate={{ y: ['-20vh', '120vh'] }}
        transition={{ duration: 3, ease: 'linear', repeat: Infinity }}
      />

      <motion.div
        className="absolute w-[40vw] h-[40vw] rounded-full blur-[100px] z-0 pointer-events-none"
        animate={{ 
          scale: [1, 1.2, 1],
          opacity: [0.08, 0.15, 0.08],
          backgroundColor: ['#D4A843', '#D4A843', '#D4A843']
        }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        style={{ top: '10%', left: '10%' }}
      />

      <motion.div
        className="absolute w-[50vw] h-[50vw] rounded-full blur-[120px] z-0 pointer-events-none"
        animate={{ 
          scale: [1.2, 1, 1.2],
          opacity: [0.08, 0.15, 0.08],
          backgroundColor: ['#D4A843', '#D4A843', '#D4A843']
        }}
        transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        style={{ bottom: '10%', right: '10%' }}
      />

      <div className="relative z-10 flex flex-col items-center w-full max-w-6xl text-center">
        <motion.h1
          className="font-display text-[5vw] font-bold text-[#FFFFFF] tracking-tighter leading-tight drop-shadow-xl"
        >
          {"AI decisions worth ".split('').map((char, i) => (
            <motion.span key={i} className="inline-block"
              initial={{ opacity: 0, scale: 0, rotate: 10, filter: 'blur(10px)' }}
              animate={{ opacity: 1, scale: 1, rotate: 0, filter: 'blur(0px)' }}
              transition={{ duration: 0.6, delay: i * 0.03, ease }}
            >
              {char === ' ' ? '\u00A0' : char}
            </motion.span>
          ))}
          <span className="text-[#D4A843]">
            {"$50,000,000".split('').map((char, i) => (
              <motion.span key={i} className="inline-block relative"
                initial={{ opacity: 0, scale: 0, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.6, delay: ("AI decisions worth ".length * 0.03) + i * 0.05, ease }}
              >
                {char === ' ' ? '\u00A0' : char}
              </motion.span>
            ))}
          </span>
        </motion.h1>

        <div className="mt-12 flex flex-col gap-4 font-display text-[2.5vw] text-[#94A3B8] font-medium tracking-wide drop-shadow-lg">
          <motion.div
            initial={{ opacity: 0, y: 30, filter: 'blur(5px)' }}
            animate={phase >= 1 ? { opacity: 1, y: 0, filter: 'blur(0px)' } : { opacity: 0, y: 30, filter: 'blur(5px)' }}
            transition={{ duration: 0.8, ease }}
          >
            No audit trail.
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 30, filter: 'blur(5px)' }}
            animate={phase >= 2 ? { opacity: 1, y: 0, filter: 'blur(0px)' } : { opacity: 0, y: 30, filter: 'blur(5px)' }}
            transition={{ duration: 0.8, ease }}
          >
            No verification.
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 30, filter: 'blur(5px)' }}
            animate={phase >= 3 ? { opacity: 1, y: 0, filter: 'blur(0px)' } : { opacity: 0, y: 30, filter: 'blur(5px)' }}
            transition={{ duration: 0.8, ease }}
          >
            No accountability.
          </motion.div>
        </div>

        <motion.div
          className="mt-16 font-display text-[4.5vw] font-bold text-[#FFFFFF] tracking-widest relative"
          initial={{ opacity: 0 }}
          animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
        >
          {"Until now.".split('').map((char, i) => (
            <motion.span key={i} className="inline-block"
              initial={{ opacity: 0, y: 20, scale: 1.2 }}
              animate={phase >= 4 ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: 20, scale: 1.2 }}
              transition={{ duration: 0.4, delay: i * 0.1, ease: [0.16, 1, 0.3, 1] }}
            >
              {char === ' ' ? '\u00A0' : char}
            </motion.span>
          ))}
          {/* Amber glow flash on completion */}
          <motion.div
            className="absolute inset-0 z-[-1] rounded-full blur-[40px] bg-[#D4A843]/50 pointer-events-none"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={phase >= 4 ? { opacity: [0, 1, 0], scale: [0.5, 1.5, 1.8] } : { opacity: 0, scale: 0.5 }}
            transition={{ duration: 1.5, delay: "Until now.".length * 0.1, ease: "easeOut" }}
          />
        </motion.div>
      </div>
    </motion.div>
  );
}

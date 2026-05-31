import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

export function Scene4() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 300),
      setTimeout(() => setPhase(2), 1000),
      setTimeout(() => setPhase(3), 1600),
      setTimeout(() => setPhase(4), 2200),
      setTimeout(() => setPhase(5), 3200),
      setTimeout(() => setPhase(6), 4000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      style={{ backgroundColor: '#100303' }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Scanner Lines */}
      {phase >= 4 && phase < 6 && (
        <motion.div
          className="absolute left-0 right-0 h-[18vh] pointer-events-none z-0"
          style={{
            background: 'linear-gradient(to bottom, transparent, rgba(229,62,62,0.18), transparent)',
          }}
          initial={{ top: '-20vh' }}
          animate={{ top: '120vh' }}
          transition={{ duration: 1.2, ease: 'linear' }}
        />
      )}

      {/* GCFR Hash with strike */}
      <div className="relative z-10 mb-[6vh]">
        <motion.div
          className="font-mono text-[3.5vw] text-white tracking-wider"
          initial={{ opacity: 0, y: 20 }}
          animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.5 }}
        >
          GCFR-96D8BA6CA0FF4295
        </motion.div>

        {/* Red strike line */}
        {phase >= 2 && (
          <svg
            className="absolute inset-0 w-full h-full overflow-visible"
            preserveAspectRatio="none"
          >
            <motion.line
              x1="0%" y1="100%" x2="100%" y2="0%"
              stroke="#E53E3E"
              strokeWidth="5"
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            />
          </svg>
        )}
      </div>

      {/* FAIL messages */}
      <div className="flex flex-col items-center gap-[2vh] mb-[8vh] z-10">
        <motion.div
          className="font-mono text-[2.5vw] font-bold text-[#E53E3E]"
          initial={{ opacity: 0, x: -40 }}
          animate={phase >= 3 ? { opacity: 1, x: 0 } : { opacity: 0, x: -40 }}
          transition={{ duration: 0.4 }}
        >
          INT-ADM-GCFR-HASH FAIL
        </motion.div>
        <motion.div
          className="font-mono text-[2.5vw] font-bold text-[#E53E3E]"
          initial={{ opacity: 0, x: 40 }}
          animate={phase >= 3 ? { opacity: 1, x: 0 } : { opacity: 0, x: 40 }}
          transition={{ duration: 0.4, delay: 0.12 }}
        >
          INT-ADM-GCFR-SIG FAIL
        </motion.div>
      </div>

      {/* HALT PROVEN badge */}
      <motion.div
        className="relative z-20"
        initial={{ opacity: 0, scale: 0.5 }}
        animate={phase >= 6 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.5 }}
        transition={{ type: 'spring', stiffness: 320, damping: 22 }}
      >
        <div
          className="absolute inset-0 rounded-sm -m-[1.5vw]"
          style={{
            backgroundColor: '#D4A843',
            transform: 'skewX(-10deg)',
          }}
        />
        <h2 className="relative font-display font-black text-[8vw] leading-none text-white px-[2vw]">
          HALT PROVEN
        </h2>
      </motion.div>
    </motion.div>
  );
}

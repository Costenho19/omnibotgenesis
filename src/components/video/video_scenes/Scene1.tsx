import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

export function Scene1() {
  const [phase, setPhase] = useState(0);
  const [amount, setAmount] = useState('');

  useEffect(() => {
    const target = '$50,000,000';
    let current = '';
    let i = 0;
    const interval = setInterval(() => {
      if (i < target.length) {
        current += target[i];
        setAmount(current);
        i++;
      } else {
        clearInterval(interval);
      }
    }, 40);

    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 1200),
      setTimeout(() => setPhase(3), 2000),
      setTimeout(() => setPhase(4), 2800),
    ];
    return () => {
      clearInterval(interval);
      timers.forEach(clearTimeout);
    };
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col justify-center px-[10vw]"
      initial={{ clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)' }}
      animate={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)' }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.8, ease }}
    >
      <div className="relative z-10 max-w-5xl">
        <motion.p
          className="text-[#94A3B8] font-mono text-[1.5vw] mb-4 tracking-[0.3em] uppercase"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease, delay: 0.2 }}
        >
          AI decided. No one could prove it.
        </motion.p>

        <div className="flex flex-col gap-6 mt-8">
          <div className="flex items-baseline gap-6">
            <motion.div
              className="font-mono text-[8vw] text-[#FFFFFF] font-bold tracking-tighter"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              {amount}
            </motion.div>
          </div>

          <div className="flex flex-col gap-3 font-mono text-[1.4vw]">
            <motion.div
              className="text-[#94A3B8] tracking-widest uppercase"
              initial={{ opacity: 0, x: -20 }}
              animate={phase >= 1 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
              transition={{ duration: 0.5, ease }}
            >
              Cross-border transfer · SWIFT MT202 / XRPL RLUSD
            </motion.div>
            <motion.div
              className="text-[#E53E3E] tracking-widest uppercase"
              initial={{ opacity: 0, x: -20 }}
              animate={phase >= 2 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
              transition={{ duration: 0.5, ease }}
            >
              [!] No audit trail
            </motion.div>
            <motion.div
              className="text-[#E53E3E] tracking-widest uppercase"
              initial={{ opacity: 0, x: -20 }}
              animate={phase >= 3 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
              transition={{ duration: 0.5, ease }}
            >
              [!] No cryptographic proof
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

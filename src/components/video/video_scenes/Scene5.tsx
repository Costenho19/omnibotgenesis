import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];
const clipReveal = {
  initial: { clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)', opacity: 0 },
  animate: { clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)', opacity: 1 },
};

const CMD = '$ python verify_treasury_execution_trace.py package.json';

export function Scene5() {
  const [phase, setPhase] = useState(0);
  const [cmdText, setCmdText] = useState('');

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      if (i <= CMD.length) {
        setCmdText(CMD.substring(0, i));
        i++;
      } else {
        clearInterval(interval);
      }
    }, 40);

    const timers = [
      setTimeout(() => setPhase(1), CMD.length * 40 + 500), // Output appears
      setTimeout(() => setPhase(2), CMD.length * 40 + 2500), // Statement
      setTimeout(() => setPhase(3), CMD.length * 40 + 4500), // Badges
    ];

    return () => {
      clearInterval(interval);
      timers.forEach(t => clearTimeout(t));
    };
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center px-[10vw]"
      initial="initial" animate="animate" exit={{ opacity: 0, scale: 1.1, filter: 'blur(20px)' }}
      transition={{ duration: 0.8, ease }}
      {...clipReveal}
    >
      <div className="w-full max-w-5xl">
        <div className="bg-[#0A0A0E] border border-[#333333] p-8 rounded-sm shadow-2xl min-h-[30vh] flex flex-col justify-end font-mono text-[1.8vw] mb-16">
          <div className="text-[#D4A843] tracking-wider mb-6">
            {cmdText}<motion.span animate={{ opacity: [1,0] }} transition={{ repeat: Infinity, duration: 0.8 }}>_</motion.span>
          </div>
          {phase >= 1 && (
            <motion.div 
              className="text-[#E8E8E8] tracking-widest flex flex-col gap-2"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            >
              <div>Verifying ML-DSA-65 signatures... OK</div>
              <div>Checking 187 governance predicates... OK</div>
              <div className="text-[#22C55E] font-bold mt-4">187/187 checks PASSED · exit code 0</div>
            </motion.div>
          )}
        </div>

        {phase >= 2 && (
          <motion.div 
            className="text-center font-display text-[2.5vw] font-bold text-[#FFFFFF] tracking-wide mb-12"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}
          >
            Zero trust. Zero OMNIX infrastructure. Zero account required.
          </motion.div>
        )}

        <div className="flex justify-center gap-6">
          {['EU AI Act Art. 9/11', 'MiCA Title VI', 'DORA Art. 11', 'NIST AU-2'].map((badge, i) => (
            phase >= 3 && (
              <motion.div
                key={badge}
                className="border border-[#D4A843]/40 bg-[#D4A843]/5 px-6 py-2 rounded-full font-mono text-[1vw] text-[#D4A843] tracking-widest"
                initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4, delay: i * 0.15 }}
              >
                {badge}
              </motion.div>
            )
          ))}
        </div>
      </div>
    </motion.div>
  );
}
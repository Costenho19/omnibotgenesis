import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

const CMD1 = '$ pip install oqs-python';
const CMD2 = '$ python verify_treasury_execution_trace.py package.json';

export function Scene5() {
  const [phase, setPhase] = useState(0);
  const [cmd1Text, setCmd1Text] = useState('');
  const [cmd2Text, setCmd2Text] = useState('');

  useEffect(() => {
    let i1 = 0;
    const interval1 = setInterval(() => {
      if (i1 <= CMD1.length) {
        setCmd1Text(CMD1.substring(0, i1));
        i1++;
      } else {
        clearInterval(interval1);
        setTimeout(() => setPhase(0.5), 300); // Trigger CMD2
      }
    }, 30);

    let interval2: ReturnType<typeof setInterval>;

    const timers = [
      setTimeout(() => {
        let i2 = 0;
        interval2 = setInterval(() => {
          if (i2 <= CMD2.length) {
            setCmd2Text(CMD2.substring(0, i2));
            i2++;
          } else {
            clearInterval(interval2);
          }
        }, 30);
      }, CMD1.length * 30 + 800),

      setTimeout(() => setPhase(1), CMD1.length * 30 + CMD2.length * 30 + 1500), // Output appears
      setTimeout(() => setPhase(2), CMD1.length * 30 + CMD2.length * 30 + 3500), // Statement
      setTimeout(() => setPhase(3), CMD1.length * 30 + CMD2.length * 30 + 5500), // Badges
    ];

    return () => {
      clearInterval(interval1);
      clearInterval(interval2);
      timers.forEach(t => clearTimeout(t));
    };
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center px-[10vw] z-10 bg-[#050508]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ scale: 0.9, opacity: 0 }}
      transition={{ duration: 0.8, ease }}
    >
      <div className="absolute inset-0 z-0 pointer-events-none opacity-5 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMDUiLz4KPC9zdmc+')] mix-blend-overlay" />
      
      <div className="w-full max-w-5xl relative z-10">
        <div className="bg-[#0A0A0E]/90 backdrop-blur-md border border-[#333333] p-8 rounded-sm shadow-[0_0_60px_rgba(0,0,0,0.8)] min-h-[35vh] flex flex-col justify-end font-mono text-[1.8vw] mb-16 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#333333] to-transparent opacity-30" />
          
          <div className="flex flex-col gap-4">
            <div className="text-[#94A3B8] tracking-wider">
              {cmd1Text}{phase < 0.5 && <motion.span animate={{ opacity: [1,0] }} transition={{ repeat: Infinity, duration: 0.5 }}>_</motion.span>}
            </div>
            {phase >= 0.5 && (
              <div className="text-[#94A3B8] tracking-widest text-[1.4vw] mb-4">
                Successfully installed oqs-python-1.2.0
              </div>
            )}
            
            {phase >= 0.5 && (
              <div className="text-[#D4A843] tracking-wider mb-6">
                {cmd2Text}{phase >= 0.5 && phase < 1 && <motion.span animate={{ opacity: [1,0] }} transition={{ repeat: Infinity, duration: 0.5 }}>_</motion.span>}
              </div>
            )}

            <div className="flex flex-col gap-2 h-[8vw] overflow-hidden">
              <motion.div 
                className="text-[#E8E8E8] tracking-widest"
                initial={{ opacity: 0, y: 10 }} 
                animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
              >
                Verifying ML-DSA-65 signatures... OK
              </motion.div>
              <motion.div 
                className="text-[#E8E8E8] tracking-widest"
                initial={{ opacity: 0, y: 10 }} 
                animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
                transition={{ delay: 0.2 }}
              >
                Checking 187 governance predicates... OK
              </motion.div>
              <motion.div 
                className="text-[#22C55E] font-bold mt-2"
                initial={{ opacity: 0, y: 10 }} 
                animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
                transition={{ delay: 0.4 }}
              >
                187/187 checks PASSED · exit code 0
              </motion.div>
            </div>
          </div>
        </div>

        <motion.div 
          className="text-center font-display text-[2.5vw] font-bold text-[#FFFFFF] tracking-wide mb-12"
          initial={{ opacity: 0, y: 20 }} 
          animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.8, ease }}
        >
          Zero trust. Zero OMNIX infrastructure. Zero account required.
        </motion.div>

        <div className="flex justify-center gap-6">
          {['EU AI Act Art. 9/11', 'MiCA Title VI', 'DORA Art. 11', 'NIST AU-2'].map((badge, i) => (
            <motion.div
              key={badge}
              className="border border-[#D4A843]/40 bg-[#D4A843]/5 px-6 py-2 rounded-full font-mono text-[1vw] text-[#D4A843] tracking-widest"
              initial={{ opacity: 0, scale: 0.8, y: 20 }} 
              animate={phase >= 3 ? { opacity: 1, scale: 1, y: 0 } : { opacity: 0, scale: 0.8, y: 20 }}
              transition={{ duration: 0.6, delay: i * 0.15, type: 'spring' }}
            >
              {badge}
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

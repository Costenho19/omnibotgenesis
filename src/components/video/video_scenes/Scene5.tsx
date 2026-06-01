import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

const CMD1 = '$ pip install oqs-python';
const CMD2 = '$ python verify_treasury_execution_trace.py package.json';

export function Scene5() {
  const [phase, setPhase] = useState(0);
  const [cmd1Text, setCmd1Text] = useState('');
  const [cmd2Text, setCmd2Text] = useState('');
  const [progress, setProgress] = useState(0);

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
    }, 25); // Faster typing

    let interval2: ReturnType<typeof setInterval>;
    let progressInterval: ReturnType<typeof setInterval>;

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
        }, 25);
      }, CMD1.length * 25 + 600),

      setTimeout(() => {
        setPhase(1); // Output starts
        progressInterval = setInterval(() => {
          setProgress(p => {
            if (p >= 100) {
              clearInterval(progressInterval);
              return 100;
            }
            return p + 2;
          });
        }, 20);
      }, CMD1.length * 25 + CMD2.length * 25 + 1200),

      setTimeout(() => setPhase(2), CMD1.length * 25 + CMD2.length * 25 + 3200), // Statement
      setTimeout(() => setPhase(3), CMD1.length * 25 + CMD2.length * 25 + 4800), // Badges
    ];

    return () => {
      clearInterval(interval1);
      clearInterval(interval2);
      if(progressInterval) clearInterval(progressInterval);
      timers.forEach(t => clearTimeout(t));
    };
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center px-[8vw] z-10 bg-[#050508]"
      initial={{ y: '100%', opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: '-100%', opacity: 0, scale: 0.9 }}
      transition={{ duration: 1, ease }}
    >
      <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.03] bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMDUiLz4KPC9zdmc+')] mix-blend-overlay" />
      
      <div className="w-full max-w-6xl relative z-10 flex flex-col items-center">
        
        <div className="w-full bg-[#0A0A0E]/90 backdrop-blur-xl border border-[#333333] p-10 rounded-sm shadow-[0_0_80px_rgba(0,0,0,0.6)] min-h-[40vh] flex flex-col justify-end font-mono text-[1.8vw] mb-16 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#22C55E] to-transparent opacity-50" />
          
          <div className="flex justify-between items-end">
            <div className="flex flex-col gap-5 w-3/4">
              <div className="text-[#94A3B8] tracking-wider font-semibold">
                {cmd1Text}{phase < 0.5 && <motion.span animate={{ opacity: [1,0] }} transition={{ repeat: Infinity, duration: 0.5 }}>_</motion.span>}
              </div>
              {phase >= 0.5 && (
                <div className="text-[#94A3B8] tracking-widest text-[1.4vw] mb-2 opacity-80">
                  Successfully installed oqs-python-1.2.0
                </div>
              )}
              
              {phase >= 0.5 && (
                <div className="text-[#D4A843] tracking-wider mb-8 font-bold">
                  {cmd2Text}{phase >= 0.5 && phase < 1 && <motion.span animate={{ opacity: [1,0] }} transition={{ repeat: Infinity, duration: 0.5 }}>_</motion.span>}
                </div>
              )}

              <div className="flex flex-col gap-3 h-[10vw] overflow-hidden">
                <motion.div 
                  className="text-[#E8E8E8] tracking-widest flex items-center gap-3"
                  initial={{ opacity: 0, x: -20 }} 
                  animate={phase >= 1 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
                  transition={{ duration: 0.4 }}
                >
                  Verifying ML-DSA-65 signatures... <span className="text-[#22C55E]">OK</span>
                </motion.div>
                <motion.div 
                  className="text-[#E8E8E8] tracking-widest flex items-center gap-3"
                  initial={{ opacity: 0, x: -20 }} 
                  animate={phase >= 1 ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
                  transition={{ delay: 0.2, duration: 0.4 }}
                >
                  Checking 187 governance predicates... <span className="text-[#22C55E]">OK</span>
                </motion.div>
                {progress === 100 && (
                  <motion.div 
                    className="text-[#22C55E] font-bold mt-4 text-[2vw] bg-[#22C55E]/10 p-3 border-l-4 border-[#22C55E] w-max"
                    initial={{ opacity: 0, scale: 0.9 }} 
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ type: "spring", bounce: 0.5 }}
                  >
                    187/187 PASSED · exit code 0
                  </motion.div>
                )}
              </div>
            </div>

            {/* Progress Ring */}
            <motion.div 
              className="w-[12vw] h-[12vw] relative mr-10"
              initial={{ opacity: 0, scale: 0 }}
              animate={phase >= 1 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0 }}
              transition={{ duration: 0.6, ease }}
            >
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#333333" strokeWidth="10" />
                <motion.circle 
                  cx="50" cy="50" r="45" 
                  fill="none" stroke="#22C55E" strokeWidth="10"
                  strokeDasharray={283}
                  strokeDashoffset={283 - (283 * progress) / 100}
                  strokeLinecap="round"
                  style={{ filter: 'drop-shadow(0 0 8px #22C55E)' }}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center flex-col">
                <span className="font-mono font-bold text-[2vw] text-white">{progress}%</span>
              </div>
            </motion.div>
          </div>
        </div>

        <motion.div 
          className="text-center font-display text-[2.8vw] font-bold text-[#FFFFFF] tracking-wide mb-14 drop-shadow-md"
          initial={{ opacity: 0, y: 30 }} 
          animate={phase >= 2 ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8, ease }}
        >
          Zero trust. Zero OMNIX infrastructure. Zero account required.
        </motion.div>

        <div className="flex justify-center gap-8 w-full">
          {['EU AI Act Art. 9/11', 'MiCA Title VI', 'DORA Art. 11', 'NIST AU-2'].map((badge, i) => (
            <motion.div
              key={badge}
              className="border-2 border-[#D4A843]/60 bg-[#D4A843]/10 px-8 py-3 rounded-full font-mono text-[1.2vw] font-bold text-[#D4A843] tracking-widest shadow-[0_0_20px_rgba(212,168,67,0.2)] backdrop-blur-sm"
              initial={{ opacity: 0, scale: 3, y: -50 }} 
              animate={phase >= 3 ? { opacity: 1, scale: 1, y: 0 } : { opacity: 0, scale: 3, y: -50 }}
              transition={{ duration: 0.5, delay: i * 0.15, type: 'spring', stiffness: 300, damping: 12 }}
            >
              {badge}
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

const ORIGINAL = "96D8BA6CA0FF4295";
const TAMPERED = "96D8BA6CA0FF4296";

export function Scene4() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 1800),
      setTimeout(() => setPhase(3), 2800),
      setTimeout(() => setPhase(4), 3800),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  const hashDisplay = phase >= 2 ? TAMPERED : ORIGINAL;

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.94 }}
      transition={{ duration: 0.5 }}
    >
      {/* Headline */}
      <motion.div
        className="text-center mb-[5vh] z-10"
        initial={{ opacity: 0, y: -16 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -16 }}
        transition={{ duration: 0.7 }}
      >
        <div className="text-[3vw] font-black text-white" style={{ fontFamily: 'var(--font-display)' }}>
          Tamper with one byte.
        </div>
        <div className="text-[3vw] font-black text-[#EF4444]" style={{ fontFamily: 'var(--font-display)' }}>
          The chain breaks instantly.
        </div>
      </motion.div>

      {/* Check panel */}
      <div className="w-[56vw] bg-[#050508]/90 border border-white/10 rounded-xl p-8 font-mono text-[1.4vw] flex flex-col gap-5 z-10">

        {/* Hash row */}
        <div className="flex items-center justify-between pb-5 border-b border-white/8">
          <div>
            <div className="text-white/40 text-[0.9vw] mb-1 tracking-widest">GCFR HASH</div>
            <motion.div
              className={phase >= 2 ? 'text-[#EF4444]' : 'text-white/80'}
              transition={{ duration: 0.2 }}
            >
              GCFR-{hashDisplay}
            </motion.div>
          </div>
          <div className="text-right">
            <div className="text-white/40 text-[0.9vw] mb-1 tracking-widest">INT-ADM-GCFR-HASH</div>
            {phase < 2 ? (
              <span className="text-green-500 font-bold">✓ PASS</span>
            ) : (
              <motion.span
                className="text-[#EF4444] font-black"
                initial={{ scale: 1.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 500, damping: 14 }}
              >
                ✗ FAIL
              </motion.span>
            )}
          </div>
        </div>

        {/* Signature row */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-white/40 text-[0.9vw] mb-1 tracking-widest">PQC SIGNATURE</div>
            <div className="text-white/60 text-[1.1vw]">ML-DSA-65 · {phase >= 3 ? 'INVALID' : 'VALID'}</div>
          </div>
          <div className="text-right">
            <div className="text-white/40 text-[0.9vw] mb-1 tracking-widest">INT-ADM-GCFR-SIG</div>
            {phase < 3 ? (
              <span className="text-green-500 font-bold">✓ PASS</span>
            ) : (
              <motion.span
                className="text-[#EF4444] font-bold"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.4 }}
              >
                ✗ FAIL
              </motion.span>
            )}
          </div>
        </div>

        {/* Exit code */}
        <motion.div
          className="border-t border-white/10 pt-5 mt-1 flex items-center justify-between"
          initial={{ opacity: 0 }}
          animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.5 }}
        >
          <span className="text-white/50">verifier exit</span>
          <span className="text-[#EF4444] font-black text-[2vw]">{'>'} exit code 1</span>
        </motion.div>
      </div>

      {/* Red border pulse on tamper */}
      {phase >= 3 && (
        <motion.div
          className="absolute inset-0 border-[3px] border-[#EF4444] pointer-events-none rounded-none"
          style={{ boxShadow: 'inset 0 0 40px rgba(239,68,68,0.12)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 0.8, 0.2, 0.8, 0.2, 0.7] }}
          transition={{ duration: 1.4, times: [0, 0.15, 0.3, 0.5, 0.7, 1] }}
        />
      )}
    </motion.div>
  );
}

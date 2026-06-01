import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

export function Scene4() {
  const [phase, setPhase] = useState(0);
  const [hashText, setHashText] = useState('a3f7c2b9d1e4f508a3f7c2b9d1e4f508');

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000), // Mutation starts
      setTimeout(() => setPhase(2), 4000), // Tamper occurs
      setTimeout(() => setPhase(3), 5000), // Red X marks
      setTimeout(() => setPhase(4), 7000), // Exit code 1
    ];

    let hashInterval: ReturnType<typeof setInterval>;
    timers.push(
      setTimeout(() => {
        let i = 0;
        const target = '00000000TAMPERED00000000TAMPERED';
        hashInterval = setInterval(() => {
          setHashText(prev => {
            const next = prev.split('');
            next[i] = target[i];
            return next.join('');
          });
          i++;
          if (i >= target.length) clearInterval(hashInterval);
        }, 50);
      }, 4000)
    );

    return () => {
      timers.forEach(t => clearTimeout(t));
      clearInterval(hashInterval);
    };
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex items-center justify-center bg-[#050508] z-10"
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ y: '100%', opacity: 0 }}
      transition={{ duration: 0.8, ease }}
    >
      <motion.div 
        className="absolute inset-0 bg-[#E53E3E] mix-blend-overlay z-0 pointer-events-none"
        animate={phase >= 2 ? { opacity: [0.1, 0.3, 0.15] } : { opacity: 0 }}
        transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
      />
      
      {/* Background hex strings */}
      <motion.div className="absolute inset-0 overflow-hidden opacity-5 pointer-events-none z-0">
        {Array.from({ length: 20 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute font-mono text-[1.5vw] whitespace-nowrap"
            style={{ top: `${i * 5}%`, left: `${(i * 13) % 100}%` }}
            animate={phase >= 2 ? { color: '#E53E3E', x: [0, -10, 5, -5, 0] } : { color: '#FFFFFF', x: 0 }}
            transition={phase >= 2 ? { duration: 0.2, repeat: Infinity } : {}}
          >
            {phase >= 2 ? 'ERR_TAMPER_0xBADF00D ' : '0xA3F7C2B9D1E4F508 '}
            {phase >= 2 ? 'ERR_TAMPER_0xBADF00D ' : '0xA3F7C2B9D1E4F508 '}
          </motion.div>
        ))}
      </motion.div>

      <motion.div 
        className="w-full h-full relative z-10 flex"
        animate={phase >= 2 ? { x: [-15, 15, -8, 8, -3, 3, 0], y: [8, -8, 15, -15, 5, -5, 0] } : { x: 0, y: 0 }}
        transition={{ duration: 0.5, type: 'spring', stiffness: 500, damping: 10 }}
      >
        <div className="w-1/2 h-full border-r border-[#333333] flex flex-col justify-center px-[8vw] gap-12 relative overflow-hidden bg-[#0A0A0E]/80 backdrop-blur-sm">
          <div className="absolute top-12 left-12 font-mono text-[#94A3B8] text-[1.2vw] tracking-widest uppercase">Clean Package</div>
          <div className="flex flex-col gap-6 font-mono text-[1.8vw] text-[#E8E8E8]">
            <div className="flex gap-4 items-center">
              <div className="w-4 h-4 bg-[#22C55E] rounded-full shadow-[0_0_10px_#22C55E]" />
              <span>INT-ADM-GCFR-HASH</span>
            </div>
            <div className="flex gap-4 items-center">
              <div className="w-4 h-4 bg-[#22C55E] rounded-full shadow-[0_0_10px_#22C55E]" />
              <span>INT-ADM-GCFR-SIG</span>
            </div>
            <div className="flex gap-4 items-center opacity-40">
              <div className="w-4 h-4 border border-[#FFFFFF] rounded-full" />
              <span>IPFL-INV-007</span>
            </div>
          </div>
        </div>

        <div className="w-1/2 h-full flex flex-col justify-center px-[8vw] gap-12 relative bg-[#0A0A0E]/80 backdrop-blur-sm">
          <div className="absolute top-12 left-12 font-mono text-[#94A3B8] text-[1.2vw] tracking-widest uppercase flex items-center gap-4">
            Tampered Package
            <motion.div 
              className="w-3 h-3 rounded-full bg-[#E53E3E]"
              animate={phase >= 2 ? { opacity: [1, 0, 1] } : { opacity: 0 }}
              transition={{ duration: 0.5, repeat: Infinity }}
            />
          </div>
          
          <div className="font-mono text-[1.5vw] text-[#94A3B8] break-all leading-tight">
            HASH_VAL: <br/>
            <span className={phase >= 2 ? "text-[#E53E3E] font-bold" : "text-[#E8E8E8]"}>
              {hashText}
            </span>
          </div>

          <div className="flex flex-col gap-4">
            <motion.div 
              className="font-mono text-[1.6vw] text-[#E53E3E] font-bold tracking-wide"
              initial={{ opacity: 0, x: 20 }} 
              animate={phase >= 3 ? { opacity: 1, x: 0 } : { opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              ✗ [INT-ADM-GCFR-HASH] component_hash MISMATCH
            </motion.div>
            <motion.div 
              className="font-mono text-[1.6vw] text-[#E53E3E] font-bold tracking-wide"
              initial={{ opacity: 0, x: 20 }} 
              animate={phase >= 3 ? { opacity: 1, x: 0 } : { opacity: 0, x: 20 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              ✗ [INT-ADM-GCFR-SIG] PQC signature INVALID
            </motion.div>
          </div>

          <motion.div 
            className="mt-8 font-display text-[5vw] font-black text-[#E53E3E] tracking-tighter leading-none"
            initial={{ opacity: 0, scale: 0.5, y: 50 }} 
            animate={phase >= 4 ? { opacity: 1, scale: 1, y: 0 } : { opacity: 0, scale: 0.5, y: 50 }}
            transition={{ type: 'spring', stiffness: 400, damping: 15 }}
          >
            exit code 1
          </motion.div>
        </div>
      </motion.div>
    </motion.div>
  );
}

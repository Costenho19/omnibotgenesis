import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const ease = [0.16, 1, 0.3, 1];

export function Scene4() {
  const [phase, setPhase] = useState(0);
  const [hashText, setHashText] = useState('a3f7c2b9d1e4f508a3f7c2b9d1e4f508');

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1000), // Mutation starts
      setTimeout(() => setPhase(2), 4000), // Tamper occurs - crack & shift
      setTimeout(() => setPhase(3), 5000), // Red X marks
      setTimeout(() => setPhase(4), 7000), // Exit code 1 glitch
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
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 1.1, opacity: 0, filter: 'blur(20px)' }}
      transition={{ duration: 0.8, ease }}
    >
      {/* Intense Red Overlay on Tamper */}
      <motion.div 
        className="absolute inset-0 bg-[#E53E3E] mix-blend-overlay z-0 pointer-events-none"
        animate={phase >= 2 ? { opacity: [0.1, 0.4, 0.15, 0.5, 0.2] } : { opacity: 0 }}
        transition={{ duration: 0.8, repeat: Infinity, repeatType: 'reverse' }}
      />

      {/* Screen Crack SVG Effect */}
      {phase >= 2 && (
        <svg className="absolute inset-0 w-full h-full z-50 pointer-events-none opacity-80" preserveAspectRatio="none">
          <motion.path
            d="M 20vw, 0 L 30vw, 30vh L 25vw, 50vh L 45vw, 65vh L 40vw, 100vh M 70vw, 0 L 65vw, 40vh L 80vw, 60vh L 75vw, 100vh"
            stroke="#E53E3E"
            strokeWidth="3"
            fill="none"
            initial={{ pathLength: 0, opacity: 1 }}
            animate={{ pathLength: 1, opacity: 0.8 }}
            transition={{ duration: 0.2 }}
            style={{ filter: 'drop-shadow(0 0 10px #E53E3E)' }}
          />
        </svg>
      )}
      
      {/* Background hex strings */}
      <motion.div className="absolute inset-0 overflow-hidden opacity-[0.08] pointer-events-none z-0">
        {Array.from({ length: 25 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute font-mono text-[1.5vw] whitespace-nowrap"
            style={{ top: `${i * 4}%`, left: `${(i * 17) % 100}%` }}
            animate={phase >= 2 ? { color: '#E53E3E', x: [0, -15, 8, -8, 0] } : { color: '#FFFFFF', x: 0 }}
            transition={phase >= 2 ? { duration: 0.15, repeat: Infinity } : {}}
          >
            {phase >= 2 ? 'ERR_TAMPER_0xBADF00D ' : '0xA3F7C2B9D1E4F508 '}
            {phase >= 2 ? 'ERR_TAMPER_0xBADF00D ' : '0xA3F7C2B9D1E4F508 '}
          </motion.div>
        ))}
      </motion.div>

      {/* Chromatic Aberration Container */}
      <motion.div 
        className="w-full h-full relative z-10 flex"
        animate={phase >= 2 ? { 
          x: [-20, 20, -10, 10, -5, 5, 0], 
          y: [10, -10, 20, -20, 8, -8, 0],
        } : { x: 0, y: 0 }}
        transition={{ duration: 0.4, type: 'tween', ease: 'easeOut' }}
      >
        <div className="w-1/2 h-full border-r border-[#333333] flex flex-col justify-center px-[8vw] gap-12 relative overflow-hidden bg-[#0A0A0E]/90 backdrop-blur-md shadow-2xl">
          <div className="absolute top-12 left-12 font-mono text-[#94A3B8] text-[1.2vw] tracking-widest uppercase">Clean Package</div>
          <div className="flex flex-col gap-8 font-mono text-[1.8vw] text-[#E8E8E8]">
            <div className="flex gap-5 items-center">
              <div className="w-5 h-5 bg-[#22C55E] rounded-full shadow-[0_0_15px_#22C55E]" />
              <span>INT-ADM-GCFR-HASH</span>
            </div>
            <div className="flex gap-5 items-center">
              <div className="w-5 h-5 bg-[#22C55E] rounded-full shadow-[0_0_15px_#22C55E]" />
              <span>INT-ADM-GCFR-SIG</span>
            </div>
            <div className="flex gap-5 items-center opacity-30">
              <div className="w-5 h-5 border-2 border-[#FFFFFF] rounded-full" />
              <span>IPFL-INV-007</span>
            </div>
          </div>
        </div>

        <div className="w-1/2 h-full flex flex-col justify-center px-[8vw] gap-12 relative bg-[#0A0A0E]/90 backdrop-blur-md shadow-2xl">
          <div className="absolute top-12 left-12 font-mono text-[#E53E3E] text-[1.2vw] tracking-widest uppercase flex items-center gap-4 font-bold">
            Tampered Package
            <motion.div 
              className="w-4 h-4 rounded-full bg-[#E53E3E] shadow-[0_0_20px_#E53E3E]"
              animate={phase >= 2 ? { opacity: [1, 0, 1] } : { opacity: 0 }}
              transition={{ duration: 0.3, repeat: Infinity }}
            />
          </div>
          
          <div className="font-mono text-[1.6vw] text-[#94A3B8] break-all leading-tight bg-black/50 p-6 border border-white/10 rounded-sm">
            HASH_VAL: <br/>
            <span className={phase >= 2 ? "text-[#E53E3E] font-bold drop-shadow-[0_0_8px_#E53E3E]" : "text-[#E8E8E8]"}>
              {hashText}
            </span>
          </div>

          <div className="flex flex-col gap-5">
            <motion.div 
              className="font-mono text-[1.7vw] text-[#E53E3E] font-bold tracking-wide bg-[#E53E3E]/10 p-3 border-l-4 border-[#E53E3E]"
              initial={{ opacity: 0, x: 30 }} 
              animate={phase >= 3 ? { opacity: 1, x: 0 } : { opacity: 0, x: 30 }}
              transition={{ duration: 0.4, type: "spring", bounce: 0.6 }}
            >
              ✗ [INT-ADM-GCFR-HASH] MISMATCH
            </motion.div>
            <motion.div 
              className="font-mono text-[1.7vw] text-[#E53E3E] font-bold tracking-wide bg-[#E53E3E]/10 p-3 border-l-4 border-[#E53E3E]"
              initial={{ opacity: 0, x: 30 }} 
              animate={phase >= 3 ? { opacity: 1, x: 0 } : { opacity: 0, x: 30 }}
              transition={{ duration: 0.4, delay: 0.15, type: "spring", bounce: 0.6 }}
            >
              ✗ [INT-ADM-GCFR-SIG] INVALID
            </motion.div>
          </div>

          <motion.div 
            className="mt-10 font-display text-[6vw] font-black text-[#E53E3E] tracking-tighter leading-none uppercase"
            initial={{ opacity: 0, scale: 0.5, y: 50 }} 
            animate={phase >= 4 ? { 
              opacity: 1, 
              scale: 1, 
              y: 0,
              textShadow: ['0px 0px 0px #E53E3E', '5px 5px 0px #0ff', '-5px -5px 0px #f0f', '0px 0px 20px #E53E3E']
            } : { opacity: 0, scale: 0.5, y: 50 }}
            transition={{ 
              opacity: { duration: 0.5 },
              scale: { type: 'spring', stiffness: 300, damping: 12 },
              textShadow: { duration: 0.2, repeat: Infinity, repeatType: "mirror", delay: 0.5 }
            }}
          >
            exit code 1
          </motion.div>
        </div>
      </motion.div>
    </motion.div>
  );
}

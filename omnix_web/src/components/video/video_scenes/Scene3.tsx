import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

const scores = [100, 91, 83, 75, 62, 8.33];

export function Scene3() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const sequence = [
      setTimeout(() => setStep(1), 1500),
      setTimeout(() => setStep(2), 2500),
      setTimeout(() => setStep(3), 3500),
      setTimeout(() => setStep(4), 4500),
      setTimeout(() => setStep(5), 6000),
    ];
    return () => sequence.forEach(t => clearTimeout(t));
  }, []);

  const currentScore = scores[step];
  const isCritical = currentScore < 10;
  const isDegraded = currentScore < 80 && !isCritical;
  
  const scoreColor = isCritical ? 'var(--danger)' : isDegraded ? '#f59e0b' : 'var(--success)';

  return (
    <motion.div
      className="absolute inset-0 flex"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, filter: 'blur(10px)' }}
      transition={{ duration: 1 }}
      style={{ background: '#020617' }} // Full dark scene
    >
      <div className="w-1/2 h-full flex flex-col items-center justify-center border-r border-white/5">
        <h3 className="text-[1.2vw] text-[var(--muted)] mb-[10vh]" style={{ fontFamily: 'var(--font-mono)' }}>
          CONTINUITY ELIGIBILITY SCORE
        </h3>
        
        <div className="relative w-[15vw] h-[40vh] bg-[var(--navy-light)]/30 border border-white/10 rounded-sm overflow-hidden flex items-end">
          <motion.div
            className="w-full"
            style={{ backgroundColor: scoreColor }}
            animate={{ height: `${Math.max(currentScore, 5)}%` }}
            transition={{ type: 'spring', stiffness: 100, damping: 20 }}
          />
          {/* Grid lines */}
          {[25, 50, 75].map(y => (
            <div key={y} className="absolute w-full h-[1px] bg-white/5" style={{ bottom: `${y}%` }} />
          ))}
        </div>
        
        <motion.div 
          className="mt-[5vh] text-[4vw] font-bold"
          style={{ color: scoreColor, fontFamily: 'var(--font-mono)' }}
          animate={isCritical ? { opacity: [1, 0.5, 1] } : { opacity: 1 }}
          transition={isCritical ? { repeat: Infinity, duration: 0.5 } : {}}
        >
          {isCritical ? `CRITICAL: ${currentScore}` : currentScore}
        </motion.div>
      </div>

      <div className="w-1/2 h-full flex flex-col items-start justify-center pl-[10vw] gap-[4vh]">
        <StatusLine label="NOMINAL" active={!isDegraded && !isCritical} color="var(--success)" />
        <StatusLine label="DEGRADED" active={isDegraded} color="#f59e0b" />
        <StatusLine label="CRITICAL" active={isCritical} color="var(--danger)" blink={isCritical} />
      </div>
    </motion.div>
  );
}

function StatusLine({ label, active, color, blink = false }: { label: string, active: boolean, color: string, blink?: boolean }) {
  return (
    <motion.div 
      className="flex items-center gap-6"
      animate={{ opacity: active ? 1 : 0.3 }}
      transition={{ duration: 0.5 }}
    >
      <motion.div
        className="w-[2vw] h-[2vw]"
        style={{ backgroundColor: active ? color : 'transparent', border: `1px solid ${color}` }}
        animate={blink && active ? { opacity: [1, 0, 1] } : { opacity: 1 }}
        transition={blink && active ? { repeat: Infinity, duration: 0.5 } : {}}
      />
      <span className="text-[2vw] tracking-widest" style={{ color: active ? color : 'var(--muted)', fontFamily: 'var(--font-mono)' }}>
        {label}
      </span>
    </motion.div>
  );
}

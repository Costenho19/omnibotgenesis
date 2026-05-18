import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import { Zap, ShieldCheck, Archive } from 'lucide-react';

const columns = [
  { id: 'HOT', icon: Zap, label: 'HOT', desc: 'active receipts, ML-DSA-65 signed', color: 'var(--danger)' },
  { id: 'WARM', icon: ShieldCheck, label: 'WARM', desc: '90-day retention, Merkle chained', color: 'var(--gold)' },
  { id: 'COLD', icon: Archive, label: 'COLD', desc: 'permanent archive, offline verifiable', color: 'var(--cyan)' },
];

export function Scene5() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 1500),
      setTimeout(() => setPhase(3), 2500),
      setTimeout(() => setPhase(4), 4000),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--navy)]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: 50 }}
      transition={{ duration: 1 }}
    >
      <motion.h2
        className="absolute top-[15vh] text-[1.5vw] text-[var(--platinum)] tracking-[0.2em]"
        style={{ fontFamily: 'var(--font-mono)' }}
        initial={{ opacity: 0, y: -20 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -20 }}
        transition={{ duration: 0.8 }}
      >
        IMMUTABLE EVIDENCE LIFECYCLE
      </motion.h2>

      <div className="relative w-[80vw] h-[40vh] flex items-center justify-between mt-[5vh]">
        {/* Connecting line */}
        <div className="absolute top-1/2 left-[10%] right-[10%] h-[1px] -translate-y-1/2 overflow-hidden z-0">
          <motion.div
            className="w-full h-full bg-white/20"
            initial={{ scaleX: 0, transformOrigin: 'left' }}
            animate={phase >= 2 ? { scaleX: 1 } : { scaleX: 0 }}
            transition={{ duration: 2, ease: "easeInOut" }}
          />
        </div>

        {columns.map((col, i) => {
          const Icon = col.icon;
          const isVisible = phase >= i + 2;
          return (
            <motion.div
              key={col.id}
              className="relative z-10 w-[20vw] flex flex-col items-center text-center bg-[var(--navy-light)]/80 p-8 rounded-lg border border-white/5 backdrop-blur-md"
              initial={{ opacity: 0, y: 30 }}
              animate={isVisible ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            >
              <div className="w-16 h-16 rounded-full flex items-center justify-center mb-6" style={{ backgroundColor: `${col.color}20`, border: `1px solid ${col.color}50` }}>
                <Icon size={28} color={col.color} />
              </div>
              <h3 className="text-[1.5vw] font-bold mb-4 tracking-widest" style={{ color: col.color, fontFamily: 'var(--font-mono)' }}>
                {col.label}
              </h3>
              <p className="text-[1vw] text-[var(--muted)]" style={{ fontFamily: 'var(--font-display)' }}>
                {col.desc}
              </p>
            </motion.div>
          );
        })}
      </div>

      <motion.p
        className="absolute bottom-[15vh] text-[1.5vw] text-[var(--platinum)]"
        style={{ fontFamily: 'var(--font-display)' }}
        initial={{ opacity: 0 }}
        animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 1.5 }}
      >
        Every governance event. Preserved permanently.
      </motion.p>
    </motion.div>
  );
}

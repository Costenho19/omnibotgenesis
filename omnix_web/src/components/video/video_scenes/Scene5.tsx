import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

const LINES = [
  { prompt: '$', cmd: 'pip install oqs-python', out: null },
  { prompt: '$', cmd: 'python verify_pogc_offline.py --file package.json', out: null },
  { prompt: '>', cmd: null, out: '✓ [1/7] Content hash        PASS' },
  { prompt: '>', cmd: null, out: '✓ [2/7] PQC signature       PASS' },
  { prompt: '>', cmd: null, out: '✓ [7/7] Route completeness  PASS' },
  { prompt: '>', cmd: null, out: 'exit code 0 — package INTACT' },
];

export function Scene5() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 400),
      setTimeout(() => setPhase(2), 1300),
      setTimeout(() => setPhase(3), 2200),
      setTimeout(() => setPhase(4), 3100),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: 40 }}
      transition={{ duration: 0.7 }}
    >
      {/* Headline */}
      <motion.div
        className="text-center mb-[5vh] z-10"
        initial={{ opacity: 0, y: -14 }}
        animate={phase >= 1 ? { opacity: 1, y: 0 } : { opacity: 0, y: -14 }}
        transition={{ duration: 0.7 }}
      >
        <div className="text-[3vw] font-black text-white" style={{ fontFamily: 'var(--font-display)' }}>
          Verified offline.
        </div>
        <div className="text-[3vw] font-black text-[#D4A843]" style={{ fontFamily: 'var(--font-display)' }}>
          Zero OMNIX access required.
        </div>
      </motion.div>

      {/* Terminal */}
      <div className="w-[52vw] bg-[#0A0A0F] border border-white/15 rounded-xl overflow-hidden shadow-2xl z-10">
        {/* Terminal bar */}
        <div className="flex items-center gap-2 px-5 py-3 border-b border-white/8 bg-white/[0.02]">
          <div className="w-3 h-3 rounded-full bg-[#FF5F57]" />
          <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
          <div className="w-3 h-3 rounded-full bg-[#28C840]" />
          <span className="ml-3 text-[0.85vw] font-mono text-white/30 tracking-widest">
            terminal — verify_pogc_offline.py
          </span>
        </div>

        {/* Lines */}
        <div className="p-6 font-mono text-[1.2vw] leading-loose flex flex-col gap-1">
          {LINES.map((line, i) => {
            const visible = phase >= Math.floor((i / LINES.length) * 3) + 1;
            const isExit = line.out?.startsWith('exit');
            return (
              <motion.div
                key={i}
                className="flex gap-3"
                initial={{ opacity: 0, x: -8 }}
                animate={visible ? { opacity: 1, x: 0 } : { opacity: 0, x: -8 }}
                transition={{ duration: 0.35, delay: i * 0.08 }}
              >
                <span className={line.cmd ? 'text-[#3B82F6]' : 'text-white/30'}>{line.prompt}</span>
                {line.cmd && <span className="text-white/85">{line.cmd}</span>}
                {line.out && (
                  <span className={isExit ? 'text-green-400 font-bold' : 'text-green-500/80'}>
                    {line.out}
                  </span>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Foot note */}
      <motion.div
        className="mt-6 text-[1vw] text-white/30 font-mono tracking-widest z-10"
        initial={{ opacity: 0 }}
        animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.8 }}
      >
        pip install oqs-python · no account · no API key · open source
      </motion.div>
    </motion.div>
  );
}

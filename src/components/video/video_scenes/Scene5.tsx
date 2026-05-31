import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

export function Scene5() {
  const [phase, setPhase] = useState(0);

  const lines = [
    { text: "$ python verify_pogc_offline.py package.json", delay: 0 },
    { text: "[1/7] POGC-EXT-A7F3C2B1D9E4F508 — Loading...", delay: 600 },
    { text: "[2/7] Algorithm: ML-DSA-65 (FIPS 204) — ✓", delay: 1200 },
    { text: "[3/7] Hash chain: SHA3-256 — ✓", delay: 1800 },
    { text: "[4/7] PQC Signature: VERIFIED ✓", delay: 2400 },
    { text: "[5/7] Mandate: MANDATE-BOUND ✓", delay: 3000 },
    { text: "[6/7] Compliance: EU AI Act Art.9 · MiCA · DORA ✓", delay: 3600 },
    { text: "[7/7] Exit code: 1 (TAMPER DETECTED)", delay: 4200, isError: true },
  ];

  useEffect(() => {
    const timers = lines.map((line, i) => setTimeout(() => setPhase(i + 1), line.delay));
    const finalTimer = setTimeout(() => setPhase(10), 5000);
    return () => {
      timers.forEach(t => clearTimeout(t));
      clearTimeout(finalTimer);
    };
  }, []);

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col justify-center bg-[#050508] p-[10vw]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ scale: 0.9, opacity: 0 }}
      transition={{ duration: 0.8 }}
    >
      {/* Scanlines */}
      <div className="absolute inset-0 pointer-events-none opacity-20" 
           style={{ background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, #000 2px, #000 4px)' }} />

      <div className="font-mono text-[1.8vw] text-[#C8C8D0] flex flex-col gap-[1.5vh] relative z-10">
        {lines.map((line, i) => (
          <motion.div 
            key={i}
            initial={{ opacity: 0 }}
            animate={phase > i ? { opacity: 1 } : { opacity: 0 }}
            className={line.isError ? "text-[#E53E3E] font-bold" : ""}
          >
            {line.text}
          </motion.div>
        ))}
      </div>

      {/* ZERO OMNIX DEPENDENCIES */}
      <motion.div
        className="absolute bottom-[10vh] left-[10vw] border-l-4 border-[#D4A843] pl-[2vw]"
        initial={{ y: 50, opacity: 0 }}
        animate={phase >= 10 ? { y: 0, opacity: 1 } : { y: 50, opacity: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="font-display font-bold text-[3vw] tracking-wider text-[#D4A843]">
          ZERO OMNIX DEPENDENCIES
        </span>
      </motion.div>
    </motion.div>
  );
}
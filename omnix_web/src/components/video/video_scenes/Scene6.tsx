import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import { FileJson, Key } from 'lucide-react';

export function Scene6() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 1500),
      setTimeout(() => setPhase(3), 3000), // Merge
      setTimeout(() => setPhase(4), 4500), // Text reveals
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div
      className="absolute inset-0 bg-[var(--navy)]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.1 }}
      transition={{ duration: 1 }}
    >
      <div className="absolute inset-0 flex">
        {/* Left side */}
        <motion.div 
          className="h-full bg-[#020617] flex flex-col items-center justify-center relative overflow-hidden"
          animate={{ width: phase >= 3 ? '50%' : '50%' }}
          initial={{ width: '50%' }}
        >
          <motion.div
            className="flex flex-col items-center"
            animate={{ 
              x: phase >= 3 ? '15vw' : 0,
              opacity: phase >= 3 ? 0 : 1
            }}
            transition={{ duration: 1, ease: "easeInOut" }}
          >
            <motion.div
              initial={{ y: -50, opacity: 0 }}
              animate={phase >= 1 ? { y: 0, opacity: 1 } : { y: -50, opacity: 0 }}
              transition={{ duration: 0.6, type: "spring", bounce: 0.4 }}
            >
              <FileJson size={80} className="text-[var(--cyan)] mb-6" />
            </motion.div>
            <motion.p
              className="text-[1.2vw] text-[var(--platinum)]"
              style={{ fontFamily: 'var(--font-mono)' }}
              initial={{ opacity: 0 }}
              animate={phase >= 1 ? { opacity: 1 } : { opacity: 0 }}
              transition={{ delay: 0.3 }}
            >
              .json block file
            </motion.p>
          </motion.div>
        </motion.div>

        {/* Vertical divider */}
        <motion.div
          className="absolute top-0 bottom-0 left-1/2 w-[1px] bg-white/10 z-10"
          animate={{ opacity: phase >= 3 ? 0 : 1 }}
          transition={{ duration: 0.5 }}
        />

        {/* Right side */}
        <motion.div 
          className="h-full bg-[var(--navy-light)] flex flex-col items-center justify-center relative overflow-hidden"
          animate={{ width: phase >= 3 ? '50%' : '50%' }}
          initial={{ width: '50%' }}
        >
          <motion.div
            className="flex flex-col items-center"
            animate={{ 
              x: phase >= 3 ? '-15vw' : 0,
              opacity: phase >= 3 ? 0 : 1
            }}
            transition={{ duration: 1, ease: "easeInOut" }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0 }}
              animate={phase >= 2 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0 }}
              transition={{ duration: 0.6, type: "spring" }}
            >
              <Key size={80} className="text-[var(--gold)] mb-6" />
            </motion.div>
            <motion.p
              className="text-[1.2vw] text-[var(--platinum)]"
              style={{ fontFamily: 'var(--font-mono)' }}
              initial={{ opacity: 0 }}
              animate={phase >= 2 ? { opacity: 1 } : { opacity: 0 }}
              transition={{ delay: 0.3 }}
            >
              platform public key
            </motion.p>
          </motion.div>
        </motion.div>
      </div>

      {/* Center Merge Result */}
      <motion.div
        className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
      >
        <motion.div
          className="w-[15vh] h-[15vh] flex items-center justify-center mb-8"
          initial={{ opacity: 0, scale: 0 }}
          animate={phase >= 3 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <svg viewBox="0 0 100 100" className="w-full h-full">
            <motion.circle
              cx="50" cy="50" r="45"
              fill="transparent"
              stroke="var(--success)"
              strokeWidth="4"
              initial={{ pathLength: 0 }}
              animate={phase >= 3 ? { pathLength: 1 } : { pathLength: 0 }}
              transition={{ duration: 1, delay: 0.8 }}
            />
            <motion.path
              d="M30 50 L45 65 L70 35"
              fill="transparent"
              stroke="var(--success)"
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={phase >= 3 ? { pathLength: 1 } : { pathLength: 0 }}
              transition={{ duration: 0.5, delay: 1.8 }}
            />
          </svg>
        </motion.div>

        <motion.div
          className="text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={phase >= 4 ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.8 }}
        >
          <p className="text-[2vw] text-[var(--success)] mb-4" style={{ fontFamily: 'var(--font-mono)' }}>
            Verified offline. No OMNIX runtime required.
          </p>
          <p className="text-[1.2vw] text-[var(--muted)]" style={{ fontFamily: 'var(--font-mono)' }}>
            Plane 3 · EAP-INV-005 · Any auditor. Anywhere.
          </p>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}

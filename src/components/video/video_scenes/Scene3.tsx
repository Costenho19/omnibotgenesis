import { motion, useTransform, useMotionValue, animate } from 'framer-motion';
import { useEffect, useState } from 'react';

export function Scene3() {
  const [phase, setPhase] = useState(0);
  const count = useMotionValue(0);
  const rounded = useTransform(count, Math.round);

  const steps = [
    "INTAKE VALIDATION",
    "PQC SIGNATURE VERIFIED",
    "MANDATE BINDING",
    "SCOPE AUTHORIZATION",
    "AVM APPROVAL",
    "EXECUTION INTEGRITY",
    "BEV CONFORMANCE",
    "SETTLEMENT GATE",
    "PROOF OF GOVERNANCE"
  ];

  useEffect(() => {
    const timers = steps.map((_, i) => setTimeout(() => setPhase(i + 1), 500 + i * 400));
    const counterTimer = setTimeout(() => {
      animate(count, 187, { duration: 3, ease: "easeOut" });
    }, 1000);
    
    return () => {
      timers.forEach(t => clearTimeout(t));
      clearTimeout(counterTimer);
    };
  }, []);

  return (
    <motion.div 
      className="absolute inset-0 flex"
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '-100%' }}
      transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Left Panel */}
      <div className="w-[60%] h-full bg-[#030305] border-r border-[#111] relative p-[8vw] flex flex-col justify-center">
        {/* Vertical Line */}
        <motion.div 
          className="absolute left-[6vw] top-[10vh] bottom-[10vh] w-[2px] bg-[#D4A843]/30"
        />

        <div className="flex flex-col gap-[3vh] relative z-10 pl-[2vw]">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-[2vw]">
              <motion.div
                className="w-[2vw] h-[2vw] flex items-center justify-center shrink-0"
                initial={{ scale: 0 }}
                animate={phase > i ? { scale: 1 } : { scale: 0 }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="#D4A843" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <motion.polyline
                    points="20 6 9 17 4 12"
                    initial={{ pathLength: 0 }}
                    animate={phase > i ? { pathLength: 1 } : { pathLength: 0 }}
                    transition={{ duration: 0.3, ease: "easeOut", delay: 0.1 }}
                  />
                </svg>
              </motion.div>
              <motion.span 
                className="font-mono text-[1.8vw] tracking-wider"
                initial={{ opacity: 0, x: -20, color: "#444" }}
                animate={phase > i ? { opacity: 1, x: 0, color: "#C8C8D0" } : { opacity: 0, x: -20 }}
                transition={{ duration: 0.4 }}
              >
                {step}
              </motion.span>
            </div>
          ))}
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-[40%] h-full flex flex-col items-center justify-center relative overflow-hidden">
        <motion.div className="text-center relative z-10">
          <motion.h1 className="font-mono text-[10vw] font-bold text-white leading-none">
            {rounded}
          </motion.h1>
          <motion.p className="font-display font-bold text-[1.5vw] tracking-[0.3em] text-[#C8C8D0] mt-[2vh]">
            CHECKS VERIFIED
          </motion.p>
        </motion.div>
      </div>
    </motion.div>
  );
}
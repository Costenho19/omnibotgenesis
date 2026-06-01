import { motion, AnimatePresence } from 'framer-motion';
import { useVideoPlayer } from '@/lib/video';
import { Scene1 } from './video_scenes/Scene1';
import { Scene2 } from './video_scenes/Scene2';
import { Scene3 } from './video_scenes/Scene3';
import { Scene4 } from './video_scenes/Scene4';
import { Scene5 } from './video_scenes/Scene5';
import { Scene6 } from './video_scenes/Scene6';
import { OmnixLogo } from './OmnixLogo';
import { useEffect, useState } from 'react';

const SCENE_DURATIONS = {
  problem:   12000,
  protocol:  18000,
  execution: 18000,
  tamper:    18000,
  verify:    12000,
  trust:     12000,
};

export default function VideoTemplate() {
  const { currentScene } = useVideoPlayer({ durations: SCENE_DURATIONS });

  const hidePersistentLogo = currentScene === 5;

  return (
    <div
      className="relative w-full h-screen overflow-hidden"
      style={{ backgroundColor: '#050508', fontFamily: "'Plus Jakarta Sans', sans-serif" }}
    >
      {/* Persistent noise layer */}
      <div className="absolute inset-0 bg-noise pointer-events-none opacity-[0.03] z-0" />

      {/* Subtle grid lines */}
      <div className="absolute inset-0 z-0 pointer-events-none flex justify-center items-center opacity-[0.08]">
        <motion.div 
          className="w-[200vw] h-px bg-white absolute" 
          animate={{ y: ['-20vh', '120vh'] }} 
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div 
          className="w-[200vw] h-px bg-white absolute" 
          animate={{ y: ['120vh', '-20vh'] }} 
          transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div 
          className="h-[200vh] w-px bg-white absolute" 
          animate={{ x: ['-20vw', '120vw'] }} 
          transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
        />
      </div>

      {/* Persistent Hash Fragments */}
      {Array.from({ length: 15 }).map((_, i) => (
        <motion.div
          key={`hash-${i}`}
          className="absolute font-mono text-[0.8vw] text-white/10 pointer-events-none z-0"
          style={{ top: `${(i * 17) % 100}%`, left: `${(i * 23) % 100}%` }}
          animate={{
            y: ['0%', '100%'],
            opacity: [0.1, 0.3, 0.1]
          }}
          transition={{
            duration: 15 + (i % 5) * 2,
            repeat: Infinity,
            ease: 'linear',
            delay: i * 0.5
          }}
        >
          {['0xA3F7', '0xB9D1', '0xE4F5', '0x08A3'][i % 4]}
        </motion.div>
      ))}

      {/* Persistent Circuit Element — viewBox coordinates only, no vw/vh in SVG */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-10 opacity-20" viewBox="0 0 100 100" preserveAspectRatio="none">
        <motion.polyline
          points={[
            [10 + currentScene * 8, 20],
            [25 + currentScene * 5, 50],
            [15 + currentScene * 6, 80],
          ].map(([x, y]) => `${x},${y}`).join(' ')}
          fill="none"
          stroke="#D4A843"
          strokeWidth="0.4"
          animate={{
            pathLength: [0, 1],
            opacity: [0, 0.8, 0],
          }}
          transition={{ duration: 4, ease: "easeInOut", repeat: Infinity }}
        />
      </svg>

      {/* Persistent OMNIX logo — hidden on Scene6 (it renders its own) */}
      <motion.div
        className="absolute"
        style={{ top: '3.5vh', right: '3.5vw', zIndex: 50 }}
        animate={{ opacity: hidePersistentLogo ? 0 : 0.85, scale: hidePersistentLogo ? 0.8 : 1 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <OmnixLogo size="7vw" opacity={1} />
      </motion.div>

      {/* Scanline Wipes on Scene Change */}
      <motion.div
        key={`wipe-1-${currentScene}`}
        className="absolute top-0 bottom-0 w-[4vw] bg-gradient-to-r from-transparent via-[#D4A843]/50 to-transparent z-40 pointer-events-none"
        initial={{ left: '-10%', opacity: 1, skewX: -20 }}
        animate={{ left: '110%', opacity: 0 }}
        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
      />
      <motion.div
        key={`wipe-2-${currentScene}`}
        className="absolute top-0 bottom-0 w-px bg-[#D4A843] z-40 pointer-events-none shadow-[0_0_15px_#D4A843]"
        initial={{ left: '-5%', opacity: 1 }}
        animate={{ left: '105%', opacity: 0 }}
        transition={{ duration: 1.0, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
      />

      {/* Persistent amber accent line — transforms with scene */}
      <motion.div 
        className="absolute h-[2px] bg-[#D4A843] z-20 pointer-events-none shadow-[0_0_10px_#D4A843]"
        animate={{
          left: ['5%','60%','5%','55%','10%','35%'][currentScene],
          width: ['25%','20%','35%','15%','30%','20%'][currentScene],
          top: ['15%','85%','50%','75%','20%','50%'][currentScene],
          opacity: 0.8
        }}
        transition={{ duration: 1.2, ease: [0.16,1,0.3,1] }}
      />

      {/* Persistent geometric shape — amber bordered square */}
      <motion.div
        className="absolute border border-[#D4A843]/40 z-20 pointer-events-none backdrop-blur-[2px]"
        animate={{
          width: ['8vw','6vw','10vw','5vw','7vw','12vw'][currentScene],
          height: ['8vw','6vw','10vw','5vw','7vw','12vw'][currentScene],
          left: ['75%','10%','80%','15%','70%','40%'][currentScene],
          top: ['70%','20%','15%','60%','75%','35%'][currentScene],
          rotate: [0,45,90,135,180,225][currentScene],
          opacity: [0.5,0.4,0.6,0.7,0.4,0.6][currentScene],
        }}
        transition={{ duration: 1.4, ease: [0.16,1,0.3,1] }}
      />

      {/* Persistent radial ambient light */}
      <motion.div
        className="absolute rounded-full blur-[90px] pointer-events-none z-0 mix-blend-screen"
        animate={{
          width: ['40vw','30vw','50vw','20vw','35vw','45vw'][currentScene],
          height: ['40vw','30vw','50vw','20vw','35vw','45vw'][currentScene],
          left: ['50%','20%','40%','70%','50%','45%'][currentScene],
          top: ['50%','30%','60%','40%','50%','50%'][currentScene],
          opacity: [0.08,0.1,0.06,0.12,0.08,0.1][currentScene],
          backgroundColor: ['#D4A843','#D4A843','#22C55E','#E53E3E','#D4A843','#D4A843'][currentScene],
        }}
        style={{ transform: 'translate(-50%, -50%)' }}
        transition={{ duration: 1.5, ease: [0.16,1,0.3,1] }}
      />

      <AnimatePresence mode="sync">
        {currentScene === 0 && <Scene1 key="scene0" />}
        {currentScene === 1 && <Scene2 key="scene1" />}
        {currentScene === 2 && <Scene3 key="scene2" />}
        {currentScene === 3 && <Scene4 key="scene3" />}
        {currentScene === 4 && <Scene5 key="scene4" />}
        {currentScene === 5 && <Scene6 key="scene5" />}
      </AnimatePresence>
    </div>
  );
}

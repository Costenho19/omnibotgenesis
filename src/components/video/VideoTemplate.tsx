import { motion, AnimatePresence } from 'framer-motion';
import { useVideoPlayer } from '@/lib/video';
import { Scene1 } from './video_scenes/Scene1';
import { Scene2 } from './video_scenes/Scene2';
import { Scene3 } from './video_scenes/Scene3';
import { Scene4 } from './video_scenes/Scene4';
import { Scene5 } from './video_scenes/Scene5';
import { Scene6 } from './video_scenes/Scene6';

const SCENE_DURATIONS = {
  problem:    5000,
  protocol:   5500,
  execution:  6000,
  tamper:     5000,
  verify:     5500,
  trust:      6000,
};

export default function VideoTemplate() {
  const { currentScene } = useVideoPlayer({ durations: SCENE_DURATIONS });

  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#050508] font-display">
      {/* Persistent Background Layer */}
      <div className="absolute inset-0">
        {/* Generative dark blue texture */}
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-40 mix-blend-screen"
          style={{ backgroundImage: `url(${import.meta.env.BASE_URL}images/bg-texture.png)` }}
        />
        {/* Subtle noise */}
        <div className="absolute inset-0 bg-noise opacity-30 pointer-events-none" />
      </div>

      {/* Persistent Cross-Scene Elements */}
      <motion.div 
        className="absolute top-[5vh] left-[4vw] z-50 flex flex-col"
        animate={{
          scale: currentScene === 5 ? 0 : 1,
          opacity: currentScene === 5 ? 0 : 0.3
        }}
        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="font-display font-black text-[2vw] tracking-widest text-[#C8C8D0]">OMNIX</span>
        <span className="font-mono text-[0.8vw] tracking-widest text-[#C8C8D0]">QUANTUM</span>
      </motion.div>

      <motion.div 
        className="absolute bottom-[5vh] right-[4vw] z-50 rounded-full"
        animate={{
          width: currentScene === 3 ? '1vw' : '0.5vw',
          height: currentScene === 3 ? '1vw' : '0.5vw',
          opacity: currentScene === 5 ? 0 : 0.7,
          backgroundColor: currentScene === 3 ? '#E53E3E' : '#D4A843'
        }}
        transition={{ duration: 0.8, ease: "easeInOut" }}
      />

      {/* Dynamic Content Layer */}
      <AnimatePresence mode="sync">
        {currentScene === 0 && <Scene1 key="problem" />}
        {currentScene === 1 && <Scene2 key="protocol" />}
        {currentScene === 2 && <Scene3 key="execution" />}
        {currentScene === 3 && <Scene4 key="tamper" />}
        {currentScene === 4 && <Scene5 key="verify" />}
        {currentScene === 5 && <Scene6 key="trust" />}
      </AnimatePresence>
    </div>
  );
}
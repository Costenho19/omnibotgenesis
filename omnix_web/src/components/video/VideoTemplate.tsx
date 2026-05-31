import { motion, AnimatePresence } from 'framer-motion';
import { useVideoPlayer } from '../../lib/video';
import { Scene1 } from './video_scenes/Scene1';
import { Scene2 } from './video_scenes/Scene2';
import { Scene3 } from './video_scenes/Scene3';
import { Scene4 } from './video_scenes/Scene4';
import { Scene5 } from './video_scenes/Scene5';
import { Scene6 } from './video_scenes/Scene6';

const SCENE_DURATIONS = {
  s1: 6000,
  s2: 10000,
  s3: 10000,
  s4: 10000,
  s5: 9000,
  s6: 12000
};

export default function VideoTemplate() {
  const { currentScene } = useVideoPlayer({ durations: SCENE_DURATIONS });

  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#050508] font-display text-[#F8F8FF]">

      {/* Grid overlay — subtle precision feel */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: 'linear-gradient(rgba(212,168,67,1) 1px, transparent 1px), linear-gradient(90deg, rgba(212,168,67,1) 1px, transparent 1px)',
          backgroundSize: '80px 80px'
        }}
      />

      {/* Amber accent line — left edge */}
      <motion.div
        className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#D4A843] z-50 origin-top"
        animate={{
          scaleY: [0.15, 0.5, 1, 0.7, 0.85, 1][currentScene % 6],
          opacity: [1, 0.9, 1, 0.95, 0.8, 1][currentScene % 6],
        }}
        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
      />

      {/* Persistent logo — top left */}
      <motion.div
        className="absolute top-5 left-8 z-50 flex items-center gap-3"
        initial={{ opacity: 0, x: -16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
      >
        <img
          src={`${import.meta.env.BASE_URL}logo_nobg.png`}
          alt="OMNIX QUANTUM"
          style={{
            height: '44px',
            width: 'auto',
            filter: 'drop-shadow(0 0 10px rgba(212,168,67,0.35))'
          }}
        />
      </motion.div>

      {/* Scene counter — top right */}
      <div className="absolute top-6 right-8 z-50 font-mono text-[0.8vw] text-white/25 tracking-widest">
        {String(currentScene + 1).padStart(2, '0')} / 06
      </div>

      {/* Scenes */}
      <div className="absolute inset-0 z-10">
        <AnimatePresence mode="popLayout">
          {currentScene === 0 && <Scene1 key="s1" />}
          {currentScene === 1 && <Scene2 key="s2" />}
          {currentScene === 2 && <Scene3 key="s3" />}
          {currentScene === 3 && <Scene4 key="s4" />}
          {currentScene === 4 && <Scene5 key="s5" />}
          {currentScene === 5 && <Scene6 key="s6" />}
        </AnimatePresence>
      </div>
    </div>
  );
}

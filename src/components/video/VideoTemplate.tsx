import { motion, AnimatePresence } from 'framer-motion';
import { useVideoPlayer } from '@/lib/video';
import { Scene1 } from './video_scenes/Scene1';
import { Scene2 } from './video_scenes/Scene2';
import { Scene3 } from './video_scenes/Scene3';
import { Scene4 } from './video_scenes/Scene4';
import { Scene5 } from './video_scenes/Scene5';
import { Scene6 } from './video_scenes/Scene6';
import { OmnixLogo } from './OmnixLogo';

const SCENE_DURATIONS = {
  problem:   12000,
  protocol:  18000,
  execution: 18000,
  tamper:    18000,
  verify:    12000,
  trust:     12000,
};

const SCENES = [Scene1, Scene2, Scene3, Scene4, Scene5, Scene6];

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
      <div className="absolute inset-0 z-0 pointer-events-none flex justify-center items-center opacity-10">
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

      {/* Persistent OMNIX logo — hidden on Scene6 (it renders its own) */}
      <motion.div
        className="absolute"
        style={{ top: '3.5vh', right: '3.5vw', zIndex: 50 }}
        animate={{ opacity: hidePersistentLogo ? 0 : 0.85, scale: hidePersistentLogo ? 0.8 : 1 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <OmnixLogo size="7vw" opacity={1} />
      </motion.div>

      {/* Scene wipe line — amber vertical sweep on scene change */}
      <motion.div
        key={`wipe-${currentScene}`}
        className="absolute top-0 bottom-0 w-1 bg-[#D4A843] z-40 pointer-events-none"
        initial={{ left: '-2%', opacity: 1 }}
        animate={{ left: '102%', opacity: 0 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
      />

      {/* All scenes rendered, only the active one is visible — no AnimatePresence */}
      {SCENES.map((SceneComponent, idx) => (
        <motion.div
          key={idx}
          className="absolute inset-0"
          style={{ zIndex: currentScene === idx ? 10 : 1 }}
          initial={false}
          animate={{
            opacity: currentScene === idx ? 1 : 0,
            pointerEvents: currentScene === idx ? 'auto' : 'none',
          }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          {currentScene === idx && <SceneComponent />}
        </motion.div>
      ))}
    </div>
  );
}
import { motion, AnimatePresence } from 'framer-motion';
import { useVideoPlayer } from '@/lib/video';
import { Scene1 } from './video_scenes/Scene1';
import { Scene2 } from './video_scenes/Scene2';
import { Scene3 } from './video_scenes/Scene3';
import { Scene4 } from './video_scenes/Scene4';
import { Scene5 } from './video_scenes/Scene5';
import { Scene6 } from './video_scenes/Scene6';
import { OmnixLogo } from './OmnixLogo';

// Total: 15+15+18+15+15+12 = 90 seconds
const SCENE_DURATIONS = {
  problem:   15000,
  protocol:  15000,
  execution: 18000,
  tamper:    15000,
  verify:    15000,
  trust:     12000,
};

export default function VideoTemplate() {
  const { currentScene } = useVideoPlayer({ durations: SCENE_DURATIONS });

  // Scene 6 owns the logo — hide persistent badge there
  const hidePersistentLogo = currentScene === 5;

  return (
    <div
      className="relative w-full h-screen overflow-hidden"
      style={{ backgroundColor: '#050508', fontFamily: "'Plus Jakarta Sans', sans-serif" }}
    >
      {/* Persistent OMNIX logo — top-right badge (all scenes except S6) */}
      <AnimatePresence>
        {!hidePersistentLogo && (
          <motion.div
            key="persistent-logo"
            className="absolute"
            style={{ top: '3.5vh', right: '3.5vw', zIndex: 50 }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 0.85, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            <OmnixLogo size="7vw" opacity={1} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Persistent amber dot — becomes red on tamper scene */}
      <motion.div
        className="absolute rounded-full"
        style={{ bottom: '5vh', right: '4vw', zIndex: 50 }}
        animate={{
          width: currentScene === 3 ? '0.9vw' : '0.45vw',
          height: currentScene === 3 ? '0.9vw' : '0.45vw',
          backgroundColor: currentScene === 3 ? '#E53E3E' : '#D4A843',
          opacity: hidePersistentLogo ? 0 : 0.7,
        }}
        transition={{ duration: 0.7, ease: 'easeInOut' }}
      />

      {/* Scene counter */}
      <motion.div
        className="absolute"
        style={{ bottom: '5vh', left: '4vw', zIndex: 50 }}
        animate={{ opacity: 0.2 }}
      >
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '0.85vw',
            color: '#C8C8D0',
            letterSpacing: '0.2em',
          }}
        >
          {String(currentScene + 1).padStart(2, '0')}&nbsp;/&nbsp;06
        </span>
      </motion.div>

      {/* Dynamic content */}
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

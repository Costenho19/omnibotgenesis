import { motion, AnimatePresence } from 'framer-motion';
import { useVideoPlayer } from '../../lib/video';
import { Scene1 } from './video_scenes/Scene1';
import { Scene2 } from './video_scenes/Scene2';
import { Scene3 } from './video_scenes/Scene3';
import { Scene4 } from './video_scenes/Scene4';
import { Scene5 } from './video_scenes/Scene5';
import { Scene6 } from './video_scenes/Scene6';

const SCENE_DURATIONS = {
  s1: 9000,
  s2: 18000,
  s3: 18000,
  s4: 18000,
  s5: 15000,
  s6: 18000
};

export default function VideoTemplate() {
  const { currentScene } = useVideoPlayer({ durations: SCENE_DURATIONS });

  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#050508] font-display text-[#F8F8FF]">
      
      {/* Persistent Video Background */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-40">
        <video 
          src={`${import.meta.env.BASE_URL}videos/bg_abstract.mp4`} 
          autoPlay 
          muted 
          loop 
          playsInline
          className="w-full h-full object-cover"
        />
      </div>

      {/* Persistent Vertical Amber Line Motif */}
      <motion.div
        className="absolute left-0 top-0 bottom-0 w-[4px] bg-[#D4A843] z-50 origin-top"
        animate={{
          scaleY: [0.1, 0.4, 1, 0.6, 0.8, 1][currentScene % 6],
          opacity: [1, 0.8, 1, 0.9, 0.7, 1][currentScene % 6],
          filter: ['blur(0px)', 'blur(2px)', 'blur(0px)', 'blur(1px)', 'blur(0px)', 'blur(0px)'][currentScene % 6]
        }}
        transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1] }}
      />

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
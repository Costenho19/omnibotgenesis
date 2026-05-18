import { motion, AnimatePresence } from 'framer-motion';
import { useVideoPlayer } from '../../lib/video';
import { Scene1 } from './video_scenes/Scene1';
import { Scene2 } from './video_scenes/Scene2';
import { Scene3 } from './video_scenes/Scene3';
import { Scene4 } from './video_scenes/Scene4';
import { Scene5 } from './video_scenes/Scene5';
import { Scene6 } from './video_scenes/Scene6';
import { Scene7 } from './video_scenes/Scene7';

const SCENE_DURATIONS = {
  problem: 8000,
  flow: 12000,
  ces: 10000,
  halt: 10000,
  evidence: 12000,
  verify: 10000,
  closing: 13000
};

export default function VideoTemplate() {
  const { currentScene } = useVideoPlayer({ durations: SCENE_DURATIONS });

  return (
    <div className="relative w-full h-screen overflow-hidden" style={{ background: 'var(--navy)' }}>
      {/* Persistent Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(var(--navy-light) 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
        
        {/* Slow gold radial pulse */}
        <motion.div
          className="absolute w-[800px] h-[800px] rounded-full blur-[100px] opacity-10"
          style={{ background: 'radial-gradient(circle, var(--gold), transparent)' }}
          animate={{
            x: ['-20%', '50%', '10%', '-30%', '40%', '60%', '20%', '-20%'][currentScene % 8],
            y: ['10%', '-20%', '40%', '50%', '-10%', '30%', '60%', '10%'][currentScene % 8],
            scale: [1, 1.2, 0.9, 1.4, 1.1, 0.8, 1.3, 1][currentScene % 8],
          }}
          transition={{ duration: 4, ease: "easeInOut" }}
        />
      </div>

      {/* Persistent Top Protocol Signal Bar */}
      <div className="absolute top-0 left-0 w-full h-[2px] bg-[var(--navy-light)] z-50">
        <motion.div
          className="h-full bg-[var(--gold)]"
          animate={{
            width: ['10%', '25%', '45%', '50%', '75%', '90%', '100%'][currentScene],
            opacity: [0.3, 0.5, 0.7, 1, 0.6, 0.8, 0.2][currentScene]
          }}
          transition={{ duration: 2, ease: "easeInOut" }}
        />
      </div>

      <AnimatePresence mode="popLayout">
        {currentScene === 0 && <Scene1 key="problem" />}
        {currentScene === 1 && <Scene2 key="flow" />}
        {currentScene === 2 && <Scene3 key="ces" />}
        {currentScene === 3 && <Scene4 key="halt" />}
        {currentScene === 4 && <Scene5 key="evidence" />}
        {currentScene === 5 && <Scene6 key="verify" />}
        {currentScene === 6 && <Scene7 key="closing" />}
      </AnimatePresence>
    </div>
  );
}

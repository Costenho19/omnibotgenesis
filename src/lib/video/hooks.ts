import { useState, useEffect, useRef } from 'react';

type SceneDurations = Record<string, number>;

interface VideoPlayerOptions {
  durations: SceneDurations;
}

interface VideoPlayerResult {
  currentScene: number;
}

export function useVideoPlayer({ durations }: VideoPlayerOptions): VideoPlayerResult {
  const [currentScene, setCurrentScene] = useState(0);
  const sceneKeys = Object.keys(durations);
  const totalScenes = sceneKeys.length;
  const hasStoppedRef = useRef(false);
  const sceneIndexRef = useRef(0);

  useEffect(() => {
    window.startRecording?.();

    let timeoutId: ReturnType<typeof setTimeout>;

    const advance = () => {
      const idx = sceneIndexRef.current;
      const key = sceneKeys[idx];
      const duration = durations[key];

      timeoutId = setTimeout(() => {
        const nextIdx = idx + 1;

        if (nextIdx >= totalScenes) {
          if (!hasStoppedRef.current) {
            hasStoppedRef.current = true;
            window.stopRecording?.();
          }
          sceneIndexRef.current = 0;
          setCurrentScene(0);
          advance();
        } else {
          sceneIndexRef.current = nextIdx;
          setCurrentScene(nextIdx);
          advance();
        }
      }, duration);
    };

    advance();

    return () => clearTimeout(timeoutId);
  }, []);

  return { currentScene };
}

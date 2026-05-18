import { useState, useEffect, useRef } from 'react'

interface UseVideoPlayerOptions {
  durations: Record<string, number>
}

interface UseVideoPlayerResult {
  currentScene: number
}

declare global {
  interface Window {
    startRecording?: () => void
    stopRecording?: () => void
  }
}

export function useVideoPlayer({ durations }: UseVideoPlayerOptions): UseVideoPlayerResult {
  const [currentScene, setCurrentScene] = useState(0)
  const keys = Object.keys(durations)
  const stoppedRef = useRef(false)

  useEffect(() => {
    window.startRecording?.()

    let sceneIndex = 0
    let timeoutId: ReturnType<typeof setTimeout>

    function advance() {
      sceneIndex++
      if (sceneIndex >= keys.length) {
        if (!stoppedRef.current) {
          stoppedRef.current = true
          window.stopRecording?.()
        }
        sceneIndex = 0
      }
      setCurrentScene(sceneIndex)
      timeoutId = setTimeout(advance, durations[keys[sceneIndex]])
    }

    timeoutId = setTimeout(advance, durations[keys[0]])

    return () => clearTimeout(timeoutId)
  }, [])

  return { currentScene }
}

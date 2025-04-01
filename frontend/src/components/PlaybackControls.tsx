import { h } from "preact";
import { useState, useEffect, useRef, useCallback } from "preact/hooks";
import { PlaybackController } from "../utils/playbackController";

// Update interface to match what App.tsx provides
interface PlaybackControlsProps {
  isPlaying?: boolean;
  onPlayPause?: () => void;
  onStepForward?: () => void;
  onStepBackward?: () => void;
  canStepForward?: boolean;
  canStepBackward?: boolean;
  // Add these for our internal implementation
  itemCount?: number;
  currentIndex?: number;
  onChangeIndex?: (newIndex: number) => void;
}

export function PlaybackControls({
  // Use all possible props
  isPlaying: externalIsPlaying = false,
  onPlayPause,
  onStepForward,
  onStepBackward,
  canStepForward = true,
  canStepBackward = true,
  itemCount = 0,
  currentIndex = 0,
  onChangeIndex,
}: PlaybackControlsProps) {
  // Internal state
  const [internalIsPlaying, setInternalIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // items per second
  const playbackControllerRef = useRef<PlaybackController | null>(null);

  // Use either external or internal playing state
  const isPlaying = onPlayPause ? externalIsPlaying : internalIsPlaying;

  // Create a stable callback reference
  const handleIndexChange = useCallback(
    (newIndex: number) => {
      if (typeof newIndex !== "number" || isNaN(newIndex)) {
        console.error("Invalid index received:", newIndex);
        return;
      }

      console.log("Advancing to valid index:", newIndex);
      // Use either onChangeIndex or onStepForward/onStepBackward
      if (typeof onChangeIndex === "function") {
        onChangeIndex(newIndex);
      } else if (
        newIndex > currentIndex &&
        typeof onStepForward === "function"
      ) {
        onStepForward();
      } else if (
        newIndex < currentIndex &&
        typeof onStepBackward === "function"
      ) {
        onStepBackward();
      } else {
        console.warn("No valid callback function for index change");
      }
    },
    [onChangeIndex, onStepForward, onStepBackward, currentIndex],
  );

  // Initialize or update the playback controller
  useEffect(() => {
    // Dispose previous controller if it exists
    if (playbackControllerRef.current) {
      playbackControllerRef.current.dispose();
    }

    // Create a new controller with current props
    const controller = new PlaybackController({
      speed: playbackSpeed,
      onAdvance: handleIndexChange,
      getItemCount: () => (typeof itemCount === "number" ? itemCount : 0),
      getCurrentIndex: () =>
        typeof currentIndex === "number" ? currentIndex : 0,
    });

    playbackControllerRef.current = controller;

    // If we were playing before, restart playback
    if (isPlaying) {
      controller.start();
    }

    return () => {
      controller.dispose();
    };
  }, [handleIndexChange, itemCount, currentIndex, playbackSpeed, isPlaying]);

  // Toggle playback
  const togglePlayback = () => {
    if (typeof onPlayPause === "function") {
      // Use external control if provided
      onPlayPause();
    } else if (playbackControllerRef.current) {
      // Otherwise use internal controller
      playbackControllerRef.current.toggle();
      setInternalIsPlaying(playbackControllerRef.current.isPlaying());
    }
  };

  // Reset to beginning
  const resetPlayback = () => {
    // Stop playback first
    if (playbackControllerRef.current) {
      playbackControllerRef.current.stop();
    }

    if (typeof onPlayPause === "function" && isPlaying) {
      onPlayPause(); // Turn off playing state in parent
    } else {
      setInternalIsPlaying(false);
    }

    // Reset to first item - try different approaches based on available props
    if (typeof onChangeIndex === "function") {
      onChangeIndex(0);
    } else if (typeof onStepBackward === "function" && currentIndex > 0) {
      // Simulate reset by stepping back to the first item
      // This is not ideal but works as a fallback
      for (let i = 0; i < currentIndex; i++) {
        onStepBackward();
      }
    }
  };

  // Skip to next item
  const nextItem = () => {
    if (typeof onStepForward === "function") {
      onStepForward();
    } else if (
      typeof onChangeIndex === "function" &&
      currentIndex < itemCount - 1
    ) {
      onChangeIndex(currentIndex + 1);
    }
  };

  // Skip to previous item
  const prevItem = () => {
    if (typeof onStepBackward === "function") {
      onStepBackward();
    } else if (typeof onChangeIndex === "function" && currentIndex > 0) {
      onChangeIndex(currentIndex - 1);
    }
  };

  // Change speed
  const changeSpeed = (newSpeed: number) => {
    setPlaybackSpeed(newSpeed);
  };

  return (
    <div className="playback-controls">
      <button
        className="control-button"
        onClick={resetPlayback}
        title="Reset to beginning"
      >
        ⏮️
      </button>

      <button
        className="control-button"
        onClick={prevItem}
        disabled={!canStepBackward}
        title="Previous item"
      >
        ⏪
      </button>

      <button
        className="control-button play-pause"
        onClick={togglePlayback}
        title={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? "⏸️ Pause" : "▶️ Play"}
      </button>

      <button
        className="control-button"
        onClick={nextItem}
        disabled={!canStepForward}
        title="Next item"
      >
        ⏩
      </button>

      <div className="speed-control">
        <span>Speed:</span>
        <select
          value={playbackSpeed}
          onChange={(e) =>
            changeSpeed(Number((e.target as HTMLSelectElement).value))
          }
        >
          <option value="0.5">0.5×</option>
          <option value="1">1×</option>
          <option value="2">2×</option>
          <option value="4">4×</option>
        </select>
      </div>

      <div className="playback-progress">
        {currentIndex + 1} / {itemCount}
      </div>
    </div>
  );
}

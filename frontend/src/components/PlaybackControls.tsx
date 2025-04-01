import { h } from 'preact';

interface PlaybackControlsProps {
  isPlaying: boolean;
  canStepForward: boolean;
  canStepBackward: boolean;
  onPlayPause: () => void;
  onStepForward: () => void;
  onStepBackward: () => void;
}

export function PlaybackControls({
  isPlaying,
  canStepForward,
  canStepBackward,
  onPlayPause,
  onStepForward,
  onStepBackward
}: PlaybackControlsProps) {
  return (
    <div className="playback-controls">
      <button 
        className="control-button" 
        onClick={onStepBackward}
        disabled={!canStepBackward}
      >
        ⏮️ Previous
      </button>
      
      <button 
        className="control-button play-pause" 
        onClick={onPlayPause}
      >
        {isPlaying ? '⏸️ Pause' : '▶️ Play'}
      </button>
      
      <button 
        className="control-button" 
        onClick={onStepForward}
        disabled={!canStepForward}
      >
        Next ⏭️
      </button>
    </div>
  );
}

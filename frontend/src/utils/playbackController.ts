/**
 * Manages playback functionality for timeline items.
 * This allows automatic stepping through timeline items at a configurable speed.
 */

type PlaybackOptions = {
  speed: number; // Playback speed (items per second)
  onAdvance: (newIndex: number) => void; // Callback when advancing to next item
  getItemCount: () => number; // Function to get total number of items
  getCurrentIndex: () => number; // Function to get current index
};

export class PlaybackController {
  private playing: boolean = false;
  private intervalId: number | null = null;
  private speed: number;
  private onAdvance: ((newIndex: number) => void) | null;
  private getItemCount: () => number;
  private getCurrentIndex: () => number;

  constructor(options: PlaybackOptions) {
    // Store the callback function
    this.speed = options.speed;
    this.onAdvance = options.onAdvance;
    this.getItemCount = options.getItemCount;
    this.getCurrentIndex = options.getCurrentIndex;

    // Validate callbacks immediately
    if (typeof this.onAdvance !== "function") {
      console.error(
        "PlaybackController: onAdvance is not a function",
        this.onAdvance,
      );
      this.onAdvance = null;
    }

    // Bind methods to ensure 'this' is correct
    this.start = this.start.bind(this);
    this.stop = this.stop.bind(this);
    this.toggle = this.toggle.bind(this);
    this.reset = this.reset.bind(this);
    this.setSpeed = this.setSpeed.bind(this);
    this.dispose = this.dispose.bind(this);
  }

  public start(): void {
    if (this.playing || !this.onAdvance) return;

    this.playing = true;
    const intervalMs = 1000 / this.speed;

    this.intervalId = window.setInterval(() => {
      try {
        const currentIndex = this.getCurrentIndex();
        const itemCount = this.getItemCount();

        // Validate the indices to prevent NaN and other issues
        if (typeof currentIndex !== "number" || isNaN(currentIndex)) {
          console.error(
            "PlaybackController: getCurrentIndex returned invalid value:",
            currentIndex,
          );
          this.stop();
          return;
        }

        if (
          typeof itemCount !== "number" ||
          isNaN(itemCount) ||
          itemCount <= 0
        ) {
          console.error(
            "PlaybackController: getItemCount returned invalid value:",
            itemCount,
          );
          this.stop();
          return;
        }

        // If we've reached the end, stop playback
        if (currentIndex >= itemCount - 1) {
          this.stop();
          return;
        }

        // Calculate the next index (safely)
        const nextIndex = Math.min(currentIndex + 1, itemCount - 1);

        // Use the callback if it exists
        if (typeof this.onAdvance === "function") {
          this.onAdvance(nextIndex);
        } else {
          console.error("PlaybackController: onAdvance is not a function");
          this.stop();
        }
      } catch (error) {
        console.error("Error in PlaybackController interval:", error);
        this.stop();
      }
    }, intervalMs);
  }

  public stop(): void {
    if (!this.playing) return;

    this.playing = false;
    if (this.intervalId !== null) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  public toggle(): void {
    if (this.playing) {
      this.stop();
    } else {
      this.start();
    }
  }

  public isPlaying(): boolean {
    return this.playing;
  }

  public setSpeed(speed: number): void {
    this.speed = speed;

    // Restart with new speed if currently playing
    if (this.playing) {
      this.stop();
      this.start();
    }
  }

  public reset(): void {
    this.stop();

    // Skip calling onAdvance if it's not a function
    if (this.onAdvance) {
      try {
        this.onAdvance(0);
      } catch (error) {
        console.error("Error in PlaybackController.reset:", error);
      }
    } else {
      console.error("Cannot reset: onAdvance callback is missing");
    }
  }

  // Ensure we clean up properly
  public dispose(): void {
    this.stop();
    this.onAdvance = null; // Clear the reference
  }
}

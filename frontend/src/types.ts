export interface BufferItem {
  timestamp: string;
  tags: Record<string, string | string[]>;
  type: "event" | "query" | "prompt";
  data: any;
}

export interface TimelineState {
  items: BufferItem[];
  selectedItemIndex: number | null;
  matchedIndices: number[]; // Add this to track items referenced by the selected query
  filters: {
    types: Set<string>;
    tags: Record<string, Set<string>>;
  };
  playback: {
    isPlaying: boolean;
    speed: number;
    currentIndex: number;
  };
}

import { h } from "preact";
import { useState, useEffect } from "preact/hooks";
import "./styles.css";

// Types
import { BufferItem, TimelineState } from "./types";
import { Header } from "./components/Header";
import { TimelineView } from "./components/TimelineView";
import { DetailSidebar } from "./components/DetailSidebar";
import { PlaybackControls } from "./components/PlaybackControls";

// Declare the global window type extension
declare global {
  interface Window {
    __PLOMP_BUFFER_JSON__: { buffer_items: BufferItem[] };
  }
}

export default function App() {
  // Initialize state with data from global window variable
  const [state, setState] = useState<TimelineState>({
    items: window.__PLOMP_BUFFER_JSON__?.buffer_items || [],
    selectedItemIndex: null,
    matchedIndices: [],
    filters: {
      types: new Set(["event", "query", "prompt"]),
      tags: {},
    },
    playback: {
      isPlaying: false,
      speed: 1,
      currentIndex: 0,
    },
  });

  // Select an item from the timeline
  const selectItem = (index: number, originalIndex: number) => {
    const item = state.items[originalIndex];
    let matchedIndices: number[] = [];

    // If the selected item is a query, check for matched_indices
    if (
      item &&
      item.type === "query" &&
      item.data &&
      item.data.matched_indices
    ) {
      matchedIndices = Array.isArray(item.data.matched_indices)
        ? item.data.matched_indices
        : [];
    }

    setState((prev) => ({
      ...prev,
      selectedItemIndex: originalIndex,
      matchedIndices: matchedIndices,
      playback: {
        ...prev.playback,
        currentIndex: index, // Keep track of the filtered index for playback
      },
    }));
  };

  // Apply filtering to timeline items and maintain original indices
  const filteredItemsWithIndices = state.items
    .map((item, index) => ({ item, originalIndex: index }))
    .filter(({ item }) => {
      // Filter by type
      if (!state.filters.types.has(item.type)) return false;

      // Filter by tags
      for (const [tagKey, tagValues] of Object.entries(state.filters.tags)) {
        if (tagValues.size === 0) continue;

        // If the item doesn't have this tag, filter it out
        if (!item.tags[tagKey]) return false;

        // If the item has the tag but not with a value we want, filter it out
        const itemTagValue = item.tags[tagKey];
        const tagValuesArray = Array.from(tagValues);

        if (Array.isArray(itemTagValue)) {
          if (!itemTagValue.some((v) => tagValuesArray.includes(v)))
            return false;
        } else if (!tagValuesArray.includes(itemTagValue)) {
          return false;
        }
      }

      return true;
    });

  // Extract just the items for components that don't need the original indices
  const filteredItems = filteredItemsWithIndices.map(({ item }) => item);

  // Map from filtered index to original index
  const originalIndices = filteredItemsWithIndices.map(
    ({ originalIndex }) => originalIndex,
  );

  // Find the filtered index that corresponds to the selected original index
  const filteredSelectedIndex = originalIndices.findIndex(
    (origIndex) => origIndex === state.selectedItemIndex,
  );

  // Toggle type filter
  const toggleTypeFilter = (type: string) => {
    setState((prev) => {
      const newTypes = new Set(prev.filters.types);
      if (newTypes.has(type)) {
        newTypes.delete(type);
      } else {
        newTypes.add(type);
      }
      return {
        ...prev,
        filters: {
          ...prev.filters,
          types: newTypes,
        },
      };
    });
  };

  // Toggle tag filter
  const toggleTagFilter = (tagKey: string, tagValue: string) => {
    setState((prev) => {
      const newTags = { ...prev.filters.tags };
      if (!newTags[tagKey]) {
        newTags[tagKey] = new Set([tagValue]);
      } else {
        const tagSet = new Set(newTags[tagKey]);
        if (tagSet.has(tagValue)) {
          tagSet.delete(tagValue);
        } else {
          tagSet.add(tagValue);
        }
        newTags[tagKey] = tagSet;
      }
      return {
        ...prev,
        filters: {
          ...prev.filters,
          tags: newTags,
        },
      };
    });
  };

  // Playback controls
  const handlePlayPause = () => {
    setState((prev) => ({
      ...prev,
      playback: {
        ...prev.playback,
        isPlaying: !prev.playback.isPlaying,
      },
    }));
  };

  const handleStepForward = () => {
    if (state.playback.currentIndex < filteredItems.length - 1) {
      const nextFilteredIndex = state.playback.currentIndex + 1;
      const nextOriginalIndex = originalIndices[nextFilteredIndex];

      setState((prev) => ({
        ...prev,
        selectedItemIndex: nextOriginalIndex,
        playback: {
          ...prev.playback,
          currentIndex: nextFilteredIndex,
        },
      }));
    }
  };

  const handleStepBackward = () => {
    if (state.playback.currentIndex > 0) {
      const prevFilteredIndex = state.playback.currentIndex - 1;
      const prevOriginalIndex = originalIndices[prevFilteredIndex];

      setState((prev) => ({
        ...prev,
        selectedItemIndex: prevOriginalIndex,
        playback: {
          ...prev.playback,
          currentIndex: prevFilteredIndex,
        },
      }));
    }
  };

  const handleChangeIndex = (index: number) => {
    const originalIndex = originalIndices[index];

    setState((prev) => ({
      ...prev,
      selectedItemIndex: originalIndex,
      playback: {
        ...prev.playback,
        currentIndex: index,
      },
    }));
  };

  // Collect unique tag keys and values for filtering
  const availableTags: Record<string, Set<string>> = {};
  state.items.forEach((item) => {
    Object.entries(item.tags).forEach(([key, value]) => {
      if (!availableTags[key]) {
        availableTags[key] = new Set();
      }

      if (Array.isArray(value)) {
        value.forEach((v) => availableTags[key].add(v));
      } else {
        availableTags[key].add(value);
      }
    });
  });

  return (
    <div className="app-container">
      <Header
        availableTags={availableTags}
        selectedTypes={state.filters.types}
        selectedTags={state.filters.tags}
        onToggleType={toggleTypeFilter}
        onToggleTag={toggleTagFilter}
      />

      <div className="main-content">
        <PlaybackControls
          isPlaying={state.playback.isPlaying}
          onPlayPause={handlePlayPause}
          onStepForward={handleStepForward}
          onStepBackward={handleStepBackward}
          canStepForward={
            state.playback.currentIndex < filteredItems.length - 1
          }
          canStepBackward={state.playback.currentIndex > 0}
          itemCount={filteredItems.length}
          currentIndex={state.playback.currentIndex}
          onChangeIndex={handleChangeIndex}
        />

        <div className="content-area">
          <TimelineView
            items={filteredItems}
            originalIndices={originalIndices}
            selectedIndex={
              filteredSelectedIndex !== -1 ? filteredSelectedIndex : null
            }
            currentIndex={state.playback.currentIndex}
            matchedIndices={state.matchedIndices
              .map((origIndex) =>
                originalIndices.findIndex((idx) => idx === origIndex),
              )
              .filter((idx) => idx !== -1)}
            onSelectItem={selectItem}
          />

          <DetailSidebar
            item={
              state.selectedItemIndex !== null
                ? state.items[state.selectedItemIndex]
                : null
            }
            allItems={state.items}
          />
        </div>
      </div>
    </div>
  );
}

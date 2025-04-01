import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import sampleData from './vite-plugins/sample-buffer-data.json';
import './styles.css';

// Types
import { BufferItem, TimelineState } from './types';
import { Header } from './components/Header';
import { TimelineView } from './components/TimelineView';
import { DetailSidebar } from './components/DetailSidebar';
import { PlaybackControls } from './components/PlaybackControls';

export default function App() {
  // Initialize state with sample data
  const [state, setState] = useState<TimelineState>({
    items: sampleData.buffer_items,
    selectedItemIndex: null,
    filters: {
      types: new Set(['event', 'query', 'prompt']),
      tags: {}
    },
    playback: {
      isPlaying: false,
      speed: 1,
      currentIndex: 0
    }
  });

  // Select an item from the timeline
  const selectItem = (index: number) => {
    setState(prev => ({
      ...prev,
      selectedItemIndex: index,
      playback: {
        ...prev.playback,
        currentIndex: index
      }
    }));
  };

  // Apply filtering to timeline items
  const filteredItems = state.items.filter(item => {
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
        if (!itemTagValue.some(v => tagValuesArray.includes(v))) return false;
      } else if (!tagValuesArray.includes(itemTagValue)) {
        return false;
      }
    }
    
    return true;
  });

  // Toggle type filter
  const toggleTypeFilter = (type: string) => {
    setState(prev => {
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
          types: newTypes
        }
      };
    });
  };

  // Toggle tag filter
  const toggleTagFilter = (tagKey: string, tagValue: string) => {
    setState(prev => {
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
          tags: newTags
        }
      };
    });
  };

  // Playback controls
  const handlePlayPause = () => {
    setState(prev => ({
      ...prev,
      playback: {
        ...prev.playback,
        isPlaying: !prev.playback.isPlaying
      }
    }));
  };

  const handleStepForward = () => {
    if (state.playback.currentIndex < filteredItems.length - 1) {
      const nextIndex = state.playback.currentIndex + 1;
      setState(prev => ({
        ...prev,
        selectedItemIndex: nextIndex,
        playback: {
          ...prev.playback,
          currentIndex: nextIndex
        }
      }));
    }
  };

  const handleStepBackward = () => {
    if (state.playback.currentIndex > 0) {
      const prevIndex = state.playback.currentIndex - 1;
      setState(prev => ({
        ...prev,
        selectedItemIndex: prevIndex,
        playback: {
          ...prev.playback,
          currentIndex: prevIndex
        }
      }));
    }
  };

  // Collect unique tag keys and values for filtering
  const availableTags: Record<string, Set<string>> = {};
  state.items.forEach(item => {
    Object.entries(item.tags).forEach(([key, value]) => {
      if (!availableTags[key]) {
        availableTags[key] = new Set();
      }
      
      if (Array.isArray(value)) {
        value.forEach(v => availableTags[key].add(v));
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
          canStepForward={state.playback.currentIndex < filteredItems.length - 1}
          canStepBackward={state.playback.currentIndex > 0}
        />
        
        <div className="content-area">
          <TimelineView 
            items={filteredItems}
            selectedIndex={state.selectedItemIndex}
            currentIndex={state.playback.currentIndex}
            onSelectItem={selectItem}
          />
          
          <DetailSidebar 
            item={state.selectedItemIndex !== null ? state.items[state.selectedItemIndex] : null}
          />
        </div>
      </div>
    </div>
  );
}

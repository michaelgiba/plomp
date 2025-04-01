import { h } from "preact";
import { useEffect, useRef } from "preact/hooks";
import { BufferItem } from "../types";
import { TimelineItem } from "./TimelineItem";
import { setupTimelineKeyboardNavigation } from "../utils/keyboardNavigation";

interface TimelineViewProps {
  items: BufferItem[];
  selectedIndex: number | null;
  currentIndex: number;
  matchedIndices: number[]; // Add matched indices prop
  onSelectItem: (index: number) => void;
}

export function TimelineView({
  items,
  selectedIndex,
  currentIndex,
  matchedIndices,
  onSelectItem,
}: TimelineViewProps) {
  const timelineRef = useRef<HTMLDivElement>(null);

  // Set up keyboard navigation
  useEffect(() => {
    // Function to get all timeline items
    const getTimelineItems = () => {
      if (!timelineRef.current) return [];
      return Array.from(timelineRef.current.querySelectorAll(".timeline-item"));
    };

    // Set up keyboard navigation and get cleanup function
    const cleanup = setupTimelineKeyboardNavigation(
      getTimelineItems,
      onSelectItem,
    );

    // Clean up event listener on unmount
    return cleanup;
  }, [onSelectItem]);

  // Scroll selected item into view when selection changes
  useEffect(() => {
    if (selectedIndex !== null && timelineRef.current) {
      const items = timelineRef.current.querySelectorAll(".timeline-item");
      if (items[selectedIndex]) {
        items[selectedIndex].scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }
    }
  }, [selectedIndex]);

  return (
    <div className="timeline-view" ref={timelineRef}>
      <div className="timeline-items">
        {items.map((item, index) => (
          <TimelineItem
            key={index}
            item={item}
            index={index}
            isSelected={selectedIndex === index}
            isCurrent={currentIndex === index}
            isMatched={matchedIndices.includes(index)}
            onSelect={() => onSelectItem(index)}
          />
        ))}
      </div>
    </div>
  );
}

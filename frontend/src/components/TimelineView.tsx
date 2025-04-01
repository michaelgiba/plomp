import { h } from 'preact';
import { BufferItem } from '../types';
import { TimelineItem } from './TimelineItem';

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
  onSelectItem 
}: TimelineViewProps) {
  return (
    <div className="timeline-view">
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

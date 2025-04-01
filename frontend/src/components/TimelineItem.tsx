import { h } from 'preact';
import { BufferItem } from '../types';

interface TimelineItemProps {
  item: BufferItem;
  index: number;
  isSelected: boolean;
  isCurrent: boolean;
  onSelect: () => void;
}

export function TimelineItem({ 
  item, 
  index, 
  isSelected, 
  isCurrent, 
  onSelect 
}: TimelineItemProps) {
  const timestamp = new Date(item.timestamp);
  const formattedTime = timestamp.toLocaleTimeString();
  
  // Generate a summary based on the item type
  let summary = '';
  if (item.type === 'event') {
    const eventType = item.tags.event_type || 'unknown';
    const message = item.data.payload?.message || '';
    summary = `${eventType}: ${message}`;
  } else if (item.type === 'query') {
    summary = item.data.op_name || 'Query operation';
  } else if (item.type === 'prompt') {
    const model = item.tags.model || 'unknown';
    const promptText = item.data.prompt || '';
    summary = `${model}: ${promptText}`;
  }
  
  // Truncate summary if it's too long
  if (summary.length > 100) {
    summary = summary.substring(0, 97) + '...';
  }
  
  return (
    <div 
      className={`timeline-item ${item.type} ${isSelected ? 'selected' : ''} ${isCurrent ? 'current' : ''}`}
      onClick={onSelect}
    >
      <div className="item-header">
        <div className="item-timestamp">{formattedTime}</div>
        <div className="item-type">{item.type}</div>
      </div>
      <div className="item-summary">{summary}</div>
      <div className="item-tags">
        {Object.entries(item.tags).map(([key, value]) => (
          <span key={key} className="tag">
            {key}:{String(value)}
          </span>
        ))}
      </div>
    </div>
  );
}

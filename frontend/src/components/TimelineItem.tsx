import { h } from "preact";
import { BufferItem } from "../types";

interface TimelineItemProps {
  item: BufferItem;
  index: number;
  isSelected: boolean;
  isCurrent: boolean;
  isMatched: boolean; // Add this prop
  onSelect: () => void;
}

export function TimelineItem({
  item,
  index,
  isSelected,
  isCurrent,
  isMatched,
  onSelect,
}: TimelineItemProps) {
  const timestamp = new Date(item.timestamp);
  const formattedTime = timestamp.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  // Generate a short summary based on the item type
  let summary = "";
  if (item.type === "event") {
    const eventType = item.tags.event_type || "unknown";
    const context = item.data.payload?.context || "";
    summary = `${eventType}: ${context}`;
  } else if (item.type === "query") {
    summary = `query: ${item.data.op_name}` || "Query operation";
  } else if (item.type === "prompt") {
    const promptText = item.data.prompt || "";
    summary = `prompt: "${promptText}"`;
  }

  // Truncate summary if it's too long
  if (summary.length > 80) {
    summary = summary.substring(0, 77) + "...";
  }

  // Check if prompt is incomplete (has no completion/response)
  const isIncompletePrompt =
    item.type === "prompt" &&
    !item.data.response &&
    !item.data.completion &&
    !item.data.answer;

  return (
    <div
      className={`timeline-item ${item.type} ${isSelected ? "selected" : ""} ${isCurrent ? "current" : ""} ${isMatched ? "matched" : ""} ${isIncompletePrompt ? "incomplete" : ""}`}
      onClick={onSelect}
    >
      <div className="item-header">
        <div className="item-timestamp">{formattedTime}</div>
        <div className="item-type">
          {item.type}
          {isIncompletePrompt && (
            <span className="incomplete-indicator">•</span>
          )}
        </div>
      </div>
      <div className="item-summary">{summary}</div>
    </div>
  );
}

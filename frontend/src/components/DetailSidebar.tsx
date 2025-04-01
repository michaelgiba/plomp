import { h } from "preact";
import { useState } from "preact/hooks";
import { BufferItem } from "../types";

interface DetailSidebarProps {
  item: BufferItem | null;
  allItems: BufferItem[]; // Add this prop to access all items
}

export function DetailSidebar({ item, allItems }: DetailSidebarProps) {
  const [showRawJson, setShowRawJson] = useState(false);

  if (!item) {
    return (
      <div className="detail-sidebar">
        <div className="no-selection">Select an item to view details</div>
      </div>
    );
  }

  const timestamp = new Date(item.timestamp);

  // Render tags as chip components
  const renderTags = () => {
    if (Object.keys(item.tags).length === 0) {
      return <div className="detail-empty">No tags</div>;
    }

    return (
      <div className="detail-tags">
        {Object.entries(item.tags).map(([key, value]) => (
          <div key={key} className="detail-tag">
            <span className="detail-tag-key">{key}:</span>
            <span className="detail-tag-value">{String(value)}</span>
          </div>
        ))}
      </div>
    );
  };

  // Get a summary description for an item (used for matched items)
  const getItemSummary = (item: BufferItem): string => {
    if (item.type === "event") {
      const eventType = item.tags.event_type || "unknown";
      const message = item.data.payload?.message || "";
      return `${eventType}: ${message}`;
    } else if (item.type === "query") {
      return item.data.op_name || "Query operation";
    } else if (item.type === "prompt") {
      const model = item.tags.model || "unknown";
      const promptText = item.data.prompt || "";
      return `${model}: ${promptText}`;
    }
    return "Unknown item";
  };

  // Render content based on item type
  const renderContent = () => {
    switch (item.type) {
      case "event":
        return renderEventContent();
      case "query":
        return renderQueryContent();
      case "prompt":
        return renderPromptContent();
      default:
        return <div className="detail-empty">Unknown item type</div>;
    }
  };

  // Render event-specific content
  const renderEventContent = () => {
    const eventType = item.tags.event_type || "Unknown";
    const message = item.data.payload?.message || "";
    const metadata = item.data.metadata || {};

    return (
      <div className="structured-content event-content">
        <div className="content-section">
          <div className="content-section-title">Event Details</div>
          <div className="content-item">
            <span className="content-item-label">Event Type</span>
            <span className="content-item-value">{eventType}</span>
          </div>
          {message && (
            <div className="content-item">
              <span className="content-item-label">Message</span>
              <span className="content-item-value">{message}</span>
            </div>
          )}
        </div>

        {Object.keys(metadata).length > 0 && (
          <div className="content-section">
            <div className="content-section-title">Metadata</div>
            {Object.entries(metadata).map(([key, value]) => (
              <div key={key} className="content-item">
                <span className="content-item-label">{key}</span>
                <span className="content-item-value">
                  {typeof value === "object"
                    ? JSON.stringify(value, null, 2)
                    : String(value)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Render query-specific content
  const renderQueryContent = () => {
    const opName = item.data.op_name || "Unknown Operation";
    const matchedIndices = item.data.matched_indices || [];
    const parameters = item.data.parameters || {};

    return (
      <div className="structured-content query-content">
        <div className="content-section">
          <div className="content-section-title">Query Details</div>
          <div className="content-item">
            <span className="content-item-label">Operation</span>
            <span className="content-item-value">{opName}</span>
          </div>

          {matchedIndices.length > 0 && (
            <div className="content-item">
              <span className="content-item-label">Matched Items</span>
              <div className="matched-items-list">
                {matchedIndices.map((idx, i) => {
                  const matchedItem = allItems[idx];
                  if (!matchedItem) return null;

                  const summary = getItemSummary(matchedItem);
                  const timestamp = new Date(
                    matchedItem.timestamp,
                  ).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  });

                  return (
                    <div key={i} className="matched-item">
                      <div className="matched-item-header">
                        <span className="matched-item-type">
                          {matchedItem.type}
                        </span>
                        <span className="matched-item-time">{timestamp}</span>
                      </div>
                      <div className="matched-item-summary">{summary}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {Object.keys(parameters).length > 0 && (
          <div className="content-section">
            <div className="content-section-title">Parameters</div>
            {Object.entries(parameters).map(([key, value]) => (
              <div key={key} className="content-item">
                <span className="content-item-label">{key}</span>
                <span className="content-item-value">
                  {typeof value === "object"
                    ? JSON.stringify(value, null, 2)
                    : String(value)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Render prompt-specific content
  const renderPromptContent = () => {
    const model = item.tags.model || "Unknown";
    const promptText = item.data.prompt || "";

    // Improved completion extraction logic
    let completion = "";
    let completionTimestamp = "";

    // Check for different completion structures
    if (item.data.completion) {
      // Handle case where completion is an object with response field
      if (
        typeof item.data.completion === "object" &&
        item.data.completion !== null
      ) {
        completion = item.data.completion.response || "";
        completionTimestamp = item.data.completion.completion_timestamp || "";
      } else {
        // Handle case where completion is a direct string
        completion = String(item.data.completion);
      }
    } else if (item.data.response) {
      completion = item.data.response;
    } else if (item.data.answer) {
      completion = item.data.answer;
    } else if (item.data.content) {
      completion = item.data.content;
    } else if (item.data.choices && item.data.choices.length > 0) {
      // Handle OpenAI-style response format
      const firstChoice = item.data.choices[0];
      completion =
        firstChoice.text ||
        firstChoice.message?.content ||
        firstChoice.content ||
        "";
    }

    const isComplete = completion !== "";

    return (
      <div className="structured-content prompt-content">
        <div className="content-section">
          <div className="content-section-title">
            Prompt Details
            {!isComplete && (
              <span className="prompt-status incomplete">Incomplete</span>
            )}
            {isComplete && (
              <span className="prompt-status complete">Complete</span>
            )}
          </div>

          <div className="content-item">
            <span className="content-item-label">Model</span>
            <span className="content-item-value">{model}</span>
          </div>

          {promptText && (
            <div className="content-item">
              <span className="content-item-label">Prompt</span>
              <span className="content-item-value prompt-text">
                {promptText}
              </span>
            </div>
          )}

          {isComplete ? (
            <div className="content-item">
              <span className="content-item-label">Completion</span>
              <pre className="content-item-value completion-text">
                {completion}
              </pre>
            </div>
          ) : (
            <div className="content-item">
              <span className="content-item-label">Completion</span>
              <span className="content-item-value completion-missing">
                No completion available - the model may still be processing or
                an error occurred.
              </span>
            </div>
          )}

          {completionTimestamp && (
            <div className="content-item">
              <span className="content-item-label">Completion Time</span>
              <span className="content-item-value">
                {new Date(completionTimestamp).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="detail-sidebar">
      <div className="item-details">
        <h2>
          {item.type.charAt(0).toUpperCase() + item.type.slice(1)} Details
        </h2>

        <div className="detail-section">
          <h3>Basic Information</h3>
          <div className="detail-row">
            <span className="detail-label">Timestamp:</span>
            <span className="detail-value">{timestamp.toLocaleString()}</span>
          </div>
        </div>

        <div className="detail-section">
          <h3>Tags</h3>
          {renderTags()}
        </div>

        <div className="detail-section">
          <h3>Content</h3>
          {renderContent()}
        </div>

        <div className="json-toggle">
          <button
            className="json-toggle-button"
            onClick={() => setShowRawJson(!showRawJson)}
          >
            {showRawJson ? "Hide Raw JSON" : "View Raw JSON"}
          </button>
        </div>

        {showRawJson && (
          <div className="json-data-container">
            <h3>Raw JSON Data</h3>
            <pre className="json-data">
              {JSON.stringify(
                item.data,
                (key, value) => {
                  // Safely handle circular references and complex objects
                  try {
                    if (typeof value === "object" && value !== null) {
                      if (Object.keys(value).length > 100) {
                        return `[Complex Object with ${Object.keys(value).length} keys]`;
                      }
                    }
                    return value;
                  } catch (error) {
                    return "[Error displaying value]";
                  }
                },
                2,
              )}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

import { h } from 'preact';
import { BufferItem } from '../types';

interface DetailSidebarProps {
  item: BufferItem | null;
}

export function DetailSidebar({ item }: DetailSidebarProps) {
  if (!item) {
    return (
      <div className="detail-sidebar">
        <div className="no-selection">Select an item to view details</div>
      </div>
    );
  }

  const timestamp = new Date(item.timestamp);

  return (
    <div className="detail-sidebar">
      <div className="item-details">
        <h2>Item Details</h2>
        <div className="detail-section">
          <h3>Basic Information</h3>
          <div className="detail-row">
            <span className="detail-label">Type:</span>
            <span className="detail-value">{item.type}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Timestamp:</span>
            <span className="detail-value">{timestamp.toLocaleString()}</span>
          </div>
        </div>

        <div className="detail-section">
          <h3>Tags</h3>
          {Object.keys(item.tags).length === 0 ? (
            <div className="detail-empty">No tags</div>
          ) : (
            Object.entries(item.tags).map(([key, value]) => (
              <div key={key} className="detail-row">
                <span className="detail-label">{key}:</span>
                <span className="detail-value">{String(value)}</span>
              </div>
            ))
          )}
        </div>

        <div className="detail-section">
          <h3>Data</h3>
          <pre className="json-data">
            {JSON.stringify(item.data, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

import { h } from 'preact';

interface HeaderProps {
  availableTags: Record<string, Set<string>>;
  selectedTypes: Set<string>;
  selectedTags: Record<string, Set<string>>;
  onToggleType: (type: string) => void;
  onToggleTag: (tagKey: string, tagValue: string) => void;
}

export function Header({ 
  availableTags, 
  selectedTypes, 
  selectedTags, 
  onToggleType, 
  onToggleTag 
}: HeaderProps) {
  return (
    <header className="app-header">
      <div className="filter-controls">
        <div className="type-filters">
          <h3>Types:</h3>
          <div className="filter-options">
            {['event', 'query', 'prompt'].map(type => (
              <label key={type} className="filter-option">
                <input
                  type="checkbox"
                  checked={selectedTypes.has(type)}
                  onChange={() => onToggleType(type)}
                />
                {type}
              </label>
            ))}
          </div>
        </div>
        
        <div className="tag-filters">
          {Object.entries(availableTags).map(([tagKey, tagValues]) => (
            <div key={tagKey} className="tag-filter-group">
              <h4>{tagKey}:</h4>
              <div className="filter-options">
                {Array.from(tagValues).map(tagValue => (
                  <label key={`${tagKey}-${tagValue}`} className="filter-option">
                    <input
                      type="checkbox"
                      checked={selectedTags[tagKey]?.has(tagValue) || false}
                      onChange={() => onToggleTag(tagKey, tagValue)}
                    />
                    {tagValue}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}

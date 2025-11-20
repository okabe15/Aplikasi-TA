import React from 'react';
import { CheckSquare, Square } from 'lucide-react';

export default function TopicSelector({
  topics,
  selectedTopics,
  onTopicToggle,
  onSelectAll,
  onSelectBasic,
  onClearAll
}) {
  return (
    <div className="topic-selector">
      <h4>Choose Grammar Topics to Focus On:</h4>
      <p className="hint">
        Select which grammar areas you want to practice. Questions will be generated focusing on these topics.
      </p>

      <div className="topic-grid">
        {topics.map(topic => (
          <label key={topic.id} className="topic-item">
            <input
              type="checkbox"
              checked={selectedTopics.includes(topic.id)}
              onChange={() => onTopicToggle(topic.id)}
            />
            {selectedTopics.includes(topic.id) ? (
              <CheckSquare size={20} color="#667eea" />
            ) : (
              <Square size={20} color="#999" />
            )}
            <div className="topic-info">
              <strong>{topic.label}</strong>
              <span className="topic-desc">{topic.description}</span>
              {topic.is_basic && <span className="badge">Basic</span>}
            </div>
          </label>
        ))}
      </div>

      <div className="topic-selection-summary">
        <strong>Selected Topics:</strong>{' '}
        {selectedTopics.length > 0 ? (
          topics
            .filter(t => selectedTopics.includes(t.id))
            .map(t => t.label)
            .join(', ')
        ) : (
          <span className="text-warning">None selected - Please select at least one topic</span>
        )}
      </div>

      <div className="button-group">
        <button onClick={onSelectAll} className="btn btn-secondary btn-sm">
          Select All
        </button>
        <button onClick={onSelectBasic} className="btn btn-secondary btn-sm">
          Select Basic
        </button>
        <button onClick={onClearAll} className="btn btn-secondary btn-sm">
          Clear All
        </button>
      </div>
    </div>
  );
}
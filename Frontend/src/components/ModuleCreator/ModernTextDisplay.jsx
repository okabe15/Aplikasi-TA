import React from 'react';
import { ArrowRight, Volume2, Edit3 } from 'lucide-react';

export default function ModernTextDisplay({
  originalText,
  modernText,
  onEdit,
  onGenerateComic,
  onPlayAudio,
  loading
}) {
  return (
    <div className="modern-text-section">
      <div className="section-header">
        <ArrowRight size={24} />
        <h2>Step 2: Modernized Text</h2>
      </div>

      <div className="comparison-view">
        <div className="text-panel">
          <h3>Original Classic Text</h3>
          <div className="text-content">{originalText}</div>
          <button
            className="btn-audio"
            onClick={() => onPlayAudio(originalText, 'classic')}
          >
            <Volume2 size={16} />
            Play Classic Version
          </button>
        </div>

        <div className="text-panel">
          <h3>Modernized Text</h3>
          <div className="text-content">{modernText}</div>
          <button
            className="btn-audio"
            onClick={() => onPlayAudio(modernText, 'modern')}
          >
            <Volume2 size={16} />
            Play Modern Version
          </button>
        </div>
      </div>

      <div className="button-group">
        <button className="btn btn-secondary" onClick={onEdit}>
          <Edit3 size={18} />
          Edit Text
        </button>
        <button
          className="btn btn-success"
          onClick={onGenerateComic}
          disabled={loading}
        >
          Create Comic
        </button>
      </div>
    </div>
  );
}
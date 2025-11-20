import React from 'react';
import { Wand2 } from 'lucide-react';

export default function ComicScriptDisplay({ script, onGeneratePanels, loading }) {
  return (
    <div className="comic-script-section">
      <div className="section-header">
        <Wand2 size={24} />
        <h2>Step 3: Comic Script Generated</h2>
      </div>

      <div className="script-preview">
        <h4>Generated Comic Script:</h4>
        <div className="text-display">
          {script.raw_script}
        </div>
        <p className="hint">
          {script.panels.length} panels will be generated with images and audio
        </p>
      </div>

      <div className="panels-summary">
        <h4>Panels Summary:</h4>
        {script.panels.map(panel => (
          <div key={panel.id} className="panel-summary-card">
            <strong>Panel {panel.id}:</strong>
            <div><em>Dialogue:</em> {panel.dialogue}</div>
            <div><em>Narration:</em> {panel.narration.substring(0, 100)}...</div>
          </div>
        ))}
      </div>

      <div className="button-group">
        <button
          onClick={onGeneratePanels}
          className="btn btn-success"
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate Comic Panels with Audio'}
        </button>
      </div>
    </div>
  );
}
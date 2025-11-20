import React, { useState } from 'react';
import { BookOpen, Sparkles } from 'lucide-react';

const EXAMPLE_TEXT = `"Thou art more lovely and more temperate than a summer's day, fair maiden," quoth the knight unto the lady fair. "Verily, thy beauty doth surpass the fairest roses that bloom in all the gardens of the realm. Pray tell, what manner of enchantment hast thou wrought upon my heart, that I should find myself so bewitched by thy countenance?"

The lady blushed most prettily and replied, "Good sir knight, thy words are honeyed and sweet, yet I fear thou dost flatter me beyond all measure. I am but a simple maid, unworthy of such praise from one so noble as thyself."`;

export default function ClassicTextInput({ onSubmit, loading }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim()) {
      onSubmit(text);
    }
  };

  const useExample = () => {
    setText(EXAMPLE_TEXT);
  };

  return (
    <div className="classic-input-section">
      <div className="section-header">
        <BookOpen size={24} />
        <h2>Step 1: Input Classic English Text</h2>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="classicText">
            Classic English Text
            <span className="hint">From Shakespeare, Dickens, Austen, etc.</span>
          </label>
          <textarea
            id="classicText"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste your classic English text here..."
            rows={10}
            disabled={loading}
          />
        </div>

        <div className="button-group">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !text.trim()}
          >
            <Sparkles size={18} />
            {loading ? 'Processing...' : 'Modernize Text'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={useExample}
            disabled={loading}
          >
            Use Example
          </button>
        </div>
      </form>
    </div>
  );
}
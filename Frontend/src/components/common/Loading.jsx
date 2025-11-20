import React from 'react';
import { Loader2 } from 'lucide-react';

export default function Loading({ message = 'Processing...' }) {
  return (
    <div className="loading-overlay">
      <div className="loading-content">
        <Loader2 size={48} className="spinner" />
        <p>{message}</p>
      </div>
    </div>
  );
}
import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default function ConfirmDialog({ 
  title, 
  message, 
  onConfirm, 
  onCancel, 
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmColor = 'danger' 
}) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content confirm-dialog" onClick={e => e.stopPropagation()}>
        <div className="confirm-icon">
          <AlertTriangle size={48} color="#dc3545" />
        </div>
        
        <h3>{title}</h3>
        <p>{message}</p>
        
        <div className="confirm-actions">
          <button 
            onClick={onCancel} 
            className="btn btn-secondary"
          >
            {cancelText}
          </button>
          <button 
            onClick={onConfirm} 
            className={`btn btn-${confirmColor}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
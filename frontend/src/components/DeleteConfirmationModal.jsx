import React from 'react';

function DeleteConfirmationModal({ 
  selectedStockIds, 
  onClose, 
  onConfirm, 
  isDeleting 
}) {
  return (
    <div className="modal modal--overlay" onClick={onClose}>
      <div className="modal-content modal-content--small" onClick={(e) => e.stopPropagation()}>
        <span className="close" onClick={onClose}>&times;</span>
        <h2>Aktien löschen?</h2>
        <p className="modal-subtitle">
          {selectedStockIds.size === 1 
            ? 'Möchten Sie diese Aktie wirklich aus der Watchlist entfernen?'
            : `Möchten Sie wirklich ${selectedStockIds.size} Aktien aus der Watchlist entfernen?`
          }
        </p>
        <p style={{ color: '#6b7280', fontSize: '0.9rem', marginTop: '12px' }}>
          Diese Aktion kann nicht rückgängig gemacht werden.
        </p>

        <div className="modal-actions modal-actions--right" style={{ marginTop: '24px' }}>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={onClose}
            disabled={isDeleting}
          >
            Abbrechen
          </button>
          <button
            type="button"
            className="btn btn--danger"
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? 'Wird gelöscht...' : 'Löschen'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default DeleteConfirmationModal;

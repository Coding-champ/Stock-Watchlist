import React from 'react';

function TransferModal({ 
  selectedStockIds, 
  transferAction, 
  watchlists, 
  currentWatchlistId, 
  selectedTargetWatchlist, 
  setSelectedTargetWatchlist, 
  onClose, 
  onConfirm, 
  isTransferring 
}) {
  return (
    <div className="modal modal--overlay" onClick={onClose}>
      <div className="modal-content modal-content--small" onClick={(e) => e.stopPropagation()}>
        <span className="close" onClick={onClose}>&times;</span>
        <h2>
          {transferAction === 'move' ? 'Aktien verschieben' : 'Aktien kopieren'}
        </h2>
        <p className="modal-subtitle">
          {selectedStockIds.size === 1 
            ? `Diese Aktie in eine andere Watchlist ${transferAction === 'move' ? 'verschieben' : 'kopieren'}:`
            : `${selectedStockIds.size} Aktien in eine andere Watchlist ${transferAction === 'move' ? 'verschieben' : 'kopieren'}:`
          }
        </p>

        <div className="form-group" style={{ marginTop: '20px' }}>
          <label htmlFor="target-watchlist">Ziel-Watchlist</label>
          <select
            id="target-watchlist"
            value={selectedTargetWatchlist || ''}
            onChange={(e) => setSelectedTargetWatchlist(Number(e.target.value))}
            disabled={isTransferring}
          >
            {watchlists
              .filter(wl => wl.id !== currentWatchlistId)
              .map(wl => (
                <option key={wl.id} value={wl.id}>
                  {wl.name}
                </option>
              ))
            }
          </select>
        </div>

        {transferAction === 'move' && (
          <p style={{ color: '#6b7280', fontSize: '0.9rem', marginTop: '12px' }}>
            Die Aktien werden aus der aktuellen Watchlist entfernt.
          </p>
        )}

        <div className="modal-actions modal-actions--right" style={{ marginTop: '24px' }}>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={onClose}
            disabled={isTransferring}
          >
            Abbrechen
          </button>
          <button
            type="button"
            className="btn btn--primary"
            onClick={onConfirm}
            disabled={isTransferring || !selectedTargetWatchlist}
          >
            {isTransferring 
              ? `Wird ${transferAction === 'move' ? 'verschoben' : 'kopiert'}...` 
              : transferAction === 'move' ? 'Verschieben' : 'Kopieren'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default TransferModal;

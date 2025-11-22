import React from 'react';

function MultiSelectionToolbar({
  selectedStockIds,
  totalStocks,
  selectAllStocks,
  clearSelection,
  openTransferModal,
  confirmDeleteSelectedStocks,
  toggleSelectionMode,
  isDeleting,
  watchlists,
  currentWatchlistId
}) {
  return (
    <div className="stock-selection-toolbar">
      <div className="stock-selection-toolbar__info">
        <span className="stock-selection-toolbar__count">
          {selectedStockIds.size} von {totalStocks} ausgewählt
        </span>
      </div>
      <div className="stock-selection-toolbar__actions">
        <button
          type="button"
          className="btn btn--ghost btn--small"
          onClick={selectAllStocks}
        >
          Alle auswählen
        </button>
        <button
          type="button"
          className="btn btn--ghost btn--small"
          onClick={clearSelection}
          disabled={selectedStockIds.size === 0}
        >
          Auswahl aufheben
        </button>
        <button
          type="button"
          className="btn btn--primary btn--small"
          onClick={() => openTransferModal('move')}
          disabled={selectedStockIds.size === 0 || watchlists.filter(wl => wl.id !== currentWatchlistId).length === 0}
        >
          Verschieben
        </button>
        <button
          type="button"
          className="btn btn--primary btn--small"
          onClick={() => openTransferModal('copy')}
          disabled={selectedStockIds.size === 0 || watchlists.filter(wl => wl.id !== currentWatchlistId).length === 0}
        >
          Kopieren
        </button>
        <button
          type="button"
          className="btn btn--danger btn--small"
          onClick={confirmDeleteSelectedStocks}
          disabled={selectedStockIds.size === 0 || isDeleting}
        >
          {isDeleting 
            ? 'Wird gelöscht...' 
            : selectedStockIds.size > 0 
              ? `${selectedStockIds.size} Löschen` 
              : 'Löschen'}
        </button>
        <button
          type="button"
          className="btn btn--secondary btn--small"
          onClick={toggleSelectionMode}
        >
          Abbrechen
        </button>
      </div>
    </div>
  );
}

export default MultiSelectionToolbar;

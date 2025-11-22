import React from 'react';
import { createPortal } from 'react-dom';

function ActionMenu({
  openMenuId,
  menuCoords,
  enrichedStocks,
  stocks,
  sparklineSeries,
  watchlists,
  currentWatchlistId,
  setOpenMenuId,
  setAlertModalStock,
  setEditObservationsStock,
  onUpdateMarketData,
  openTransferPanel,
  transferContext,
  handleTransferSelectionChange,
  handleCancelTransfer,
  handleConfirmTransfer,
  setSelectionMode,
  setSelectedStockIds
}) {
  if (typeof document === 'undefined' || openMenuId === null) {
    return null;
  }

  return createPortal(
    <div
      className="action-menu__list action-menu__list--portal"
      role="menu"
      style={{
        position: (menuCoords && menuCoords.absolute) ? 'absolute' : 'fixed',
        top: `${(menuCoords && menuCoords.top) ? `${menuCoords.top}px` : '50%'}`,
        left: `${(menuCoords && menuCoords.left) ? `${menuCoords.left}px` : '50%'}`,
        width: `${(menuCoords && menuCoords.width) ? `${menuCoords.width}px` : 'min(320px, 92vw)'}`,
        transform: `${menuCoords ? 'none' : 'translate(-50%, -50%)'}`,
        zIndex: 99999
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {(() => {
        // Try to locate the stock entry robustly: prefer enrichedStocks (full data),
        // fall back to raw stocks array if needed (may happen when filters changed).
        let entry = enrichedStocks.find((en) => en.stock.id === openMenuId) || null;
        if (!entry) {
          const raw = stocks.find((s) => s.id === openMenuId);
          if (raw) {
            entry = {
              stock: raw,
              latestData: raw.latest_data || raw.latestData || {},
              sparkData: sparklineSeries[raw.id]?.values || [],
              displayPrice: (raw.latest_data?.current_price || raw.latestData?.current_price) || null,
              priceTimestamp: raw.latest_data?.timestamp || raw.latestData?.timestamp || null
            };
          }
        }

        const stock = entry?.stock;
        const availableTargets = stock ? watchlists.filter((wl) => wl.id !== currentWatchlistId) : [];

        if (!stock) {
          return (
            <div className="action-menu__item">Nicht verfügbar</div>
          );
        }

        return (
          <>
            <button
              type="button"
              className="action-menu__item"
              role="menuitem"
              onClick={(event) => {
              }}
            >
              <span>Chart anzeigen</span>
            </button>
            <button
              type="button"
              className="action-menu__item"
              role="menuitem"
              onClick={(event) => {
                event.stopPropagation();
                setOpenMenuId(null);
                setAlertModalStock(stock);
              }}
            >
              <span>Alarm hinzufügen</span>
            </button>
            <button
              type="button"
              className="action-menu__item"
              role="menuitem"
              onClick={(event) => {
                event.stopPropagation();
                setOpenMenuId(null);
                setEditObservationsStock(stock);
              }}
            >
              <span>Beobachtungen bearbeiten</span>
            </button>
            <button
              type="button"
              className="action-menu__item"
              role="menuitem"
              onClick={(event) => {
                event.stopPropagation();
                setOpenMenuId(null);
                if (onUpdateMarketData) {
                  onUpdateMarketData(stock.id);
                }
              }}
            >
              <span>Marktdaten aktualisieren</span>
            </button>
            <button
              type="button"
              className="action-menu__item"
              role="menuitem"
              disabled={availableTargets.length === 0}
              aria-disabled={availableTargets.length === 0}
              onClick={(event) => {
                openTransferPanel(event, stock.id, availableTargets, 'move');
              }}
            >
              <span>Verschieben</span>
            </button>
            <button
              type="button"
              className="action-menu__item"
              role="menuitem"
              disabled={availableTargets.length === 0}
              aria-disabled={availableTargets.length === 0}
              onClick={(event) => {
                openTransferPanel(event, stock.id, availableTargets, 'copy');
              }}
            >
              <span>Kopieren</span>
            </button>
            {transferContext?.stockId === stock.id && availableTargets.length > 0 && (
              <div
                className="action-menu__move-panel"
                role="group"
                onClick={(event) => event.stopPropagation()}
              >
                <span className="action-menu__move-label">
                  {transferContext?.action === 'copy' ? 'In Watchlist kopieren' : 'Ziel-Watchlist'}
                </span>
                <select
                  value={transferContext.selectedWatchlistId ?? ''}
                  onChange={handleTransferSelectionChange}
                >
                  {availableTargets.map((watchlist) => (
                    <option key={watchlist.id} value={String(watchlist.id)}>
                      {watchlist.name || `Watchlist ${watchlist.id}`}
                    </option>
                  ))}
                </select>
                <div className="action-menu__move-actions">
                  <button
                    type="button"
                    className="action-menu__move-button action-menu__move-button--cancel"
                    onClick={handleCancelTransfer}
                  >
                    Abbrechen
                  </button>
                  <button
                    type="button"
                    className="action-menu__move-button action-menu__move-button--confirm"
                    onClick={(event) => handleConfirmTransfer(event, stock.id, availableTargets)}
                  >
                    {transferContext?.action === 'copy' ? 'Kopieren' : 'Verschieben'}
                  </button>
                </div>
              </div>
            )}
            {availableTargets.length === 0 && (
              <div className="action-menu__hint">Keine weiteren Watchlists verfügbar</div>
            )}
            <button
              type="button"
              className="action-menu__item action-menu__item--danger"
              role="menuitem"
              onClick={(event) => {
                event.stopPropagation();
                setOpenMenuId(null);
                // Activate selection mode and pre-select this stock
                setSelectionMode(true);
                setSelectedStockIds(new Set([stock.id]));
              }}
            >
              <span>Löschen</span>
            </button>
          </>
        );
      })()}
    </div>,
    document.body
  );
}

export default ActionMenu;

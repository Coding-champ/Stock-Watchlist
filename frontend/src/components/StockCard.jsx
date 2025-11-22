import React from 'react';
import { formatPrice } from '../utils/currencyUtils';
import { formatTime } from '../utils/formatting';
import { getInitials } from '../utils/tableHelpers';
import { getLocalizedQuoteType } from '../utils/quoteTypeLabel';
import { OBSERVATION_REASON_LABELS } from '../constants/stockTable';
import Sparkline from './Sparkline';
import PerformanceMetric from './PerformanceMetric';

function StockCard({
  stock,
  entry,
  extendedDataMap,
  sparkData,
  displayPrice,
  stockHint,
  priceTimestamp,
  currentPerformance,
  watchlistPerformance,
  weekPerformance,
  fiftyTwoWeekLow,
  fiftyTwoWeekHigh,
  fiftyTwoWeekPosition,
  watchlistDuration,
  chartId,
  observationReasons,
  observationNote,
  openMenuId,
  selectionMode,
  selectedStockIds,
  toggleStockSelection,
  setOpenMenuId,
  onStockClick,
  onUpdateMarketData,
  toggleMenu
}) {
  const trimmedObservationNote = observationNote && observationNote.trim();

  return (
    <div
      key={stock.id}
      className={`stock-card ${openMenuId === stock.id ? 'stock-card--menu-open' : ''} ${selectionMode ? 'stock-card--selectable' : ''} ${selectedStockIds.has(stock.id) ? 'stock-card--selected' : ''}`}
      onClick={() => {
        if (selectionMode) {
          toggleStockSelection(stock.id);
        } else {
          setOpenMenuId(null);
          onStockClick(stock);
        }
      }}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          if (selectionMode) {
            toggleStockSelection(stock.id);
          } else {
            setOpenMenuId(null);
            onStockClick(stock);
          }
        }
      }}
    >
      {/* Checkbox for multi-selection */}
      {selectionMode && (
        <div 
          className="stock-card__checkbox"
          onClick={(e) => {
            e.stopPropagation();
            toggleStockSelection(stock.id);
          }}
        >
          <input
            type="checkbox"
            checked={selectedStockIds.has(stock.id)}
            onChange={() => toggleStockSelection(stock.id)}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
      
      <div className="stock-card__identity">
        <div className="stock-avatar" aria-hidden="true">
          {getInitials(stock)}
        </div>
        <div className="stock-card__meta">
          <div className="stock-card__title">{stock.name}</div>
          <div className="stock-card__subtitle">
          {(() => {
            // Try several locations where quote_type may be provided
            const ext = extendedDataMap[stock.id];
            const extQuote = ext && ext.price_data && ext.price_data.quote_type;
            const latestQuote = (stock.latest_data && stock.latest_data.quote_type) || (stock.latestData && stock.latestData.quote_type);
            const top = stock.quote_type || stock.fast_info?.quote_type || stock.quoteType || stock.quoteType;
            const localized = getLocalizedQuoteType(extQuote || latestQuote || top);
            return `${localized} · Ticker ${stock.ticker_symbol}`;
          })()}
          </div>
          <div className="stock-card__tags">
            <span>{stock.ticker_symbol}</span>
            {stock.sector && <span>{stock.sector}</span>}
            {stock.country && <span>{stock.country}</span>}
          </div>
          {(observationReasons.length > 0 || trimmedObservationNote) && (
            <div className="stock-card__observations">
              {observationReasons.length > 0 && (
                <div className="stock-card__observation-reasons">
                  {observationReasons.map((reason, index) => (
                    <span key={`${reason}-${index}`} className="stock-card__observation-chip">
                      {OBSERVATION_REASON_LABELS[reason] || reason}
                    </span>
                  ))}
                </div>
              )}
              {trimmedObservationNote && (
                <div className="stock-card__observation-note">
                  {trimmedObservationNote}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="stock-card__price">
        <span className="stock-card__price-value">{formatPrice(displayPrice, stockHint)}</span>
        <span className="stock-card__price-meta">
          {priceTimestamp ? formatTime(priceTimestamp) : 'Keine aktuellen Marktdaten'}
          {onUpdateMarketData && (() => {
            const latest = stock.latest_data || stock.latestData || {};
            if (latest.__updating) {
              return <span className="icon-spinner" aria-hidden="true" style={{ marginLeft: 8 }}>⟳</span>;
            }
            if (latest.__failed) {
              return (
                <button
                  type="button"
                  className="icon-retry"
                  onClick={(e) => { e.stopPropagation(); onUpdateMarketData(stock.id); }}
                  title="Erneut versuchen"
                  style={{ marginLeft: 8 }}
                >
                  ↺
                </button>
              );
            }

            return null;
          })()}
        </span>
        {fiftyTwoWeekLow && fiftyTwoWeekHigh && fiftyTwoWeekPosition !== null && (
          <div className="stock-card__price-range-container">
            <div className="stock-card__price-range-bar">
              <div className="stock-card__price-range-track">
                <div 
                  className="stock-card__price-range-marker"
                  style={{ left: `${Math.max(0, Math.min(100, fiftyTwoWeekPosition))}%` }}
                >
                  <div className="stock-card__price-range-marker-dot"></div>
                </div>
              </div>
            </div>
            <div className="stock-card__price-range-labels">
              <span className="stock-card__price-range-label">{fiftyTwoWeekLow}</span>
              <span className="stock-card__price-range-label">{fiftyTwoWeekHigh}</span>
            </div>
          </div>
        )}
      </div>

      <div className="stock-card__chart" onClick={(event) => event.stopPropagation()}>
        <div className="stock-card__chart-wrapper">
          <Sparkline data={sparkData} id={chartId} />
          <span className="stock-card__chart-caption">seit Aufnahme</span>
        </div>
      </div>

      <div className="stock-card__performance" onClick={(event) => event.stopPropagation()}>
        <PerformanceMetric
          label="aktuell"
          data={currentPerformance}
          stock={stock}
        />
        <PerformanceMetric
          label="52 Wochen"
          data={weekPerformance}
          stock={stock}
        />
        <PerformanceMetric
          label="Watchlist"
          data={watchlistPerformance}
          hint={watchlistDuration}
          stock={stock}
        />
      </div>

      <div className="stock-card__actions" onClick={(e) => e.stopPropagation()}>
        {!selectionMode && (
          <div
            className="action-menu"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="action-menu__trigger"
              data-stock-id={stock.id}
              aria-haspopup="menu"
              aria-expanded={openMenuId === stock.id}
              aria-label="Weitere Aktionen"
              title="Weitere Aktionen"
              onClick={(event) => toggleMenu(event, stock.id)}
            >
              ⋮
            </button>
            {/* menu is rendered via portal to avoid being clipped by overflow: hidden ancestors */}
          </div>
        )}
      </div>
    </div>
  );
}

export default StockCard;

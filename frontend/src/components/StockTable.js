import React, { useEffect, useRef, useState } from 'react';
import AlertModal from './AlertModal';

const API_BASE = (process.env.REACT_APP_API_BASE || '').replace(/\/$/, '');
const SPARKLINE_POINT_LIMIT = 90;

const PERFORMANCE_SORT_KEYS = {
  CURRENT: 'current_performance',
  WATCHLIST: 'watchlist_performance',
  WEEK: 'week_performance'
};

const OBSERVATION_REASON_LABELS = {
  chart_technical: 'Charttechnische Indikatoren',
  fundamentals: 'Fundamentaldaten',
  industry: 'Branchendaten',
  economics: 'Wirtschaftsdaten'
};

function StockTable({
  stocks,
  watchlists,
  currentWatchlistId,
  onStockClick,
  onDeleteStock,
  onMoveStock,
  onCopyStock,
  onUpdateMarketData,
  onShowChart,
  performanceFilter = 'all',
  onShowToast
}) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [openMenuId, setOpenMenuId] = useState(null);
  const [transferContext, setTransferContext] = useState(null);
  const [sparklineSeries, setSparklineSeries] = useState({});
  const [extendedDataMap, setExtendedDataMap] = useState({});
  const fetchedExtendedIdsRef = useRef(new Set());
  const [alertModalStock, setAlertModalStock] = useState(null);

  const notify = (message, appearance = 'info') => {
    if (typeof onShowToast === 'function') {
      onShowToast(message, appearance);
    } else if (message) {
      window.alert(message);
    }
  };

  const getPerformanceScore = (stock, key) => {
    const latestData = stock.latest_data || stock.latestData || {};
    const sparkData = sparklineSeries[stock.id]?.values || [];
    const displayPrice = typeof latestData.current_price === 'number'
      ? latestData.current_price
      : (sparkData.length ? sparkData[sparkData.length - 1] : null);
    if (typeof displayPrice !== 'number') {
      return null;
    }

    const previousPrice = sparkData.length > 1 ? sparkData[sparkData.length - 2] : null;
    const earliestPrice = sparkData.length > 0 ? sparkData[0] : null;
    const priceData = extendedDataMap[stock.id]?.price_data;

    switch (key) {
      case PERFORMANCE_SORT_KEYS.CURRENT: {
        const perf = calculatePerformance(previousPrice, displayPrice);
        return perf ? perf.percent : null;
      }
      case PERFORMANCE_SORT_KEYS.WATCHLIST: {
        const perf = calculatePerformance(earliestPrice, displayPrice);
        return perf ? perf.percent : null;
      }
      case PERFORMANCE_SORT_KEYS.WEEK: {
        if (!priceData || typeof priceData.fifty_two_week_low !== 'number') {
          return null;
        }
        const perf = calculatePerformance(priceData.fifty_two_week_low, displayPrice);
        return perf ? perf.percent : null;
      }
      default:
        return null;
    }
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortedStocks = () => {
    if (!sortConfig.key) return stocks;

    if (Object.values(PERFORMANCE_SORT_KEYS).includes(sortConfig.key)) {
      const sorted = [...stocks].sort((a, b) => {
        const aScoreRaw = getPerformanceScore(a, sortConfig.key);
        const bScoreRaw = getPerformanceScore(b, sortConfig.key);

        const aScore = normalizeSortScore(aScoreRaw, sortConfig.direction);
        const bScore = normalizeSortScore(bScoreRaw, sortConfig.direction);

        if (aScore < bScore) return -1;
        if (aScore > bScore) return 1;
        return 0;
      });

      return sortConfig.direction === 'asc' ? sorted : sorted.reverse();
    }

    const sorted = [...stocks].sort((a, b) => {
      let aValue, bValue;

      if (sortConfig.key === 'current_price' || sortConfig.key === 'pe_ratio' || 
          sortConfig.key === 'rsi' || sortConfig.key === 'volatility') {
        aValue = (a.latest_data?.[sortConfig.key] || a.latestData?.[sortConfig.key]) || 0;
        bValue = (b.latest_data?.[sortConfig.key] || b.latestData?.[sortConfig.key]) || 0;
      } else {
        aValue = a[sortConfig.key] || '';
        bValue = b[sortConfig.key] || '';
      }

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  };

  const openTransferPanel = (event, stockId, availableWatchlists, action) => {
    event.stopPropagation();

    if (!Array.isArray(availableWatchlists) || availableWatchlists.length === 0) {
      notify('Keine anderen Watchlists verfügbar', 'info');
      setTransferContext(null);
      return;
    }

    setTransferContext((prev) => {
      if (prev && prev.stockId === stockId && prev.action === action) {
        return null;
      }

      const defaultTarget = availableWatchlists[0];
      return {
        stockId,
        action,
        selectedWatchlistId: defaultTarget ? String(defaultTarget.id) : ''
      };
    });
  };

  const handleTransferSelectionChange = (event) => {
    event.stopPropagation();
    const { value } = event.target;
    setTransferContext((prev) => (prev ? { ...prev, selectedWatchlistId: value } : prev));
  };

  const handleConfirmTransfer = (event, stockId, availableWatchlists) => {
    event.stopPropagation();

    if (!transferContext || transferContext.stockId !== stockId) {
      return;
    }

    const targetWatchlist = availableWatchlists.find(
      (wl) => String(wl.id) === transferContext.selectedWatchlistId
    );

    if (!targetWatchlist) {
      notify('Bitte eine Ziel-Watchlist auswählen.', 'warning');
      return;
    }

    if (transferContext.action === 'copy') {
      if (typeof onCopyStock === 'function') {
        onCopyStock(stockId, targetWatchlist.id);
      } else {
        notify('Kopieren wird aktuell nicht unterstützt.', 'warning');
      }
    } else {
      onMoveStock(stockId, targetWatchlist.id);
    }

    setTransferContext(null);
    setOpenMenuId(null);
  };

  const handleCancelTransfer = (event) => {
    event.stopPropagation();
    setTransferContext(null);
  };

  useEffect(() => {
    if (openMenuId === null) {
      if (transferContext) {
        setTransferContext(null);
      }
      return undefined;
    }

    if (transferContext && transferContext.stockId !== openMenuId) {
      setTransferContext(null);
    }

    const handleClickOutside = () => {
      setOpenMenuId(null);
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [openMenuId, transferContext]);

  useEffect(() => {
    if (!transferContext) {
      return;
    }

    const availableWatchlists = watchlists.filter((wl) => wl.id !== currentWatchlistId);

    if (availableWatchlists.length === 0) {
      setTransferContext(null);
      return;
    }

    const isValidSelection = availableWatchlists.some(
      (wl) => String(wl.id) === transferContext.selectedWatchlistId
    );

    if (!isValidSelection) {
      const fallback = availableWatchlists[0];
      const fallbackId = fallback ? String(fallback.id) : '';
      if (fallbackId && fallbackId !== transferContext.selectedWatchlistId) {
        setTransferContext((prev) => (prev ? { ...prev, selectedWatchlistId: fallbackId } : prev));
      }
    }
  }, [watchlists, currentWatchlistId, transferContext]);

  useEffect(() => {
    if (!stocks || stocks.length === 0) {
      setSparklineSeries({});
      return;
    }

    let cancelled = false;

    const loadSparklines = async () => {
      const responses = await Promise.all(
        stocks.map(async (stock) => {
          try {
            const url = `${API_BASE}/stock-data/${stock.id}?limit=${SPARKLINE_POINT_LIMIT}`;
            const response = await fetch(url);
            if (!response.ok) {
              throw new Error(`Request failed: ${response.status}`);
            }
            const data = await response.json();
            const filtered = (data || []).filter((entry) => typeof entry.current_price === 'number');
            const ordered = filtered.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            return {
              id: stock.id,
              values: ordered.map((entry) => entry.current_price),
              timestamps: ordered.map((entry) => entry.timestamp)
            };
          } catch (error) {
            console.error('Fehler beim Laden der Kursverlaufdaten:', error);
            return { id: stock.id, values: [], timestamps: [] };
          }
        })
      );

      if (cancelled) {
        return;
      }

      const seriesMap = responses.reduce((acc, item) => {
        acc[item.id] = { values: item.values, timestamps: item.timestamps };
        return acc;
      }, {});

      setSparklineSeries(seriesMap);
    };

    loadSparklines();

    return () => {
      cancelled = true;
    };
  }, [stocks]);

  useEffect(() => {
    if (!stocks || stocks.length === 0) {
      setExtendedDataMap({});
      fetchedExtendedIdsRef.current.clear();
      return;
    }

    const pendingStocks = stocks.filter((stock) => !fetchedExtendedIdsRef.current.has(stock.id));
    if (pendingStocks.length === 0) {
      return;
    }

    let cancelled = false;

    const loadExtendedData = async () => {
      const responses = await Promise.all(
        pendingStocks.map(async (stock) => {
          try {
            const response = await fetch(`${API_BASE}/stocks/${stock.id}/detailed`);
            if (!response.ok) {
              throw new Error(`Request failed: ${response.status}`);
            }
            const data = await response.json();
            return { id: stock.id, extended: data.extended_data || null };
          } catch (error) {
            console.error('Fehler beim Laden erweiterter Daten:', error);
            return { id: stock.id, extended: null };
          }
        })
      );

      if (cancelled) {
        return;
      }

      const updates = {};
      responses.forEach(({ id, extended }) => {
        fetchedExtendedIdsRef.current.add(id);
        updates[id] = extended;
      });

      setExtendedDataMap((prev) => ({ ...prev, ...updates }));
    };

    loadExtendedData();

    return () => {
      cancelled = true;
    };
  }, [stocks]);

  const toggleMenu = (event, stockId) => {
    event.stopPropagation();
    setTransferContext(null);
    setOpenMenuId((prev) => (prev === stockId ? null : stockId));
  };

  const sortedStocks = getSortedStocks();

  const enrichedStocks = sortedStocks.map((stock) => {
    const latestData = stock.latest_data || stock.latestData || {};
    const priceTimestamp = latestData.timestamp || (sparklineSeries[stock.id]?.timestamps?.slice(-1)[0] || null);
    const sparkData = sparklineSeries[stock.id]?.values || [];
    const displayPrice = typeof latestData.current_price === 'number'
      ? latestData.current_price
      : (sparkData.length ? sparkData[sparkData.length - 1] : null);
    const previousPrice = sparkData.length > 1 ? sparkData[sparkData.length - 2] : null;
    const earliestPrice = sparkData.length > 0 ? sparkData[0] : null;
    const currentPerformance = calculatePerformance(previousPrice, displayPrice);
    const watchlistPerformance = calculatePerformance(earliestPrice, displayPrice);
    const priceData = extendedDataMap[stock.id]?.price_data;
    const weekPerformance = priceData && typeof priceData.fifty_two_week_low === 'number'
      ? calculatePerformance(priceData.fifty_two_week_low, displayPrice)
      : null;
    const fiftyTwoWeekRange = priceData && 
      typeof priceData.fifty_two_week_low === 'number' && 
      typeof priceData.fifty_two_week_high === 'number'
      ? `${formatCurrency(priceData.fifty_two_week_low)} - ${formatCurrency(priceData.fifty_two_week_high)}`
      : null;
    
    const fiftyTwoWeekLow = priceData && typeof priceData.fifty_two_week_low === 'number'
      ? formatCurrency(priceData.fifty_two_week_low)
      : null;
    
    const fiftyTwoWeekHigh = priceData && typeof priceData.fifty_two_week_high === 'number'
      ? formatCurrency(priceData.fifty_two_week_high)
      : null;
    
    // Calculate position for range bar (0-100%)
    const fiftyTwoWeekPosition = priceData && 
      typeof priceData.fifty_two_week_low === 'number' && 
      typeof priceData.fifty_two_week_high === 'number' &&
      priceData.fifty_two_week_high > priceData.fifty_two_week_low
      ? ((displayPrice - priceData.fifty_two_week_low) / (priceData.fifty_two_week_high - priceData.fifty_two_week_low)) * 100
      : null;
    
    const watchlistDuration = formatWatchlistDuration(stock.created_at);
    const chartId = `sparkline-${stock.id}`;
    const observationReasons = Array.isArray(stock.observation_reasons) ? stock.observation_reasons : [];
    const observationNote = typeof stock.observation_notes === 'string' ? stock.observation_notes : null;

    return {
      stock,
      latestData,
      sparkData,
      displayPrice,
      priceTimestamp,
      currentPerformance,
      watchlistPerformance,
      weekPerformance,
      fiftyTwoWeekRange,
      fiftyTwoWeekLow,
      fiftyTwoWeekHigh,
      fiftyTwoWeekPosition,
      watchlistDuration,
      chartId,
      observationReasons,
      observationNote
    };
  });

  const filteredStocks = enrichedStocks.filter((entry) => matchesPerformanceFilter(performanceFilter, entry));

  const applySortPreset = (key, direction = 'desc') => {
    setSortConfig({ key, direction });
  };

  const isSortPresetActive = (key, direction = 'desc') => (
    sortConfig.key === key && sortConfig.direction === direction
  );

  if (stocks.length === 0) {
    return (
      <div className="empty-state">
        Keine Aktien in dieser Watchlist. Fügen Sie eine Aktie hinzu.
      </div>
    );
  }

  return (
    <div className="stock-table">
      <div className="stock-table__toolbar">
        <span className="stock-table__toolbar-label">Sortierung</span>
        <div className="stock-table__toolbar-group">
          <button
            type="button"
            className={`sort-chip ${isSortPresetActive(PERFORMANCE_SORT_KEYS.CURRENT) ? 'sort-chip--active' : ''}`}
            onClick={() => applySortPreset(PERFORMANCE_SORT_KEYS.CURRENT, 'desc')}
          >
            Aktuelle Gewinner
          </button>
          <button
            type="button"
            className={`sort-chip ${isSortPresetActive(PERFORMANCE_SORT_KEYS.WATCHLIST) ? 'sort-chip--active' : ''}`}
            onClick={() => applySortPreset(PERFORMANCE_SORT_KEYS.WATCHLIST, 'desc')}
          >
            Watchlist-Gewinner
          </button>
          <button
            type="button"
            className={`sort-chip ${isSortPresetActive(PERFORMANCE_SORT_KEYS.WEEK) ? 'sort-chip--active' : ''}`}
            onClick={() => applySortPreset(PERFORMANCE_SORT_KEYS.WEEK, 'desc')}
          >
            52-Wochen-Gewinner
          </button>
          <button
            type="button"
            className={`sort-chip ${sortConfig.key === null ? 'sort-chip--active' : (!Object.values(PERFORMANCE_SORT_KEYS).includes(sortConfig.key) && sortConfig.key ? 'sort-chip--muted' : '')}`}
            onClick={() => setSortConfig({ key: null, direction: 'asc' })}
          >
            Standard
          </button>
        </div>
      </div>

      <div className="stock-table__header">
        <div>
          <button
            type="button"
            className="stock-table__header-button"
            onClick={() => handleSort('name')}
          >
            Name {renderSortIndicator('name', sortConfig)}
          </button>
        </div>
        <div>
          <button
            type="button"
            className="stock-table__header-button"
            onClick={() => handleSort('current_price')}
          >
            Kurs aktuell {renderSortIndicator('current_price', sortConfig)}
          </button>
        </div>
        <div>Chart</div>
        <div>Performance</div>
        <div></div>
      </div>

      <div className="stock-table__body">
        {filteredStocks.map((entry) => {
          const {
            stock,
            sparkData,
            displayPrice,
            priceTimestamp,
            currentPerformance,
            watchlistPerformance,
            weekPerformance,
            fiftyTwoWeekRange,
            fiftyTwoWeekLow,
            fiftyTwoWeekHigh,
            fiftyTwoWeekPosition,
            watchlistDuration,
            chartId,
            observationReasons,
            observationNote
          } = entry;
          const trimmedObservationNote = observationNote && observationNote.trim();
          const availableTargets = watchlists.filter((wl) => wl.id !== currentWatchlistId);
          return (
            <div
              key={stock.id}
              className="stock-card"
              onClick={() => {
                setOpenMenuId(null);
                onStockClick(stock);
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  setOpenMenuId(null);
                  onStockClick(stock);
                }
              }}
            >
              <div className="stock-card__identity">
                <div className="stock-avatar" aria-hidden="true">
                  {getInitials(stock)}
                </div>
                <div className="stock-card__meta">
                  <div className="stock-card__title">{stock.name}</div>
                  <div className="stock-card__subtitle">
                    Aktie · Ticker {stock.ticker_symbol} · {stock.isin ? `ISIN ${stock.isin}` : 'Keine ISIN'}
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
                <span className="stock-card__price-value">{formatCurrency(displayPrice)}</span>
                <span className="stock-card__price-meta">
                  {priceTimestamp ? formatTime(priceTimestamp) : 'Keine aktuellen Marktdaten'}
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
                />
                <PerformanceMetric
                  label="52 Wochen"
                  data={weekPerformance}
                />
                <PerformanceMetric
                  label="in Watchlist"
                  data={watchlistPerformance}
                  hint={watchlistDuration}
                />
              </div>

              <div className="stock-card__actions" onClick={(e) => e.stopPropagation()}>
                <div
                  className="action-menu"
                  onClick={(event) => event.stopPropagation()}
                >
                  <button
                    type="button"
                    className="action-menu__trigger"
                    aria-haspopup="menu"
                    aria-expanded={openMenuId === stock.id}
                    aria-label="Weitere Aktionen"
                    title="Weitere Aktionen"
                    onClick={(event) => toggleMenu(event, stock.id)}
                  >
                    ⋮
                  </button>
                  {openMenuId === stock.id && (
                    <div className="action-menu__list" role="menu">
                      <button
                        type="button"
                        className="action-menu__item"
                        role="menuitem"
                        onClick={(event) => {
                          event.stopPropagation();
                          setOpenMenuId(null);
                          if (onShowChart) {
                            onShowChart(stock);
                          }
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
                        <span>🔔 Alarm hinzufügen</span>
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
                          onDeleteStock(stock.id);
                        }}
                      >
                        <span>Löschen</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Alert Modal */}
      {alertModalStock && (
        <AlertModal
          stock={alertModalStock}
          onClose={() => setAlertModalStock(null)}
          onAlertSaved={() => {
            notify(`Alarm erstellt · Für ${alertModalStock.ticker_symbol}`, 'success');
          }}
        />
      )}
    </div>
  );
}

export default StockTable;

function renderSortIndicator(key, sortConfig) {
  if (sortConfig.key !== key) {
    return null;
  }

  return (
    <span className="stock-table__header-sort" aria-hidden="true">
      {sortConfig.direction === 'asc' ? '▲' : '▼'}
    </span>
  );
}

function getInitials(stock) {
  const source = stock.name || stock.ticker_symbol || '';
  const parts = source.trim().split(/\s+/);
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }

  return (parts[0][0] + parts[1][0]).toUpperCase();
}

function normalizeSortScore(score, direction) {
  if (typeof score !== 'number' || Number.isNaN(score)) {
    return direction === 'asc' ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY;
  }

  return score;
}

function matchesPerformanceFilter(filter, entry) {
  if (!filter || filter === 'all') {
    return true;
  }

  const { currentPerformance, watchlistPerformance, weekPerformance } = entry;

  switch (filter) {
    case 'current-positive':
      return currentPerformance?.direction === 'positive';
    case 'current-negative':
      return currentPerformance?.direction === 'negative';
    case 'watchlist-positive':
      return watchlistPerformance?.direction === 'positive';
    case 'watchlist-negative':
      return watchlistPerformance?.direction === 'negative';
    case 'week-positive':
      return weekPerformance?.direction === 'positive';
    case 'week-negative':
      return weekPerformance?.direction === 'negative';
    default:
      return true;
  }
}

function formatCurrency(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '-';
  }

  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function formatTime(timestamp) {
  const date = timestamp ? new Date(timestamp) : null;
  if (!date || Number.isNaN(date.getTime())) {
    return '-';
  }

  return `${date.toLocaleDateString('de-DE')} · ${date.toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit'
  })}`;
}

function formatSignedCurrency(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '-';
  }

  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  const formatted = new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(Math.abs(value));

  return `${sign}${formatted} USD`;
}

function formatPercent(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '-';
  }

  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  const formatted = new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(Math.abs(value));

  return `${sign}${formatted} %`;
}

function calculatePerformance(fromValue, toValue) {
  if (typeof fromValue !== 'number' || typeof toValue !== 'number') {
    return null;
  }

  if (fromValue === 0) {
    return null;
  }

  const amount = toValue - fromValue;
  const percent = (amount / fromValue) * 100;
  let direction = 'neutral';
  if (amount > 0) {
    direction = 'positive';
  } else if (amount < 0) {
    direction = 'negative';
  }

  return {
    amount,
    percent,
    direction
  };
}

function formatWatchlistDuration(createdAt) {
  if (!createdAt) {
    return null;
  }

  const created = new Date(createdAt);
  if (Number.isNaN(created.getTime())) {
    return null;
  }

  const diffMs = Date.now() - created.getTime();
  const diffDays = Math.max(0, Math.floor(diffMs / (1000 * 60 * 60 * 24)));

  if (diffDays === 0) {
    return 'Heute hinzugefügt';
  }

  return `${diffDays} ${diffDays === 1 ? 'Tag' : 'Tage'}`;
}

function Sparkline({ data, id, width = 140, height = 48, color = '#7c3aed' }) {
  if (!data || data.length < 2) {
    return <div className="sparkline sparkline--empty">Keine Daten</div>;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return { x, y };
  });

  const pathD = points.reduce((acc, point, index) => (
    index === 0 ? `M ${point.x},${point.y}` : `${acc} L ${point.x},${point.y}`
  ), '');

  const areaD = `${pathD} L ${width},${height} L 0,${height} Z`;
  const gradientId = `${id}-gradient`;
  const lastPoint = points[points.length - 1];

  return (
    <div className="sparkline" aria-hidden="true">
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.35" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaD} fill={`url(#${gradientId})`} className="sparkline__area" />
        <path d={pathD} stroke={color} strokeWidth="2" className="sparkline__line" />
        <circle
          cx={lastPoint.x}
          cy={lastPoint.y}
          r={3.5}
          fill={color}
          className="sparkline__dot"
        />
      </svg>
    </div>
  );
}

function PerformanceMetric({ label, data, hint }) {
  const state = data ? data.direction : 'neutral';
  const appearance = state === 'positive' ? 'positive' : state === 'negative' ? 'negative' : 'neutral';

  return (
    <div className={`performance-metric performance-metric--${appearance}`}>
      <span className="performance-metric__label">{label}</span>
      <span className="performance-metric__value">{data ? formatPercent(data.percent) : '-'}</span>
      <span className="performance-metric__delta">{data ? formatSignedCurrency(data.amount) : '-'}</span>
      {hint && <span className="performance-metric__hint">{hint}</span>}
    </div>
  );
}

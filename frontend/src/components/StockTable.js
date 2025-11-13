import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import AlertModal from './AlertModal';
import EditObservationsModal from './EditObservationsModal';
import { getLocalizedQuoteType } from '../utils/quoteTypeLabel';

import API_BASE from '../config';
import { useQueryClient } from '@tanstack/react-query';
import { formatPrice } from '../utils/currencyUtils';
const SPARKLINE_POINT_LIMIT = 90;

const PERFORMANCE_SORT_KEYS = {
  CURRENT: 'current_performance',
  WATCHLIST: 'watchlist_performance',
  WEEK: 'week_performance'
};

const OBSERVATION_REASON_LABELS = {
  chart_technical: 'Charttechnische Indikatoren',
  earnings: 'Earnings Berichte',
  fundamentals: 'Fundamentaldaten',
  company: 'Unternehmensdaten',
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
  onStocksReload,
  onShowChart,
  performanceFilter = 'all',
  onShowToast
}) {
  // Expect parent to pass updating/failed sets via props if desired in future.
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [openMenuId, setOpenMenuId] = useState(null);
  const [menuCoords, setMenuCoords] = useState(null);
  const [transferContext, setTransferContext] = useState(null);
  const [sparklineSeries, setSparklineSeries] = useState({});
  const [extendedDataMap, setExtendedDataMap] = useState({});
  const fetchedExtendedIdsRef = useRef(new Set());
  const fetchedSparklineIdsRef = useRef(new Set());
  const [alertModalStock, setAlertModalStock] = useState(null);
  const [editObservationsStock, setEditObservationsStock] = useState(null);
  
  // Multi-selection state
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedStockIds, setSelectedStockIds] = useState(new Set());
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferAction, setTransferAction] = useState(null); // 'move' or 'copy'
  const [selectedTargetWatchlist, setSelectedTargetWatchlist] = useState(null);
  const [isTransferring, setIsTransferring] = useState(false);

  const queryClient = useQueryClient();

  const notify = (message, appearance = 'info') => {
    if (typeof onShowToast === 'function') {
      onShowToast(message, appearance);
    } else if (message) {
      window.alert(message);
    }
  };

  // Multi-selection handlers
  const toggleSelectionMode = () => {
    setSelectionMode(!selectionMode);
    setSelectedStockIds(new Set());
  };

  const toggleStockSelection = (stockId) => {
    setSelectedStockIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(stockId)) {
        newSet.delete(stockId);
      } else {
        newSet.add(stockId);
      }
      return newSet;
    });
  };

  const selectAllStocks = () => {
    const allIds = new Set(stocks.map(s => s.id));
    setSelectedStockIds(allIds);
  };

  const clearSelection = () => {
    setSelectedStockIds(new Set());
  };

  const confirmDeleteSelectedStocks = () => {
    if (selectedStockIds.size === 0) return;
    setShowDeleteConfirmation(true);
  };

  const deleteSelectedStocks = async () => {
    if (selectedStockIds.size === 0) return;

    setIsDeleting(true);
    const count = selectedStockIds.size;

    try {
      // Delete stocks sequentially - skip individual toasts
      for (const stockId of Array.from(selectedStockIds)) {
        await onDeleteStock(stockId, true); // true = skipToast
      }

      // Clear selection and close modal first
      setSelectedStockIds(new Set());
      setSelectionMode(false);
      setShowDeleteConfirmation(false);
      
      // Reload the stocks list
      if (onStocksReload) {
        await onStocksReload();
      }
      
      // Show single success message
      notify(count === 1 ? 'Aktie erfolgreich entfernt' : `${count} Aktien erfolgreich entfernt`, 'success');
    } catch (error) {
      console.error('Delete error:', error);
      notify('Fehler beim Löschen der Aktien', 'error');
      setShowDeleteConfirmation(false);
    } finally {
      setIsDeleting(false);
    }
  };

  // Transfer (move/copy) handlers
  const openTransferModal = (action) => {
    if (selectedStockIds.size === 0) return;
    setTransferAction(action);
    setShowTransferModal(true);
    // Pre-select first available watchlist
    const availableWatchlists = watchlists.filter(wl => wl.id !== currentWatchlistId);
    if (availableWatchlists.length > 0) {
      setSelectedTargetWatchlist(availableWatchlists[0].id);
    }
  };

  const confirmTransfer = async () => {
    if (selectedStockIds.size === 0 || !selectedTargetWatchlist) return;

    setIsTransferring(true);
    const count = selectedStockIds.size;
    const actionLabel = transferAction === 'move' ? 'verschoben' : 'kopiert';

    try {
      // Transfer stocks sequentially
      for (const stockId of Array.from(selectedStockIds)) {
        if (transferAction === 'move') {
          await onMoveStock(stockId, selectedTargetWatchlist);
        } else {
          await onCopyStock(stockId, selectedTargetWatchlist);
        }
      }

      // Clear selection and close modal
      setSelectedStockIds(new Set());
      setSelectionMode(false);
      setShowTransferModal(false);
      setTransferAction(null);
      
      // Reload the stocks list
      if (onStocksReload) {
        await onStocksReload();
      }
      
      // Show success message
      notify(
        count === 1 
          ? `Aktie erfolgreich ${actionLabel}` 
          : `${count} Aktien erfolgreich ${actionLabel}`, 
        'success'
      );
    } catch (error) {
      console.error('Transfer error:', error);
      notify(`Fehler beim ${transferAction === 'move' ? 'Verschieben' : 'Kopieren'} der Aktien`, 'error');
      setShowTransferModal(false);
    } finally {
      setIsTransferring(false);
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

  // Close menu on Escape
  useEffect(() => {
    if (openMenuId === null) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpenMenuId(null);
        setMenuCoords(null);
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [openMenuId]);

  // (debug DOM append removed)

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
      fetchedSparklineIdsRef.current.clear();
      return;
    }

    // Only fetch sparklines for stocks we haven't fetched yet
    const pendingStocks = stocks.filter((stock) => !fetchedSparklineIdsRef.current.has(stock.id));
    if (pendingStocks.length === 0) {
      return;
    }

    let cancelled = false;

    const loadSparklines = async () => {
      const responses = await Promise.all(
        pendingStocks.map(async (stock) => {
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

      const updates = {};
      responses.forEach(({ id, values, timestamps }) => {
        fetchedSparklineIdsRef.current.add(id);
        updates[id] = { values, timestamps };
      });

      setSparklineSeries((prev) => ({ ...prev, ...updates }));
    };

    loadSparklines();

    return () => {
      cancelled = true;
    };
  }, [stocks, queryClient]);

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
            // Use queryClient.fetchQuery so identical requests are deduped and cached.
            const url = `${API_BASE}/stocks/${stock.id}/detailed`;
            const data = await queryClient.fetchQuery(['api', url], async () => {
              const response = await fetch(url);
              if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
              }
              return await response.json();
            }, { staleTime: 300000 });

            return { id: stock.id, extended: data?.extended_data || null };
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
  }, [stocks, queryClient]);

  const toggleMenu = (event, stockId) => {
    event.stopPropagation();
    setTransferContext(null);
    setOpenMenuId((prev) => {
      const willOpen = prev !== stockId;
      if (willOpen) {
        try {
          const MENU_WIDTH = 240;
          const MENU_ESTIMATED_HEIGHT = 320; // used only for flip heuristic
          const winW = typeof window !== 'undefined' ? window.innerWidth : 1024;
          const winH = typeof window !== 'undefined' ? window.innerHeight : 768;

          // Resolve the trigger element reliably
          let triggerEl = null;
          try {
            triggerEl = event.currentTarget || (event.target && event.target.closest && event.target.closest('.action-menu__trigger')) || event.target || null;
          } catch (err) {
            triggerEl = event.currentTarget || event.target || null;
          }

          if (!triggerEl || !(triggerEl instanceof Element) || !triggerEl.classList || !triggerEl.classList.contains('action-menu__trigger')) {
            const byAttr = document.querySelector(`.action-menu__trigger[data-stock-id="${stockId}"]`);
            if (byAttr) triggerEl = byAttr;
          }

          const rect = triggerEl && triggerEl.getBoundingClientRect ? triggerEl.getBoundingClientRect() : null;

          // We render the portal with position: fixed, so coordinates must be viewport-based (client coordinates)

          if (rect) {
            const desiredLeft = rect.left + (rect.width / 2) - (MENU_WIDTH / 2);
            const clampedLeft = Math.round(Math.max(8, Math.min(desiredLeft, winW - MENU_WIDTH - 8)));

            // Compute page-relative coordinates so the portal moves with page scroll
            const scrollY = typeof window !== 'undefined' ? window.scrollY || window.pageYOffset || 0 : 0;
            const scrollX = typeof window !== 'undefined' ? window.scrollX || window.pageXOffset || 0 : 0;
            const pageLeft = clampedLeft + scrollX;

            // default pageTop below trigger (shift a few pixels down for better spacing)
            let pageTop = Math.round(rect.bottom + 18 + scrollY);
            // Flip above if there isn't enough space in the viewport below
            if (rect.bottom + MENU_ESTIMATED_HEIGHT + 16 > winH) {
              pageTop = Math.round(Math.max(8, rect.top - MENU_ESTIMATED_HEIGHT - 8 + scrollY));
            }

            setMenuCoords({ top: pageTop, left: pageLeft, width: MENU_WIDTH, absolute: true });
          } else {
            // Fallback to click coordinates (client coords are already viewport-relative)
            const clientX = event.clientX || (event.nativeEvent && event.nativeEvent.clientX) || Math.round(winW / 2);
            const clientY = event.clientY || (event.nativeEvent && event.nativeEvent.clientY) || Math.round(winH / 2);
            const desiredLeft = clientX - (MENU_WIDTH / 2);
            const clampedLeft = Math.round(Math.max(8, Math.min(desiredLeft, winW - MENU_WIDTH - 8)));
            const scrollY = typeof window !== 'undefined' ? window.scrollY || window.pageYOffset || 0 : 0;
            const scrollX = typeof window !== 'undefined' ? window.scrollX || window.pageXOffset || 0 : 0;
            const pageLeft = clampedLeft + scrollX;
            let pageTop = Math.round((clientY + 18) + scrollY);
            if (clientY + MENU_ESTIMATED_HEIGHT + 16 > winH) {
              pageTop = Math.round(Math.max(8, clientY - MENU_ESTIMATED_HEIGHT - 8 + scrollY));
            }
            setMenuCoords({ top: pageTop, left: pageLeft, width: MENU_WIDTH, absolute: true });
          }

          // keep the page-based coordinates set above; do not overwrite with viewport defaults
        } catch (err) {
          setMenuCoords(null);
        }
      } else {
        setMenuCoords(null);
      }

      return willOpen ? stockId : null;
    });
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
  const stockHint = { ...stock, currency: priceData?.currency || stock.currency || stock.exchange };
    const weekPerformance = priceData && typeof priceData.fifty_two_week_low === 'number'
      ? calculatePerformance(priceData.fifty_two_week_low, displayPrice)
      : null;
    
    
    const fiftyTwoWeekLow = priceData && typeof priceData.fifty_two_week_low === 'number'
      ? formatPrice(priceData.fifty_two_week_low, stockHint)
      : null;
    
    const fiftyTwoWeekHigh = priceData && typeof priceData.fifty_two_week_high === 'number'
      ? formatPrice(priceData.fifty_two_week_high, stockHint)
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

      {/* Multi-selection toolbar */}
      {selectionMode && (
        <div className="stock-selection-toolbar">
          <div className="stock-selection-toolbar__info">
            <span className="stock-selection-toolbar__count">
              {selectedStockIds.size} von {stocks.length} ausgewählt
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
      )}

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
            fiftyTwoWeekLow,
            fiftyTwoWeekHigh,
            fiftyTwoWeekPosition,
            watchlistDuration,
            chartId,
            observationReasons,
            observationNote
          } = entry;
          const { stockHint } = entry;
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
        })}
      </div>

      {/* Portal action menu (renders to body to avoid clipping) */}
      {typeof document !== 'undefined' && openMenuId !== null && createPortal(
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
      )}

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

      {/* Edit Observations Modal */}
      {editObservationsStock && (
        <EditObservationsModal
          stock={editObservationsStock}
          watchlistId={currentWatchlistId}
          onClose={() => setEditObservationsStock(null)}
          onSaved={() => {
            // Reload stocks list after successful save
            if (onStocksReload) {
              onStocksReload();
            }
          }}
          onShowToast={notify}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirmation && (
        <div className="modal modal--overlay" onClick={() => setShowDeleteConfirmation(false)}>
          <div className="modal-content modal-content--small" onClick={(e) => e.stopPropagation()}>
            <span className="close" onClick={() => setShowDeleteConfirmation(false)}>&times;</span>
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
                onClick={() => setShowDeleteConfirmation(false)}
                disabled={isDeleting}
              >
                Abbrechen
              </button>
              <button
                type="button"
                className="btn btn--danger"
                onClick={deleteSelectedStocks}
                disabled={isDeleting}
              >
                {isDeleting ? 'Wird gelöscht...' : 'Löschen'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Transfer (Move/Copy) Modal */}
      {showTransferModal && (
        <div className="modal modal--overlay" onClick={() => setShowTransferModal(false)}>
          <div className="modal-content modal-content--small" onClick={(e) => e.stopPropagation()}>
            <span className="close" onClick={() => setShowTransferModal(false)}>&times;</span>
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
                onClick={() => setShowTransferModal(false)}
                disabled={isTransferring}
              >
                Abbrechen
              </button>
              <button
                type="button"
                className="btn btn--primary"
                onClick={confirmTransfer}
                disabled={isTransferring || !selectedTargetWatchlist}
              >
                {isTransferring 
                  ? `Wird ${transferAction === 'move' ? 'verschoben' : 'kopiert'}...` 
                  : transferAction === 'move' ? 'Verschieben' : 'Kopieren'}
              </button>
            </div>
          </div>
        </div>
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

// formatPrice from utils is used directly throughout this component; remove wrapper to avoid unused symbol

function formatTime(timestamp) {
  if (!timestamp) return '-';

  // Handle numeric epoch seconds
  if (typeof timestamp === 'number') {
    // assume seconds
    const dateNum = new Date(timestamp * 1000);
    if (!isNaN(dateNum.getTime())) {
      return `${dateNum.toLocaleDateString('de-DE')} · ${dateNum.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
    }
  }

  // Handle Date objects
  if (timestamp instanceof Date) {
    const d = timestamp;
    if (Number.isNaN(d.getTime())) return '-';
    return `${d.toLocaleDateString('de-DE')} · ${d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
  }

  // Handle strings
  if (typeof timestamp === 'string') {
    const trimmed = timestamp.trim();
    // Date-only format YYYY-MM-DD -> show only date (no 00:00)
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      try {
        const d = new Date(trimmed + 'T00:00:00');
        if (!isNaN(d.getTime())) return d.toLocaleDateString('de-DE');
      } catch (e) {
        return trimmed;
      }
    }

    // Pure epoch digits in string
    if (/^\d+$/.test(trimmed)) {
      try {
        const sec = parseInt(trimmed, 10);
        const d = new Date(sec * 1000);
        if (!isNaN(d.getTime())) return `${d.toLocaleDateString('de-DE')} · ${d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
      } catch (e) {
        // fallthrough
      }
    }

    // Fallback: let Date parse ISO strings
    const parsed = new Date(trimmed);
    if (!isNaN(parsed.getTime())) {
      return `${parsed.toLocaleDateString('de-DE')} · ${parsed.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
    }

    return trimmed;
  }

  return '-';
}

function formatSignedCurrency(value, stockLike) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '-';
  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  // Use formatPrice for localized formatting; strip sign from formatted and prepend our sign
  const formatted = formatPrice(Math.abs(value), stockLike);
  return `${sign}${formatted}`;
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

function PerformanceMetric({ label, data, hint, stock }) {
  const state = data ? data.direction : 'neutral';
  const appearance = state === 'positive' ? 'positive' : state === 'negative' ? 'negative' : 'neutral';

  return (
    <div className={`performance-metric performance-metric--${appearance}`}>
      <span className="performance-metric__label">{label}</span>
      <span className="performance-metric__value">{data ? formatPercent(data.percent) : '-'}</span>
      <span className="performance-metric__delta">{data ? formatSignedCurrency(data.amount, stock) : '-'}</span>
      {hint && <span className="performance-metric__hint">{hint}</span>}
    </div>
  );
}

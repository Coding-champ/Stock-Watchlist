import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import API_BASE from '../config';
import { formatPrice } from '../utils/currencyUtils';
import { createPortal } from 'react-dom';
import StockTable from './StockTable';
import StockModal from './StockModal';
import StockDetailModal from './StockDetailModal';


function StocksSection({ watchlist, watchlists, onShowToast }) {
  const [stocks, setStocks] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sectorFilter, setSectorFilter] = useState('');
  const [countryFilter, setCountryFilter] = useState('');
  const [observationReasonFilter, setObservationReasonFilter] = useState('');
  const [performanceFilter, setPerformanceFilter] = useState('all');
  const [toast, setToast] = useState(null);
  const toastTimeoutRef = useRef(null);
  // Track updating/failed ids via local state when necessary. We only use the setters
  // in this component so ignore the first tuple item to avoid unused-variable lint.
  const [, setUpdatingIds] = useState(new Set());
  const [, setFailedIds] = useState(new Set());

  const dismissToast = useCallback(() => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }
    setToast(null);
  }, []);

  const showToast = useCallback((message, appearance = 'info') => {
    if (!message) {
      return;
    }

    if (onShowToast) {
      onShowToast(message, appearance);
      return;
    }

    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }

    setToast({ message, appearance });
    toastTimeoutRef.current = setTimeout(() => {
      setToast(null);
      toastTimeoutRef.current = null;
    }, 4000);
  }, [onShowToast]);

  // Stable loadStocks function - only depends on watchlist.id
  const loadStocks = useCallback(async () => {
    if (!watchlist) {
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/stocks/?watchlist_id=${watchlist.id}`, {
        cache: 'no-store' // Prevent browser caching to always get fresh data
      });
      const data = await response.json();
      setStocks(data);
    } catch (error) {
      console.error('Error loading stocks:', error);
      showToast('Fehler beim Laden der Aktien', 'error');
    } finally {
      setLoading(false);
    }
  }, [watchlist?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Use useMemo instead of useEffect to avoid unnecessary re-renders
  const filteredStocks = useMemo(() => {
    const term = searchTerm.toLowerCase();
    return stocks.filter(stock => {
      const matchesSearch = !term
        || (stock.name || '').toLowerCase().includes(term)
        || (stock.isin || '').toLowerCase().includes(term)
        || (stock.ticker_symbol || '').toLowerCase().includes(term);

      const matchesSector = !sectorFilter
        || (stock.sector || '').toLowerCase() === sectorFilter.toLowerCase();

      const matchesCountry = !countryFilter
        || (stock.country || '').toLowerCase() === countryFilter.toLowerCase();

      const matchesObservationReason = !observationReasonFilter
        || (Array.isArray(stock.observation_reasons) && 
            stock.observation_reasons.some(reason => 
              reason.toLowerCase() === observationReasonFilter.toLowerCase()
            ));

      return matchesSearch && matchesSector && matchesCountry && matchesObservationReason;
    });
  }, [stocks, searchTerm, sectorFilter, countryFilter, observationReasonFilter]);

  // Load stocks when watchlist changes
  useEffect(() => {
    if (watchlist) {
      loadStocks();
    }
  }, [watchlist, loadStocks]);

  useEffect(() => () => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }
  }, []);

  const handleAddStock = () => {
    setShowAddModal(true);
  };

  const uniqueSectors = useMemo(() => {
    const unique = new Set();
    stocks.forEach(stock => {
      if (stock.sector) {
        unique.add(stock.sector);
      }
    });
    return Array.from(unique).sort((a, b) => a.localeCompare(b));
  }, [stocks]);

  const uniqueCountries = useMemo(() => {
    const unique = new Set();
    stocks.forEach(stock => {
      if (stock.country) {
        unique.add(stock.country);
      }
    });
    return Array.from(unique).sort((a, b) => a.localeCompare(b));
  }, [stocks]);

  const uniqueObservationReasons = useMemo(() => {
    const unique = new Set();
    stocks.forEach(stock => {
      if (Array.isArray(stock.observation_reasons)) {
        stock.observation_reasons.forEach(reason => {
          if (reason && typeof reason === 'string') {
            unique.add(reason);
          }
        });
      }
    });
    return Array.from(unique).sort((a, b) => a.localeCompare(b));
  }, [stocks]);

  const handleStockAdded = () => {
    setShowAddModal(false);
    loadStocks();
  };

  const handleStockClick = (stock) => {
    setSelectedStock(stock);
  };

  const handleDeleteStock = async (stockId) => {
    if (!window.confirm('Möchten Sie diese Aktie wirklich löschen?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/stocks/${stockId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        loadStocks();
        showToast('Aktie gelöscht', 'success');
      } else {
        let message = 'Fehler beim Löschen der Aktie';
        try {
          const errorData = await response.json();
          if (errorData?.detail) {
            message = errorData.detail;
          }
        } catch (parseError) {
          console.warn('Delete stock: konnte Fehlermeldung nicht parsen', parseError);
        }
        showToast(message, 'error');
      }
    } catch (error) {
      console.error('Error deleting stock:', error);
      showToast('Fehler beim Löschen der Aktie', 'error');
    }
  };

  const handleMoveStock = async (stockId, targetWatchlistId) => {
    try {
      const response = await fetch(`${API_BASE}/stocks/${stockId}/move`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_watchlist_id: targetWatchlistId })
      });

      if (response.ok) {
        loadStocks();
        showToast('Aktie erfolgreich verschoben!', 'success');
        return;
      }

      let fallbackMessage = 'Fehler beim Verschieben der Aktie';
      let responseBody = null;

      try {
        responseBody = await response.json();
      } catch (parseError) {
        console.warn('Move stock: konnte Fehlermeldung nicht parsen', parseError);
      }

      if (responseBody) {
        const detailMessage = responseBody.detail || responseBody.message || responseBody.error;
        if (typeof detailMessage === 'string' && detailMessage.trim().length > 0) {
          const normalized = detailMessage.toLowerCase();
          if (
            normalized.includes('already') &&
            normalized.includes('watchlist')
          ) {
            fallbackMessage = 'Aktie ist schon in der Ziel-Watchlist vorhanden!';
          } else {
            fallbackMessage = detailMessage;
          }
        }
      } else if (response.status === 409) {
        fallbackMessage = 'Aktie ist schon in der Ziel-Watchlist vorhanden!';
      }

      showToast(fallbackMessage, 'error');
    } catch (error) {
      console.error('Error moving stock:', error);
      showToast('Fehler beim Verschieben der Aktie', 'error');
    }
  };

  const handleCopyStock = async (stockId, targetWatchlistId) => {
    try {
      const response = await fetch(`${API_BASE}/stocks/${stockId}/copy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_watchlist_id: targetWatchlistId })
      });

      if (response.ok) {
        loadStocks();
        const stockName = stocks.find((stock) => stock.id === stockId)?.name;
        showToast(
          `Aktie kopiert${stockName ? ` · ${stockName}` : ''}`,
          'success'
        );
        return;
      }

      let fallbackMessage = 'Fehler beim Kopieren der Aktie';
      let responseBody = null;

      try {
        responseBody = await response.json();
      } catch (parseError) {
        console.warn('Copy stock: konnte Fehlermeldung nicht parsen', parseError);
      }

      if (responseBody) {
        const detailMessage = responseBody.detail || responseBody.message || responseBody.error;
        if (typeof detailMessage === 'string' && detailMessage.trim().length > 0) {
          const normalized = detailMessage.toLowerCase();
          if (
            normalized.includes('already') &&
            normalized.includes('watchlist')
          ) {
            fallbackMessage = 'Aktie ist schon in der Ziel-Watchlist vorhanden!';
          } else {
            fallbackMessage = detailMessage;
          }
        }
      } else if (response.status === 409) {
        fallbackMessage = 'Aktie ist schon in der Ziel-Watchlist vorhanden!';
      }

      showToast(fallbackMessage, 'error');
    } catch (error) {
      console.error('Error copying stock:', error);
      showToast('Fehler beim Kopieren der Aktie', 'error');
    }
  };

  const handleUpdateMarketData = async (stockId) => {
    // clear any previous failure state for this id and mark as updating
    setFailedIds(prev => {
      const s = new Set(prev);
      s.delete(stockId);
      return s;
    });
    setUpdatingIds(prev => {
      const s = new Set(prev);
      s.add(stockId);
      return s;
    });
    // mark the stock in local state as updating (so StockTable can read latest_data.__updating)
    setStocks(prev => prev.map(s => s.id === stockId ? { ...s, latest_data: { ...(s.latest_data||s.latestData||{}), __updating: true, __failed: false } } : s));
    try {
      const response = await fetch(`${API_BASE}/stocks/${stockId}/update-market-data`, {
        method: 'POST'
      });

      if (response.ok) {
        // success -> clear updating and failed state
        setUpdatingIds(prev => {
          const s = new Set(prev);
          s.delete(stockId);
          return s;
        });
        setFailedIds(prev => {
          const s = new Set(prev);
          s.delete(stockId);
          return s;
        });
        setStocks(prev => prev.map(s => s.id === stockId ? { ...s, latest_data: { ...(s.latest_data||s.latestData||{}), __updating: false, __failed: false } } : s));
        const result = await response.json();
  const priceNum = typeof result?.data?.current_price === 'number' ? result.data.current_price : null;
  const pe = typeof result?.data?.pe_ratio === 'number' ? result.data.pe_ratio.toFixed(2) : 'N/A';
  showToast(`Marktdaten aktualisiert · Kurs ${formatPrice(priceNum, stocks.find(s => s.id === stockId))} · KGV ${pe}`, 'success');

        // Update only the single stock in the local state so the card shows the precise timestamp
        try {
          const updatedData = result?.data || {};
          setStocks((prev) => prev.map((s) => {
            if (s.id !== stockId) return s;
            // Merge latest_data, preserving existing fields
            const prevLatest = s.latest_data || s.latestData || {};
            const newLatest = {
              ...prevLatest,
              current_price: typeof updatedData.current_price === 'number' ? updatedData.current_price : prevLatest.current_price,
              pe_ratio: typeof updatedData.pe_ratio === 'number' ? updatedData.pe_ratio : prevLatest.pe_ratio,
              timestamp: (updatedData.timestamp || updatedData.date) ? (updatedData.timestamp || updatedData.date) : prevLatest.timestamp
            };
            return { ...s, latest_data: newLatest };
          }));
        } catch (err) {
          // If anything goes wrong updating local state, mark only the single stock as failed
          // and show a retry toast instead of reloading all stocks. This avoids unexpected
          // full-list reloads during bulk operations.
          console.warn('Could not apply single-stock update locally; marking single stock as failed', err);
          // mark failed for this stock so the UI shows retry affordance
          setFailedIds(prev => {
            const s = new Set(prev);
            s.add(stockId);
            return s;
          });
          setStocks(prev => prev.map(s => s.id === stockId ? { ...s, latest_data: { ...(s.latest_data||s.latestData||{}), __updating: false, __failed: true } } : s));
          showToast('Konnte die lokale Aktualisierung nicht anwenden. Bitte erneut versuchen.', 'warning');
        }
      } else {
        // mark failed
        setUpdatingIds(prev => {
          const s = new Set(prev);
          s.delete(stockId);
          return s;
        });
        setFailedIds(prev => {
          const s = new Set(prev);
          s.add(stockId);
          return s;
        });
        setStocks(prev => prev.map(s => s.id === stockId ? { ...s, latest_data: { ...(s.latest_data||s.latestData||{}), __updating: false, __failed: true } } : s));
        let errorMessage = 'Fehler beim Aktualisieren der Marktdaten';
        try {
          const error = await response.json();
          if (error?.detail) {
            errorMessage = error.detail;
          }
        } catch (parseError) {
          console.warn('Update market data: konnte Fehlermeldung nicht parsen', parseError);
        }
        showToast(errorMessage, 'error');
      }
    } catch (error) {
      // network/other error -> mark failed
      setUpdatingIds(prev => {
        const s = new Set(prev);
        s.delete(stockId);
        return s;
      });
      setFailedIds(prev => {
        const s = new Set(prev);
        s.add(stockId);
        return s;
      });
      setStocks(prev => prev.map(s => s.id === stockId ? { ...s, latest_data: { ...(s.latest_data||s.latestData||{}), __updating: false, __failed: true } } : s));
      console.error('Error updating market data:', error);
      showToast('Fehler beim Aktualisieren der Marktdaten', 'error');
    }
  };

  const handleUpdateAllMarketData = async () => {
    if (stocks.length === 0) {
      showToast('Keine Aktien zum Aktualisieren vorhanden', 'info');
      return;
    }

    setLoading(true);
    showToast(`Aktualisiere ${stocks.length} Aktien...`, 'info');

    let successCount = 0;
    let failCount = 0;

    // Update all stocks sequentially to avoid overwhelming the API
    for (const stock of stocks) {
      // mark this stock as updating in local state
      setStocks(prev => prev.map(s => s.id === stock.id ? { ...s, latest_data: { ...(s.latest_data||s.latestData||{}), __updating: true, __failed: false } } : s));
      try {
        const response = await fetch(`${API_BASE}/stocks/${stock.id}/update-market-data`, {
          method: 'POST'
        });

        if (response.ok) {
          successCount++;
          try {
            const result = await response.json();
            const updatedData = result?.data || {};
            // Apply the update to the single stock in local state
            setStocks((prev) => prev.map((s) => {
              if (s.id !== stock.id) return s;
              const prevLatest = s.latest_data || s.latestData || {};
              const newLatest = {
                ...prevLatest,
                current_price: typeof updatedData.current_price === 'number' ? updatedData.current_price : prevLatest.current_price,
                pe_ratio: typeof updatedData.pe_ratio === 'number' ? updatedData.pe_ratio : prevLatest.pe_ratio,
                timestamp: (updatedData.timestamp || updatedData.date) ? (updatedData.timestamp || updatedData.date) : prevLatest.timestamp,
                __updating: false,
                __failed: false
              };
              return { ...s, latest_data: newLatest };
            }));
          } catch (err) {
            console.warn(`Updated ${stock.ticker_symbol} but could not apply local update`, err);
            setStocks(prev => prev.map(s => s.id === stock.id ? { ...s, latest_data: { ...(s.latest_data||s.latestData||{}), __updating: false } } : s));
          }
        } else {
          failCount++;
          console.warn(`Failed to update ${stock.ticker_symbol}`);
          setStocks(prev => prev.map(s => s.id === stock.id ? { ...s, latest_data: { ...(s.latest_data||s.latestData||{}), __updating: false, __failed: true } } : s));
        }

        // Small delay between requests to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 200));
      } catch (error) {
        failCount++;
        console.error(`Error updating ${stock.ticker_symbol}:`, error);
      }
    }

    // Show summary toast
    if (failCount === 0) {
      showToast(`✓ Alle ${successCount} Aktien erfolgreich aktualisiert`, 'success');
    } else if (successCount === 0) {
      showToast(`✗ Fehler beim Aktualisieren aller ${stocks.length} Aktien`, 'error');
    } else {
      showToast(`${successCount} erfolgreich, ${failCount} fehlgeschlagen`, 'warning');
    }

    setLoading(false);
  };

  const watchlistSubtitle = watchlist.description
    ? watchlist.description
    : 'Beobachte Kursverläufe, Gewinner und Risiken in Echtzeit.';

  const toastMarkup = !onShowToast && toast && typeof document !== 'undefined'
    ? createPortal(
        (
          <div className="toast-container" role="status" aria-live="polite">
            <div className={`toast toast--${toast.appearance}`}>
              <span className="toast__message">{toast.message}</span>
              <button
                type="button"
                className="toast__close"
                onClick={dismissToast}
                aria-label="Hinweis schließen"
              >
                ×
              </button>
            </div>
          </div>
        ),
        document.body
      )
    : null;

  return (
    <>
      {toastMarkup}

      <section
        className="panel panel--stocks"
        aria-label={`Aktien in ${watchlist.name}`}
      >
      <div className="panel__header">
        <div className="panel__title-group">
          <span className="panel__eyebrow">Aktien</span>
          <h2 className="panel__title">Aktien in {watchlist.name}</h2>
          <p className="panel__subtitle">{watchlistSubtitle}</p>
        </div>
        <div className="panel__actions">
          <button type="button" className="btn" onClick={handleAddStock}>
            <span className="btn__icon" aria-hidden="true">＋</span>
            <span>Aktie hinzufügen</span>
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={handleUpdateAllMarketData}
            disabled={loading}
            title="Aktualisiert alle Marktdaten in dieser Watchlist"
          >
            <span className="btn__icon" aria-hidden="true">⟳</span>
            <span>Daten aktualisieren</span>
          </button>
        </div>
      </div>

      <div className="panel__toolbar">
        <div className="panel__toolbar-row">
          <div className="search-field">
            <span className="search-field__icon" aria-hidden="true">🔍</span>
            <input
              type="text"
              className="search-field__input"
              placeholder="Suche nach Name, ISIN oder Ticker..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              aria-label="Aktien in dieser Watchlist durchsuchen"
            />
          </div>
        </div>

        <div className="filter-bar filter-bar--surface">
          <div className="filter-group">
            <label htmlFor="sector-filter">Sektor</label>
            <select
              id="sector-filter"
              value={sectorFilter}
              onChange={(event) => setSectorFilter(event.target.value)}
            >
              <option value="">Alle</option>
              {uniqueSectors.map((sector) => (
                <option key={sector} value={sector}>{sector}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="country-filter">Land</label>
            <select
              id="country-filter"
              value={countryFilter}
              onChange={(event) => setCountryFilter(event.target.value)}
            >
              <option value="">Alle</option>
              {uniqueCountries.map((country) => (
                <option key={country} value={country}>{country}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="observation-reason-filter">Beobachtungsgrund</label>
            <select
              id="observation-reason-filter"
              value={observationReasonFilter}
              onChange={(event) => setObservationReasonFilter(event.target.value)}
            >
              <option value="">Alle</option>
              {uniqueObservationReasons.map((reason) => (
                <option key={reason} value={reason}>{reason}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="performance-filter">Performance</label>
            <select
              id="performance-filter"
              value={performanceFilter}
              onChange={(event) => setPerformanceFilter(event.target.value)}
            >
              <option value="all">Alle</option>
              <option value="current-positive">Aktuell · Gewinner</option>
              <option value="current-negative">Aktuell · Verlierer</option>
              <option value="week-positive">52 Wochen · Gewinner</option>
              <option value="week-negative">52 Wochen · Verlierer</option>
              <option value="watchlist-positive">Watchlist · Gewinner</option>
              <option value="watchlist-negative">Watchlist · Verlierer</option>
            </select>
          </div>
        </div>
      </div>

      <div className="panel__body">
        {loading ? (
          <div className="loading loading--inline">
            <div className="spinner"></div>
          </div>
        ) : (
          <StockTable
            stocks={filteredStocks}
            watchlists={watchlists}
            currentWatchlistId={watchlist.id}
            onStockClick={handleStockClick}
            onDeleteStock={handleDeleteStock}
            onMoveStock={handleMoveStock}
            onCopyStock={handleCopyStock}
            onUpdateMarketData={handleUpdateMarketData}
            performanceFilter={performanceFilter}
            onShowToast={showToast}
          />
        )}
      </div>

      {showAddModal && (
        <StockModal
          watchlistId={watchlist.id}
          onShowToast={showToast}
          onClose={() => setShowAddModal(false)}
          onStockAdded={handleStockAdded}
        />
      )}

      {selectedStock && (
        <StockDetailModal
          stock={selectedStock}
          onClose={() => setSelectedStock(null)}
        />
      )}

      </section>
    </>
  );
}

export default StocksSection;

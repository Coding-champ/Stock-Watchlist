import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import '../styles/skeletons.css';
import { formatPrice } from '../utils/currencyUtils';
import { parseCSV, exportCSV } from '../utils/csvUtils';
import { createPortal } from 'react-dom';
import StockTable from './StockTable';
import StockModal from './StockModal';
import { useApi } from '../hooks/useApi';


function StocksSection({ watchlist, watchlists, onShowToast, onOpenStock }) {
  const [stocks, setStocks] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [bulkUpdating, setBulkUpdating] = useState(false);
  const [tableFadeVisible, setTableFadeVisible] = useState(false);
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
  
  const { fetchApi } = useApi();

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
      const data = await fetchApi(`/stocks/?watchlist_id=${watchlist.id}`, { useCache: false });
      setStocks(data);
    } catch (error) {
      console.error('Error loading stocks:', error);
      showToast('Fehler beim Laden der Aktien', 'error');
    } finally {
      setLoading(false);
    }
  }, [watchlist?.id, fetchApi]); // eslint-disable-line react-hooks/exhaustive-deps

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

  // Trigger a small fade-in when the table content becomes available.
  useEffect(() => {
    if (stocks.length > 0) {
      // reset then enable to ensure transition triggers
      setTableFadeVisible(false);
      const t = setTimeout(() => setTableFadeVisible(true), 20);
      return () => clearTimeout(t);
    }
    setTableFadeVisible(false);
  }, [stocks.length]);

  useEffect(() => () => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }
  }, []);

  const handleAddStock = () => {
    setShowAddModal(true);
  };

  const fileInputRef = useRef(null);

  const handleExportCSV = () => {
    if (!stocks || stocks.length === 0) {
      showToast('Keine Aktien zum Exportieren vorhanden', 'info');
      return;
    }

    const headers = ['Asset', 'Ticker', 'ISIN', 'Name', 'Branche', 'Sektor', 'Land'];

    const rows = stocks.map((s) => {
      const asset = s.asset_type || 'Aktie';
      return [
        asset,
        s.ticker_symbol || s.ticker || '',
        s.isin || '',
        s.name || '',
        s.industry || s.branche || '',
        s.sector || '',
        s.country || ''
      ];
    });

    const csv = exportCSV(headers, rows);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const safeName = (watchlist && watchlist.name) ? watchlist.name.replace(/[^a-z0-9\-_ ]/gi, '') : 'watchlist';
    link.download = `${safeName}-export.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const handleImportClick = () => {
    if (fileInputRef.current) fileInputRef.current.click();
  };

  const handleFileSelected = async (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      const { headers, rows } = parseCSV(text);
      const idxIsin = headers.findIndex(h => h.includes('isin'));
      const idxTicker = headers.findIndex(h => h.includes('ticker') || h.includes('symbol'));

      const identifiers = rows.map(cols => {
        let val = '';
        if (idxIsin !== -1) val = cols[idxIsin] || '';
        if (!val && idxTicker !== -1) val = cols[idxTicker] || '';
        if (!val) val = cols[0] || '';
        return String(val).trim().toUpperCase();
      }).filter(i => i && i.length > 0);

      if (identifiers.length === 0) {
        showToast('Keine gültigen Ticker/ISINs in der Datei gefunden', 'warning');
        event.target.value = '';
        return;
      }

      showToast(`Importiere ${identifiers.length} Einträge...`, 'info');
      const data = await fetchApi(`/stocks/bulk-add`, {
        method: 'POST',
        body: { watchlist_id: watchlist.id, identifiers, identifier_type: 'auto' },
        onError: (err) => {
          showToast(err.message || 'Fehler beim Import', 'error');
        }
      });
      
      if (data.created_count > 0) {
        showToast(`${data.created_count} Aktien hinzugefügt`, 'success');
        loadStocks();
      }
      if (data.exists_count > 0) {
        showToast(`${data.exists_count} waren bereits vorhanden`, 'info');
      }
      if (data.failed_count > 0) {
        showToast(`${data.failed_count} Einträge konnten nicht hinzugefügt werden`, 'warning');
      }
    } catch (err) {
      console.error('Error importing CSV:', err);
      showToast('Fehler beim Lesen der Datei', 'error');
    } finally {
      if (event.target) event.target.value = '';
    }
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
    // Open the dedicated stock page. No inline fallback modal anymore.
    if (typeof onOpenStock === 'function') {
      onOpenStock(stock);
      return;
    }

    // If no navigation callback provided, log a warning (developer oversight)
    // Previously an inline modal fallback existed; that has been removed intentionally.
    // eslint-disable-next-line no-console
    console.warn('No onOpenStock handler provided; stock click ignored.', stock);
  };

  const handleDeleteStock = async (stockId, skipToast = false) => {
    try {
      await fetchApi(`/stocks/${stockId}?watchlist_id=${watchlist.id}`, {
        method: 'DELETE',
        onError: (err) => {
          if (!skipToast) {
            showToast(err.message || 'Fehler beim Löschen der Aktie', 'error');
          }
        }
      });
      
      loadStocks();
      if (!skipToast) {
        showToast('Aktie gelöscht', 'success');
      }
    } catch (error) {
      console.error('Error deleting stock:', error);
      throw error;
    }
  };

  const handleMoveStock = async (stockId, targetWatchlistId) => {
    try {
      await fetchApi(`/stocks/${stockId}/move?source_watchlist_id=${watchlist.id}`, {
        method: 'PUT',
        body: { target_watchlist_id: targetWatchlistId },
        onError: (err) => {
          const message = err.message || 'Fehler beim Verschieben der Aktie';
          const normalized = message.toLowerCase();
          if (normalized.includes('already') && normalized.includes('watchlist')) {
            showToast('Aktie ist schon in der Ziel-Watchlist vorhanden!', 'error');
          } else {
            showToast(message, 'error');
          }
        }
      });
      
      loadStocks();
      showToast('Aktie erfolgreich verschoben!', 'success');
    } catch (error) {
      console.error('Error moving stock:', error);
    }
  };

  const handleCopyStock = async (stockId, targetWatchlistId) => {
    try {
      await fetchApi(`/stocks/${stockId}/copy?source_watchlist_id=${watchlist.id}`, {
        method: 'POST',
        body: { target_watchlist_id: targetWatchlistId },
        onError: (err) => {
          const message = err.message || 'Fehler beim Kopieren der Aktie';
          const normalized = message.toLowerCase();
          if (normalized.includes('already') && normalized.includes('watchlist')) {
            showToast('Aktie ist schon in der Ziel-Watchlist vorhanden!', 'error');
          } else {
            showToast(message, 'error');
          }
        }
      });
      
      loadStocks();
      const stockName = stocks.find((stock) => stock.id === stockId)?.name;
      showToast(
        `Aktie kopiert${stockName ? ` · ${stockName}` : ''}`,
        'success'
      );
    } catch (error) {
      console.error('Error copying stock:', error);
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
      const result = await fetchApi(`/stocks/${stockId}/update-market-data`, {
        method: 'POST',
        onError: (err) => {
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
          showToast(err.message || 'Fehler beim Aktualisieren der Marktdaten', 'error');
        }
      });

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
    } catch (error) {
      console.error('Error updating market data:', error);
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
    }
  };

  const handleUpdateAllMarketData = async () => {
    if (stocks.length === 0) {
      showToast('Keine Aktien zum Aktualisieren vorhanden', 'info');
      return;
    }
    // Don't toggle the global loading spinner here - update individual cards
    // and use a bulkUpdating flag to disable the button while running.
    setBulkUpdating(true);
    showToast(`Aktualisiere ${stocks.length} Aktien...`, 'info');

    let successCount = 0;
    let failCount = 0;

    // Update all stocks sequentially to avoid overwhelming the API
    for (const stock of stocks) {
      // mark this stock as updating in local state
      setStocks(prev => prev.map(s => s.id === stock.id ? { ...s, latest_data: { ...(s.latest_data||s.latestData||{}), __updating: true, __failed: false } } : s));
      try {
        const result = await fetchApi(`/stocks/${stock.id}/update-market-data`, {
          method: 'POST'
        });

        successCount++;
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

    setBulkUpdating(false);
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
          <button 
            type="button" 
            className="btn" 
            onClick={handleAddStock}
          >
            <span className="btn__icon" aria-hidden="true">＋</span>
            <span>Aktie hinzufügen</span>
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={handleExportCSV}
            title="Exportiert die Aktien dieser Watchlist als CSV"
          >
            <span className="btn__icon" aria-hidden="true"></span>
            <span>Export CSV</span>
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={handleImportClick}
            title="Importiere Aktien (CSV) in diese Watchlist"
          >
            <span className="btn__icon" aria-hidden="true"></span>
            <span>Import CSV</span>
          </button>
          <button
            type="button"
            className="btn"
            onClick={handleUpdateAllMarketData}
            disabled={loading || bulkUpdating}
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
        {loading && stocks.length === 0 ? (
          <div className="skeleton-table" aria-busy="true">
            <table className="stock-table">
              <tbody>
                {Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i} className="skeleton-row">
                    <td><span className="skeleton" style={{ width: 48, height: 16 }} /></td>
                    <td><span className="skeleton" style={{ width: 140, height: 16 }} /></td>
                    <td><span className="skeleton" style={{ width: 80, height: 16 }} /></td>
                    <td><span className="skeleton" style={{ width: 80, height: 16 }} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className={`fade-in ${tableFadeVisible ? 'visible' : ''}`}>
            <StockTable
              stocks={filteredStocks}
              watchlists={watchlists}
              currentWatchlistId={watchlist.id}
              onStockClick={handleStockClick}
              onDeleteStock={handleDeleteStock}
              onMoveStock={handleMoveStock}
              onCopyStock={handleCopyStock}
              onUpdateMarketData={handleUpdateMarketData}
              onStocksReload={loadStocks}
              performanceFilter={performanceFilter}
              onShowToast={showToast}
            />
          </div>
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

      {/* Hidden file input for CSV import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,text/csv"
        style={{ display: 'none' }}
        onChange={handleFileSelected}
      />

      {/* Stock details are rendered as a dedicated page via App routing; no inline modal fallback. */}

      </section>
    </>
  );
}

export default StocksSection;

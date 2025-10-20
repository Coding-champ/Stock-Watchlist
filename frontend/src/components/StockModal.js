import React, { useState, useEffect, useRef } from 'react';
import API_BASE from '../config';

const OBSERVATION_REASON_OPTIONS = [
  { value: 'chart_technical', label: 'Charttechnische Indikatoren' },
  { value: 'fundamentals', label: 'Fundamentaldaten' },
  { value: 'industry', label: 'Branchendaten' },
  { value: 'economics', label: 'Wirtschaftsdaten' }
];

const createInitialManualForm = () => ({
  isin: '',
  ticker_symbol: '',
  name: '',
  country: '',
  industry: '',
  sector: ''
});

function StockModal({ watchlistId, onClose, onStockAdded, onShowToast }) {
  const [mode, setMode] = useState('ticker'); // 'ticker' oder 'manual'
  const [tickerInput, setTickerInput] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [formData, setFormData] = useState(createInitialManualForm);
  const [bulkInput, setBulkInput] = useState('');
  const [bulkIdentifierMode, setBulkIdentifierMode] = useState('auto');
  const [bulkResults, setBulkResults] = useState(null);
  const [bulkSubmitting, setBulkSubmitting] = useState(false);
  const [observationReasons, setObservationReasons] = useState([]);
  const [observationNotes, setObservationNotes] = useState('');
  const [showReasonsDropdown, setShowReasonsDropdown] = useState(false);
  
  const dropdownRef = useRef(null);

  // Dropdown schließen bei Klick außerhalb
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowReasonsDropdown(false);
      }
    };

    if (showReasonsDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showReasonsDropdown]);

  const handleModeChange = (nextMode) => {
    setMode(nextMode);
    if (nextMode !== 'bulk') {
      setBulkResults(null);
    }
  };

  const resetModalState = () => {
    setMode('ticker');
    setTickerInput('');
    setSearching(false);
    setSearchResult(null);
    setFormData(createInitialManualForm());
    setBulkInput('');
    setBulkIdentifierMode('auto');
    setBulkResults(null);
    setBulkSubmitting(false);
    setObservationReasons([]);
    setObservationNotes('');
  };

  const handleClose = () => {
    resetModalState();
    onClose();
  };

  const handleObservationReasonsChange = (value) => {
    if (observationReasons.includes(value)) {
      // Entfernen wenn bereits ausgewählt
      setObservationReasons(observationReasons.filter(r => r !== value));
    } else {
      // Hinzufügen wenn noch nicht ausgewählt
      setObservationReasons([...observationReasons, value]);
    }
  };

  const handleObservationNotesChange = (event) => {
    setObservationNotes(event.target.value);
  };

  const renderObservationFields = (suffix) => {
    const notesId = `observation-notes-${suffix}`;
    const reasonsSelectId = `observation-reasons-${suffix}`;

    return (
      <div className="observation-section">
        <div className="form-group observation-section__reasons">
          <label htmlFor={reasonsSelectId}>Warum beobachtest du diese Aktie?</label>
          
          {/* Custom Dropdown mit Checkboxen */}
          <div className="custom-dropdown-container" ref={dropdownRef}>
            <button
              type="button"
              className={`custom-dropdown-toggle ${showReasonsDropdown ? 'open' : ''}`}
              onClick={() => setShowReasonsDropdown(!showReasonsDropdown)}
            >
              <span className="dropdown-text">
                {observationReasons.length === 0 
                  ? 'Kategorien auswählen...'
                  : `${observationReasons.length} ausgewählt`}
              </span>
              <span className="dropdown-arrow">{showReasonsDropdown ? '▲' : '▼'}</span>
            </button>
            
            {showReasonsDropdown && (
              <div className="custom-dropdown-menu">
                {OBSERVATION_REASON_OPTIONS.map((option) => (
                  <label key={option.value} className="dropdown-item">
                    <input
                      type="checkbox"
                      checked={observationReasons.includes(option.value)}
                      onChange={() => handleObservationReasonsChange(option.value)}
                    />
                    <span>{option.label}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
          
          {/* Ausgewählte Kategorien anzeigen */}
          {observationReasons.length > 0 && (
            <div className="selected-tags">
              {observationReasons.map((reason) => {
                const option = OBSERVATION_REASON_OPTIONS.find(opt => opt.value === reason);
                return option ? (
                  <span key={reason} className="tag">
                    {option.label}
                    <button
                      type="button"
                      className="tag-remove"
                      onClick={() => handleObservationReasonsChange(reason)}
                    >
                      ×
                    </button>
                  </span>
                ) : null;
              })}
            </div>
          )}
        </div>
        
        <div className="form-group observation-section__notes">
          <label htmlFor={notesId}>Kurze Notiz (optional)</label>
          <textarea
            id={notesId}
            value={observationNotes}
            onChange={handleObservationNotesChange}
            placeholder="Optional – ergänze dir einen Gedanken oder ein Setup"
            rows={3}
          />
        </div>
      </div>
    );
  };

  // Suche nach Aktie via yfinance
  const searchStock = async () => {
    if (!tickerInput.trim()) return;

    try {
      setSearching(true);
      const response = await fetch(`${API_BASE}/stocks/search/${tickerInput.toUpperCase()}`);
      const data = await response.json();
      
      if (data.found) {
        setSearchResult(data.stock);
        if (onShowToast) {
          onShowToast(`Aktie ${data.stock.name || data.stock.ticker_symbol} gefunden`, 'success');
        }
      } else {
        setSearchResult(null);
        if (onShowToast) {
          onShowToast(`Keine Aktie mit dem Ticker "${tickerInput}" gefunden.`, 'warning');
        } else {
          alert(`Keine Aktie mit dem Ticker "${tickerInput}" gefunden.`);
        }
      }
    } catch (error) {
      console.error('Error searching stock:', error);
      if (onShowToast) {
        onShowToast('Fehler bei der Suche', 'error');
      } else {
        alert('Fehler bei der Suche');
      }
    } finally {
      setSearching(false);
    }
  };

  // Aktie über yfinance hinzufügen
  const addStockByTicker = async () => {
    try {
      const trimmedNotes = observationNotes.trim();
      const payload = {
        ticker_symbol: tickerInput.toUpperCase(),
        watchlist_id: watchlistId,
        observation_reasons: observationReasons
      };

      if (trimmedNotes) {
        payload.observation_notes = trimmedNotes;
      }

      const response = await fetch(`${API_BASE}/stocks/add-by-ticker`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        resetModalState();
        onStockAdded();
        if (onShowToast) {
          onShowToast('Aktie zur Watchlist hinzugefügt', 'success');
        }
      } else {
        let message = 'Fehler beim Hinzufügen der Aktie';
        try {
          const error = await response.json();
          if (error?.detail) {
            message = error.detail;
          }
        } catch (parseError) {
          console.warn('addStockByTicker: konnte Fehlermeldung nicht parsen', parseError);
        }

        if (onShowToast) {
          onShowToast(message, 'error');
        } else {
          alert(message);
        }
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      if (onShowToast) {
        onShowToast('Fehler beim Hinzufügen der Aktie', 'error');
      } else {
        alert('Fehler beim Hinzufügen der Aktie');
      }
    }
  };

  // Manuelle Eingabe
  const handleManualSubmit = async (e) => {
    e.preventDefault();

    try {
      const trimmedNotes = observationNotes.trim();
      const payload = {
        ...formData,
        watchlist_id: watchlistId,
        observation_reasons: observationReasons
      };

      if (trimmedNotes) {
        payload.observation_notes = trimmedNotes;
      }

      const response = await fetch(`${API_BASE}/stocks/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        resetModalState();
        onStockAdded();
        if (onShowToast) {
          onShowToast('Aktie zur Watchlist hinzugefügt', 'success');
        }
      } else {
        let message = 'Fehler beim Hinzufügen der Aktie';
        try {
          const error = await response.json();
          if (error?.detail) {
            message = error.detail;
          }
        } catch (parseError) {
          console.warn('handleManualSubmit: konnte Fehlermeldung nicht parsen', parseError);
        }

        if (onShowToast) {
          onShowToast(message, 'error');
        } else {
          alert(message);
        }
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      if (onShowToast) {
        onShowToast('Fehler beim Hinzufügen der Aktie', 'error');
      } else {
        alert('Fehler beim Hinzufügen der Aktie');
      }
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const parseBulkIdentifiers = (input) => {
    return input
      .split(/[\s,;]+/)
      .map((item) => item.trim().toUpperCase())
      .filter((item) => item.length > 0);
  };

  const handleBulkSubmit = async () => {
    const identifiers = parseBulkIdentifiers(bulkInput);
    if (identifiers.length === 0) {
      if (onShowToast) {
        onShowToast('Bitte geben Sie mindestens einen Ticker oder eine ISIN ein.', 'warning');
      } else {
        alert('Bitte geben Sie mindestens einen Ticker oder eine ISIN ein.');
      }
      return;
    }

    try {
      setBulkSubmitting(true);
      setBulkResults(null);
      const response = await fetch(`${API_BASE}/stocks/bulk-add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          watchlist_id: watchlistId,
          identifiers,
          identifier_type: bulkIdentifierMode
        })
      });

      const data = await response.json();
      if (response.ok) {
        setBulkResults(data);
        if (data.created_count > 0) {
          onStockAdded();
          if (onShowToast) {
            onShowToast(`${data.created_count} Aktien hinzugefügt`, 'success');
          }
        }

        if (data.exists_count > 0 && onShowToast) {
          onShowToast(`${data.exists_count} Aktien waren bereits vorhanden`, 'info');
        }
        if (data.errors && data.errors.length > 0 && onShowToast) {
          onShowToast(`${data.errors.length} Einträge konnten nicht hinzugefügt werden`, 'warning');
        }
      } else {
        const message = data.detail || 'Fehler beim Hinzufügen der Aktien';
        if (onShowToast) {
          onShowToast(message, 'error');
        } else {
          alert(message);
        }
      }
    } catch (error) {
      console.error('Error during bulk add:', error);
      if (onShowToast) {
        onShowToast('Fehler beim Hinzufügen der Aktien', 'error');
      } else {
        alert('Fehler beim Hinzufügen der Aktien');
      }
    } finally {
      setBulkSubmitting(false);
    }
  };

  return (
    <div className="modal" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <span className="close" onClick={handleClose}>&times;</span>
        <h2>Aktie hinzufügen</h2>

        <div className="mode-toggle">
          <button
            className={`toggle-btn ${mode === 'ticker' ? 'active' : ''}`}
            onClick={() => handleModeChange('ticker')}
          >
            Per Ticker-Symbol
          </button>
          <button
            className={`toggle-btn ${mode === 'manual' ? 'active' : ''}`}
            onClick={() => handleModeChange('manual')}
          >
            Manuell eingeben
          </button>
          <button
            className={`toggle-btn ${mode === 'bulk' ? 'active' : ''}`}
            onClick={() => handleModeChange('bulk')}
          >
            Mehrere hinzufügen
          </button>
        </div>

        {mode === 'ticker' ? (
          <div className="ticker-mode">
            <div className="form-group">
              <label>Ticker-Symbol (z.B. AAPL, MSFT, GOOGL)</label>
              <div className="ticker-input-group">
                <input
                  type="text"
                  placeholder="AAPL"
                  value={tickerInput}
                  onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
                  onKeyDown={(e) => e.key === 'Enter' && searchStock()}
                />
                <button
                  type="button"
                  className="btn search-btn"
                  onClick={searchStock}
                  disabled={searching || !tickerInput.trim()}
                >
                  {searching ? '🔍 Suche...' : '🔍 Suchen'}
                </button>
              </div>
            </div>

            {searchResult && (
              <div className="search-result">
                <h3>📊 Gefundene Aktie:</h3>
                <div className="stock-info">
                  <p><strong>Name:</strong> {searchResult.name}</p>
                  <p><strong>Ticker:</strong> {searchResult.ticker}</p>
                  {searchResult.sector && <p><strong>Sektor:</strong> {searchResult.sector}</p>}
                  {searchResult.industry && <p><strong>Branche:</strong> {searchResult.industry}</p>}
                  {searchResult.country && <p><strong>Land:</strong> {searchResult.country}</p>}
                  {searchResult.current_price && (
                    <p><strong>Aktueller Kurs:</strong> ${searchResult.current_price}</p>
                  )}
                  {searchResult.pe_ratio && (
                    <p><strong>KGV:</strong> {searchResult.pe_ratio}</p>
                  )}
                </div>
                {renderObservationFields('ticker')}
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={addStockByTicker}
                >
                  ✅ Zur Watchlist hinzufügen
                </button>
              </div>
            )}

            <div className="help-text">
              <p>💡 <strong>Tipps:</strong></p>
              <ul>
                <li>US-Aktien: AAPL, MSFT, GOOGL, TSLA</li>
                <li>Deutsche Aktien: SAP.DE, VOW3.DE, BMW.DE</li>
                <li>UK Aktien: TSCO.L, BP.L</li>
                <li>Die Aktieninformationen werden automatisch von Yahoo Finance abgerufen</li>
              </ul>
            </div>
          </div>
        ) : mode === 'manual' ? (
          <form onSubmit={handleManualSubmit} className="manual-mode">
            <div className="form-group">
              <label>ISIN *</label>
              <input
                type="text"
                name="isin"
                required
                value={formData.isin}
                onChange={handleChange}
                placeholder="US0378331005"
              />
            </div>
            <div className="form-group">
              <label>Ticker Symbol *</label>
              <input
                type="text"
                name="ticker_symbol"
                required
                value={formData.ticker_symbol}
                onChange={handleChange}
                placeholder="AAPL"
              />
            </div>
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                placeholder="Apple Inc."
              />
            </div>
            <div className="form-group">
              <label>Land</label>
              <input
                type="text"
                name="country"
                value={formData.country}
                onChange={handleChange}
                placeholder="US"
              />
            </div>
            <div className="form-group">
              <label>Branche</label>
              <input
                type="text"
                name="industry"
                value={formData.industry}
                onChange={handleChange}
                placeholder="Consumer Electronics"
              />
            </div>
            <div className="form-group">
              <label>Sektor</label>
              <input
                type="text"
                name="sector"
                value={formData.sector}
                onChange={handleChange}
                placeholder="Technology"
              />
            </div>
            {renderObservationFields('manual')}
            <button type="submit" className="btn btn-primary">✅ Hinzufügen</button>
          </form>
        ) : (
          <div className="bulk-mode">
            <div className="form-group">
              <label>Mehrere Ticker oder ISINs *</label>
              <textarea
                value={bulkInput}
                onChange={(e) => {
                  setBulkInput(e.target.value);
                  setBulkResults(null);
                }}
                placeholder={"AAPL, MSFT, TSLA.DE\nUS0378331005; DE000BASF111"}
              />
              <small className="hint-text">
                Trennen Sie Einträge mit Komma, Semikolon oder Zeilenumbrüchen. Im Modus
                "Automatisch" wird jede Eingabe zunächst als Ticker versucht und bei Bedarf als ISIN interpretiert.
              </small>
            </div>
            <div className="form-group">
              <label>Identifikator-Typ</label>
              <select
                value={bulkIdentifierMode}
                onChange={(e) => setBulkIdentifierMode(e.target.value)}
              >
                <option value="auto">Automatisch erkennen</option>
                <option value="ticker">Nur Ticker-Symbole</option>
                <option value="isin">Nur ISINs</option>
              </select>
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleBulkSubmit}
              disabled={bulkSubmitting}
            >
              {bulkSubmitting ? '⏳ Wird hinzugefügt...' : '✅ Alle hinzufügen'}
            </button>

            {bulkResults && (
              <div className="bulk-results">
                <h3>Ergebnisübersicht</h3>
                <p>
                  <strong>{bulkResults.created_count}</strong> erfolgreich,{' '}
                  <strong>{bulkResults.failed_count}</strong> fehlgeschlagen
                </p>
                <ul>
                  {bulkResults.results.map((result, index) => (
                    <li
                      key={`${result.identifier || 'entry'}-${index}`}
                      className={`bulk-result-item status-${result.status}`}
                    >
                      <span className="identifier">{result.identifier || '—'}</span>
                      {result.resolved_ticker && result.identifier &&
                        result.resolved_ticker !== result.identifier.toUpperCase() && (
                          <span className="resolved">→ {result.resolved_ticker}</span>
                        )}
                      <span className="status-label">{result.status}</span>
                      {result.message && <span className="message">{result.message}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default StockModal;

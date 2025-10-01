import React, { useState } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function StockModal({ watchlistId, onClose, onStockAdded }) {
  const [mode, setMode] = useState('ticker'); // 'ticker' oder 'manual'
  const [tickerInput, setTickerInput] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [formData, setFormData] = useState({
    isin: '',
    ticker_symbol: '',
    name: '',
    country: '',
    industry: '',
    sector: ''
  });

  // Suche nach Aktie via yfinance
  const searchStock = async () => {
    if (!tickerInput.trim()) return;

    try {
      setSearching(true);
      const response = await fetch(`${API_BASE}/stocks/search/${tickerInput.toUpperCase()}`);
      const data = await response.json();
      
      if (data.found) {
        setSearchResult(data.stock);
      } else {
        setSearchResult(null);
        alert(`Keine Aktie mit dem Ticker "${tickerInput}" gefunden.`);
      }
    } catch (error) {
      console.error('Error searching stock:', error);
      alert('Fehler bei der Suche');
    } finally {
      setSearching(false);
    }
  };

  // Aktie über yfinance hinzufügen
  const addStockByTicker = async () => {
    try {
      const response = await fetch(`${API_BASE}/stocks/add-by-ticker`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker_symbol: tickerInput.toUpperCase(),
          watchlist_id: watchlistId
        })
      });

      if (response.ok) {
        onStockAdded();
      } else {
        const error = await response.json();
        alert(error.detail || 'Fehler beim Hinzufügen der Aktie');
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      alert('Fehler beim Hinzufügen der Aktie');
    }
  };

  // Manuelle Eingabe
  const handleManualSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(`${API_BASE}/stocks/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          watchlist_id: watchlistId
        })
      });

      if (response.ok) {
        onStockAdded();
      } else {
        alert('Fehler beim Hinzufügen der Aktie');
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      alert('Fehler beim Hinzufügen der Aktie');
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <span className="close" onClick={onClose}>&times;</span>
        <h2>Aktie hinzufügen</h2>
        
        {/* Mode Toggle */}
        <div className="mode-toggle">
          <button 
            className={`toggle-btn ${mode === 'ticker' ? 'active' : ''}`}
            onClick={() => setMode('ticker')}
          >
            📈 Per Ticker-Symbol
          </button>
          <button 
            className={`toggle-btn ${mode === 'manual' ? 'active' : ''}`}
            onClick={() => setMode('manual')}
          >
            ✏️ Manuell eingeben
          </button>
        </div>

        {mode === 'ticker' ? (
          /* Ticker-Modus */
          <div className="ticker-mode">
            <div className="form-group">
              <label>Ticker-Symbol (z.B. AAPL, MSFT, GOOGL)</label>
              <div className="ticker-input-group">
                <input
                  type="text"
                  placeholder="AAPL"
                  value={tickerInput}
                  onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
                  onKeyPress={(e) => e.key === 'Enter' && searchStock()}
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
        ) : (
          /* Manueller Modus */
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
            <button type="submit" className="btn btn-primary">✅ Hinzufügen</button>
          </form>
        )}
      </div>
    </div>
  );
}

export default StockModal;

import React, { useState } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function StockModal({ watchlistId, onClose, onStockAdded }) {
  const [formData, setFormData] = useState({
    isin: '',
    ticker_symbol: '',
    name: '',
    country: '',
    industry: '',
    sector: ''
  });

  const handleSubmit = async (e) => {
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
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>ISIN *</label>
            <input
              type="text"
              name="isin"
              required
              value={formData.isin}
              onChange={handleChange}
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
            />
          </div>
          <div className="form-group">
            <label>Land</label>
            <input
              type="text"
              name="country"
              value={formData.country}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label>Branche</label>
            <input
              type="text"
              name="industry"
              value={formData.industry}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label>Sektor</label>
            <input
              type="text"
              name="sector"
              value={formData.sector}
              onChange={handleChange}
            />
          </div>
          <button type="submit" className="btn">Hinzufügen</button>
        </form>
      </div>
    </div>
  );
}

export default StockModal;

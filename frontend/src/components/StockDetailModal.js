import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function StockDetailModal({ stock, onClose }) {
  const [stockData, setStockData] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const loadStockData = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/stock-data/?stock_id=${stock.id}`);
      const data = await response.json();
      setStockData(data);
    } catch (error) {
      console.error('Error loading stock data:', error);
    }
  }, [stock.id]);

  const loadAlerts = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/alerts/?stock_id=${stock.id}`);
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  }, [stock.id]);

  useEffect(() => {
    loadStockData();
    loadAlerts();
  }, [loadStockData, loadAlerts]);

  const latestData = stockData.length > 0 ? stockData[0] : {};

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <span className="close" onClick={onClose}>&times;</span>
        <div className="stock-detail-content">
          <h2>{stock.name}</h2>
          
          <div className="detail-grid">
            <div className="detail-item">
              <strong>ISIN</strong>
              {stock.isin}
            </div>
            <div className="detail-item">
              <strong>Ticker</strong>
              {stock.ticker_symbol}
            </div>
            <div className="detail-item">
              <strong>Land</strong>
              {stock.country || '-'}
            </div>
            <div className="detail-item">
              <strong>Branche</strong>
              {stock.industry || '-'}
            </div>
            <div className="detail-item">
              <strong>Sektor</strong>
              {stock.sector || '-'}
            </div>
            <div className="detail-item">
              <strong>Aktueller Preis</strong>
              {latestData.current_price ? latestData.current_price.toFixed(2) + ' €' : '-'}
            </div>
            <div className="detail-item">
              <strong>KGV (P/E Ratio)</strong>
              {latestData.pe_ratio ? latestData.pe_ratio.toFixed(2) : '-'}
            </div>
            <div className="detail-item">
              <strong>RSI</strong>
              {latestData.rsi ? latestData.rsi.toFixed(2) : '-'}
            </div>
            <div className="detail-item">
              <strong>Volatilität</strong>
              {latestData.volatility ? latestData.volatility.toFixed(2) + '%' : '-'}
            </div>
          </div>

          {alerts.length > 0 && (
            <>
              <h3>Aktive Alerts</h3>
              {alerts.map((alert) => (
                <div 
                  key={alert.id} 
                  className={`alert-item ${alert.is_active ? '' : 'inactive'}`}
                >
                  <strong>{alert.alert_type}</strong> {alert.condition} {alert.threshold_value}
                  {!alert.is_active && ' (Inaktiv)'}
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default StockDetailModal;

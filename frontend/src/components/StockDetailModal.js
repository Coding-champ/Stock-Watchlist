import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

function StockDetailModal({ stock, onClose }) {
  const [stockData, setStockData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [extendedData, setExtendedData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadStockData = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/stock-data/?stock_id=${stock.id}`);
      const data = await response.json();
      setStockData(data);
    } catch (error) {
      console.error('Error loading stock data:', error);
    }
  }, [stock.id]);

  const loadExtendedData = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/stocks/${stock.id}/detailed`);
      const data = await response.json();
      setExtendedData(data.extended_data);
    } catch (error) {
      console.error('Error loading extended stock data:', error);
    } finally {
      setLoading(false);
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
    loadExtendedData();
  }, [loadStockData, loadAlerts, loadExtendedData]);

  const latestData = stockData.length > 0 ? stockData[0] : {};
  
  const formatNumber = (value, decimals = 2, suffix = '') => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      return value.toFixed(decimals) + suffix;
    }
    return '-';
  };

  const formatCurrency = (value, currency = '$') => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      return currency + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return '-';
  };

  const formatLargeNumber = (value) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      if (value >= 1e12) return (value / 1e12).toFixed(2) + 'T';
      if (value >= 1e9) return (value / 1e9).toFixed(2) + 'B';
      if (value >= 1e6) return (value / 1e6).toFixed(2) + 'M';
      if (value >= 1e3) return (value / 1e3).toFixed(2) + 'K';
      return value.toFixed(2);
    }
    return '-';
  };

  // KORREKTE Prozentformatierung für yfinance
  const formatPercentAsIs = (value) => formatNumber(value, 2, '%'); // Bereits Prozent (dividendYield)
  const formatPercentFromDecimal = (value) => formatNumber(value * 100, 2, '%'); // Dezimal zu Prozent
  
  const formatDate = (timestamp) => {
    if (!timestamp) return '-';
    return new Date(timestamp * 1000).toLocaleDateString('de-DE');
  };

  if (loading) {
    return (
      <div className="modal" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <span className="close" onClick={onClose}>&times;</span>
          <div className="stock-detail-content">
            <div className="loading">Lade erweiterte Daten...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal-content expanded" onClick={(e) => e.stopPropagation()}>
        <span className="close" onClick={onClose}>&times;</span>
        <div className="stock-detail-content">
          <h2>{stock.name} ({stock.ticker_symbol})</h2>
          
          {/* Business Summary */}
          {extendedData?.business_summary && (
            <div className="business-summary">
              <h3>Unternehmensbeschreibung</h3>
              <p>{extendedData.business_summary.substring(0, 500)}...</p>
            </div>
          )}

          {/* Price Data Section */}
          <div className="data-section">
            <h3>📈 Preisdaten</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>Aktueller Kurs</strong>
                {formatCurrency(extendedData?.price_data?.current_price)}
              </div>
              <div className="detail-item">
                <strong>Tageshoch</strong>
                {formatCurrency(extendedData?.price_data?.day_high)}
              </div>
              <div className="detail-item">
                <strong>Tagestief</strong>
                {formatCurrency(extendedData?.price_data?.day_low)}
              </div>
              <div className="detail-item">
                <strong>52-Wochen Hoch</strong>
                {formatCurrency(extendedData?.price_data?.fifty_two_week_high)}
              </div>
              <div className="detail-item">
                <strong>52-Wochen Tief</strong>
                {formatCurrency(extendedData?.price_data?.fifty_two_week_low)}
              </div>
              <div className="detail-item">
                <strong>50-Tage Ø</strong>
                {formatCurrency(extendedData?.price_data?.fifty_day_average)}
              </div>
              <div className="detail-item">
                <strong>200-Tage Ø</strong>
                {formatCurrency(extendedData?.price_data?.two_hundred_day_average)}
              </div>
            </div>
          </div>

          {/* Financial Ratios Section */}
          <div className="data-section">
            <h3>📊 Finanzielle Kennzahlen</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>Marktkapitalisierung</strong>
                {formatLargeNumber(extendedData?.financial_ratios?.market_cap)}
              </div>
              <div className="detail-item">
                <strong>KGV (P/E)</strong>
                {formatNumber(extendedData?.financial_ratios?.pe_ratio)}
              </div>
              <div className="detail-item">
                <strong>PEG-Ratio</strong>
                {formatNumber(extendedData?.financial_ratios?.peg_ratio)}
              </div>
              <div className="detail-item">
                <strong>Kurs-Buchwert (P/B)</strong>
                {formatNumber(extendedData?.financial_ratios?.price_to_book)}
              </div>
              <div className="detail-item">
                <strong>Kurs-Umsatz (P/S)</strong>
                {formatNumber(extendedData?.financial_ratios?.price_to_sales)}
              </div>
              <div className="detail-item">
                <strong>Gewinnmarge</strong>
                {formatPercentFromDecimal(extendedData?.financial_ratios?.profit_margins)}
              </div>
              <div className="detail-item">
                <strong>Operative Marge</strong>
                {formatPercentFromDecimal(extendedData?.financial_ratios?.operating_margins)}
              </div>
              <div className="detail-item">
                <strong>Eigenkapitalrendite (ROE)</strong>
                {formatPercentFromDecimal(extendedData?.financial_ratios?.return_on_equity)}
              </div>
              <div className="detail-item">
                <strong>Gesamtkapitalrendite (ROA)</strong>
                {formatPercentFromDecimal(extendedData?.financial_ratios?.return_on_assets)}
              </div>
            </div>
          </div>

          {/* Cashflow Section */}
          <div className="data-section">
            <h3>💰 Cashflow & Bilanz</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>Operativer Cashflow</strong>
                {formatLargeNumber(extendedData?.cashflow_data?.operating_cashflow)}
              </div>
              <div className="detail-item">
                <strong>Freier Cashflow</strong>
                {formatLargeNumber(extendedData?.cashflow_data?.free_cashflow)}
              </div>
              <div className="detail-item">
                <strong>Liquide Mittel</strong>
                {formatLargeNumber(extendedData?.cashflow_data?.total_cash)}
              </div>
              <div className="detail-item">
                <strong>Gesamtverschuldung</strong>
                {formatLargeNumber(extendedData?.cashflow_data?.total_debt)}
              </div>
              <div className="detail-item">
                <strong>Verschuldungsgrad</strong>
                {formatNumber(extendedData?.cashflow_data?.debt_to_equity)}
              </div>
            </div>
          </div>

          {/* Dividend Section - KORRIGIERTE PROZENTANZEIGE */}
          {(extendedData?.dividend_info?.dividend_rate || extendedData?.dividend_info?.dividend_yield) && (
            <div className="data-section">
              <h3>💎 Dividenden</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <strong>Dividende (jährlich)</strong>
                  {formatCurrency(extendedData?.dividend_info?.dividend_rate)}
                </div>
                <div className="detail-item">
                  <strong>Dividendenrendite</strong>
                  {formatPercentAsIs(extendedData?.dividend_info?.dividend_yield)}
                </div>
                <div className="detail-item">
                  <strong>Ausschüttungsquote</strong>
                  {formatPercentFromDecimal(extendedData?.dividend_info?.payout_ratio)}
                </div>
                <div className="detail-item">
                  <strong>5-Jahres Ø Rendite</strong>
                  {formatPercentAsIs(extendedData?.dividend_info?.five_year_avg_dividend_yield)}
                </div>
                <div className="detail-item">
                  <strong>Ex-Dividenden-Datum</strong>
                  {formatDate(extendedData?.dividend_info?.ex_dividend_date)}
                </div>
              </div>
            </div>
          )}

          {/* Volume Section */}
          <div className="data-section">
            <h3>📊 Handelsvolumen</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>Tagesvolumen</strong>
                {formatLargeNumber(extendedData?.volume_data?.volume)}
              </div>
              <div className="detail-item">
                <strong>Durchschnittsvolumen</strong>
                {formatLargeNumber(extendedData?.volume_data?.average_volume)}
              </div>
              <div className="detail-item">
                <strong>10-Tage Durchschnitt</strong>
                {formatLargeNumber(extendedData?.volume_data?.average_volume_10days)}
              </div>
            </div>
          </div>

          {/* Risk Metrics Section */}
          <div className="data-section">
            <h3>⚠️ Volatilität & Risiko</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>Beta</strong>
                {formatNumber(extendedData?.risk_metrics?.beta)}
              </div>
              <div className="detail-item">
                <strong>30-Tage Volatilität</strong>
                {formatPercentFromDecimal(extendedData?.risk_metrics?.volatility_30d)}
              </div>
              <div className="detail-item">
                <strong>Aktien im Umlauf</strong>
                {formatLargeNumber(extendedData?.risk_metrics?.shares_outstanding)}
              </div>
              <div className="detail-item">
                <strong>Free Float</strong>
                {formatLargeNumber(extendedData?.risk_metrics?.float_shares)}
              </div>
              <div className="detail-item">
                <strong>Insider-Anteil</strong>
                {formatPercentFromDecimal(extendedData?.risk_metrics?.held_percent_insiders)}
              </div>
              <div className="detail-item">
                <strong>Institutionsanteil</strong>
                {formatPercentFromDecimal(extendedData?.risk_metrics?.held_percent_institutions)}
              </div>
            </div>
          </div>

          {/* Company Info */}
          <div className="data-section">
            <h3>🏢 Unternehmensdaten</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <strong>ISIN</strong>
                {stock.isin || '-'}
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
            </div>
          </div>

          {alerts.length > 0 && (
            <div className="data-section">
              <h3>🔔 Aktive Alerts</h3>
              {alerts.map((alert) => (
                <div 
                  key={alert.id} 
                  className={`alert-item ${alert.is_active ? '' : 'inactive'}`}
                >
                  <strong>{alert.alert_type}</strong> {alert.condition} {alert.threshold_value}
                  {!alert.is_active && ' (Inaktiv)'}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default StockDetailModal;

import React, { useState, useEffect, useCallback } from 'react';
import CalculatedMetricsTab from './CalculatedMetricsTab';
import AnalystTab from './AnalystTab';
import SeasonalityTab from './SeasonalityTab';
import StockChart from './StockChart';
import AlertModal from './AlertModal';
import { getCurrencyForStock, getUnitForAlertType, getAlertTypeLabel, getConditionLabel, formatNumber } from '../utils/currencyUtils';
import { useAlerts } from '../hooks/useAlerts';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

function StockDetailModal({ stock, onClose }) {
  const { alerts, loadAlerts, toggleAlert, deleteAlert } = useAlerts(stock.id);
  const [extendedData, setExtendedData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('chart'); // 'chart', 'fundamentals', 'analysis', 'investment', 'company'
  const [alertModalConfig, setAlertModalConfig] = useState(null); // { mode: 'create' | 'edit', alert: null | Alert }

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

  const handleDeleteAlert = async (alertId) => {
    await deleteAlert(alertId);
  };

  const handleToggleAlert = async (alert) => {
    await toggleAlert(alert);
  };

  useEffect(() => {
    loadAlerts();
    loadExtendedData();
  }, [loadAlerts, loadExtendedData]);

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
          
          {/* Tab Navigation */}
          <div className="tab-navigation">
            <button 
              className={`tab-button ${activeTab === 'chart' ? 'active' : ''}`}
              onClick={() => setActiveTab('chart')}
            >
              📈 Chart
            </button>
            <button 
              className={`tab-button ${activeTab === 'fundamentals' ? 'active' : ''}`}
              onClick={() => setActiveTab('fundamentals')}
            >
              🔢 Fundamentaldaten
            </button>
            <button 
              className={`tab-button ${activeTab === 'analysis' ? 'active' : ''}`}
              onClick={() => setActiveTab('analysis')}
            >
              📋 Auswertung
            </button>
            <button 
              className={`tab-button ${activeTab === 'investment' ? 'active' : ''}`}
              onClick={() => setActiveTab('investment')}
            >
              🎯 Investment
            </button>
            <button
              key="Saisonalität"
              className={`tab-button${activeTab === 'saisonalität' ? ' active' : ''}`}
              onClick={() => setActiveTab('saisonalität')}
            >
              🌦️ Saisonalität
            </button>
            <button
              key="Analysten"
              className={`tab-button${activeTab === 'analysten' ? ' active' : ''}`}
              onClick={() => setActiveTab('analysten')}
            >
              🧑 Analysten
            </button>
            <button 
              className={`tab-button ${activeTab === 'company' ? 'active' : ''}`}
              onClick={() => setActiveTab('company')}
            >
              🏢 Unternehmensinfos
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {/* CHART TAB */}
            {activeTab === 'chart' && (
              <div className="tab-panel">
                <StockChart stock={stock} isEmbedded={true} />
              </div>
            )}

            {/* FUNDAMENTALDATEN TAB */}
            {activeTab === 'fundamentals' && (
              <div className="tab-panel">
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

                {/* Dividend Section */}
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
              </div>
            )}

            {/* AUSWERTUNG (STATISTICS) TAB */}
            {activeTab === 'analysis' && (
              <div className="tab-panel">
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

                {/* Calculated Metrics */}
                <CalculatedMetricsTab stockId={stock.id} />
              </div>
            )}

            {/* SAISONALITÄT TAB */}
            {activeTab === 'saisonalität' && (
              <div className="tab-panel">
                <SeasonalityTab stockId={stock.id} />
              </div>
            )}

            {/* ANALYSTEN TAB */}
            {activeTab === 'analysten' && (
              <div className="tab-panel">
                <AnalystTab stockId={stock.id} />
              </div>
            )}

            {/* INVESTMENT TAB */}
            {activeTab === 'investment' && (
              <div className="tab-panel">
                {/* Observation Reasons */}
                {stock.observation_reasons && stock.observation_reasons.length > 0 && (
                  <div className="data-section">
                    <h3>💡 Beobachtungsgründe</h3>
                    <div className="observation-reasons">
                      {stock.observation_reasons.map((reason, index) => (
                        <div key={index} className="reason-tag">
                          {reason}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Observation Notes */}
                {stock.observation_notes && (
                  <div className="data-section">
                    <h3>📝 Bemerkungen</h3>
                    <div className="observation-notes">
                      <p>{stock.observation_notes}</p>
                    </div>
                  </div>
                )}

                {/* Price Alerts */}
                <div className="data-section">
                  <div className="section-header-with-action">
                    <h3>🔔 Kursalarme</h3>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => setAlertModalConfig({ mode: 'create', alert: null })}
                    >
                      ➕ Alarm hinzufügen
                    </button>
                  </div>
                  {alerts.length > 0 ? (
                    <div className="alerts-list">
                      {alerts.map((alert) => {
                        // Einheit basierend auf Alarm-Typ bestimmen
                        const unit = getUnitForAlertType(alert.alert_type, stock);
                        
                        return (
                        <div 
                          key={alert.id} 
                          className={`alert-item ${alert.is_active ? 'active' : 'inactive'}`}
                        >
                          <div className="alert-header">
                            <span className="alert-type-badge">{getAlertTypeLabel(alert.alert_type)}</span>
                            <span className={`alert-status ${alert.is_active ? 'status-active' : 'status-inactive'}`}>
                              {alert.is_active ? '✓ Aktiv' : '○ Inaktiv'}
                            </span>
                          </div>
                          <div className="alert-details">
                            <div className="alert-condition">
                              <strong>{getConditionLabel(alert.condition)}</strong> 
                              {alert.alert_type !== 'ma_cross' && (
                                <> {formatNumber(alert.threshold_value, 2)}{unit && ` ${unit}`}</>
                              )}
                              {alert.timeframe_days && (
                                <span style={{ marginLeft: '5px', color: '#666', fontSize: '0.9em' }}>
                                  ({alert.timeframe_days} Tag{alert.timeframe_days > 1 ? 'e' : ''})
                                </span>
                              )}
                            </div>
                            {alert.last_triggered && (
                              <div className="alert-triggered" style={{ fontSize: '0.85em', color: '#ff9800', marginTop: '4px' }}>
                                🔔 Zuletzt ausgelöst: {new Date(alert.last_triggered).toLocaleString('de-DE')}
                                {alert.trigger_count > 1 && ` (${alert.trigger_count}x)`}
                              </div>
                            )}
                            {alert.notes && (
                              <div className="alert-note">
                                💬 {alert.notes}
                              </div>
                            )}
                            {alert.expiry_date && (
                              <div className="alert-expiry">
                                ⏰ Läuft ab: {new Date(alert.expiry_date).toLocaleDateString('de-DE')}
                              </div>
                            )}
                          </div>
                          <div className="alert-actions">
                            <button
                              className="btn btn-sm btn-secondary"
                              onClick={() => handleToggleAlert(alert)}
                            >
                              {alert.is_active ? '⏸️ Deaktivieren' : '▶️ Aktivieren'}
                            </button>
                            <button
                              className="btn btn-sm btn-info"
                              onClick={() => setAlertModalConfig({ mode: 'edit', alert })}
                            >
                              ✏️ Bearbeiten
                            </button>
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => handleDeleteAlert(alert.id)}
                            >
                              🗑️ Löschen
                            </button>
                          </div>
                        </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="no-data">Keine Kursalarme gesetzt</p>
                  )}
                </div>
              </div>
            )}

            {/* COMPANY INFO TAB */}
            {activeTab === 'company' && (
              <div className="tab-panel">
                {/* Business Summary */}
                {extendedData?.business_summary && (
                  <div className="data-section">
                    <h3>📄 Unternehmensbeschreibung</h3>
                    <div className="business-summary">
                      <p>{extendedData.business_summary}</p>
                    </div>
                  </div>
                )}

                {/* Company Info */}
                <div className="data-section">
                  <h3>🏢 Unternehmensdaten</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <strong>Ticker-Symbol</strong>
                      {stock.ticker_symbol}
                    </div>
                    <div className="detail-item">
                      <strong>ISIN</strong>
                      {stock.isin || '-'}
                    </div>
                    <div className="detail-item">
                      <strong>Name</strong>
                      {stock.name}
                    </div>
                    <div className="detail-item">
                      <strong>Land</strong>
                      {stock.country || '-'}
                    </div>
                    <div className="detail-item">
                      <strong>Sektor</strong>
                      {stock.sector || '-'}
                    </div>
                    <div className="detail-item">
                      <strong>Branche</strong>
                      {stock.industry || '-'}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Alert Modal */}
      {alertModalConfig && (
        <AlertModal
          stock={stock}
          existingAlert={alertModalConfig.alert}
          onClose={() => setAlertModalConfig(null)}
          onAlertSaved={async () => {
            await loadAlerts();
            setAlertModalConfig(null);
          }}
        />
      )}
    </div>
  );
}

export default StockDetailModal;


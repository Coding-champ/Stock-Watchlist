import React, { useState, useEffect, useCallback } from 'react';
import CalculatedMetricsTab from './CalculatedMetricsTab';
import AnalystTab from './AnalystTab';
import '../styles/skeletons.css';
import SeasonalityTab from './SeasonalityTab';
import StockChart from './StockChart';
import FundamentalsTimeSeriesTab from './FundamentalsTimeSeriesTab';
import SectorComparisonTab from './SectorComparisonTab';
import AlertModal from './AlertModal';
import { getUnitForAlertType, getAlertTypeLabel, getConditionLabel, formatNumber, formatPrice } from '../utils/currencyUtils';
import { useAlerts } from '../hooks/useAlerts';
import { useQueryClient } from '@tanstack/react-query';

import API_BASE from '../config';
import { OBSERVATION_REASON_OPTIONS } from './ObservationFields';

function StockDetailPage({ stock, onBack }) {
  const [chartLatestVwap, setChartLatestVwap] = useState(null);
  const { alerts, loadAlerts, toggleAlert, deleteAlert } = useAlerts(stock.id);
  const queryClient = useQueryClient();
  const [extendedData, setExtendedData] = useState(null);
  const [latestFundamentals, setLatestFundamentals] = useState(null);
  const [irWebsite, setIrWebsite] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('chart');
  const [alertModalConfig, setAlertModalConfig] = useState(null);

  const loadExtendedData = useCallback(async () => {
    try {
      const detailedUrl = `${API_BASE}/stocks/${stock.id}/detailed`;
      const data = await queryClient.fetchQuery(['api', detailedUrl], async () => {
        const r = await fetch(detailedUrl);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }, { staleTime: 300000 });

      setExtendedData(data.extended_data);
      const website = data.ir_website || data.extended_data?.website || data.extended_data?.info_full?.website || data.extended_data?.business_summary?.website || null;
      setIrWebsite(website);

      try {
        const fundamentalsUrl = `${API_BASE}/stocks/${stock.id}/fundamentals?periods=1`;
        const fJson = await queryClient.fetchQuery(['api', fundamentalsUrl], async () => {
          const rr = await fetch(fundamentalsUrl);
          if (!rr.ok) throw new Error(`HTTP ${rr.status}`);
          return rr.json();
        }, { staleTime: 300000 });
        if (fJson && Array.isArray(fJson.data) && fJson.data.length > 0) {
          setLatestFundamentals(fJson.data[0]);
        }
      } catch (e) {
        // non-fatal
      }

    } catch (error) {
      console.error('Error loading extended stock data:', error);
    } finally {
      setLoading(false);
    }
  }, [stock.id, queryClient]);

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

  const changeInfo = React.useMemo(() => {
    const current = extendedData?.price_data?.current_price;
    const prev = extendedData?.price_data?.previous_close ?? extendedData?.price_data?.previousClose ?? extendedData?.price_data?.previous_close_price ?? null;
    if (typeof current === 'number' && typeof prev === 'number') {
      const absolute = current - prev;
      const relative = prev !== 0 ? (absolute / prev) * 100 : 0;
      return { absolute, relative };
    }
    return null;
  }, [extendedData]);

  const [fetchedChangeInfo, setFetchedChangeInfo] = useState(null);
  useEffect(() => {
    let mounted = true;
    const controller = new AbortController();

    const needsFetch = !changeInfo && stock && stock.id;
    if (!needsFetch) return undefined;

    (async () => {
      try {
        const resp = await fetch(`${API_BASE}/stock-data/${stock.id}?limit=2`, { signal: controller.signal });
        if (!resp.ok) return;
        const json = await resp.json();
        const raw = Array.isArray(json) ? json : [];
        const filtered = raw.filter((e) => e && e.current_price != null);
        const ordered = filtered.slice().sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        if (ordered.length >= 2 && mounted) {
          const first = Number(ordered[ordered.length - 2].current_price);
          const last = Number(ordered[ordered.length - 1].current_price);
          if (!Number.isNaN(first) && !Number.isNaN(last)) {
            const absolute = last - first;
            const relative = first !== 0 ? (absolute / first) * 100 : 0;
            setFetchedChangeInfo({ absolute, relative });
          }
        }
      } catch (e) {
        // ignore
      }
    })();

    return () => {
      mounted = false;
      controller.abort();
    };
  }, [changeInfo, stock]);

  const formatLargeNumber = (value) => {
    if (value === null || value === undefined) return '-';
    const numVal = (typeof value === 'number') ? value : (Number(String(value).replace(/[,\s]/g, '')));
    if (typeof numVal === 'number' && !Number.isNaN(numVal)) {
      if (value >= 1e12) return (value / 1e12).toFixed(2) + 'T';
      if (value >= 1e9) return (value / 1e9).toFixed(2) + 'B';
      if (value >= 1e6) return (value / 1e6).toFixed(2) + 'M';
      if (value >= 1e3) return (value / 1e3).toFixed(2) + 'K';
      return numVal.toFixed(2);
    }
    return '-';
  };

  const formatPercentAsIs = (value) => formatNumber(value, 2, '%');
  const formatPercentFromDecimal = (value) => formatNumber(value * 100, 2, '%');
  const formatDate = (timestamp) => {
    if (!timestamp) return '-';
    try {
      if (typeof timestamp === 'number') return new Date(timestamp * 1000).toLocaleDateString('de-DE');
      return new Date(timestamp).toLocaleDateString('de-DE');
    } catch (e) {
      return '-';
    }
  };

  // Defensive fallback: some API responses may place risk metrics under different keys
  const riskMetrics = extendedData?.risk_metrics ?? extendedData?.riskMetrics ?? extendedData?.riskMetricsSummary ?? extendedData?.statistics?.risk_metrics ?? extendedData?.statistics ?? {};

  if (loading) {
    return (
      <section className="panel">
        <div className="panel__header">
          <div className="panel__title-group">
            <h2 className="panel__title">Lade Aktie…</h2>
          </div>
        </div>
        <div className="panel__body">
          <div className="loading">Lade erweiterte Daten…</div>
        </div>
      </section>
    );
  }

  return (
    <section className="panel panel--stock-detail">
      <div className="panel__header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button className="btn btn--ghost" onClick={() => onBack && onBack()} aria-label="Zurück">‹ Zurück</button>
          <div>
            <h2 className="panel__title">{stock.name} ({stock.ticker_symbol})</h2>
            <p className="panel__subtitle">Details und Kennzahlen</p>
          </div>
        </div>
      </div>

      <div className="panel__body">
        <div className="stock-detail-content">
          <div className="stock-header">
            <h2>{stock.name} ({stock.ticker_symbol})</h2>
            {
              (() => {
                const info = changeInfo ?? fetchedChangeInfo;
                const cls = info ? (info.absolute >= 0 ? 'positive' : 'negative') : '';
                return (
                  <div className={`stock-change-badge ${cls}`} role="status" aria-live="polite">
                    <div className="stock-change-label">Veränderung:</div>
                    <div className="stock-change-values">
                      {info ? (
                        <>{info.absolute >= 0 ? '+' : ''}{formatPrice(info.absolute, stock, 2)} ({info.relative >= 0 ? '+' : ''}{info.relative.toFixed(2)}%)</>
                      ) : (
                        <span className="stock-change-placeholder">—</span>
                      )}
                    </div>
                  </div>
                );
              })()
            }
          </div>

          {/* Tab Navigation and content (same as modal tabs) */}
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
              className={`tab-button ${activeTab === 'fundamentals_ts' ? 'active' : ''}`}
              onClick={() => setActiveTab('fundamentals_ts')}
            >
              Fundamentaldaten (Zeitreihe)
            </button>
            <button
              className={`tab-button ${activeTab === 'sector_comparison' ? 'active' : ''}`}
              onClick={() => setActiveTab('sector_comparison')}
            >
              Branchenvergleich
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

          <div className="tab-content">
            {activeTab === 'chart' && (
              <div className="tab-panel">
                <StockChart stock={stock} isEmbedded={false} onLatestVwap={setChartLatestVwap} />
              </div>
            )}

            {activeTab === 'fundamentals' && (
              <div className="tab-panel">
                {/* Price Data Section */}
                <div className="data-section">
                  <h3>📈 Preisdaten</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <strong>Aktueller Kurs</strong>
                      {formatPrice(extendedData?.price_data?.current_price, stock)}
                    </div>
                    <div className="detail-item">
                      <strong>Tageshoch</strong>
                      {formatPrice(extendedData?.price_data?.day_high, stock)}
                    </div>
                    <div className="detail-item">
                      <strong>Tagestief</strong>
                      {formatPrice(extendedData?.price_data?.day_low, stock)}
                    </div>
                    <div className="detail-item">
                      <strong>52-Wochen Hoch</strong>
                      {formatPrice(extendedData?.price_data?.fifty_two_week_high, stock)}
                    </div>
                    <div className="detail-item">
                      <strong>52-Wochen Tief</strong>
                      {formatPrice(extendedData?.price_data?.fifty_two_week_low, stock)}
                    </div>
                    <div className="detail-item">
                      <strong>50-Tage SMA</strong>
                      {formatPrice(extendedData?.price_data?.fifty_day_average, stock)}
                    </div>
                    <div className="detail-item">
                      <strong>200-Tage SMA</strong>
                      {formatPrice(extendedData?.price_data?.two_hundred_day_average, stock)}
                    </div>
                    <div className="detail-item">
                      <strong>All-Time High</strong>
                      {formatPrice(extendedData?.price_data?.all_time_high, stock)}
                    </div>
                    <div className="detail-item">
                      <strong>All-Time Low</strong>
                      {formatPrice(extendedData?.price_data?.all_time_low, stock)}
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
                      <strong>Enterprise Value</strong>
                      {formatLargeNumber(extendedData?.enterprise_value ?? extendedData?.financial_ratios?.enterprise_value)}
                    </div>
                    <div className="detail-item">
                      <strong>PEG-Ratio</strong>
                      {formatNumber(extendedData?.financial_ratios?.peg_ratio)}
                    </div>
                    <div className="detail-item">
                      <strong>Kurs-Gewinn (P/E)</strong>
                      {formatNumber(extendedData?.financial_ratios?.pe_ratio)}
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
                      <strong>EPS (TTM)</strong>
                      {formatNumber(latestFundamentals?.eps_basic ?? extendedData?.financial_ratios?.eps)}
                    </div>
                    <div className="detail-item">
                      <strong>Buchwert je Aktie</strong>
                      {formatNumber(latestFundamentals?.book_value ?? extendedData?.book_value)}
                    </div>
                    <div className="detail-item">
                      <strong>Gewinnwachstum</strong>
                      {formatPercentFromDecimal(latestFundamentals?.earnings_growth ?? extendedData?.financial_ratios?.earnings_growth ?? extendedData?.earnings_growth)}
                    </div>
                    <div className="detail-item">
                      <strong>Umsatzwachstum</strong>
                      {formatPercentFromDecimal(latestFundamentals?.revenue_growth ?? extendedData?.financial_ratios?.revenue_growth ?? extendedData?.revenue_growth)}
                    </div>
                  </div>
                </div>

                {/* Income Statement (GuV) */}
                <div className="data-section">
                  <h3>📈 GuV (Ergebnisrechnung)</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <strong>Umsatz</strong>
                      {formatLargeNumber(latestFundamentals?.revenue ?? extendedData?.financial_ratios?.total_revenue ?? extendedData?.total_revenue)}
                    </div>
                    <div className="detail-item">
                      <strong>Bruttogewinn</strong>
                      {formatLargeNumber(latestFundamentals?.gross_profit ?? extendedData?.gross_profits ?? extendedData?.financial_ratios?.gross_profit)}
                    </div>
                    <div className="detail-item">
                      <strong>EBITDA</strong>
                      {formatLargeNumber(latestFundamentals?.ebitda ?? extendedData?.ebitda)}
                    </div>
                    <div className="detail-item">
                      <strong>Nettogewinn</strong>
                      {formatLargeNumber(latestFundamentals?.earnings ?? extendedData?.net_income_to_common)}
                    </div>
                  </div>
                </div>

                {/* Balance Sheet (Bilanz) */}
                <div className="data-section">
                  <h3>🏦 Bilanz</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <strong>Gesamtkapital</strong>
                      {formatLargeNumber(latestFundamentals?.total_assets ?? extendedData?.balance_sheet?.total_assets ?? extendedData?.total_assets)}
                    </div>
                    <div className="detail-item">
                      <strong>Eigenkapital</strong>
                      {formatLargeNumber(latestFundamentals?.shareholders_equity ?? extendedData?.balance_sheet?.shareholders_equity ?? extendedData?.shareholders_equity)}
                    </div>
                    <div className="detail-item">
                      <strong>Gesamtverschuldung</strong>
                      {formatLargeNumber(latestFundamentals?.total_liabilities ?? latestFundamentals?.total_debt ?? extendedData?.cashflow_data?.total_debt)}
                    </div>
                    <div className="detail-item">
                      <strong>Liquide Mittel</strong>
                      {formatLargeNumber(latestFundamentals?.total_cash ?? extendedData?.cashflow_data?.total_cash)}
                    </div>
                    <div className="detail-item">
                      <strong>Gesamtkapitalrendite (ROA)</strong>
                      {formatPercentFromDecimal(extendedData?.financial_ratios?.return_on_assets)}
                    </div>
                    <div className="detail-item">
                      <strong>Eigenkapitalrendite (ROE)</strong>
                      {formatPercentFromDecimal(extendedData?.financial_ratios?.return_on_equity)}
                    </div>
                    <div className="detail-item">
                      <strong>Verschuldungsgrad</strong>
                      {formatNumber(latestFundamentals?.debt_to_equity ?? extendedData?.cashflow_data?.debt_to_equity)}
                    </div>   
                  </div>
                </div>

                {/* Cashflow Section */}
                <div className="data-section">
                  <h3>💰 Cashflow</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <strong>Operativer Cashflow</strong>
                      {formatLargeNumber(latestFundamentals?.operating_cashflow ?? extendedData?.cashflow_data?.operating_cashflow)}
                    </div>
                    <div className="detail-item">
                      <strong>Freier Cashflow</strong>
                      {formatLargeNumber(latestFundamentals?.free_cashflow ?? extendedData?.cashflow_data?.free_cashflow)}
                    </div>
                  </div>
                </div>

                {/* Margins */}
                <div className="data-section">
                  <h3> Margen (Rentabilität)</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <strong>Gewinnmarge</strong>
                      {formatPercentFromDecimal(extendedData?.financial_ratios?.profit_margins)}
                    </div>
                    <div className="detail-item">
                      <strong>Operative Marge</strong>
                      {formatPercentFromDecimal(extendedData?.financial_ratios?.operating_margins)}
                    </div>
                    <div className="detail-item">
                      <strong>Bruttomarge</strong>
                      {formatPercentFromDecimal(extendedData?.financial_ratios?.gross_margins ?? extendedData?.financial_ratios?.gross_margin)}
                    </div>
                    <div className="detail-item">
                      <strong>EBITDA-Marge</strong>
                      {formatPercentFromDecimal(extendedData?.financial_ratios?.ebitda_margins)}
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
                        {formatPrice(extendedData?.dividend_info?.dividend_rate, stock)}
                      </div>
                      <div className="detail-item">
                        <strong>Letzte Dividende</strong>
                        {formatPrice(extendedData?.dividend_info?.last_dividend_value ?? latestFundamentals?.last_dividend_value, stock)}
                      </div>
                      <div className="detail-item">
                        <strong>Letztes Dividenden-Datum</strong>
                        {formatDate(extendedData?.dividend_info?.last_dividend_date ?? latestFundamentals?.last_dividend_date)}
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

            {activeTab === 'fundamentals_ts' && (
              <div className="tab-panel">
                <FundamentalsTimeSeriesTab stockId={stock.id} />
              </div>
            )}

            {activeTab === 'sector_comparison' && (
              <div className="tab-panel">
                <SectorComparisonTab stockId={stock.id} />
              </div>
            )}

            {activeTab === 'analysis' && (
              <div className="tab-panel">
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

                <div className="data-section">
                  <h3>⚠️ Volatilität & Risiko</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <strong>Beta</strong>
                      {formatNumber(riskMetrics?.beta)}
                    </div>
                    <div className="detail-item">
                      <strong>30-Tage Volatilität</strong>
                      {formatPercentFromDecimal(riskMetrics?.volatility_30d)}
                    </div>
                    <div className="detail-item">
                      <strong>Aktien im Umlauf</strong>
                      {formatLargeNumber(riskMetrics?.shares_outstanding)}
                    </div>
                    <div className="detail-item">
                      <strong>Free Float</strong>
                      {formatLargeNumber(riskMetrics?.float_shares)}
                    </div>
                    <div className="detail-item">
                      <strong>Insider-Anteil</strong>
                      {formatPercentFromDecimal(riskMetrics?.held_percent_insiders)}
                    </div>
                    <div className="detail-item">
                      <strong>Institutionsanteil</strong>
                      {formatPercentFromDecimal(riskMetrics?.held_percent_institutions)}
                    </div>
                    <div className="detail-item" title="Anzahl der leerverkauften Aktien (ungefähr)">
                      <strong>Short Interest</strong>
                      {formatLargeNumber(riskMetrics?.short_interest)}
                    </div>
                    <div className="detail-item" title="Short Ratio: durchschnittliche Anzahl Tage, um Short-Positionen bei aktuellem Volumen zu decken">
                      <strong>Short Ratio</strong>
                      {(() => {
                        const sr = riskMetrics?.short_ratio;
                        if (sr === null || sr === undefined) return '-';
                        const num = Number(sr);
                        if (Number.isNaN(num)) return '-';
                        const isHigh = num > 5;
                        return (
                          <span style={isHigh ? { color: '#c62828', fontWeight: 600 } : {}}>
                            {formatNumber(num, 2)}{isHigh ? ' ⚠️' : ''}
                          </span>
                        );
                      })()}
                    </div>
                    <div className="detail-item" title="Prozentualer Anteil der leerverkauften Aktien (als Prozent)">
                      <strong>Short %</strong>
                      {(() => {
                        const sp = riskMetrics?.short_percent;
                        if (sp === null || sp === undefined) return '-';
                        const num = Number(sp);
                        if (Number.isNaN(num)) return '-';
                        const decimal = Math.abs(num) > 1 ? num / 100.0 : num;
                        return formatPercentFromDecimal(decimal);
                      })()}
                    </div>
                  </div>
                </div>

                <CalculatedMetricsTab stockId={stock.id} isActive={activeTab === 'analysis'} prefetch={true} chartLatestVwap={chartLatestVwap} />
              </div>
            )}

            {activeTab === 'saisonalität' && (
              <div className="tab-panel">
                <SeasonalityTab stockId={stock.id} />
              </div>
            )}

            {activeTab === 'analysten' && (
              <div className="tab-panel">
                <AnalystTab stockId={stock.id} />
              </div>
            )}

            {activeTab === 'investment' && (
              <div className="tab-panel">
                {stock.observation_reasons && stock.observation_reasons.length > 0 && (
                  <div className="data-section">
                    <h3>💡 Beobachtungsgründe</h3>
                    <div className="observation-reasons">
                      {stock.observation_reasons.map((reason, index) => {
                        const label = OBSERVATION_REASON_OPTIONS.find(opt => opt.value === reason)?.label || reason;
                        return (
                          <div key={index} className="reason-tag">
                            {label}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {stock.observation_notes && (
                  <div className="data-section">
                    <h3>📝 Bemerkungen</h3>
                    <div className="observation-notes">
                      <p>{stock.observation_notes}</p>
                    </div>
                  </div>
                )}

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

            {activeTab === 'company' && (
              <div className="tab-panel">
                {extendedData?.business_summary && (
                  <div className="data-section">
                    <h3>📄 Unternehmensbeschreibung</h3>
                    <div className="business-summary">
                      <p>{extendedData.business_summary}</p>
                    </div>
                  </div>
                )}

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
                    <div className="detail-item">
                      <strong>Investor Relations</strong>
                      {<a href={irWebsite} target="_blank" rel="noreferrer">{irWebsite}</a> || '-'}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

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
      </div>
    </section>
  );
}

export default StockDetailPage;

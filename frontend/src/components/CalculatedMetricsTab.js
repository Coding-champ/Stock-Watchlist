import React, { useState, useEffect, useCallback, useRef } from 'react';
import MetricTooltip from './MetricTooltip';
import './CalculatedMetrics.css';
import '../styles/skeletons.css';

import API_BASE from '../config';
import { useQueryClient } from '@tanstack/react-query';
import { formatPrice } from '../utils/currencyUtils';

/**
 * CalculatedMetricsTab Component
 * Displays comprehensive calculated metrics for a stock
 */
function CalculatedMetricsTab({ stockId, isActive = true, prefetch = false, chartLatestVwap = null }) {
  // Debug: log mount/prop changes so devtools can confirm the component is active
  // Remove these logs after verification
  useEffect(() => {
    // mount props change - no debug logging in production
  }, [stockId, isActive, prefetch, chartLatestVwap]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [vwapData, setVwapData] = useState(null);
  const [vwapFallbackUsed, setVwapFallbackUsed] = useState(false);
  const [animateReady, setAnimateReady] = useState(false);

  // Ref to store the current AbortController so we can cancel in-flight requests
  const controllerRef = useRef(null);
  const queryClient = useQueryClient();

  const loadMetrics = useCallback(async () => {
    // Abort previous in-flight request to avoid race conditions
    if (controllerRef.current) {
      try { controllerRef.current.abort(); } catch (e) { /* ignore */ }
      controllerRef.current = null;
    }

    const controller = new AbortController();
    controllerRef.current = controller;
    const { signal } = controller;

    setLoading(true);
    setError(null);

  // load initiated

    try {
      // Load calculated metrics via React Query to enable caching/dedupe
      const calcUrl = `${API_BASE}/stock-data/${stockId}/calculated-metrics`;
      const data = await queryClient.fetchQuery(['api', calcUrl], async () => {
        const r = await fetch(calcUrl);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }, { staleTime: 60000 });
      setMetrics(data);

      // If SMA values are missing from calculated-metrics, try to fetch them from
      // the technical-indicators endpoint and merge the latest value into metrics
      {
        const hasSma50 = data?.metrics?.basic_indicators?.sma_50 !== undefined && data?.metrics?.basic_indicators?.sma_50 !== null;
        const hasSma200 = data?.metrics?.basic_indicators?.sma_200 !== undefined && data?.metrics?.basic_indicators?.sma_200 !== null;
        if (!hasSma50 || !hasSma200) {
          const smaUrl = `${API_BASE}/stock-data/${stockId}/technical-indicators?period=1y&indicators=sma_50&indicators=sma_200`;
          try {
            const smaJson = await queryClient.fetchQuery(['api', smaUrl], async () => {
              const r = await fetch(smaUrl);
              if (!r.ok) throw new Error(`HTTP ${r.status}`);
              return r.json();
            }, { staleTime: 60000 });

            const extractLatestNumber = (maybeArray) => {
              if (!maybeArray) return null;
              if (Array.isArray(maybeArray) && maybeArray.length > 0) {
                for (let i = maybeArray.length - 1; i >= 0; i--) {
                  const v = maybeArray[i];
                  if (v !== null && v !== undefined && typeof v === 'number' && !Number.isNaN(v)) return v;
                  if (v && typeof v === 'object') {
                    const candidate = v.value ?? v.y ?? v.sma ?? null;
                    if (typeof candidate === 'number' && !Number.isNaN(candidate)) return candidate;
                  }
                }
              }
              if (typeof maybeArray === 'number' && !Number.isNaN(maybeArray)) return maybeArray;
              return null;
            };

            const sma50Val = extractLatestNumber(smaJson?.indicators?.sma_50);
            const sma200Val = extractLatestNumber(smaJson?.indicators?.sma_200);
            if (sma50Val !== null || sma200Val !== null) {
              setMetrics(prev => {
                const next = { ...(prev || {} ) };
                next.metrics = { ...(next.metrics || {} ) };
                next.metrics.basic_indicators = { ...(next.metrics.basic_indicators || {} ) };
                if (sma50Val !== null) next.metrics.basic_indicators.sma_50 = sma50Val;
                if (sma200Val !== null) next.metrics.basic_indicators.sma_200 = sma200Val;
                return next;
              });
            }
          } catch (smaErr) {
            // ignore SMA fetch errors
          }
        }
      }

      // Load VWAP from technical indicators (use same signal so both requests can be aborted)
      const vwapUrl = `${API_BASE}/stock-data/${stockId}/technical-indicators?period=1y&indicators=vwap`;
      const vwapJson = await queryClient.fetchQuery(['api', vwapUrl], async () => {
        const r = await fetch(vwapUrl);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }, { staleTime: 60000 });
      if (vwapJson) {

        // Helper: try to extract the last numeric value from different shapes
        const extractLatestNumber = (maybeArray) => {
          if (!maybeArray) return null;
          if (Array.isArray(maybeArray) && maybeArray.length > 0) {
            // find last defined numeric element (skip null/undefined)
            for (let i = maybeArray.length - 1; i >= 0; i--) {
              const v = maybeArray[i];
              if (v !== null && v !== undefined && typeof v === 'number' && !Number.isNaN(v)) return v;
              // allow objects like {value: 123}
              if (v && typeof v === 'object') {
                const candidate = v.value ?? v.y ?? v.vwap ?? null;
                if (typeof candidate === 'number' && !Number.isNaN(candidate)) return candidate;
              }
            }
          }
          // if it's a single number
          if (typeof maybeArray === 'number' && !Number.isNaN(maybeArray)) return maybeArray;
          return null;
        };

        let currentVwap = null;
        if (vwapJson.indicators) {
          // indicators.vwap could be array or object
          currentVwap = extractLatestNumber(vwapJson.indicators.vwap);
        }

        // Fallback: if the technical-indicators endpoint didn't include VWAP,
        // try to compute a simple VWAP from recent price history (client-side)
        // using the /stocks/<id>/price-history endpoint (limit last 20 days).
        let fallbackUsed = false;
        if (currentVwap === null) {
          // Prefer computing VWAP from the same chart data the StockChart uses
          // to ensure consistency between Chart and Auswertung tabs.
          try {
            const chartUrl = `${API_BASE}/stock-data/${stockId}/chart?period=1y&include_volume=true`;
            const chartJson = await queryClient.fetchQuery(['api', chartUrl], async () => {
              const r = await fetch(chartUrl, { signal });
              if (!r.ok) throw new Error(`HTTP ${r.status}`);
              return r.json();
            }, { staleTime: 60000 });

            const closes = Array.isArray(chartJson.close) ? chartJson.close : (chartJson?.close || []);
            const volumes = Array.isArray(chartJson.volume) ? chartJson.volume : (chartJson?.volume || []);
            // take last up to 20 entries
            const n = Math.min(20, closes.length, volumes.length);
            let volSum = 0;
            let pwSum = 0;
            for (let i = closes.length - n; i < closes.length; i++) {
              const close = closes[i];
              const vol = volumes[i];
              if (typeof close === 'number' && typeof vol === 'number' && vol > 0) {
                pwSum += close * vol;
                volSum += vol;
              }
            }
            if (volSum > 0) {
              currentVwap = pwSum / volSum;
              fallbackUsed = true;
            }
          } catch (err) {
            // ignore and try older price-history endpoint next
          }

          // If chart-based fallback failed, fall back to the legacy price-history endpoint
          if (currentVwap === null) {
            try {
              const histUrl = `${API_BASE}/stocks/${stockId}/price-history?limit=20`;
              const histJson = await queryClient.fetchQuery(['api', histUrl], async () => {
                const r = await fetch(histUrl, { signal });
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
              }, { staleTime: 60000 });

              const priceRecords = Array.isArray(histJson.data) ? histJson.data : (histJson || []).slice ? histJson : [];
              let volSum = 0;
              let pwSum = 0;
              for (const r of priceRecords) {
                const close = r?.close ?? r?.price ?? r?.close_price ?? null;
                const vol = r?.volume ?? r?.vol ?? null;
                if (typeof close === 'number' && typeof vol === 'number' && vol > 0) {
                  pwSum += close * vol;
                  volSum += vol;
                }
              }
              if (volSum > 0) {
                currentVwap = pwSum / volSum;
                fallbackUsed = true;
              }
            } catch (err) {
              // ignore errors for the fallback; we'll simply not show VWAP
            }
          }
        }

        // Try multiple places for current price: vwapJson.close, vwapJson.close_price, or previously fetched metrics
        let currentPrice = extractLatestNumber(vwapJson.close) || extractLatestNumber(vwapJson.close_price) || null;
        if (!currentPrice && data && data.metrics && data.metrics.basic_indicators && typeof data.metrics.basic_indicators.current_price === 'number') {
          currentPrice = data.metrics.basic_indicators.current_price;
        }

        // If the parent (Chart) provided a latest VWAP, prefer that to ensure both tabs match
        if (typeof chartLatestVwap === 'number' && !Number.isNaN(chartLatestVwap)) {
          currentVwap = chartLatestVwap;
          // mark fallbackUsed false because chart is authoritative
          fallbackUsed = false;
        }

        if (currentVwap !== null) {
          const payload = { current: currentVwap, currentPrice };
          setVwapData(payload);
          setVwapFallbackUsed(fallbackUsed);
          // VWAP data set (no debug log)
        }
      }

      setLastUpdated(new Date());
    } catch (err) {
      // Don't treat AbortError as an error state the user needs to see
      if (err && err.name === 'AbortError') {
        // aborted - no further state updates
        // console.log('loadMetrics aborted');
        return;
      }
      console.error('Error loading calculated metrics:', err);
      setError('Fehler beim Laden der Metriken. Bitte versuche es später erneut.');
    } finally {
      // Only update loading state if not aborted
      if (!signal.aborted) setLoading(false);
      if (controllerRef.current === controller) controllerRef.current = null;
    }
  }, [stockId, chartLatestVwap, queryClient]);

  // Load metrics when component becomes active (e.g. when the "Auswertung" tab is selected).
  // Keep default isActive = true for backward compatibility so behavior is unchanged
  // when parent doesn't pass the prop.
  useEffect(() => {
    // Start loading when either the tab becomes active or prefetch is requested
    if (isActive || prefetch) {
      loadMetrics();
    } else {
      // If the tab becomes inactive and prefetch isn't requested, abort any in-flight request.
      if (controllerRef.current) {
        try { controllerRef.current.abort(); } catch (e) { /* ignore */ }
        controllerRef.current = null;
      }
    }

    // Cleanup on unmount: ensure any in-flight request is aborted
  }, [isActive, prefetch, loadMetrics]);

  useEffect(() => {
    return () => {
      if (controllerRef.current) {
        try { controllerRef.current.abort(); } catch (e) { /* ignore */ }
        controllerRef.current = null;
      }
    };
  }, []);

  // Trigger a short fade-in when loading completes
  useEffect(() => {
    let t;
    if (!loading) {
      // small delay so skeleton unmounts before fade-in
      t = setTimeout(() => setAnimateReady(true), 60);
    } else {
      setAnimateReady(false);
    }
    return () => clearTimeout(t);
  }, [loading]);

  const formatNumber = (value, decimals = 2, suffix = '') => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      return value.toFixed(decimals) + suffix;
    }
    return '-';
  };

  // Use centralized formatPrice to ensure correct currency symbol per stock/exchange
  const formatCurrency = (value) => formatPrice(value, { id: stockId });

  const getScoreClass = (score) => {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'moderate';
    if (score >= 20) return 'poor';
    return 'bad';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Exzellent 🟢';
    if (score >= 60) return 'Gut 🟢';
    if (score >= 40) return 'Moderat 🟡';
    if (score >= 20) return 'Schwach 🟠';
    return 'Schlecht 🔴';
  };

  const getTrendIcon = (value, threshold = 0) => {
    if (value === null || value === undefined) return '→';
    if (value > threshold) return '📈';
    if (value < threshold) return '📉';
    return '→';
  };

  const getRiskRatingColor = (rating) => {
    const ratingColors = {
      'low': '#22c55e',
      'moderate': '#eab308',
      'high': '#f97316',
      'very_high': '#ef4444'
    };
    return ratingColors[rating] || '#6c757d';
  };

  const getRiskRatingLabel = (rating) => {
    const labels = {
      'low': 'Niedrig',
      'moderate': 'Moderat',
      'high': 'Hoch',
      'very_high': 'Sehr Hoch'
    };
    return labels[rating] || rating;
  };

  const formatTimeAgo = (date) => {
    if (!date) return '';
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'gerade eben';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `vor ${minutes} Min.`;
    const hours = Math.floor(minutes / 60);
    return `vor ${hours} Std.`;
  };

  if (loading) {
    // Show a non-blocking skeleton loader to avoid a jarring spinner
    return (
      <div className="calculated-metrics-container">
        <div className="calculated-metrics-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="skeleton skeleton-title" style={{ width: 160, height: 22 }} />
            <div className="skeleton skeleton-subtitle" style={{ width: 90 }} />
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <div className="skeleton skeleton-line" style={{ width: 90, height: 34, borderRadius: 6 }} />
            <div className="skeleton skeleton-line" style={{ width: 120, height: 14 }} />
          </div>
        </div>

        <div className="metrics-phase-section">
          <div className="phase-section-header phase-1">
            <div className="skeleton" style={{ width: 140, height: 18, borderRadius: 6 }} />
          </div>
          <div className="phase-section-body">
            <div className="skeleton-line" style={{ width: '60%' }} />
            <div className="skeleton-line" style={{ width: '40%' }} />
            <div style={{ height: 12 }} />
            <div className="indicator-row">
              <div className="indicator-label"><div className="skeleton-line" style={{ width: 140 }} /></div>
              <div className="indicator-value"><div className="skeleton-line" style={{ width: 120 }} /></div>
            </div>
            <div className="indicator-row">
              <div className="indicator-label"><div className="skeleton-line" style={{ width: 140 }} /></div>
              <div className="indicator-value"><div className="skeleton-line" style={{ width: 120 }} /></div>
            </div>
          </div>
        </div>

        <div className="metrics-phase-section">
          <div className="phase-section-header phase-2">
            <div className="skeleton" style={{ width: 140, height: 18, borderRadius: 6 }} />
          </div>
          <div className="phase-section-body">
            <div className="skeleton-grid">
              <div className="skeleton-card">
                <div className="skeleton-line" style={{ width: '50%', height: 18 }} />
                <div style={{ height: 12 }} />
                <div className="skeleton-line" style={{ width: '80%', height: 36 }} />
              </div>
              <div className="skeleton-card">
                <div className="skeleton-line" style={{ width: '50%', height: 18 }} />
                <div style={{ height: 12 }} />
                <div className="skeleton-line" style={{ width: '80%', height: 36 }} />
              </div>
              <div className="skeleton-card">
                <div className="skeleton-line" style={{ width: '50%', height: 18 }} />
                <div style={{ height: 12 }} />
                <div className="skeleton-line" style={{ width: '80%', height: 36 }} />
              </div>
            </div>
          </div>
        </div>

        <div className="metrics-phase-section">
          <div className="phase-section-header phase-3">
            <div className="skeleton" style={{ width: 140, height: 18, borderRadius: 6 }} />
          </div>
          <div className="phase-section-body">
            <div className="metrics-grid">
              <div className="metric-box skeleton-card">
                <div className="skeleton-line" style={{ width: '40%', height: 16 }} />
                <div style={{ height: 12 }} />
                <div className="skeleton-line" style={{ width: '90%', height: 14 }} />
                <div className="skeleton-line" style={{ width: '60%', height: 14 }} />
              </div>
              <div className="metric-box skeleton-card">
                <div className="skeleton-line" style={{ width: '40%', height: 16 }} />
                <div style={{ height: 12 }} />
                <div className="skeleton-line" style={{ width: '90%', height: 14 }} />
                <div className="skeleton-line" style={{ width: '60%', height: 14 }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="calculated-metrics-container">
        <div className="error-message">
          ⚠️ {error}
        </div>
        <button onClick={loadMetrics} className="refresh-button">
          🔄 Erneut versuchen
        </button>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="calculated-metrics-container">
        <div className="error-message">
          Keine Daten verfügbar
        </div>
      </div>
    );
  }

  // Extract nested metrics object
  const metricsData = metrics.metrics || {};
  const basicIndicators = metricsData.basic_indicators || {};
  const valuationScores = metricsData.valuation_scores || {};
  const advancedAnalysis = metricsData.advanced_analysis || {};

  return (
    <div className="calculated-metrics-container">
      {/* Header */}
  <div className={`calculated-metrics-header ${animateReady ? 'fade-in' : ''}`}>
        <div className="calculated-metrics-title">
          <span className="icon">📊</span>
          <span>Calculated Metrics</span>
        </div>
        <div className="calculated-metrics-refresh">
          <button 
            onClick={loadMetrics} 
            className="refresh-button"
            disabled={loading}
          >
            🔄 Aktualisieren
          </button>
          <span className="last-updated">
            {lastUpdated && `Aktualisiert: ${formatTimeAgo(lastUpdated)}`}
          </span>
        </div>
      </div>

      {/* Basic Indicators */}
      <div className="metrics-phase-section">
        <div className="phase-section-header phase-1">
          <span> BASIC INDICATORS</span>
        </div>
        <div className="phase-section-body">
          {/* 52-Week Range */}
          {basicIndicators.week_52_high && basicIndicators.week_52_low && basicIndicators.current_price && (
            <div className="week52-range-container">
              <div className="week52-range-label">52-Wochen Range</div>
              <div className="week52-range-bar">
                <div 
                  className="week52-range-marker"
                  style={{ 
                    left: `${((basicIndicators.current_price - basicIndicators.week_52_low) / 
                            (basicIndicators.week_52_high - basicIndicators.week_52_low)) * 100}%` 
                  }}
                />
              </div>
              <div className="week52-range-values">
                <span>Tief: {formatCurrency(basicIndicators.week_52_low)}</span>
                <span>Hoch: {formatCurrency(basicIndicators.week_52_high)}</span>
              </div>
              <div className="week52-current-value">
                Aktuell: {formatCurrency(basicIndicators.current_price)} 
                ({formatNumber(basicIndicators.percent_from_low, 1)}% vom Tief)
              </div>
            </div>
          )}

          {/* Indicators */}
          <div className="indicator-row">
            <div className="indicator-label">SMA 50</div>
            <div className="indicator-value">
              {formatCurrency(basicIndicators.sma_50)}
              {basicIndicators.current_price && basicIndicators.sma_50 && (
                <span className={`indicator-trend ${basicIndicators.current_price > basicIndicators.sma_50 ? 'up' : 'down'}`}>
                  {getTrendIcon(basicIndicators.current_price - basicIndicators.sma_50)}
                </span>
              )}
            </div>
          </div>

          <div className="indicator-row">
            <div className="indicator-label">SMA 200</div>
            <div className="indicator-value">
              {formatCurrency(basicIndicators.sma_200)}
              {basicIndicators.current_price && basicIndicators.sma_200 && (
                <span className={`indicator-trend ${basicIndicators.current_price > basicIndicators.sma_200 ? 'up' : 'down'}`}>
                  {getTrendIcon(basicIndicators.current_price - basicIndicators.sma_200)}
                </span>
              )}
            </div>
          </div>

          {/* SMA Crossover Badge */}
          {basicIndicators.sma_crossovers && basicIndicators.sma_crossovers.last_crossover_type && (
            <div style={{ 
              margin: '20px 0', 
              padding: '15px', 
              backgroundColor: basicIndicators.sma_crossovers.last_crossover_type === 'golden_cross' ? '#e8f5e9' : '#ffebee',
              borderRadius: '8px',
              borderLeft: `4px solid ${basicIndicators.sma_crossovers.last_crossover_type === 'golden_cross' ? '#4caf50' : '#f44336'}`
            }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '24px', marginRight: '10px' }}>
                  {basicIndicators.sma_crossovers.last_crossover_type === 'golden_cross' ? '🌟' : '💀'}
                </span>
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#333' }}>
                    {basicIndicators.sma_crossovers.last_crossover_type === 'golden_cross' ? 'Golden Cross' : 'Death Cross'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {new Date(basicIndicators.sma_crossovers.last_crossover_date).toLocaleDateString('de-DE')}
                    {basicIndicators.sma_crossovers.days_since_crossover !== null && 
                      ` (vor ${basicIndicators.sma_crossovers.days_since_crossover} Tagen)`
                    }
                  </div>
                </div>
              </div>
              <div style={{ fontSize: '13px', color: '#666' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
                  <span>Preis beim Crossover:</span>
                  <strong>{formatCurrency(basicIndicators.sma_crossovers.price_at_crossover)}</strong>
                </div>
                {basicIndicators.sma_crossovers.price_change_since_crossover !== null && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
                    <span>Performance seit Crossover:</span>
                    <strong style={{ 
                      color: basicIndicators.sma_crossovers.price_change_since_crossover >= 0 ? '#4caf50' : '#f44336' 
                    }}>
                      {basicIndicators.sma_crossovers.price_change_since_crossover >= 0 ? '+' : ''}
                      {formatNumber(basicIndicators.sma_crossovers.price_change_since_crossover, 2)}%
                    </strong>
                  </div>
                )}
              </div>
              <div style={{ 
                marginTop: '12px', 
                padding: '8px', 
                backgroundColor: 'rgba(255,255,255,0.7)', 
                borderRadius: '4px',
                fontSize: '12px',
                color: '#555'
              }}>
                💡 <strong>Info:</strong> {basicIndicators.sma_crossovers.last_crossover_type === 'golden_cross' 
                  ? 'SMA50 hat SMA200 von unten nach oben gekreuzt - typisches bullishes Signal'
                  : 'SMA50 hat SMA200 von oben nach unten gekreuzt - typisches bearishes Signal'
                }
              </div>
            </div>
          )}

          <div className="indicator-row">
            <div className="indicator-label">
              <MetricTooltip
                title="Volume Ratio"
                description="Verhältnis des aktuellen Volumens zum Durchschnittsvolumen. Werte > 1.5 deuten auf erhöhtes Interesse hin."
              >
                <span>Volume Ratio</span>
              </MetricTooltip>
            </div>
            <div className="indicator-value">
              {formatNumber(basicIndicators.volume_ratio, 2)}x
              {basicIndicators.volume_ratio && (
                <span style={{ marginLeft: '8px', fontSize: '13px', color: '#666' }}>
                  ({formatNumber((basicIndicators.volume_ratio - 1) * 100, 0)}% {basicIndicators.volume_ratio > 1 ? 'über' : 'unter'} Durchschnitt)
                </span>
              )}
            </div>
          </div>

          <div className="indicator-row">
            <div className="indicator-label">
              <MetricTooltip
                title="FCF Yield"
                description="Free Cashflow Yield - zeigt, wie viel Cashflow im Verhältnis zur Marktkapitalisierung generiert wird. Höhere Werte sind besser."
              >
                <span>FCF Yield</span>
              </MetricTooltip>
            </div>
            <div className="indicator-value">
              {formatNumber(basicIndicators.fcf_yield, 2, '%')}
            </div>
          </div>
        </div>
      </div>

      {/* Valuation Scores */}
      <div className="metrics-phase-section">
        <div className="phase-section-header phase-2">
          <span>VALUATION SCORES</span>
        </div>
        <div className="phase-section-body">
            <div className={`score-cards-container ${animateReady ? 'fade-in fade-in-delay' : ''}`}>
            {/* Value Score */}
            <div className="score-card">
              <MetricTooltip
                title="Value Score"
                value={`${formatNumber(valuationScores.value_score, 1)}/100`}
                description="Bewertet die Unterbewertung einer Aktie basierend auf KGV, KBV und anderen Faktoren."
                interpretation={[
                  { range: '80-100', label: 'Exzellent', isCurrent: valuationScores.value_score >= 80 },
                  { range: '60-79', label: 'Gut', isCurrent: valuationScores.value_score >= 60 && valuationScores.value_score < 80 },
                  { range: '40-59', label: 'Moderat', isCurrent: valuationScores.value_score >= 40 && valuationScores.value_score < 60 },
                  { range: '20-39', label: 'Schwach', isCurrent: valuationScores.value_score >= 20 && valuationScores.value_score < 40 },
                  { range: '0-19', label: 'Schlecht', isCurrent: valuationScores.value_score < 20 }
                ]}
              >
                <div className="score-card-title">Value Score</div>
              </MetricTooltip>
              <div className="score-card-value">
                {formatNumber(valuationScores.value_score, 0)}
                <span className="denominator">/100</span>
              </div>
              <div className="score-bar">
                <div 
                  className={`score-bar-fill ${getScoreClass(valuationScores.value_score)}`}
                  style={{ width: `${valuationScores.value_score || 0}%` }}
                />
              </div>
              <div className={`score-badge ${getScoreClass(valuationScores.value_score)}`}>
                {getScoreLabel(valuationScores.value_score)}
              </div>
            </div>

            {/* Quality Score */}
            <div className="score-card">
              <MetricTooltip
                title="Quality Score"
                value={`${formatNumber(valuationScores.quality_score, 1)}/100`}
                description="Misst die Qualität des Unternehmens anhand von ROE, Gewinnmargen und Verschuldung."
                interpretation={[
                  { range: '80-100', label: 'Exzellent', isCurrent: valuationScores.quality_score >= 80 },
                  { range: '60-79', label: 'Gut', isCurrent: valuationScores.quality_score >= 60 && valuationScores.quality_score < 80 },
                  { range: '40-59', label: 'Moderat', isCurrent: valuationScores.quality_score >= 40 && valuationScores.quality_score < 60 },
                  { range: '20-39', label: 'Schwach', isCurrent: valuationScores.quality_score >= 20 && valuationScores.quality_score < 40 },
                  { range: '0-19', label: 'Schlecht', isCurrent: valuationScores.quality_score < 20 }
                ]}
              >
                <div className="score-card-title">Quality Score</div>
              </MetricTooltip>
              <div className="score-card-value">
                {formatNumber(valuationScores.quality_score, 0)}
                <span className="denominator">/100</span>
              </div>
              <div className="score-bar">
                <div 
                  className={`score-bar-fill ${getScoreClass(valuationScores.quality_score)}`}
                  style={{ width: `${valuationScores.quality_score || 0}%` }}
                />
              </div>
              <div className={`score-badge ${getScoreClass(valuationScores.quality_score)}`}>
                {getScoreLabel(valuationScores.quality_score)}
              </div>
            </div>

            {/* Dividend Score */}
            <div className="score-card">
              <MetricTooltip
                title="Dividend Score"
                value={`${formatNumber(valuationScores.dividend_score, 1)}/100`}
                description="Bewertet die Dividendenattraktivität basierend auf Rendite, Ausschüttungsquote und Nachhaltigkeit."
                interpretation={[
                  { range: '80-100', label: 'Exzellent', isCurrent: valuationScores.dividend_score >= 80 },
                  { range: '60-79', label: 'Gut', isCurrent: valuationScores.dividend_score >= 60 && valuationScores.dividend_score < 80 },
                  { range: '40-59', label: 'Moderat', isCurrent: valuationScores.dividend_score >= 40 && valuationScores.dividend_score < 60 },
                  { range: '20-39', label: 'Schwach', isCurrent: valuationScores.dividend_score >= 20 && valuationScores.dividend_score < 40 },
                  { range: '0-19', label: 'Schlecht', isCurrent: valuationScores.dividend_score < 20 }
                ]}
              >
                <div className="score-card-title">Dividend Score</div>
              </MetricTooltip>
              <div className="score-card-value">
                {formatNumber(valuationScores.dividend_score, 0)}
                <span className="denominator">/100</span>
              </div>
              <div className="score-bar">
                <div 
                  className={`score-bar-fill ${getScoreClass(valuationScores.dividend_score)}`}
                  style={{ width: `${valuationScores.dividend_score || 0}%` }}
                />
              </div>
              <div className={`score-badge ${getScoreClass(valuationScores.dividend_score)}`}>
                {getScoreLabel(valuationScores.dividend_score)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Advanced Analysis */}
      <div className="metrics-phase-section">
        <div className="phase-section-header phase-3">
          <span>ADVANCED ANALYSIS</span>
        </div>
        <div className="phase-section-body">
          <div className="metrics-grid">
            {/* Technical Indicators */}
            <div className="metric-box">
              <div className="metric-box-title">📈 Technical Indicators</div>
              <div className="metric-box-content">
                <div className="metric-item">
                  <span className="metric-item-label">
                    <MetricTooltip
                      title="MACD"
                      description="Moving Average Convergence Divergence - Momentum-Indikator. Kaufsignal wenn MACD > Signal."
                    >
                      <span>MACD</span>
                    </MetricTooltip>
                  </span>
                  <span className="metric-item-value">
                    {formatNumber(advancedAnalysis.macd, 2)}
                    {advancedAnalysis.macd && advancedAnalysis.macd_signal && (
                      <span className={`metric-badge-small ${advancedAnalysis.macd > advancedAnalysis.macd_signal ? 'buy' : 'sell'}`}>
                        {advancedAnalysis.macd > advancedAnalysis.macd_signal ? 'BUY ↑' : 'SELL ↓'}
                      </span>
                    )}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">MACD Signal</span>
                  <span className="metric-item-value">{formatNumber(advancedAnalysis.macd_signal, 2)}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">
                    <MetricTooltip
                      title="Stochastic %K"
                      description="Momentum-Indikator. >80: Überkauft, <20: Überverkauft, 20-80: Neutral"
                    >
                      <span>Stochastic %K</span>
                    </MetricTooltip>
                  </span>
                  <span className="metric-item-value">
                    {formatNumber(advancedAnalysis.stochastic_k, 1, '%')}
                    {advancedAnalysis.stochastic_k && (
                      <span className={`metric-badge-small ${
                        advancedAnalysis.stochastic_k > 80 ? 'sell' : 
                        advancedAnalysis.stochastic_k < 20 ? 'buy' : 'neutral'
                      }`}>
                        {advancedAnalysis.stochastic_k > 80 ? 'Überkauft' : 
                         advancedAnalysis.stochastic_k < 20 ? 'Überverkauft' : 'Neutral'}
                      </span>
                    )}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">RSI (14)</span>
                  <span className="metric-item-value">{formatNumber(advancedAnalysis.rsi, 1)}</span>
                </div>
              </div>
            </div>

            {/* Risk Metrics */}
            <div className="metric-box">
              <div className="metric-box-title">⚠️ Risk Metrics</div>
              <div className="metric-box-content">
                <div className="metric-item">
                  <span className="metric-item-label">
                    <MetricTooltip
                      title="Volatility (30d)"
                      description="Annualisierte Volatilität der letzten 30 Tage. Höhere Werte = höheres Risiko."
                    >
                      <span>Volatility (30d)</span>
                    </MetricTooltip>
                  </span>
                  <span className="metric-item-value">
                    {formatNumber(advancedAnalysis.volatility_30d, 2, '%')}
                    {advancedAnalysis.volatility_rating && (
                      <span 
                        className={`metric-badge-small ${advancedAnalysis.volatility_rating.replace('_', '-')}`}
                        style={{ background: getRiskRatingColor(advancedAnalysis.volatility_rating) }}
                      >
                        {getRiskRatingLabel(advancedAnalysis.volatility_rating)}
                      </span>
                    )}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">Max Drawdown</span>
                  <span className="metric-item-value">{formatNumber(advancedAnalysis.max_drawdown, 2, '%')}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">
                    <MetricTooltip
                      title="Beta"
                      description="Volatilität im Vergleich zum Markt (S&P 500). >1: volatiler als Markt, <1: weniger volatil"
                    >
                      <span>Beta</span>
                    </MetricTooltip>
                  </span>
                  <span className="metric-item-value">
                    {formatNumber(advancedAnalysis.beta, 2)}
                    {advancedAnalysis.beta && (
                      <span style={{ marginLeft: '8px', fontSize: '12px', color: '#666' }}>
                        ({formatNumber(Math.abs(advancedAnalysis.beta - 1) * 100, 0)}% {advancedAnalysis.beta > 1 ? 'volatiler' : 'stabiler'})
                      </span>
                    )}
                  </span>
                </div>
              </div>
            </div>

            {/* VWAP (Volume Weighted Average Price) */}
            {/* Render VWAP panel if we have a VWAP value from the indicators OR a fallback in basic_indicators */}
            {(() => {
              const vwapCurrent = (vwapData && vwapData.current) || basicIndicators.vwap || null;
              const currentPriceForVwap = (vwapData && vwapData.currentPrice) || basicIndicators.current_price || null;
              return vwapCurrent !== null ? (
              <div className="metric-box">
                <div className="metric-box-title">💧 VWAP - Volume Weighted Average Price</div>
                <div className="metric-box-content">
                  <div className="metric-item">
                    <span className="metric-item-label">
                      <MetricTooltip
                        title="VWAP (20)"
                        description="Volume Weighted Average Price - durchschnittlicher Preis gewichtet nach Volumen über 20 Tage. Wichtiger Benchmark für institutionelle Trader."
                      >
                        <span>VWAP (20)</span>
                      </MetricTooltip>
                    </span>
                    <span className="metric-item-value">
                      {vwapCurrent !== null ? formatCurrency(vwapCurrent) : 'n/a'}
                    </span>
                  </div>
                  
                  <div className="metric-item">
                    <span className="metric-item-label">
                      Current Price
                    </span>
                    <span className="metric-item-value">
                        {currentPriceForVwap !== null ? formatCurrency(currentPriceForVwap) : 'n/a'}
                    </span>
                  </div>

                  {vwapFallbackUsed && vwapData && (
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                      ℹ️ VWAP wurde clientseitig berechnet (letzte 20 Tage)
                    </div>
                  )}

                  {(() => {
                    const currentPrice = currentPriceForVwap;
                    const vwap = vwapCurrent;
                    const diffPercent = ((currentPrice - vwap) / vwap) * 100;
                    const isAboveVwap = currentPrice > vwap;
                    
                    return (
                      <>
                        <div className="metric-item">
                          <span className="metric-item-label">
                            Distance to VWAP
                          </span>
                          <span className="metric-item-value" style={{ 
                            color: (currentPrice !== null && isAboveVwap) ? '#27ae60' : '#e74c3c',
                            fontWeight: 'bold'
                          }}>
                            {currentPrice !== null ? (isAboveVwap ? '+' : '') + formatNumber(diffPercent, 2) + (isAboveVwap ? ' ↑' : ' ↓') : 'n/a'}
                          </span>
                        </div>
                        
                        <div style={{ 
                          marginTop: '15px', 
                          padding: '12px', 
                          backgroundColor: (currentPrice !== null && isAboveVwap) ? '#e8f5e9' : '#ffebee', 
                          borderRadius: '6px',
                          borderLeft: `4px solid ${(currentPrice !== null && isAboveVwap) ? '#27ae60' : '#e74c3c'}`
                        }}>
                          <div style={{ fontSize: '13px', color: '#333', marginBottom: '8px' }}>
                            <strong>
                              {(currentPrice !== null && isAboveVwap) ? '📈 Bullish Signal' : '📉 Bearish Signal'}
                            </strong>
                          </div>
                          <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.5' }}>
                            {(currentPrice !== null && isAboveVwap) ? (
                              <>
                                ✅ Preis über VWAP → Käufer dominieren<br/>
                                ✅ Institutioneller Support vorhanden<br/>
                                ✅ VWAP kann als dynamischer Support dienen
                              </>
                            ) : (
                              <>
                                ⚠️ Preis unter VWAP → Verkäufer dominieren<br/>
                                ⚠️ Institutioneller Druck vorhanden<br/>
                                ⚠️ VWAP kann als Widerstand wirken
                              </>
                            )}
                          </div>
                        </div>
                        
                        <div style={{ 
                          marginTop: '10px', 
                          padding: '8px', 
                          backgroundColor: '#f8f9fa', 
                          borderRadius: '4px',
                          fontSize: '12px',
                          color: '#666'
                        }}>
                          💡 <strong>Trading Tip:</strong> {(currentPrice !== null && isAboveVwap) 
                            ? 'Long-Positionen bevorzugen. Bei Rücksetzer auf VWAP als Entry nutzen.'
                            : 'Vorsicht bei Long-Positionen. Warten bis Preis über VWAP steigt.'}
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
              ) : null;
            })()}

            {/* ATR & Stop-Loss Levels */}
            {advancedAnalysis.atr_current && (
              <div className="metric-box">
                <div className="metric-box-title">🎯 ATR & Stop-Loss Levels</div>
                <div className="metric-box-content">
                  <div className="metric-item">
                    <span className="metric-item-label">
                      <MetricTooltip
                        title="ATR (14)"
                        description="Average True Range - misst die durchschnittliche Preisbewegung. Wichtig für Stop-Loss-Platzierung."
                      >
                        <span>ATR (14)</span>
                      </MetricTooltip>
                    </span>
                    <span className="metric-item-value">
                      {formatCurrency(advancedAnalysis.atr_current)}
                      <span style={{ marginLeft: '8px', fontSize: '12px', color: '#666' }}>
                        ({formatNumber(advancedAnalysis.atr_percentage, 2)}% des Preises)
                      </span>
                      {advancedAnalysis.volatility_rating && (
                        <span 
                          className={`metric-badge-small ${advancedAnalysis.volatility_rating.replace('_', '-')}`}
                          style={{ background: getRiskRatingColor(advancedAnalysis.volatility_rating), marginLeft: '8px' }}
                        >
                          {getRiskRatingLabel(advancedAnalysis.volatility_rating)}
                        </span>
                      )}
                    </span>
                  </div>
                  
                  <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>
                      📊 Stop-Loss Empfehlungen (Long Position):
                    </div>
                    <div className="metric-item" style={{ borderBottom: '1px solid #e0e0e0', paddingBottom: '8px', marginBottom: '8px' }}>
                      <span className="metric-item-label" style={{ color: '#f39c12' }}>
                        🟡 Conservative (1.5x ATR)
                      </span>
                      <span className="metric-item-value" style={{ color: '#f39c12', fontWeight: 'bold' }}>
                        {formatCurrency(advancedAnalysis.stop_loss_conservative)}
                      </span>
                    </div>
                    <div className="metric-item" style={{ borderBottom: '1px solid #e0e0e0', paddingBottom: '8px', marginBottom: '8px' }}>
                      <span className="metric-item-label" style={{ color: '#e67e22' }}>
                        🟠 Standard (2x ATR)
                      </span>
                      <span className="metric-item-value" style={{ color: '#e67e22', fontWeight: 'bold' }}>
                        {formatCurrency(advancedAnalysis.stop_loss_standard)}
                      </span>
                    </div>
                    <div className="metric-item" style={{ paddingBottom: '8px' }}>
                      <span className="metric-item-label" style={{ color: '#e74c3c' }}>
                        🔴 Aggressive (3x ATR)
                      </span>
                      <span className="metric-item-value" style={{ color: '#e74c3c', fontWeight: 'bold' }}>
                        {formatCurrency(advancedAnalysis.stop_loss_aggressive)}
                      </span>
                    </div>
                  </div>

                  <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#e8f5e9', borderRadius: '6px' }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>
                      🎯 Take-Profit Empfehlungen:
                    </div>
                    <div className="metric-item" style={{ borderBottom: '1px solid #c8e6c9', paddingBottom: '8px', marginBottom: '8px' }}>
                      <span className="metric-item-label" style={{ color: '#81c784' }}>
                        Conservative (2x ATR)
                      </span>
                      <span className="metric-item-value" style={{ color: '#81c784', fontWeight: 'bold' }}>
                        {formatCurrency(advancedAnalysis.take_profit_conservative)}
                      </span>
                    </div>
                    <div className="metric-item" style={{ borderBottom: '1px solid #c8e6c9', paddingBottom: '8px', marginBottom: '8px' }}>
                      <span className="metric-item-label" style={{ color: '#66bb6a' }}>
                        Standard (3x ATR)
                      </span>
                      <span className="metric-item-value" style={{ color: '#66bb6a', fontWeight: 'bold' }}>
                        {formatCurrency(advancedAnalysis.take_profit_standard)}
                      </span>
                    </div>
                    <div className="metric-item" style={{ paddingBottom: '8px' }}>
                      <span className="metric-item-label" style={{ color: '#4caf50' }}>
                        Aggressive (4x ATR)
                      </span>
                      <span className="metric-item-value" style={{ color: '#4caf50', fontWeight: 'bold' }}>
                        {formatCurrency(advancedAnalysis.take_profit_aggressive)}
                      </span>
                    </div>
                  </div>

                  {advancedAnalysis.risk_reward_ratio && (
                    <div style={{ marginTop: '10px', padding: '8px', backgroundColor: '#fff3cd', borderRadius: '4px', textAlign: 'center' }}>
                      <span style={{ fontSize: '13px', color: '#856404' }}>
                        ⚖️ <strong>Risk/Reward Ratio (2x:3x ATR):</strong> 1:{formatNumber(advancedAnalysis.risk_reward_ratio, 1)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Beta-Adjusted Performance */}
            <div className="metric-box">
              <div className="metric-box-title">🎯 Risk-Adjusted Performance</div>
              <div className="metric-box-content">
                <div className="metric-item">
                  <span className="metric-item-label">
                    <MetricTooltip
                      title="Sharpe Ratio"
                      description="Rendite pro Risikoeinheit. Höhere Werte sind besser."
                      interpretation={[
                        { range: '> 1.0', label: 'Exzellent', isCurrent: advancedAnalysis.sharpe_ratio > 1.0 },
                        { range: '0.5-1.0', label: 'Gut', isCurrent: advancedAnalysis.sharpe_ratio >= 0.5 && advancedAnalysis.sharpe_ratio <= 1.0 },
                        { range: '0-0.5', label: 'Schwach', isCurrent: advancedAnalysis.sharpe_ratio >= 0 && advancedAnalysis.sharpe_ratio < 0.5 },
                        { range: '< 0', label: 'Schlecht', isCurrent: advancedAnalysis.sharpe_ratio < 0 }
                      ]}
                    >
                      <span>Sharpe Ratio</span>
                    </MetricTooltip>
                  </span>
                  <span className="metric-item-value">
                    {formatNumber(advancedAnalysis.sharpe_ratio, 2)}
                    {advancedAnalysis.sharpe_ratio && (
                      <span className={`metric-badge-small ${
                        advancedAnalysis.sharpe_ratio > 1.0 ? 'buy' : 
                        advancedAnalysis.sharpe_ratio > 0.5 ? 'neutral' : 'sell'
                      }`}>
                        {advancedAnalysis.sharpe_ratio > 1.0 ? 'Exzellent' : 
                         advancedAnalysis.sharpe_ratio > 0.5 ? 'Gut' : 'Schwach'}
                      </span>
                    )}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">
                    <MetricTooltip
                      title="Alpha"
                      description="Überrendite im Vergleich zum Markt. Positiv = Outperformance, Negativ = Underperformance"
                    >
                      <span>Alpha</span>
                    </MetricTooltip>
                  </span>
                  <span className="metric-item-value">
                    {formatNumber(advancedAnalysis.alpha, 2, '%')}
                    {advancedAnalysis.alpha && (
                      <span style={{ marginLeft: '8px' }}>
                        {advancedAnalysis.alpha > 0 ? '🚀' : '📉'}
                      </span>
                    )}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">Treynor Ratio</span>
                  <span className="metric-item-value">{formatNumber(advancedAnalysis.treynor_ratio, 2)}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">Sortino Ratio</span>
                  <span className="metric-item-value">{formatNumber(advancedAnalysis.sortino_ratio, 2)}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">Information Ratio</span>
                  <span className="metric-item-value">{formatNumber(advancedAnalysis.information_ratio, 2)}</span>
                </div>
              </div>
            </div>

            {/* Overall Risk Score */}
            <div className="metric-box">
              <div className="metric-box-title">⭐ Risk-Adjusted Score</div>
              <div className="metric-box-content">
                <div style={{ 
                  textAlign: 'center', 
                  padding: '20px',
                  background: '#f8f9fa',
                  borderRadius: '8px'
                }}>
                  <div style={{ fontSize: '48px', fontWeight: '700', color: '#007bff', marginBottom: '10px' }}>
                    {formatNumber(advancedAnalysis.risk_adjusted_performance_score, 1)}
                    <span style={{ fontSize: '24px', color: '#999' }}>/100</span>
                  </div>
                  <div className="score-bar" style={{ maxWidth: '300px', margin: '0 auto 15px' }}>
                    <div 
                      className={`score-bar-fill ${getScoreClass(advancedAnalysis.risk_adjusted_performance_score)}`}
                      style={{ width: `${advancedAnalysis.risk_adjusted_performance_score || 0}%` }}
                    />
                  </div>
                  <div className={`score-badge ${getScoreClass(advancedAnalysis.risk_adjusted_performance_score)}`}>
                    {getScoreLabel(advancedAnalysis.risk_adjusted_performance_score)}
                  </div>
                  
                  {/* Contributions */}
                  {advancedAnalysis.sharpe_contribution !== undefined && (
                    <div style={{ marginTop: '20px', fontSize: '13px', color: '#666', textAlign: 'left' }}>
                      <div style={{ fontWeight: '600', marginBottom: '8px' }}>Beiträge zum Score:</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Sharpe Ratio:</span>
                        <strong>{formatNumber(advancedAnalysis.sharpe_contribution, 1)} Punkte</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Alpha:</span>
                        <strong>{formatNumber(advancedAnalysis.alpha_contribution, 1)} Punkte</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Treynor Ratio:</span>
                        <strong>{formatNumber(advancedAnalysis.treynor_contribution, 1)} Punkte</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Sortino Ratio:</span>
                        <strong>{formatNumber(advancedAnalysis.sortino_contribution, 1)} Punkte</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Information Ratio:</span>
                        <strong>{formatNumber(advancedAnalysis.information_ratio_contribution, 1)} Punkte</strong>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CalculatedMetricsTab;

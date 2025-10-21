import React, { useState, useEffect, useCallback } from 'react';
import MetricTooltip from './MetricTooltip';
import './CalculatedMetrics.css';

import API_BASE from '../config';
import { formatPrice } from '../utils/currencyUtils';

/**
 * CalculatedMetricsTab Component
 * Displays comprehensive calculated metrics for a stock
 */
function CalculatedMetricsTab({ stockId }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [vwapData, setVwapData] = useState(null);

  const loadMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load calculated metrics
      const response = await fetch(`${API_BASE}/stock-data/${stockId}/calculated-metrics`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMetrics(data);
      
      // Load VWAP from technical indicators
      const vwapResponse = await fetch(`${API_BASE}/stock-data/${stockId}/technical-indicators?period=1y&indicators=vwap`);
      if (vwapResponse.ok) {
        const vwapJson = await vwapResponse.json();
        if (vwapJson.indicators && vwapJson.indicators.vwap) {
          const vwapArray = vwapJson.indicators.vwap;
          const currentVwap = vwapArray[vwapArray.length - 1]; // Latest VWAP value
          
          // Get current price from close prices (last value)
          let currentPrice = null;
          if (vwapJson.close && vwapJson.close.length > 0) {
            currentPrice = vwapJson.close[vwapJson.close.length - 1];
          }
          
          setVwapData({ 
            current: currentVwap,
            currentPrice: currentPrice
          });
        }
      }
      
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error loading calculated metrics:', err);
      setError('Fehler beim Laden der Metriken. Bitte versuche es später erneut.');
    } finally {
      setLoading(false);
    }
  }, [stockId]);

  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

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
    return (
      <div className="calculated-metrics-container">
        <div className="loading-spinner">
          <div>⏳ Lade Calculated Metrics...</div>
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
      <div className="calculated-metrics-header">
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

      {/* PHASE 2: Valuation Scores (am wichtigsten, daher zuerst) */}
      <div className="metrics-phase-section">
        <div className="phase-section-header phase-2">
          <span>⭐ PHASE 2: VALUATION SCORES</span>
        </div>
        <div className="phase-section-body">
          <div className="score-cards-container">
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

      {/* PHASE 1: Basic Indicators */}
      <div className="metrics-phase-section">
        <div className="phase-section-header phase-1">
          <span>📊 PHASE 1: KEY INDICATORS</span>
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

      {/* PHASE 3: Advanced Analysis */}
      <div className="metrics-phase-section">
        <div className="phase-section-header phase-3">
          <span>🔬 PHASE 3: ADVANCED ANALYSIS</span>
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
            {vwapData && vwapData.current && vwapData.currentPrice && (
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
                      {formatCurrency(vwapData.current)}
                    </span>
                  </div>
                  
                  <div className="metric-item">
                    <span className="metric-item-label">
                      Current Price
                    </span>
                    <span className="metric-item-value">
                      {formatCurrency(vwapData.currentPrice)}
                    </span>
                  </div>

                  {(() => {
                    const currentPrice = vwapData.currentPrice;
                    const vwap = vwapData.current;
                    const diffPercent = ((currentPrice - vwap) / vwap) * 100;
                    const isAboveVwap = currentPrice > vwap;
                    
                    return (
                      <>
                        <div className="metric-item">
                          <span className="metric-item-label">
                            Distance to VWAP
                          </span>
                          <span className="metric-item-value" style={{ 
                            color: isAboveVwap ? '#27ae60' : '#e74c3c',
                            fontWeight: 'bold'
                          }}>
                            {isAboveVwap ? '+' : ''}{formatNumber(diffPercent, 2)}%
                            {isAboveVwap ? ' ↑' : ' ↓'}
                          </span>
                        </div>
                        
                        <div style={{ 
                          marginTop: '15px', 
                          padding: '12px', 
                          backgroundColor: isAboveVwap ? '#e8f5e9' : '#ffebee', 
                          borderRadius: '6px',
                          borderLeft: `4px solid ${isAboveVwap ? '#27ae60' : '#e74c3c'}`
                        }}>
                          <div style={{ fontSize: '13px', color: '#333', marginBottom: '8px' }}>
                            <strong>
                              {isAboveVwap ? '📈 Bullish Signal' : '📉 Bearish Signal'}
                            </strong>
                          </div>
                          <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.5' }}>
                            {isAboveVwap ? (
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
                          💡 <strong>Trading Tip:</strong> {isAboveVwap 
                            ? 'Long-Positionen bevorzugen. Bei Rücksetzer auf VWAP als Entry nutzen.'
                            : 'Vorsicht bei Long-Positionen. Warten bis Preis über VWAP steigt.'}
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}

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

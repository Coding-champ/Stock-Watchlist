import React, { useState, useEffect, useCallback } from 'react';
import MetricTooltip from './MetricTooltip';
import './CalculatedMetrics.css';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

/**
 * CalculatedMetricsTab Component
 * Displays comprehensive calculated metrics for a stock
 */
function CalculatedMetricsTab({ stockId }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/stock-data/${stockId}/calculated-metrics`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMetrics(data);
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

  const formatCurrency = (value, currency = '$') => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      return currency + value.toLocaleString('en-US', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });
    }
    return '-';
  };

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

  const phase1 = metrics.phase1_basic_indicators || {};
  const phase2 = metrics.phase2_valuation_scores || {};
  const phase3 = metrics.phase3_advanced_analysis || {};

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
                value={`${formatNumber(phase2.value_score, 1)}/100`}
                description="Bewertet die Unterbewertung einer Aktie basierend auf KGV, KBV und anderen Faktoren."
                interpretation={[
                  { range: '80-100', label: 'Exzellent', isCurrent: phase2.value_score >= 80 },
                  { range: '60-79', label: 'Gut', isCurrent: phase2.value_score >= 60 && phase2.value_score < 80 },
                  { range: '40-59', label: 'Moderat', isCurrent: phase2.value_score >= 40 && phase2.value_score < 60 },
                  { range: '20-39', label: 'Schwach', isCurrent: phase2.value_score >= 20 && phase2.value_score < 40 },
                  { range: '0-19', label: 'Schlecht', isCurrent: phase2.value_score < 20 }
                ]}
              >
                <div className="score-card-title">Value Score</div>
              </MetricTooltip>
              <div className="score-card-value">
                {formatNumber(phase2.value_score, 0)}
                <span className="denominator">/100</span>
              </div>
              <div className="score-bar">
                <div 
                  className={`score-bar-fill ${getScoreClass(phase2.value_score)}`}
                  style={{ width: `${phase2.value_score || 0}%` }}
                />
              </div>
              <div className={`score-badge ${getScoreClass(phase2.value_score)}`}>
                {getScoreLabel(phase2.value_score)}
              </div>
            </div>

            {/* Quality Score */}
            <div className="score-card">
              <MetricTooltip
                title="Quality Score"
                value={`${formatNumber(phase2.quality_score, 1)}/100`}
                description="Misst die Qualität des Unternehmens anhand von ROE, Gewinnmargen und Verschuldung."
                interpretation={[
                  { range: '80-100', label: 'Exzellent', isCurrent: phase2.quality_score >= 80 },
                  { range: '60-79', label: 'Gut', isCurrent: phase2.quality_score >= 60 && phase2.quality_score < 80 },
                  { range: '40-59', label: 'Moderat', isCurrent: phase2.quality_score >= 40 && phase2.quality_score < 60 },
                  { range: '20-39', label: 'Schwach', isCurrent: phase2.quality_score >= 20 && phase2.quality_score < 40 },
                  { range: '0-19', label: 'Schlecht', isCurrent: phase2.quality_score < 20 }
                ]}
              >
                <div className="score-card-title">Quality Score</div>
              </MetricTooltip>
              <div className="score-card-value">
                {formatNumber(phase2.quality_score, 0)}
                <span className="denominator">/100</span>
              </div>
              <div className="score-bar">
                <div 
                  className={`score-bar-fill ${getScoreClass(phase2.quality_score)}`}
                  style={{ width: `${phase2.quality_score || 0}%` }}
                />
              </div>
              <div className={`score-badge ${getScoreClass(phase2.quality_score)}`}>
                {getScoreLabel(phase2.quality_score)}
              </div>
            </div>

            {/* Dividend Score */}
            <div className="score-card">
              <MetricTooltip
                title="Dividend Score"
                value={`${formatNumber(phase2.dividend_score, 1)}/100`}
                description="Bewertet die Dividendenattraktivität basierend auf Rendite, Ausschüttungsquote und Nachhaltigkeit."
                interpretation={[
                  { range: '80-100', label: 'Exzellent', isCurrent: phase2.dividend_score >= 80 },
                  { range: '60-79', label: 'Gut', isCurrent: phase2.dividend_score >= 60 && phase2.dividend_score < 80 },
                  { range: '40-59', label: 'Moderat', isCurrent: phase2.dividend_score >= 40 && phase2.dividend_score < 60 },
                  { range: '20-39', label: 'Schwach', isCurrent: phase2.dividend_score >= 20 && phase2.dividend_score < 40 },
                  { range: '0-19', label: 'Schlecht', isCurrent: phase2.dividend_score < 20 }
                ]}
              >
                <div className="score-card-title">Dividend Score</div>
              </MetricTooltip>
              <div className="score-card-value">
                {formatNumber(phase2.dividend_score, 0)}
                <span className="denominator">/100</span>
              </div>
              <div className="score-bar">
                <div 
                  className={`score-bar-fill ${getScoreClass(phase2.dividend_score)}`}
                  style={{ width: `${phase2.dividend_score || 0}%` }}
                />
              </div>
              <div className={`score-badge ${getScoreClass(phase2.dividend_score)}`}>
                {getScoreLabel(phase2.dividend_score)}
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
          {phase1.week_52_high && phase1.week_52_low && phase1.current_price && (
            <div className="week52-range-container">
              <div className="week52-range-label">52-Wochen Range</div>
              <div className="week52-range-bar">
                <div 
                  className="week52-range-marker"
                  style={{ 
                    left: `${((phase1.current_price - phase1.week_52_low) / 
                            (phase1.week_52_high - phase1.week_52_low)) * 100}%` 
                  }}
                />
              </div>
              <div className="week52-range-values">
                <span>Tief: {formatCurrency(phase1.week_52_low)}</span>
                <span>Hoch: {formatCurrency(phase1.week_52_high)}</span>
              </div>
              <div className="week52-current-value">
                Aktuell: {formatCurrency(phase1.current_price)} 
                ({formatNumber(phase1.percent_from_low, 1)}% vom Tief)
              </div>
            </div>
          )}

          {/* Indicators */}
          <div className="indicator-row">
            <div className="indicator-label">SMA 50</div>
            <div className="indicator-value">
              {formatCurrency(phase1.sma_50)}
              {phase1.current_price && phase1.sma_50 && (
                <span className={`indicator-trend ${phase1.current_price > phase1.sma_50 ? 'up' : 'down'}`}>
                  {getTrendIcon(phase1.current_price - phase1.sma_50)}
                </span>
              )}
            </div>
          </div>

          <div className="indicator-row">
            <div className="indicator-label">SMA 200</div>
            <div className="indicator-value">
              {formatCurrency(phase1.sma_200)}
              {phase1.current_price && phase1.sma_200 && (
                <span className={`indicator-trend ${phase1.current_price > phase1.sma_200 ? 'up' : 'down'}`}>
                  {getTrendIcon(phase1.current_price - phase1.sma_200)}
                </span>
              )}
            </div>
          </div>

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
              {formatNumber(phase1.volume_ratio, 2)}x
              {phase1.volume_ratio && (
                <span style={{ marginLeft: '8px', fontSize: '13px', color: '#666' }}>
                  ({formatNumber((phase1.volume_ratio - 1) * 100, 0)}% {phase1.volume_ratio > 1 ? 'über' : 'unter'} Durchschnitt)
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
              {formatNumber(phase1.fcf_yield, 2, '%')}
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
                    {formatNumber(phase3.macd, 2)}
                    {phase3.macd && phase3.macd_signal && (
                      <span className={`metric-badge-small ${phase3.macd > phase3.macd_signal ? 'buy' : 'sell'}`}>
                        {phase3.macd > phase3.macd_signal ? 'BUY ↑' : 'SELL ↓'}
                      </span>
                    )}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">MACD Signal</span>
                  <span className="metric-item-value">{formatNumber(phase3.macd_signal, 2)}</span>
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
                    {formatNumber(phase3.stochastic_k, 1, '%')}
                    {phase3.stochastic_k && (
                      <span className={`metric-badge-small ${
                        phase3.stochastic_k > 80 ? 'sell' : 
                        phase3.stochastic_k < 20 ? 'buy' : 'neutral'
                      }`}>
                        {phase3.stochastic_k > 80 ? 'Überkauft' : 
                         phase3.stochastic_k < 20 ? 'Überverkauft' : 'Neutral'}
                      </span>
                    )}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">RSI (14)</span>
                  <span className="metric-item-value">{formatNumber(phase3.rsi, 1)}</span>
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
                    {formatNumber(phase3.volatility_30d, 2, '%')}
                    {phase3.volatility_rating && (
                      <span 
                        className={`metric-badge-small ${phase3.volatility_rating.replace('_', '-')}`}
                        style={{ background: getRiskRatingColor(phase3.volatility_rating) }}
                      >
                        {getRiskRatingLabel(phase3.volatility_rating)}
                      </span>
                    )}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">Max Drawdown</span>
                  <span className="metric-item-value">{formatNumber(phase3.max_drawdown, 2, '%')}</span>
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
                    {formatNumber(phase3.beta, 2)}
                    {phase3.beta && (
                      <span style={{ marginLeft: '8px', fontSize: '12px', color: '#666' }}>
                        ({formatNumber(Math.abs(phase3.beta - 1) * 100, 0)}% {phase3.beta > 1 ? 'volatiler' : 'stabiler'})
                      </span>
                    )}
                  </span>
                </div>
              </div>
            </div>

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
                        { range: '> 1.0', label: 'Exzellent', isCurrent: phase3.sharpe_ratio > 1.0 },
                        { range: '0.5-1.0', label: 'Gut', isCurrent: phase3.sharpe_ratio >= 0.5 && phase3.sharpe_ratio <= 1.0 },
                        { range: '0-0.5', label: 'Schwach', isCurrent: phase3.sharpe_ratio >= 0 && phase3.sharpe_ratio < 0.5 },
                        { range: '< 0', label: 'Schlecht', isCurrent: phase3.sharpe_ratio < 0 }
                      ]}
                    >
                      <span>Sharpe Ratio</span>
                    </MetricTooltip>
                  </span>
                  <span className="metric-item-value">
                    {formatNumber(phase3.sharpe_ratio, 2)}
                    {phase3.sharpe_ratio && (
                      <span className={`metric-badge-small ${
                        phase3.sharpe_ratio > 1.0 ? 'buy' : 
                        phase3.sharpe_ratio > 0.5 ? 'neutral' : 'sell'
                      }`}>
                        {phase3.sharpe_ratio > 1.0 ? 'Exzellent' : 
                         phase3.sharpe_ratio > 0.5 ? 'Gut' : 'Schwach'}
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
                    {formatNumber(phase3.alpha, 2, '%')}
                    {phase3.alpha && (
                      <span style={{ marginLeft: '8px' }}>
                        {phase3.alpha > 0 ? '🚀' : '📉'}
                      </span>
                    )}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">Treynor Ratio</span>
                  <span className="metric-item-value">{formatNumber(phase3.treynor_ratio, 2)}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">Sortino Ratio</span>
                  <span className="metric-item-value">{formatNumber(phase3.sortino_ratio, 2)}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-item-label">Information Ratio</span>
                  <span className="metric-item-value">{formatNumber(phase3.information_ratio, 2)}</span>
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
                    {formatNumber(phase3.risk_adjusted_performance_score, 1)}
                    <span style={{ fontSize: '24px', color: '#999' }}>/100</span>
                  </div>
                  <div className="score-bar" style={{ maxWidth: '300px', margin: '0 auto 15px' }}>
                    <div 
                      className={`score-bar-fill ${getScoreClass(phase3.risk_adjusted_performance_score)}`}
                      style={{ width: `${phase3.risk_adjusted_performance_score || 0}%` }}
                    />
                  </div>
                  <div className={`score-badge ${getScoreClass(phase3.risk_adjusted_performance_score)}`}>
                    {getScoreLabel(phase3.risk_adjusted_performance_score)}
                  </div>
                  
                  {/* Contributions */}
                  {phase3.sharpe_contribution !== undefined && (
                    <div style={{ marginTop: '20px', fontSize: '13px', color: '#666', textAlign: 'left' }}>
                      <div style={{ fontWeight: '600', marginBottom: '8px' }}>Beiträge zum Score:</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Sharpe Ratio:</span>
                        <strong>{formatNumber(phase3.sharpe_contribution, 1)} Punkte</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Alpha:</span>
                        <strong>{formatNumber(phase3.alpha_contribution, 1)} Punkte</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Treynor Ratio:</span>
                        <strong>{formatNumber(phase3.treynor_contribution, 1)} Punkte</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Sortino Ratio:</span>
                        <strong>{formatNumber(phase3.sortino_contribution, 1)} Punkte</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                        <span>Information Ratio:</span>
                        <strong>{formatNumber(phase3.information_ratio_contribution, 1)} Punkte</strong>
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

import React from 'react';
import { formatPrice } from '../../utils/currencyUtils';

/**
 * Custom tooltip component for the stock chart
 * Shows price, volume, and all active indicators
 */
export const ChartTooltip = ({ 
  active, 
  payload, 
  label, 
  stock,
  isPercentageView,
  chartType,
  showSMA50,
  showSMA200,
  showBollinger,
  showATR,
  showVWAP,
  showIchimoku,
  CHART_TYPES
}) => {
  if (!active || !payload || payload.length === 0) return null;
  
  const data = payload[0].payload;
  const isPct = isPercentageView && chartType === CHART_TYPES.LINE;
  
  const pctText = (() => {
    try {
      const idx = data && typeof data.displayClose === 'number' ? data.displayClose : null;
      if (idx != null && isFinite(idx)) {
        const pct = (idx - 1) * 100;
        const sign = pct > 0 ? '+' : '';
        return `${sign}${pct.toFixed(2)}%`;
      }
    } catch {}
    return null;
  })();

  return (
    <div className="custom-tooltip" style={{ background: 'white', padding: '8px', border: '1px solid #ddd', borderRadius: 6 }}>
      {/* Date and Price Information */}
      <p style={{ fontWeight: 'bold', marginBottom: '8px', borderBottom: '1px solid #eee', paddingBottom: '4px' }}>
        <span className="tooltip-label">{label}</span>
      </p>
      {data.close != null && (
        <p>
          <span className="tooltip-label" style={{ color: '#2196F3' }}>Preis:</span>
          {' '}
          {isPct && pctText ? (
            <>
              <span className="tooltip-value" style={{ fontWeight: 'bold' }}>{pctText}</span>
              <span> ({formatPrice(data.close, stock)})</span>
            </>
          ) : (
            <span className="tooltip-value" style={{ fontWeight: 'bold' }}>{formatPrice(data.close, stock)}</span>
          )}
        </p>
      )}
      {data.high != null && data.low != null && (
        <p style={{ fontSize: '12px', color: '#666' }}>
          H: {formatPrice(data.high, stock)} / L: {formatPrice(data.low, stock)}
        </p>
      )}
      {data.volume != null && (
        <p style={{ fontSize: '12px', color: '#666', marginBottom: '8px', borderBottom: '1px solid #eee', paddingBottom: '4px' }}>
          Vol: {(data.volume / 1000000).toFixed(2)}M
        </p>
      )}
      
      {showSMA50 && data.sma50 != null && (
        <p>
          <span className="tooltip-label" style={{ color: '#ff7f0e' }}>SMA 50:</span>
          {' '}
          <span className="tooltip-value">{formatPrice(data.sma50, stock)}</span>
        </p>
      )}
      {showSMA200 && data.sma200 != null && (
        <p>
          <span className="tooltip-label" style={{ color: '#9467bd' }}>SMA 200:</span>
          {' '}
          <span className="tooltip-value">{formatPrice(data.sma200, stock)}</span>
        </p>
      )}
      {showBollinger && data.bollingerUpper != null && (
        <>
          <p>
            <span className="tooltip-label" style={{ color: '#e74c3c' }}>BB Upper:</span>
            {' '}
            <span className="tooltip-value">{formatPrice(data.bollingerUpper, stock)}</span>
          </p>
          <p>
            <span className="tooltip-label" style={{ color: '#95a5a6' }}>BB Middle:</span>
            {' '}
            <span className="tooltip-value">{data.bollingerMiddle != null ? formatPrice(data.bollingerMiddle, stock) : 'N/A'}</span>
          </p>
          <p>
            <span className="tooltip-label" style={{ color: '#27ae60' }}>BB Lower:</span>
            {' '}
            <span className="tooltip-value">{data.bollingerLower != null ? formatPrice(data.bollingerLower, stock) : 'N/A'}</span>
          </p>
          {data.bollingerPercentB != null && (
            <p>
              <span className="tooltip-label" style={{ color: '#3498db' }}>%B:</span>
              {' '}
              <span className="tooltip-value">{data.bollingerPercentB.toFixed(2)}</span>
            </p>
          )}
          {data.bollingerBandwidth != null && (
            <p>
              <span className="tooltip-label" style={{ color: '#f39c12' }}>Bandwidth:</span>
              {' '}
              <span className="tooltip-value">{data.bollingerBandwidth.toFixed(2)}%</span>
            </p>
          )}
        </>
      )}
      {showATR && data.atr != null && (
        <p>
          <span className="tooltip-label" style={{ color: '#f39c12' }}>ATR:</span>
          {' '}
          <span className="tooltip-value">{formatPrice(data.atr, stock)}</span>
        </p>
      )}
      {showVWAP && data.vwap != null && (
        <p>
          <span className="tooltip-label" style={{ color: '#17a2b8' }}>VWAP (20):</span>
          {' '}
          <span className="tooltip-value">{formatPrice(data.vwap, stock)}</span>
        </p>
      )}
      {showIchimoku && ((data.ichimoku_conversion != null) || (data.ichimoku_base != null)) && (
        <>
          {data.ichimoku_conversion != null && (
            <p>
              <span className="tooltip-label" style={{ color: '#1f77b4' }}>Ichimoku Tenkan (Conv):</span>
              {' '}
              <span className="tooltip-value">{formatPrice(data.ichimoku_conversion, stock)}</span>
            </p>
          )}
          {data.ichimoku_base != null && (
            <p>
              <span className="tooltip-label" style={{ color: '#ff7f0e' }}>Ichimoku Kijun (Base):</span>
              {' '}
              <span className="tooltip-value">{formatPrice(data.ichimoku_base, stock)}</span>
            </p>
          )}
        </>
      )}
    </div>
  );
};

export default ChartTooltip;

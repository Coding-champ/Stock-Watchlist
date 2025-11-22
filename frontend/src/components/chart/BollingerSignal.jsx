import React from 'react';

/**
 * BollingerSignal
 * Displays Bollinger Bands signal information including squeeze alerts,
 * %B position, bandwidth, and band walking indicators.
 * 
 * @param {Object} bollingerSignal - Signal data from backend
 * @param {boolean} isExpanded - Expansion state
 * @param {Function} onToggle - Callback to toggle expansion
 */
export function BollingerSignal({
  bollingerSignal,
  isExpanded,
  onToggle
}) {
  if (!bollingerSignal) return null;

  return (
    <div className={`collapsible-panel bollinger-signal ${bollingerSignal.squeeze ? 'squeeze' : ''}`}>
      <div 
        className="collapsible-header"
        onClick={onToggle}
      >
        <span className={`collapsible-toggle-icon ${isExpanded ? 'expanded' : ''}`}></span>
        <div style={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
          <span>📊 Bollinger Bands ({bollingerSignal.period || 20})</span>
          {bollingerSignal.squeeze && (
            <span style={{ 
              fontSize: '10px', 
              backgroundColor: '#ffc107', 
              color: '#000', 
              padding: '2px 6px', 
              borderRadius: '10px',
              fontWeight: 'bold'
            }}>
              SQUEEZE!
            </span>
          )}
        </div>
      </div>
      
      <div className={`collapsible-content ${isExpanded ? 'expanded' : ''}`}>
        <div style={{ fontSize: '11px', color: '#666' }}>
          {bollingerSignal.current_percent_b !== null && (
            <div style={{ marginBottom: '4px' }}>
              <span style={{ fontWeight: 'bold' }}>%B:</span> {bollingerSignal.current_percent_b?.toFixed(2) || 'N/A'}
              {bollingerSignal.current_percent_b > 1 && <span style={{ color: '#e74c3c' }}> (über oberem Band)</span>}
              {bollingerSignal.current_percent_b < 0 && <span style={{ color: '#27ae60' }}> (unter unterem Band)</span>}
            </div>
          )}
          {bollingerSignal.current_bandwidth !== null && (
            <div style={{ marginBottom: '4px' }}>
              <span style={{ fontWeight: 'bold' }}>Bandwidth:</span> {bollingerSignal.current_bandwidth?.toFixed(2) || 'N/A'}%
            </div>
          )}
          {bollingerSignal.band_walking && (
            <div style={{ 
              marginTop: '6px', 
              padding: '4px 8px', 
              backgroundColor: bollingerSignal.band_walking === 'upper' ? '#e8f5e9' : '#ffebee',
              borderRadius: '4px',
              fontSize: '10px',
              fontWeight: 'bold',
              color: bollingerSignal.band_walking === 'upper' ? '#2e7d32' : '#c62828'
            }}>
              {bollingerSignal.band_walking === 'upper' ? '📈 Walking Upper Band (Uptrend)' : '📉 Walking Lower Band (Downtrend)'}
            </div>
          )}
          {bollingerSignal.signal_reason && (
            <div style={{ 
              marginTop: '6px', 
              padding: '4px 8px', 
              backgroundColor: '#e3f2fd',
              borderRadius: '4px',
              fontSize: '10px',
              fontStyle: 'italic'
            }}>
              💡 {bollingerSignal.signal_reason}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

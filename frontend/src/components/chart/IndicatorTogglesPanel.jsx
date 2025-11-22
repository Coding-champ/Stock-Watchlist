import React from 'react';

/**
 * IndicatorTogglesPanel
 * Extracted panel housing indicator, event marker and Fibonacci controls.
 * Pure presentational; all state passed in from parent to keep refactor incremental.
 */
export function IndicatorTogglesPanel({
  // indicator toggles
  showSMA50, setShowSMA50,
  showSMA200, setShowSMA200,
  showVolume, setShowVolume,
  showRSI, setShowRSI,
  showStochastic, setShowStochastic,
  showMACD, setShowMACD,
  showBollinger, setShowBollinger,
  showIchimoku, setShowIchimoku,
  showATR, setShowATR,
  showVWAP, setShowVWAP,
  showCrossovers, setShowCrossovers,
  showDivergences, setShowDivergences,
  // event toggles
  showDividends, setShowDividends,
  showSplits, setShowSplits,
  showEarnings, setShowEarnings,
  // fibonacci controls
  showFibonacci, setShowFibonacci,
  fibonacciPanelExpanded, setFibonacciPanelExpanded,
  fibonacciType, setFibonacciType,
  selectedFibLevels, setSelectedFibLevels,
  selectedExtensionLevels, setSelectedExtensionLevels,
  fibonacciData
}) {
  return (
    <div className="control-group">
      <label>Indikatoren:</label>
      <div className="indicator-toggles">
        {/* Basic Indicators */}
        <label className="checkbox-label">
          <input type="checkbox" checked={showSMA50} onChange={(e) => setShowSMA50(e.target.checked)} />
          <span>SMA 50</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showSMA200} onChange={(e) => setShowSMA200(e.target.checked)} />
          <span>SMA 200</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showVolume} onChange={(e) => setShowVolume(e.target.checked)} />
          <span>Volume</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showRSI} onChange={(e) => setShowRSI(e.target.checked)} />
          <span>RSI</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showStochastic} onChange={(e) => setShowStochastic(e.target.checked)} />
          <span>Stochastic</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showMACD} onChange={(e) => setShowMACD(e.target.checked)} />
          <span>MACD</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showBollinger} onChange={(e) => setShowBollinger(e.target.checked)} />
          <span>Bollinger Bands</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showIchimoku} onChange={(e) => setShowIchimoku(e.target.checked)} />
          <span>Ichimoku Cloud</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showATR} onChange={(e) => setShowATR(e.target.checked)} />
          <span>ATR</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showVWAP} onChange={(e) => setShowVWAP(e.target.checked)} />
          <span>VWAP</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showCrossovers} onChange={(e) => setShowCrossovers(e.target.checked)} />
          <span>🌟 Golden/Death Cross</span>
        </label>
        <label className="checkbox-label">
          <input type="checkbox" checked={showDivergences} onChange={(e) => setShowDivergences(e.target.checked)} />
          <span>🔺 RSI/MACD Divergenzen</span>
        </label>

        {/* Event Markers */}
        <label className="checkbox-label" style={{ color: '#3b82f6' }}>
          <input type="checkbox" checked={showDividends} onChange={(e) => setShowDividends(e.target.checked)} />
          <span>💰 Dividenden</span>
        </label>
        <label className="checkbox-label" style={{ color: '#f97316' }}>
          <input type="checkbox" checked={showSplits} onChange={(e) => setShowSplits(e.target.checked)} />
          <span>✂️ Aktiensplits</span>
        </label>
        <label className="checkbox-label" style={{ color: '#22c55e' }}>
          <input type="checkbox" checked={showEarnings} onChange={(e) => setShowEarnings(e.target.checked)} />
          <span>📊 Earnings</span>
        </label>

        {/* Fibonacci Controls */}
        <div className="collapsible-panel">
          <div className="collapsible-header" onClick={() => setFibonacciPanelExpanded(!fibonacciPanelExpanded)}>
            <span className={`collapsible-toggle-icon ${fibonacciPanelExpanded ? 'expanded' : ''}`}></span>
            <label className="checkbox-label" onClick={(e) => e.stopPropagation()}>
              <input type="checkbox" checked={showFibonacci} onChange={(e) => setShowFibonacci(e.target.checked)} />
              <span style={{ fontWeight: 'bold' }}>📐 Fibonacci Levels</span>
            </label>
          </div>
          <div className={`collapsible-content ${fibonacciPanelExpanded && showFibonacci && fibonacciData ? 'expanded' : ''}`}>
            {showFibonacci && fibonacciData && (
              <div>
                <div style={{ marginBottom: '10px', display: 'flex', gap: '5px' }}>
                  <button
                    onClick={() => setFibonacciType('retracement')}
                    style={{
                      padding: '5px 12px', fontSize: '12px', border: '1px solid #007bff', borderRadius: '4px',
                      backgroundColor: fibonacciType === 'retracement' ? '#007bff' : 'white',
                      color: fibonacciType === 'retracement' ? 'white' : '#007bff', cursor: 'pointer',
                      fontWeight: fibonacciType === 'retracement' ? 'bold' : 'normal', transition: 'all var(--motion-short)'
                    }}
                  >📉 Retracement</button>
                  <button
                    onClick={() => setFibonacciType('extension')}
                    style={{
                      padding: '5px 12px', fontSize: '12px', border: '1px solid #28a745', borderRadius: '4px',
                      backgroundColor: fibonacciType === 'extension' ? '#28a745' : 'white',
                      color: fibonacciType === 'extension' ? 'white' : '#28a745', cursor: 'pointer',
                      fontWeight: fibonacciType === 'extension' ? 'bold' : 'normal', transition: 'all var(--motion-short)'
                    }}
                  >📈 Extension</button>
                </div>
                <div style={{ fontSize: '11px', backgroundColor: 'white', padding: '8px', borderRadius: '4px', border: '1px solid #dee2e6' }}>
                  {fibonacciType === 'retracement' ? (
                    Object.entries(selectedFibLevels).map(([lvl, enabled]) => (
                      <label key={lvl} style={{ marginRight: 8 }}>
                        <input
                          type="checkbox"
                          checked={enabled}
                          onChange={(e) => {
                            setSelectedFibLevels(prev => ({ ...prev, [lvl]: e.target.checked }));
                          }}
                        /> {lvl}%
                      </label>
                    ))
                  ) : (
                    Object.entries(selectedExtensionLevels).map(([lvl, enabled]) => (
                      <label key={lvl} style={{ marginRight: 8 }}>
                        <input
                          type="checkbox"
                          checked={enabled}
                          onChange={(e) => {
                            setSelectedExtensionLevels(prev => ({ ...prev, [lvl]: e.target.checked }));
                          }}
                        /> {lvl}%
                      </label>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

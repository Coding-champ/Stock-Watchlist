import React from 'react';

export function ChartControls({
  periods,
  period,
  setPeriod,
  showCustomDatePicker,
  setShowCustomDatePicker,
  customStartDate,
  setCustomStartDate,
  customEndDate,
  setCustomEndDate,
  chartType,
  setChartType,
  CHART_TYPES,
  isLogScale,
  setIsLogScale,
  isPercentageView,
  setIsPercentageView,
  onApplyCustomRange,
  exportToPNG,
  exportToCSV
}) {
  return (
    <div className="chart-controls">
      <div className="control-group">
        <label>Zeitraum:</label>
        <div className="period-buttons">
          {periods.map(p => (
            <button
              key={p.value}
              className={`period-button ${period === p.value ? 'active' : ''}`}
              onClick={() => {
                setPeriod(p.value);
                if (p.value === 'custom') {
                  setShowCustomDatePicker(true);
                } else {
                  setShowCustomDatePicker(false);
                }
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
        {showCustomDatePicker && period === 'custom' && (
          <div className="custom-date-picker">
            <div className="date-input-group">
              <label>Von:</label>
              <input
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                max={customEndDate || new Date().toISOString().split('T')[0]}
              />
            </div>
            <div className="date-input-group">
              <label>Bis:</label>
              <input
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                min={customStartDate}
                max={new Date().toISOString().split('T')[0]}
              />
            </div>
            <button
              className="apply-custom-date"
              onClick={onApplyCustomRange}
              disabled={!customStartDate || !customEndDate}
            >
              Anwenden
            </button>
          </div>
        )}
      </div>

      <div className="control-group">
        <label>Chart-Typ:</label>
        <div className="chart-type-buttons">
          <button
            className={`type-button ${chartType === CHART_TYPES.LINE ? 'active' : ''}`}
            onClick={() => setChartType(CHART_TYPES.LINE)}
          >
            📈 Line
          </button>
          <button
            className={`type-button ${chartType === CHART_TYPES.CANDLESTICK ? 'active' : ''}`}
            onClick={() => setChartType(CHART_TYPES.CANDLESTICK)}
          >
            📊 Candlestick
          </button>
        </div>
      </div>

      <div className="control-group">
        <label>Skalierung:</label>
        <div className="indicator-toggles">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={isLogScale}
              onChange={(e) => setIsLogScale(e.target.checked)}
            />
            <span>Logarithmisch</span>
          </label>
          {chartType === CHART_TYPES.CANDLESTICK ? (
            <label className="checkbox-label disabled">
              <input type="checkbox" checked={false} disabled />
              <span>Prozent (nur Line)</span>
            </label>
          ) : (
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isPercentageView}
                onChange={(e) => setIsPercentageView(e.target.checked)}
              />
              <span>Prozent</span>
            </label>
          )}
        </div>
      </div>

      <div className="control-group">
        <label>Export:</label>
        <div className="export-buttons">
          <button onClick={exportToPNG} className="export-button">🖼️ PNG</button>
          <button onClick={exportToCSV} className="export-button">📄 CSV</button>
        </div>
      </div>
    </div>
  );
}

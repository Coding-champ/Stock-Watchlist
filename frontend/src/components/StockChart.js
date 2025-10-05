import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ComposedChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea
} from 'recharts';
import './StockChart.css';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

// Time period options
const TIME_PERIODS = [
  { value: '1d', label: '1D', interval: '5m' },
  { value: '5d', label: '5D', interval: '15m' },
  { value: '1mo', label: '1M', interval: '1h' },
  { value: '3mo', label: '3M', interval: '1d' },
  { value: '6mo', label: '6M', interval: '1d' },
  { value: '1y', label: '1Y', interval: '1d' },
  { value: '3y', label: '3Y', interval: '1wk' },
  { value: '5y', label: '5Y', interval: '1wk' },
  { value: 'max', label: 'MAX', interval: '1wk' },
  { value: 'custom', label: 'Individuell', interval: '1d' }
];

// Chart type options
const CHART_TYPES = {
  LINE: 'line',
  CANDLESTICK: 'candlestick'
};

function StockChart({ stock, isEmbedded = false }) {
  const [chartData, setChartData] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [indicators, setIndicators] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Chart settings
  const [period, setPeriod] = useState('1y');
  const [chartType, setChartType] = useState(CHART_TYPES.LINE);
  
  // Custom date range
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  
  // Indicator toggles
  const [showSMA50, setShowSMA50] = useState(true);
  const [showSMA200, setShowSMA200] = useState(true);
  const [showVolume, setShowVolume] = useState(true);
  const [showRSI, setShowRSI] = useState(false);
  const [showMACD, setShowMACD] = useState(false);

  // Fetch chart data
  const fetchChartData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const periodConfig = TIME_PERIODS.find(p => p.value === period);
      const interval = periodConfig?.interval || '1d';
      
      // Build URL with period or custom dates
      let chartUrl = `${API_BASE}/stock-data/${stock.id}/chart?interval=${interval}&include_volume=true`;
      
      if (period === 'custom' && customStartDate && customEndDate) {
        chartUrl += `&start=${customStartDate}&end=${customEndDate}`;
      } else {
        chartUrl += `&period=${period}`;
      }
      
      // Fetch main chart data
      const chartResponse = await fetch(chartUrl);
      
      if (!chartResponse.ok) {
        throw new Error('Failed to fetch chart data');
      }
      
      const chartJson = await chartResponse.json();
      
      // Fetch indicators if needed
      let indicatorsJson = null;
      // Always fetch all indicators to avoid re-loading when toggling visibility
      const indicatorsList = ['sma_50', 'sma_200', 'rsi', 'macd'];
      
      const indicatorsResponse = await fetch(
        `${API_BASE}/stock-data/${stock.id}/technical-indicators?period=${period}&${indicatorsList.map(i => `indicators=${i}`).join('&')}`
      );
      
      if (indicatorsResponse.ok) {
        indicatorsJson = await indicatorsResponse.json();
      }
      
      // Transform data for Recharts
      const transformedData = chartJson.dates.map((date, index) => ({
        date: new Date(date).toLocaleDateString('de-DE', { 
          month: 'short', 
          day: 'numeric',
          ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
        }),
        fullDate: date,
        open: chartJson.open[index],
        high: chartJson.high[index],
        low: chartJson.low[index],
        close: chartJson.close[index],
        volume: chartJson.volume ? chartJson.volume[index] : null,
        sma50: indicatorsJson?.indicators?.sma_50?.[index],
        sma200: indicatorsJson?.indicators?.sma_200?.[index],
        rsi: indicatorsJson?.indicators?.rsi?.[index],
        macd: indicatorsJson?.indicators?.macd?.macd?.[index],
        macdSignal: indicatorsJson?.indicators?.macd?.signal?.[index],
        macdHistogram: indicatorsJson?.indicators?.macd?.histogram?.[index]
      }));
      
      // Calculate 10-day Volume Moving Average
      const volumeMA10 = transformedData.map((item, index) => {
        if (index < 9) {
          // Not enough data for 10-day average
          return null;
        }
        
        let sum = 0;
        for (let i = 0; i < 10; i++) {
          const vol = transformedData[index - i].volume;
          if (vol) {
            sum += vol;
          }
        }
        return sum / 10;
      });
      
      // Add volumeMA10 to transformed data
      transformedData.forEach((item, index) => {
        item.volumeMA10 = volumeMA10[index];
      });
      
      setChartData(transformedData);
      // Store indicators for potential future use
      // eslint-disable-next-line no-unused-vars
      setIndicators(indicatorsJson);
      
    } catch (err) {
      console.error('Error fetching chart data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [stock.id, period]);

  useEffect(() => {
    fetchChartData();
  }, [fetchChartData]);

  // Export functions
  const exportToPNG = () => {
    // TODO: Implement PNG export using html2canvas
    alert('PNG Export wird implementiert...');
  };

  const exportToCSV = () => {
    if (!chartData) return;
    
    const headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'];
    const csvContent = [
      headers.join(','),
      ...chartData.map(row => [
        row.fullDate,
        row.open,
        row.high,
        row.low,
        row.close,
        row.volume || ''
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${stock.ticker_symbol}_${period}_chart_data.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Custom tooltip with cursor-based positioning
  const CustomTooltip = ({ active, payload, label, coordinate }) => {
    if (!active || !payload || payload.length === 0 || !coordinate) return null;
    
    const data = payload[0].payload;
    
    // Position tooltip left of cursor (offset by -220px to avoid covering chart)
    // If too close to left edge, position it to the right instead
    const offsetX = coordinate.x < 250 ? 15 : -220;
    const offsetY = -10; // Slightly above cursor
    
    const tooltipStyle = {
      position: 'absolute',
      left: `${coordinate.x + offsetX}px`,
      top: `${coordinate.y + offsetY}px`,
      pointerEvents: 'none', // Don't interfere with mouse events
      transform: 'translateY(-50%)', // Center vertically on cursor
    };
    
    return (
      <div className="chart-tooltip" style={tooltipStyle}>
        <p className="tooltip-date">{label}</p>
        {chartType === CHART_TYPES.CANDLESTICK ? (
          <>
            <p>
              <span className="tooltip-label">Close:</span>
              {' '}
              <span className="tooltip-value">${data.close?.toFixed(2)}</span>
            </p>
          </>
        ) : (
          <p>
            <span className="tooltip-label">Price:</span>
            {' '}
            <span className="tooltip-value">${data.close?.toFixed(2)}</span>
          </p>
        )}
        {showVolume && data.volume && (
          <p>
            <span className="tooltip-label">Volume:</span>
            {' '}
            <span className="tooltip-value">{(data.volume / 1000000).toFixed(2)}M</span>
          </p>
        )}
        {showSMA50 && data.sma50 && (
          <p>
            <span className="tooltip-label" style={{ color: '#ff7f0e' }}>SMA 50:</span>
            {' '}
            <span className="tooltip-value">${data.sma50?.toFixed(2)}</span>
          </p>
        )}
        {showSMA200 && data.sma200 && (
          <p>
            <span className="tooltip-label" style={{ color: '#9467bd' }}>SMA 200:</span>
            {' '}
            <span className="tooltip-value">${data.sma200?.toFixed(2)}</span>
          </p>
        )}
      </div>
    );
  };

  // Custom Dot component for RSI line to show color based on value
  const RsiCustomDot = (props) => {
    const { cx, cy, payload } = props;
    if (!payload || payload.rsi === null || payload.rsi === undefined) return null;
    
    let fill = '#8e44ad'; // Default purple
    if (payload.rsi >= 70) {
      fill = '#e74c3c'; // Red for overbought
    } else if (payload.rsi <= 30) {
      fill = '#27ae60'; // Green for oversold
    }
    
    return <circle cx={cx} cy={cy} r={0} fill={fill} />;
  };

  // Candlestick custom shape for Bar component
  const Candlestick = (props) => {
    const { x, y, width, height } = props;
    
    // Get the data item for this bar
    const dataIndex = props.index;
    if (!chartData || !chartData[dataIndex]) return null;
    
    const item = chartData[dataIndex];
    
    if (!item.open || !item.high || !item.low || !item.close) return null;

    // Determine color based on price movement
    const isGreen = item.close >= item.open;
    const color = isGreen ? '#26a69a' : '#ef5350';

    // When Y-axis starts at 0, the Bar component gives us:
    // - y: pixel position for 'high' value
    // - height: pixel height from 'high' to 0
    // We need to calculate positions for open, close, and low
    
    // The key insight: if high is at 'y' and 0 is at 'y + height',
    // then the scale is: pixels_per_dollar = height / high
    const pixelsPerDollar = height / item.high;
    
    // Calculate Y positions for each price point
    // For a price P: its Y position = y + (high - P) * pixelsPerDollar
    const highY = y;
    const lowY = y + (item.high - item.low) * pixelsPerDollar;
    const openY = y + (item.high - item.open) * pixelsPerDollar;
    const closeY = y + (item.high - item.close) * pixelsPerDollar;
    
    // Body dimensions
    const bodyTop = Math.min(openY, closeY);
    const bodyHeight = Math.abs(closeY - openY) || 1; // Minimum 1px for doji
    
    // Candlestick width
    const candleWidth = Math.min(width * 0.8, 10);
    const wickX = x + width / 2;

    return (
      <g>
        {/* Wick line (from high to low) */}
        <line
          x1={wickX}
          y1={highY}
          x2={wickX}
          y2={lowY}
          stroke={color}
          strokeWidth={1}
        />
        {/* Body rectangle */}
        <rect
          x={x + (width - candleWidth) / 2}
          y={bodyTop}
          width={candleWidth}
          height={bodyHeight}
          fill={color}
          stroke={color}
          strokeWidth={1}
        />
      </g>
    );
  };

  if (loading) {
    return (
      <div className="stock-chart-container">
        <div className="chart-loading">
          <div className="loading-spinner"></div>
          <p>Lade Chart-Daten...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stock-chart-container">
        <div className="chart-error">
          <p>❌ Fehler beim Laden der Chart-Daten</p>
          <p className="error-message">{error}</p>
          <button onClick={fetchChartData} className="retry-button">
            Erneut versuchen
          </button>
        </div>
      </div>
    );
  }

  if (!chartData || chartData.length === 0) {
    return (
      <div className="stock-chart-container">
        <div className="chart-error">
          <p>Keine Chart-Daten verfügbar</p>
        </div>
      </div>
    );
  }

  // Calculate min/max for Y-axis domain
  const prices = chartData.map(d => d.close).filter(p => p != null);
  const minPrice = Math.min(...prices) * 0.98;
  const maxPrice = Math.max(...prices) * 1.02;

  return (
    <div className="stock-chart-container">
      {/* Chart Controls */}
      <div className="chart-controls">
        <div className="control-group">
          <label>Zeitraum:</label>
          <div className="period-buttons">
            {TIME_PERIODS.map(p => (
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
          
          {/* Custom Date Range Picker */}
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
                onClick={() => fetchChartData()}
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
          <label>Indikatoren:</label>
          <div className="indicator-toggles">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showSMA50}
                onChange={(e) => setShowSMA50(e.target.checked)}
              />
              <span>SMA 50</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showSMA200}
                onChange={(e) => setShowSMA200(e.target.checked)}
              />
              <span>SMA 200</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showVolume}
                onChange={(e) => setShowVolume(e.target.checked)}
              />
              <span>Volume</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showRSI}
                onChange={(e) => setShowRSI(e.target.checked)}
              />
              <span>RSI</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showMACD}
                onChange={(e) => setShowMACD(e.target.checked)}
              />
              <span>MACD</span>
            </label>
          </div>
        </div>

        <div className="control-group">
          <label>Export:</label>
          <div className="export-buttons">
            <button onClick={exportToPNG} className="export-button">
              🖼️ PNG
            </button>
            <button onClick={exportToCSV} className="export-button">
              📄 CSV
            </button>
          </div>
        </div>
      </div>

      {/* Main Price Chart */}
      <div className="chart-section">
        <h3 className="chart-title">
          {stock.name} ({stock.ticker_symbol}) - {period.toUpperCase()}
        </h3>
        
        <ResponsiveContainer width="100%" height={400}>
          {chartType === CHART_TYPES.LINE ? (
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#007bff" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#007bff" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 11, angle: -45, textAnchor: 'end' }}
                height={80}
                interval="preserveStartEnd"
                minTickGap={50}
              />
              <YAxis 
                domain={[0, 'auto']}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${value.toFixed(2)}`}
              />
              <Tooltip 
                content={<CustomTooltip />}
                cursor={{ stroke: '#007bff', strokeWidth: 1, strokeDasharray: '5 5' }}
                wrapperStyle={{ pointerEvents: 'none' }}
                isAnimationActive={false}
              />
              <Legend />
              
              {/* Starting price reference line */}
              {chartData && chartData.length > 0 && chartData[0].close && (
                <ReferenceLine 
                  y={chartData[0].close} 
                  stroke="#000000" 
                  strokeDasharray="5 5" 
                  strokeWidth={1.5}
                  label={{ 
                    value: `$${chartData[0].close.toFixed(2)}`, 
                    position: "right", 
                    fill: "#000000", 
                    fontSize: 10,
                    fontWeight: "bold"
                  }}
                />
              )}
              
              <Area
                type="monotone"
                dataKey="close"
                stroke="#007bff"
                strokeWidth={2}
                fill="url(#colorPrice)"
                name="Price"
              />
              
              {showSMA50 && (
                <Line
                  type="monotone"
                  dataKey="sma50"
                  stroke="#ff7f0e"
                  strokeWidth={2}
                  dot={false}
                  name="SMA 50"
                />
              )}
              
              {showSMA200 && (
                <Line
                  type="monotone"
                  dataKey="sma200"
                  stroke="#9467bd"
                  strokeWidth={2}
                  dot={false}
                  name="SMA 200"
                />
              )}
            </ComposedChart>
          ) : (
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 11, angle: -45, textAnchor: 'end' }}
                height={80}
                interval="preserveStartEnd"
                minTickGap={50}
              />
              <YAxis 
                domain={[0, 'auto']}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${value.toFixed(2)}`}
              />
              <Tooltip 
                content={<CustomTooltip />}
                cursor={{ stroke: '#26a69a', strokeWidth: 1, strokeDasharray: '5 5' }}
                wrapperStyle={{ pointerEvents: 'none' }}
                isAnimationActive={false}
              />
              <Legend />
              
              {/* Starting price reference line */}
              {chartData && chartData.length > 0 && chartData[0].close && (
                <ReferenceLine 
                  y={chartData[0].close} 
                  stroke="#000000" 
                  strokeDasharray="5 5" 
                  strokeWidth={1.5}
                  label={{ 
                    value: `Start: $${chartData[0].close.toFixed(2)}`, 
                    position: "right", 
                    fill: "#000000", 
                    fontSize: 10,
                    fontWeight: "bold"
                  }}
                />
              )}
              
              {/* Candlesticks using Bar with custom shape */}
              <Bar 
                dataKey="high" 
                shape={<Candlestick />}
                isAnimationActive={false}
              />
              
              {showSMA50 && (
                <Line
                  type="monotone"
                  dataKey="sma50"
                  stroke="#ff7f0e"
                  strokeWidth={2}
                  dot={false}
                  name="SMA 50"
                />
              )}
              
              {showSMA200 && (
                <Line
                  type="monotone"
                  dataKey="sma200"
                  stroke="#9467bd"
                  strokeWidth={2}
                  dot={false}
                  name="SMA 200"
                />
              )}
            </ComposedChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Volume Chart */}
      {showVolume && (
        <div className="chart-section">
          <h4 className="chart-subtitle">Volume</h4>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 9, angle: -45, textAnchor: 'end' }}
                height={20}
                interval="preserveStartEnd"
                minTickGap={40}
              />
              <YAxis 
                tick={{ fontSize: 10 }}
                tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`}
              />
              <Tooltip 
                formatter={(value, name) => {
                  if (name === 'Volume MA (10)') {
                    return [`${(value / 1000000).toFixed(2)}M`, name];
                  }
                  return [`${(value / 1000000).toFixed(2)}M`, 'Volume'];
                }}
                labelStyle={{ color: '#666' }}
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.98)', 
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  padding: '10px'
                }}
                cursor={{ fill: 'rgba(0, 123, 255, 0.1)' }}
              />
              <Legend />
              <Bar dataKey="volume" fill="#007bff" opacity={0.6} name="Volume" />
              <Line 
                type="monotone" 
                dataKey="volumeMA10" 
                stroke="#ff6b6b" 
                strokeWidth={2}
                dot={false}
                name="Volume MA (10)"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* RSI Chart */}
      {showRSI && (
        <div className="chart-section">
          <h4 className="chart-subtitle">RSI (14)</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                {/* Gradient for overbought area */}
                <linearGradient id="overboughtGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#e74c3c" stopOpacity={0.15}/>
                  <stop offset="100%" stopColor="#e74c3c" stopOpacity={0.05}/>
                </linearGradient>
                {/* Gradient for oversold area */}
                <linearGradient id="oversoldGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#27ae60" stopOpacity={0.05}/>
                  <stop offset="100%" stopColor="#27ae60" stopOpacity={0.15}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 9, angle: -45, textAnchor: 'end' }}
                height={60}
                interval="preserveStartEnd"
                minTickGap={40}
              />
              <YAxis 
                domain={[0, 100]}
                tick={{ fontSize: 10 }}
                ticks={[0, 30, 50, 70, 100]}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.98)', 
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  padding: '10px'
                }}
                labelStyle={{ fontWeight: 'bold', color: '#333' }}
                cursor={{ stroke: '#6c63ff', strokeWidth: 1, strokeDasharray: '5 5' }}
              />
              <Legend />
              
              {/* Colored background areas */}
              <ReferenceArea y1={70} y2={100} fill="url(#overboughtGradient)" fillOpacity={1} />
              <ReferenceArea y1={0} y2={30} fill="url(#oversoldGradient)" fillOpacity={1} />
              
              {/* Overbought/Oversold lines */}
              <ReferenceLine y={70} stroke="#e74c3c" strokeDasharray="3 3" strokeWidth={1.5} label={{ value: "Overbought (70)", position: "right", fill: "#e74c3c", fontSize: 11 }} />
              <ReferenceLine y={30} stroke="#27ae60" strokeDasharray="3 3" strokeWidth={1.5} label={{ value: "Oversold (30)", position: "right", fill: "#27ae60", fontSize: 11 }} />
              <ReferenceLine y={50} stroke="#95a5a6" strokeDasharray="2 2" strokeWidth={1} />
              
              <Line
                type="monotone"
                dataKey="rsi"
                stroke="#8e44ad"
                strokeWidth={2.5}
                dot={false}
                name="RSI"
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* MACD Chart */}
      {showMACD && (
        <div className="chart-section">
          <h4 className="chart-subtitle">MACD</h4>
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 9, angle: -45, textAnchor: 'end' }}
                height={60}
                interval="preserveStartEnd"
                minTickGap={40}
              />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.98)', 
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  padding: '10px'
                }}
                labelStyle={{ fontWeight: 'bold', color: '#333' }}
                cursor={{ stroke: '#3498db', strokeWidth: 1, strokeDasharray: '5 5' }}
              />
              <Legend />
              
              <ReferenceLine y={0} stroke="#000" />
              
              <Bar 
                dataKey="macdHistogram" 
                fill="#3498db" 
                opacity={0.6}
                name="Histogram"
              />
              <Line
                type="monotone"
                dataKey="macd"
                stroke="#e74c3c"
                strokeWidth={2}
                dot={false}
                name="MACD"
              />
              <Line
                type="monotone"
                dataKey="macdSignal"
                stroke="#27ae60"
                strokeWidth={2}
                dot={false}
                name="Signal"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Chart Info */}
      <div className="chart-info">
        <p className="info-text">
          <small>
            📊 Datenpunkte: {chartData.length} | 
            🔄 Cache: {chartData[0]?.from_cache ? 'Ja' : 'Nein'} | 
            📅 Stand: {new Date().toLocaleString('de-DE')}
          </small>
        </p>
      </div>
    </div>
  );
}

export default StockChart;

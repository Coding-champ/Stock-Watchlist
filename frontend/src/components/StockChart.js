import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  LineChart,
  Line,
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
import VolumeProfile from './VolumeProfile';
import VolumeProfileOverlay from './VolumeProfileOverlay';
import { StochasticChart } from './AdvancedCharts';
import './StockChart.css';

import API_BASE from '../config';
import { formatPrice } from '../utils/currencyUtils';

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

function StockChart({ stock, isEmbedded = false, onLatestVwap }) {
  const [chartData, setChartData] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [indicators, setIndicators] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [crossoverData, setCrossoverData] = useState(null);
  const [divergenceData, setDivergenceData] = useState(null);
  
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
  const [showStochastic, setShowStochastic] = useState(false);
  const [showBollinger, setShowBollinger] = useState(false);
  const [showATR, setShowATR] = useState(false);
  const [showVWAP, setShowVWAP] = useState(false);
  const [showCrossovers, setShowCrossovers] = useState(true);
  const [showDivergences, setShowDivergences] = useState(true);
  
  // Fibonacci toggles
  const [showFibonacci, setShowFibonacci] = useState(false);
  const [fibonacciType, setFibonacciType] = useState('retracement'); // 'retracement' or 'extension'
  const [selectedFibLevels, setSelectedFibLevels] = useState({
    '23.6': false,
    '38.2': false,
    '50.0': true,
    '61.8': true,
    '78.6': false
  });
  const [selectedExtensionLevels, setSelectedExtensionLevels] = useState({
    '127.2': true,
    '161.8': true,
    '200.0': false,
    '261.8': false
  });
  const [fibonacciData, setFibonacciData] = useState(null);
  
  // Bollinger Bands signal data
  const [bollingerSignal, setBollingerSignal] = useState(null);
  
  // Support/Resistance toggles
  const [showSupportResistance, setShowSupportResistance] = useState(false);
  const [supportResistanceData, setSupportResistanceData] = useState(null);

  // Volume Profile toggles
  const [showVolumeProfile, setShowVolumeProfile] = useState(false);
  const [showVolumeProfileOverlay, setShowVolumeProfileOverlay] = useState(false);
  const [volumeProfileLevels, setVolumeProfileLevels] = useState(null);
  const [xAxisTicks, setXAxisTicks] = useState(null);

  // Memoized callback for Volume Profile data loading
  const handleProfileLoad = useCallback((levels) => {
    setVolumeProfileLevels(levels);
  }, []);

  // Helper function to convert period to days
  const getPeriodDays = (period) => {
    const periodMap = {
      '1d': 1,
      '5d': 5,
      '1mo': 30,
      '3mo': 90,
      '6mo': 180,
      '1y': 365,
      '3y': 1095,
      '5y': 1825,
      'max': 3650  // ~10 years
    };
    
    if (period === 'custom' && customStartDate && customEndDate) {
      const start = new Date(customStartDate);
      const end = new Date(customEndDate);
      const diffTime = Math.abs(end - start);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays;
    }
    
    return periodMap[period] || 30;
  };

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
      
  // Fetch indicators separately as a fallback, but prefer server-provided indicators
  let indicatorsJson = null;
  // Always fetch all indicators to avoid re-loading when toggling visibility (used as fallback)
  // Include 'stochastic' so the frontend can render the Slow Stochastic subchart and Auswertung
  const indicatorsList = ['sma_50', 'sma_200', 'rsi', 'macd', 'bollinger', 'atr', 'vwap', 'stochastic'];
      
      let indicatorsResponse = await fetch(
        `${API_BASE}/stock-data/${stock.id}/technical-indicators?period=${period}&${indicatorsList.map(i => `indicators=${i}`).join('&')}`
      );
      
      if (!indicatorsResponse.ok) {
        // Retry once if the indicators endpoint failed (transient network/server issue)
        try {
          console.warn('Indicators endpoint failed, retrying once...', indicatorsResponse.status);
          indicatorsResponse = await fetch(
            `${API_BASE}/stock-data/${stock.id}/technical-indicators?period=${period}&${indicatorsList.map(i => `indicators=${i}`).join('&')}`
          );
        } catch (e) {
          console.warn('Indicators retry threw error', e);
        }
      }

      if (indicatorsResponse && indicatorsResponse.ok) {
        indicatorsJson = await indicatorsResponse.json();
      }

  // Merge indicators: prefer chart payload indicators (they include warmup/alignment),
  // but fall back to the separate indicators endpoint for any missing series.
  const mergedFromApi = indicatorsJson && indicatorsJson.indicators ? indicatorsJson.indicators : {};
  const chartIndicators = chartJson && chartJson.indicators ? chartJson.indicators : {};
  const sourceIndicators = { ...mergedFromApi, ...chartIndicators };
      
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
        sma50: sourceIndicators?.sma_50?.[index],
        sma200: sourceIndicators?.sma_200?.[index],
        rsi: sourceIndicators?.rsi?.[index],
        // Stochastic series (k_percent and d_percent) if provided by backend
        k_percent: sourceIndicators?.stochastic?.k_percent?.[index],
        d_percent: sourceIndicators?.stochastic?.d_percent?.[index],
        macd: sourceIndicators?.macd?.macd?.[index] ?? sourceIndicators?.macd?.macd?.[index],
        macdSignal: sourceIndicators?.macd?.signal?.[index] ?? sourceIndicators?.macd?.signal?.[index],
        // support both 'hist' and 'histogram' keys returned by different codepaths
        macdHistogram: sourceIndicators?.macd?.histogram?.[index] ?? sourceIndicators?.macd?.hist?.[index],
        bollingerUpper: sourceIndicators?.bollinger?.upper?.[index],
        bollingerMiddle: sourceIndicators?.bollinger?.middle?.[index] ?? sourceIndicators?.bollinger?.sma?.[index],
        bollingerLower: sourceIndicators?.bollinger?.lower?.[index],
        bollingerPercentB: sourceIndicators?.bollinger?.percent_b?.[index],
        bollingerBandwidth: sourceIndicators?.bollinger?.bandwidth?.[index],
        atr: sourceIndicators?.atr?.[index],
        vwap: sourceIndicators?.vwap?.[index],
        // prefer server-provided volume moving averages if present
        volumeMA10: sourceIndicators?.volumeMA10?.[index],
        volumeMA20: sourceIndicators?.volumeMA20?.[index]
      }));

      // If the technical-indicators endpoint didn't provide VWAP series,
      // compute a simple rolling VWAP (20-period) from close and volume
      // so the chart can still display a VWAP line when the backend omits it.
  const hasVwapFromApi = !!(sourceIndicators && Array.isArray(sourceIndicators.vwap) && sourceIndicators.vwap.some(v => v !== null && v !== undefined));
  if (!hasVwapFromApi) {
        const windowSize = 20;
        for (let i = 0; i < transformedData.length; i++) {
          let volSum = 0;
          let pvSum = 0;
          // look back up to windowSize points (including current)
          for (let j = Math.max(0, i - (windowSize - 1)); j <= i; j++) {
            const rec = transformedData[j];
            const close = rec?.close;
            const vol = rec?.volume;
            if (typeof close === 'number' && typeof vol === 'number' && vol > 0) {
              pvSum += close * vol;
              volSum += vol;
            }
          }
          transformedData[i].vwap = volSum > 0 ? (pvSum / volSum) : null;
        }
      }
      
      // Calculate 10-day and 20-day Volume Moving Averages only if server didn't provide them
      const needVolMA10 = !transformedData.some(d => d.volumeMA10 !== undefined && d.volumeMA10 !== null);
      const needVolMA20 = !transformedData.some(d => d.volumeMA20 !== undefined && d.volumeMA20 !== null);

      if (needVolMA10) {
        const volumeMA10 = transformedData.map((item, index) => {
          if (index < 9) return null;
          let sum = 0;
          for (let i = 0; i < 10; i++) {
            const vol = transformedData[index - i].volume;
            if (vol) sum += vol;
          }
          return sum / 10;
        });
        transformedData.forEach((item, index) => { if (item.volumeMA10 === undefined || item.volumeMA10 === null) item.volumeMA10 = volumeMA10[index]; });
      }
      if (needVolMA20) {
        const volumeMA20 = transformedData.map((item, index) => {
          if (index < 19) return null;
          let sum = 0;
          for (let i = 0; i < 20; i++) {
            const vol = transformedData[index - i].volume;
            if (vol) sum += vol;
          }
          return sum / 20;
        });
        transformedData.forEach((item, index) => { if (item.volumeMA20 === undefined || item.volumeMA20 === null) item.volumeMA20 = volumeMA20[index]; });
      }
      
      // Compute shared X axis tick labels to keep RSI/MACD/Stochastic synchronized.
      const computeTicks = (data, targetCount = 6) => {
        if (!data || data.length === 0) return null;
        const n = Math.min(targetCount, data.length);
        const ticks = [];
        for (let i = 0; i < n; i++) {
          const idx = Math.round(i * (data.length - 1) / (n - 1));
          ticks.push(data[idx].date);
        }
        return ticks;
      };
      const sharedTicks = computeTicks(transformedData, 6);
      setXAxisTicks(sharedTicks);
      setChartData(transformedData);
      // Notify parent about latest VWAP single-value so siblings can use the same source of truth
      try {
        const latest = transformedData.length ? transformedData[transformedData.length - 1].vwap : null;
        if (typeof onLatestVwap === 'function') onLatestVwap(latest);
      } catch (e) {
        // ignore
      }
      // Store indicators for potential future use
      // eslint-disable-next-line no-unused-vars
      setIndicators(indicatorsJson);
      
      // Store Bollinger Bands signal data
      if (indicatorsJson?.indicators?.bollinger) {
        setBollingerSignal({
          squeeze: indicatorsJson.indicators.bollinger.squeeze,
          band_walking: indicatorsJson.indicators.bollinger.band_walking,
          current_percent_b: indicatorsJson.indicators.bollinger.current_percent_b,
          current_bandwidth: indicatorsJson.indicators.bollinger.current_bandwidth,
          signal: indicatorsJson.indicators.bollinger.signal,
          signal_reason: indicatorsJson.indicators.bollinger.signal_reason,
          period: indicatorsJson.indicators.bollinger.period || 20
        });
      }
      
      // Fetch crossover data
      try {
        const crossoverResponse = await fetch(`${API_BASE}/stock-data/${stock.id}/calculated-metrics`);
        if (crossoverResponse.ok) {
          const crossoverJson = await crossoverResponse.json();
          const smaCrossovers = crossoverJson?.metrics?.basic_indicators?.sma_crossovers;
          if (smaCrossovers && smaCrossovers.all_crossovers) {
            setCrossoverData(smaCrossovers);
          } else {
            setCrossoverData(null);
          }
          
          // Fetch Fibonacci data
          const fibonacciLevels = crossoverJson?.metrics?.basic_indicators?.fibonacci_levels;
          if (fibonacciLevels) {
            setFibonacciData(fibonacciLevels);
          } else {
            setFibonacciData(null);
          }
          
          // Fetch Support/Resistance data
          const supportResistance = crossoverJson?.metrics?.basic_indicators?.support_resistance;
          if (supportResistance) {
            setSupportResistanceData(supportResistance);
          } else {
            setSupportResistanceData(null);
          }
        }
      } catch (crossoverErr) {
        console.error('Error fetching crossover data:', crossoverErr);
        // Don't fail the whole chart if crossover data fails
        setCrossoverData(null);
        setFibonacciData(null);
        setSupportResistanceData(null);
      }
      
      // Fetch divergence data
      try {
        const divergenceResponse = await fetch(`${API_BASE}/stock-data/${stock.id}/divergence-analysis`);
        if (divergenceResponse.ok) {
          const divergenceJson = await divergenceResponse.json();
          if (divergenceJson?.rsi_divergence || divergenceJson?.macd_divergence) {
            setDivergenceData(divergenceJson);
          } else {
            setDivergenceData(null);
          }
        }
      } catch (divergenceErr) {
        console.error('Error fetching divergence data:', divergenceErr);
        // Don't fail the whole chart if divergence data fails
        setDivergenceData(null);
      }
      
    } catch (err) {
      console.error('Error fetching chart data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [stock.id, period, customStartDate, customEndDate, onLatestVwap]); // Include all dependencies

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
              <span className="tooltip-value">{formatPrice(data.close, stock)}</span>
            </p>
          </>
        ) : (
          <p>
            <span className="tooltip-label">Price:</span>
            {' '}
            <span className="tooltip-value">{formatPrice(data.close, stock)}</span>
          </p>
        )}
        {showVolume && data.volume && (
          <p>
            <span className="tooltip-label">Volume:</span>
            {' '}
            <span className="tooltip-value">{(data.volume / 1000000).toFixed(2)}M</span>
          </p>
        )}
        {showSMA50 && data.sma50 && data.sma50 !== null && data.sma50 !== undefined && (
            <p>
              <span className="tooltip-label" style={{ color: '#ff7f0e' }}>SMA 50:</span>
              {' '}
              <span className="tooltip-value">{formatPrice(data.sma50, stock)}</span>
            </p>
        )}
        {showSMA200 && data.sma200 && data.sma200 !== null && data.sma200 !== undefined && (
            <p>
            <span className="tooltip-label" style={{ color: '#9467bd' }}>SMA 200:</span>
            {' '}
            <span className="tooltip-value">{formatPrice(data.sma200, stock)}</span>
          </p>
        )}
        {showBollinger && data.bollingerUpper && data.bollingerUpper !== null && data.bollingerUpper !== undefined && (
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
            {data.bollingerPercentB !== undefined && data.bollingerPercentB !== null && (
              <p>
                <span className="tooltip-label" style={{ color: '#3498db' }}>%B:</span>
                {' '}
                <span className="tooltip-value">{data.bollingerPercentB.toFixed(2)}</span>
              </p>
            )}
            {data.bollingerBandwidth !== undefined && data.bollingerBandwidth !== null && (
              <p>
                <span className="tooltip-label" style={{ color: '#f39c12' }}>Bandwidth:</span>
                {' '}
                <span className="tooltip-value">{data.bollingerBandwidth.toFixed(2)}%</span>
              </p>
            )}
          </>
        )}
        {showATR && data.atr && data.atr !== null && data.atr !== undefined && (
            <p>
            <span className="tooltip-label" style={{ color: '#f39c12' }}>ATR:</span>
            {' '}
            <span className="tooltip-value">{formatPrice(data.atr, stock)}</span>
          </p>
        )}
        {showVWAP && data.vwap && data.vwap !== null && data.vwap !== undefined && (
          <p>
            <span className="tooltip-label" style={{ color: '#17a2b8' }}>VWAP (20):</span>
            {' '}
            <span className="tooltip-value">{formatPrice(data.vwap, stock)}</span>
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
    
    // Use a small visible dot (1px) to satisfy linter about unused assignment and be a no-op visually
    return <circle cx={cx} cy={cy} r={1} fill={fill} />;
  };

  // Render Divergence markers (RSI and MACD)
  const renderDivergenceMarkers = () => {
    if (!showDivergences || !divergenceData || !chartData) return null;
    
    const markers = [];
    
    // RSI Divergences
    if (divergenceData.rsi_divergence) {
      const rsiDiv = divergenceData.rsi_divergence;
      
      // Bullish divergence
      if (rsiDiv.bullish_divergence && rsiDiv.divergence_points?.bullish) {
        rsiDiv.divergence_points.bullish.forEach((point, index) => {
          const pointDate = new Date(point.date).toLocaleDateString('de-DE', { 
            month: 'short', 
            day: 'numeric',
            ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
          });
          
          const dataIndex = chartData.findIndex(d => d.date === pointDate);
          if (dataIndex === -1) return;
          
          markers.push(
            <ReferenceLine
              key={`rsi-bullish-${index}`}
              x={pointDate}
              stroke="#27ae60"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: `🔺 RSI Bull (${Math.round(rsiDiv.confidence * 100)}%)`,
                position: 'top',
                fill: '#27ae60',
                fontSize: 10,
                fontWeight: 'bold'
              }}
            />
          );
        });
      }
      
      // Bearish divergence
      if (rsiDiv.bearish_divergence && rsiDiv.divergence_points?.bearish) {
        rsiDiv.divergence_points.bearish.forEach((point, index) => {
          const pointDate = new Date(point.date).toLocaleDateString('de-DE', { 
            month: 'short', 
            day: 'numeric',
            ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
          });
          
          const dataIndex = chartData.findIndex(d => d.date === pointDate);
          if (dataIndex === -1) return;
          
          markers.push(
            <ReferenceLine
              key={`rsi-bearish-${index}`}
              x={pointDate}
              stroke="#e74c3c"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: `🔻 RSI Bear (${Math.round(rsiDiv.confidence * 100)}%)`,
                position: 'top',
                fill: '#e74c3c',
                fontSize: 10,
                fontWeight: 'bold'
              }}
            />
          );
        });
      }
    }
    
    // MACD Divergences
    if (divergenceData.macd_divergence) {
      const macdDiv = divergenceData.macd_divergence;
      
      // Bullish divergence
      if (macdDiv.bullish_divergence && macdDiv.divergence_points?.bullish) {
        macdDiv.divergence_points.bullish.forEach((point, index) => {
          const pointDate = new Date(point.date).toLocaleDateString('de-DE', { 
            month: 'short', 
            day: 'numeric',
            ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
          });
          
          const dataIndex = chartData.findIndex(d => d.date === pointDate);
          if (dataIndex === -1) return;
          
          markers.push(
            <ReferenceLine
              key={`macd-bullish-${index}`}
              x={pointDate}
              stroke="#3498db"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: `🔺 MACD Bull (${Math.round(macdDiv.confidence * 100)}%)`,
                position: 'bottom',
                fill: '#3498db',
                fontSize: 10,
                fontWeight: 'bold'
              }}
            />
          );
        });
      }
      
      // Bearish divergence
      if (macdDiv.bearish_divergence && macdDiv.divergence_points?.bearish) {
        macdDiv.divergence_points.bearish.forEach((point, index) => {
          const pointDate = new Date(point.date).toLocaleDateString('de-DE', { 
            month: 'short', 
            day: 'numeric',
            ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
          });
          
          const dataIndex = chartData.findIndex(d => d.date === pointDate);
          if (dataIndex === -1) return;
          
          markers.push(
            <ReferenceLine
              key={`macd-bearish-${index}`}
              x={pointDate}
              stroke="#e67e22"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: `🔻 MACD Bear (${Math.round(macdDiv.confidence * 100)}%)`,
                position: 'bottom',
                fill: '#e67e22',
                fontSize: 10,
                fontWeight: 'bold'
              }}
            />
          );
        });
      }
    }
    
    return markers;
  };

  // Render Golden Cross / Death Cross markers
  const renderCrossoverMarkers = () => {
    if (!showCrossovers || !crossoverData || !crossoverData.all_crossovers || !chartData) return null;
    
    return crossoverData.all_crossovers.map((crossover, index) => {
      // Find the matching date in chartData
      const crossoverDate = new Date(crossover.date).toLocaleDateString('de-DE', { 
        month: 'short', 
        day: 'numeric',
        ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
      });
      
      const dataIndex = chartData.findIndex(d => d.date === crossoverDate);
      if (dataIndex === -1) return null; // Date not in visible range
      
      // Dynamic positioning: if crossover is in the right half of chart, position label on left
      const positionPercent = (dataIndex / chartData.length) * 100;
      const isRightSide = positionPercent > 50;
      
      const isGolden = crossover.type === 'golden_cross';
      const color = isGolden ? '#4caf50' : '#f44336';
  const price = crossover.price ? formatPrice(crossover.price, stock) : '';
      const emoji = isGolden ? '🌟' : '💀';
      const label = isGolden ? 'Golden Cross' : 'Death Cross';
      
      return (
        <ReferenceLine
          key={`crossover-${index}`}
          x={crossoverDate}
          stroke={color}
          strokeWidth={2}
          strokeDasharray="3 3"
          label={{
            value: `${emoji} ${label}${price ? ' @ ' + price : ''}`,
            position: 'top',
            fill: color,
            fontSize: 10,
            fontWeight: 'bold',
            dx: isRightSide ? -50 : 10,
            dy: 5
          }}
        />
      );
    });
  };

  // Render Fibonacci Levels
  const renderFibonacciLevels = () => {
    if (!showFibonacci || !fibonacciData) return null;
    
    const levels = fibonacciType === 'retracement' ? fibonacciData.retracement : fibonacciData.extension;
    if (!levels) return null;
    
    // Farben für Fibonacci Levels (Blautöne)
    const fibColors = {
      '0.0': '#1e88e5',
      '23.6': '#42a5f5',
      '38.2': '#64b5f6',
      '50.0': '#90caf9',
      '61.8': '#64b5f6',
      '78.6': '#42a5f5',
      '100.0': '#1e88e5',
      '127.2': '#1565c0',
      '161.8': '#0d47a1',
      '200.0': '#0d47a1',
      '261.8': '#01579b'
    };
    
    return Object.entries(levels).map(([level, price]) => {
      // Check if this level should be displayed
      if (fibonacciType === 'retracement') {
        // Skip 0% and 100% for retracement, always show swing high/low
        if (level !== '0.0' && level !== '100.0' && !selectedFibLevels[level]) {
          return null;
        }
      } else {
        // Extension: Skip 0% and 100%, check selectedExtensionLevels
        if (level !== '0.0' && level !== '100.0' && !selectedExtensionLevels[level]) {
          return null;
        }
      }
      
      const color = fibColors[level] || '#2196f3';
      const labelText = fibonacciType === 'retracement'
        ? `Fib ${level}% - ${price != null ? formatPrice(price, stock) : 'N/A'}`
        : `Fib Ext ${level}% - ${price != null ? formatPrice(price, stock) : 'N/A'}`;
      
      return (
        <ReferenceLine
          key={`fib-${fibonacciType}-${level}`}
          y={price}
          stroke={color}
          strokeWidth={1.5}
          strokeDasharray="5 5"
          label={{
            value: labelText,
            position: 'right',
            fill: color,
            fontSize: 9,
            fontWeight: 'bold'
          }}
        />
      );
    }).filter(Boolean);
  };

  // Render Support/Resistance Levels
  const renderSupportResistanceLevels = () => {
    if (!showSupportResistance || !supportResistanceData) return null;
    
    const allLevels = [
      ...supportResistanceData.support.map(level => ({ ...level, type: 'support' })),
      ...supportResistanceData.resistance.map(level => ({ ...level, type: 'resistance' }))
    ];
    
    return allLevels.map((level, index) => {
      const color = level.type === 'support' ? '#27ae60' : '#e74c3c';
      const icon = level.type === 'support' ? '🟢' : '🔴';
  const labelText = `${icon} ${level.type === 'support' ? 'Support' : 'Resistance'} - ${level.price ? formatPrice(level.price, stock) : 'N/A'} (${level.strength}× getestet)`;
      
      // Linienstärke basierend auf Stärke (1-3px)
      const strokeWidth = Math.min(level.strength, 3);
      
      return (
        <ReferenceLine
          key={`sr-${level.type}-${index}`}
          y={level.price}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray="0"
          label={{
            value: labelText,
            position: 'right',
            fill: color,
            fontSize: 9,
            fontWeight: 'bold'
          }}
        />
      );
    });
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

  // Calculate min/max for Y-axis domain - memoized to prevent re-renders
  // MUST be called before any early returns (React Hooks rule)
  const { minPrice, maxPrice } = useMemo(() => {
    if (!chartData || chartData.length === 0) {
      return { minPrice: 0, maxPrice: 0 };
    }
    
    const prices = chartData.map(d => d.close).filter(p => p != null && !isNaN(p) && isFinite(p));
    
    if (prices.length === 0) {
      return { minPrice: 0, maxPrice: 0 };
    }
    
    return {
      minPrice: Math.min(...prices) * 0.98,
      maxPrice: Math.max(...prices) * 1.02
    };
  }, [chartData]);
  
  // Memoize priceRange to prevent VolumeProfileOverlay re-renders
  const priceRange = useMemo(() => ({ 
    min: minPrice, 
    max: maxPrice 
  }), [minPrice, maxPrice]);

  // Early returns AFTER all hooks
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
  
  // Early return if no valid prices
  if (minPrice === 0 && maxPrice === 0) {
    return (
      <div className="stock-chart-container">
        <div className="chart-error">
          <p>Keine gültigen Preis-Daten verfügbar</p>
        </div>
      </div>
    );
  }

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
                checked={showStochastic}
                onChange={(e) => setShowStochastic(e.target.checked)}
              />
              <span>Stochastic</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showMACD}
                onChange={(e) => setShowMACD(e.target.checked)}
              />
              <span>MACD</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showBollinger}
                onChange={(e) => setShowBollinger(e.target.checked)}
              />
              <span>Bollinger Bands</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showATR}
                onChange={(e) => setShowATR(e.target.checked)}
              />
              <span>ATR</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showVWAP}
                onChange={(e) => setShowVWAP(e.target.checked)}
              />
              <span>VWAP</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showCrossovers}
                onChange={(e) => setShowCrossovers(e.target.checked)}
              />
              <span>🌟 Golden/Death Cross</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showDivergences}
                onChange={(e) => setShowDivergences(e.target.checked)}
              />
              <span>🔺 RSI/MACD Divergenzen</span>
            </label>
            
            {/* Fibonacci Controls */}
            <div className="fibonacci-controls" style={{ 
              marginTop: '10px', 
              paddingTop: '10px', 
              borderTop: '1px solid #ddd',
              backgroundColor: '#f8f9fa',
              padding: '10px',
              borderRadius: '6px'
            }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showFibonacci}
                  onChange={(e) => setShowFibonacci(e.target.checked)}
                />
                <span style={{ fontWeight: 'bold' }}>📐 Fibonacci Levels</span>
              </label>
              
              {showFibonacci && fibonacciData && (
                <div style={{ marginLeft: '10px', marginTop: '10px' }}>
                  {/* Type Selection */}
                  <div style={{ 
                    marginBottom: '10px',
                    display: 'flex',
                    gap: '5px'
                  }}>
                    <button
                      onClick={() => setFibonacciType('retracement')}
                      style={{
                        padding: '5px 12px',
                        fontSize: '12px',
                        border: '1px solid #007bff',
                        borderRadius: '4px',
                        backgroundColor: fibonacciType === 'retracement' ? '#007bff' : 'white',
                        color: fibonacciType === 'retracement' ? 'white' : '#007bff',
                        cursor: 'pointer',
                        fontWeight: fibonacciType === 'retracement' ? 'bold' : 'normal',
                        transition: 'all var(--motion-short)'
                      }}
                    >
                      📉 Retracement
                    </button>
                    <button
                      onClick={() => setFibonacciType('extension')}
                      style={{
                        padding: '5px 12px',
                        fontSize: '12px',
                        border: '1px solid #28a745',
                        borderRadius: '4px',
                        backgroundColor: fibonacciType === 'extension' ? '#28a745' : 'white',
                        color: fibonacciType === 'extension' ? 'white' : '#28a745',
                        cursor: 'pointer',
                        fontWeight: fibonacciType === 'extension' ? 'bold' : 'normal',
                        transition: 'all var(--motion-short)'
                      }}
                    >
                      📈 Extension
                    </button>
                  </div>
                  
                  {/* Level Selection */}
                  <div style={{ 
                    fontSize: '11px',
                    backgroundColor: 'white',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #dee2e6'
                  }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#495057' }}>
                      {fibonacciType === 'retracement' ? 'Retracement Levels:' : 'Extension Levels:'}
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {fibonacciType === 'retracement' ? (
                        Object.keys(selectedFibLevels).map(level => (
                          <label key={level} style={{ 
                            display: 'flex', 
                            alignItems: 'center',
                            padding: '3px 8px',
                            backgroundColor: selectedFibLevels[level] ? '#e3f2fd' : '#f8f9fa',
                            border: '1px solid ' + (selectedFibLevels[level] ? '#2196f3' : '#dee2e6'),
                            borderRadius: '3px',
                            cursor: 'pointer',
                            transition: 'all var(--motion-short)'
                          }}>
                            <input
                              type="checkbox"
                              checked={selectedFibLevels[level]}
                              onChange={(e) => setSelectedFibLevels({
                                ...selectedFibLevels,
                                [level]: e.target.checked
                              })}
                              style={{ marginRight: '4px' }}
                            />
                            <span style={{ fontWeight: selectedFibLevels[level] ? 'bold' : 'normal' }}>
                              {level}%
                            </span>
                          </label>
                        ))
                      ) : (
                        Object.keys(selectedExtensionLevels).map(level => (
                          <label key={level} style={{ 
                            display: 'flex', 
                            alignItems: 'center',
                            padding: '3px 8px',
                            backgroundColor: selectedExtensionLevels[level] ? '#e8f5e9' : '#f8f9fa',
                            border: '1px solid ' + (selectedExtensionLevels[level] ? '#4caf50' : '#dee2e6'),
                            borderRadius: '3px',
                            cursor: 'pointer',
                            transition: 'all var(--motion-short)'
                          }}>
                            <input
                              type="checkbox"
                              checked={selectedExtensionLevels[level]}
                              onChange={(e) => setSelectedExtensionLevels({
                                ...selectedExtensionLevels,
                                [level]: e.target.checked
                              })}
                              style={{ marginRight: '4px' }}
                            />
                            <span style={{ fontWeight: selectedExtensionLevels[level] ? 'bold' : 'normal' }}>
                              {level}%
                            </span>
                          </label>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Support/Resistance Controls */}
            <div className="support-resistance-controls" style={{ 
              marginTop: '10px', 
              paddingTop: '10px', 
              borderTop: '1px solid #ddd',
              backgroundColor: '#f8f9fa',
              padding: '10px',
              borderRadius: '6px'
            }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showSupportResistance}
                  onChange={(e) => setShowSupportResistance(e.target.checked)}
                />
                <span style={{ fontWeight: 'bold' }}>📊 Support & Resistance</span>
              </label>
              
              {showSupportResistance && supportResistanceData && (
                <div style={{ 
                  marginLeft: '10px', 
                  marginTop: '8px',
                  fontSize: '11px',
                  color: '#666'
                }}>
                  <div style={{ display: 'flex', gap: '15px' }}>
                    <span>🟢 Support: {supportResistanceData.support.length}</span>
                    <span>🔴 Resistance: {supportResistanceData.resistance.length}</span>
                  </div>
                  <div style={{ marginTop: '5px', fontSize: '10px', fontStyle: 'italic' }}>
                    Linienstärke = Anzahl Tests
                  </div>
                </div>
              )}
            </div>

            {/* Bollinger Bands Signal Info */}
            {showBollinger && bollingerSignal && (
              <div style={{ 
                marginTop: '10px', 
                paddingTop: '10px', 
                borderTop: '1px solid #ddd',
                backgroundColor: bollingerSignal.squeeze ? '#fff3cd' : '#f8f9fa',
                padding: '10px',
                borderRadius: '6px',
                border: bollingerSignal.squeeze ? '2px solid #ffc107' : '1px solid #dee2e6'
              }}>
                <div style={{ fontWeight: 'bold', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
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
            )}

            {/* Volume Profile Controls */}
            <div className="volume-profile-controls" style={{ 
              marginTop: '10px', 
              paddingTop: '10px', 
              borderTop: '1px solid #ddd',
              backgroundColor: '#f8f9fa',
              padding: '10px',
              borderRadius: '6px'
            }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showVolumeProfile}
                  onChange={(e) => setShowVolumeProfile(e.target.checked)}
                />
                <span style={{ fontWeight: 'bold' }}>📊 Volume Profile (Standalone)</span>
              </label>

              <label className="checkbox-label" style={{ marginTop: '8px' }}>
                <input
                  type="checkbox"
                  checked={showVolumeProfileOverlay}
                  onChange={(e) => setShowVolumeProfileOverlay(e.target.checked)}
                />
                <span style={{ fontWeight: 'bold' }}>📊 Volume Profile (Overlay)</span>
              </label>
              
              {(showVolumeProfile || showVolumeProfileOverlay) && volumeProfileLevels && (
                <div style={{ 
                  marginLeft: '10px', 
                  marginTop: '8px',
                  fontSize: '11px',
                  color: '#666'
                }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    <span>🟢 POC: {volumeProfileLevels.poc != null ? formatPrice(volumeProfileLevels.poc, stock) : 'N/A'}</span>
                    <span>🔵 VAH: {volumeProfileLevels.vah != null ? formatPrice(volumeProfileLevels.vah, stock) : 'N/A'}</span>
                    <span>🔴 VAL: {volumeProfileLevels.val != null ? formatPrice(volumeProfileLevels.val, stock) : 'N/A'}</span>
                  </div>
                </div>
              )}
            </div>
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
      <div className="chart-section" style={{ position: 'relative' }}>
        <h3 className="chart-title">
          {stock.name} ({stock.ticker_symbol}) - {period ? period.toUpperCase() : 'N/A'}
        </h3>
        
        {/* Volume Profile Overlay */}
        {showVolumeProfileOverlay && minPrice && maxPrice && !isNaN(minPrice) && !isNaN(maxPrice) && (
          <VolumeProfileOverlay
            stockId={stock.id}
            period={getPeriodDays(period)}
            numBins={50}
            chartHeight={400}
            chartMargin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            heightAdjustment={90}
            priceRange={priceRange}
            onProfileLoad={handleProfileLoad}
          />
        )}
        
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
                domain={[minPrice, maxPrice]}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => formatPrice(value, stock)}
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
                    value: formatPrice(chartData[0]?.close, stock) || 'N/A',
                    position: 'right',
                    fill: '#000000',
                    fontSize: 10,
                    fontWeight: 'bold'
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
              
              {/* Bollinger Bands */}
              {showBollinger && (
                <>
                  <Area
                    type="monotone"
                    dataKey="bollingerUpper"
                    stroke="#e74c3c"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    fill="#e74c3c"
                    fillOpacity={0.1}
                    dot={false}
                    name="Bollinger Upper"
                  />
                  <Area
                    type="monotone"
                    dataKey="bollingerLower"
                    stroke="#27ae60"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    fill="#27ae60"
                    fillOpacity={0.1}
                    dot={false}
                    name="Bollinger Lower"
                  />
                  <Line
                    type="monotone"
                    dataKey="bollingerMiddle"
                    stroke="#95a5a6"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    dot={false}
                    name="Bollinger Middle"
                  />
                </>
              )}
              
              {/* VWAP Line */}
              {showVWAP && (
                <Line
                  type="monotone"
                  dataKey="vwap"
                  stroke="#17a2b8"
                  strokeWidth={2.5}
                  dot={false}
                  name="VWAP (20)"
                  strokeDasharray="5 5"
                />
              )}
              
              {/* Fibonacci Levels */}
              {renderFibonacciLevels()}
              
              {/* Support/Resistance Levels */}
              {renderSupportResistanceLevels()}

              {/* Volume Profile Levels (POC, VAH, VAL) */}
              {showVolumeProfileOverlay && volumeProfileLevels && volumeProfileLevels.poc && volumeProfileLevels.vah && volumeProfileLevels.val && (
                <>
                  <ReferenceLine 
                    y={volumeProfileLevels.poc} 
                    stroke="#22c55e" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  label={{ 
                    value: `POC: ${formatPrice(volumeProfileLevels.poc, stock) || 'N/A'}`, 
                    position: "left", 
                    fill: "#22c55e", 
                    fontSize: 11,
                      fontWeight: "bold"
                    }}
                  />
                  <ReferenceLine 
                    y={volumeProfileLevels.vah} 
                    stroke="#3b82f6" 
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                  label={{ 
                    value: `VAH: ${formatPrice(volumeProfileLevels.vah, stock) || 'N/A'}`, 
                    position: "left", 
                    fill: "#3b82f6", 
                    fontSize: 10
                    }}
                  />
                  <ReferenceLine 
                    y={volumeProfileLevels.val} 
                    stroke="#ef4444" 
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                  label={{ 
                    value: `VAL: ${formatPrice(volumeProfileLevels.val, stock) || 'N/A'}`, 
                    position: "left", 
                    fill: "#ef4444", 
                    fontSize: 10
                    }}
                  />
                </>
              )}
              
              {/* Golden Cross / Death Cross Markers */}
              {renderCrossoverMarkers()}
              
              {/* Divergence Markers */}
              {renderDivergenceMarkers()}
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
                domain={[minPrice, maxPrice]}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => formatPrice(value, stock)}
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
                    value: `Start: ${formatPrice(chartData[0]?.close, stock) || 'N/A'}`, 
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
              
              {/* Bollinger Bands */}
              {showBollinger && (
                <>
                  <Area
                    type="monotone"
                    dataKey="bollingerUpper"
                    stroke="#e74c3c"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    fill="#e74c3c"
                    fillOpacity={0.1}
                    dot={false}
                    name="Bollinger Upper"
                  />
                  <Area
                    type="monotone"
                    dataKey="bollingerLower"
                    stroke="#27ae60"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    fill="#27ae60"
                    fillOpacity={0.1}
                    dot={false}
                    name="Bollinger Lower"
                  />
                  <Line
                    type="monotone"
                    dataKey="bollingerMiddle"
                    stroke="#95a5a6"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    dot={false}
                    name="Bollinger Middle"
                  />
                </>
              )}
              
              {/* VWAP Line */}
              {showVWAP && (
                <Line
                  type="monotone"
                  dataKey="vwap"
                  stroke="#17a2b8"
                  strokeWidth={2.5}
                  dot={false}
                  name="VWAP (20)"
                  strokeDasharray="5 5"
                />
              )}
              
              {/* Fibonacci Levels */}
              {renderFibonacciLevels()}
              
              {/* Support/Resistance Levels */}
              {renderSupportResistanceLevels()}

              {/* Volume Profile Levels (POC, VAH, VAL) */}
              {showVolumeProfileOverlay && volumeProfileLevels && volumeProfileLevels.poc && volumeProfileLevels.vah && volumeProfileLevels.val && (
                <>
                    <ReferenceLine
                      y={volumeProfileLevels.poc}
                      stroke="#22c55e"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      label={{
                        value: `POC: ${formatPrice(volumeProfileLevels.poc, stock) || 'N/A'}`,
                        position: 'left',
                        fill: '#22c55e',
                        fontSize: 11,
                        fontWeight: 'bold'
                      }}
                    />
                  <ReferenceLine
                    y={volumeProfileLevels.vah}
                    stroke="#3b82f6"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    label={{
                      value: `VAH: ${formatPrice(volumeProfileLevels.vah, stock) || 'N/A'}`,
                      position: 'left',
                      fill: '#3b82f6',
                      fontSize: 10
                    }}
                  />
                  <ReferenceLine
                    y={volumeProfileLevels.val}
                    stroke="#ef4444"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    label={{
                      value: `VAL: ${formatPrice(volumeProfileLevels.val, stock) || 'N/A'}`,
                      position: 'left',
                      fill: '#ef4444',
                      fontSize: 10
                    }}
                  />
                </>
              )}
              
              {/* Golden Cross / Death Cross Markers */}
              {renderCrossoverMarkers()}
              
              {/* Divergence Markers */}
              {renderDivergenceMarkers()}
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
                tickFormatter={(value) => `${(value / 1000000)?.toFixed(0) || '0'}M`}
              />
              <Tooltip 
                formatter={(value, name) => {
                  if (name === 'Volume MA (10)' || name === 'Volume MA (20)') {
                    return [`${(value / 1000000)?.toFixed(2) || '0'}M`, name];
                  }
                  return [`${(value / 1000000)?.toFixed(2) || '0'}M`, 'Volume'];
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
              <Line 
                type="monotone"
                dataKey="volumeMA20"
                stroke="#6a1b9a"
                strokeWidth={1.5}
                dot={false}
                name="Volume MA (20)"
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
                ticks={xAxisTicks}
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
                dot={RsiCustomDot}
                name="RSI"
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Stochastic Chart */}
      {showStochastic && (() => {
        const latestK = chartData && chartData.length ? chartData[chartData.length - 1].k_percent : null;
        const latestD = chartData && chartData.length ? chartData[chartData.length - 1].d_percent : null;
        return (
          <div className="chart-section">
            {/* Use the shared StochasticChart component */}
            <StochasticChart data={chartData} kPercent={latestK} dPercent={latestD} ticks={xAxisTicks} />
          </div>
        );
      })()}

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
                ticks={xAxisTicks}
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

      {/* ATR Chart */}
      {showATR && (() => {
        // Calculate ATR domain for better visibility
        const atrValues = chartData.map(d => d.atr).filter(v => v != null);
        const minATR = Math.min(...atrValues);
        const maxATR = Math.max(...atrValues);
        const padding = (maxATR - minATR) * 0.1; // 10% padding
        const atrDomain = [Math.max(0, minATR - padding), maxATR + padding];
        
        return (
          <div className="chart-section">
            <h4 className="chart-subtitle">ATR (14) - Average True Range</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="atrGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f39c12" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f39c12" stopOpacity={0}/>
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
                  tick={{ fontSize: 10 }}
                  tickFormatter={(value) => formatPrice(value, stock)}
                  domain={atrDomain}
                />
                <Tooltip 
                  formatter={(value, name) => [formatPrice(value, stock), name]}
                  contentStyle={{ 
                    backgroundColor: 'rgba(255, 255, 255, 0.98)', 
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    padding: '10px'
                  }}
                  labelStyle={{ fontWeight: 'bold', color: '#333' }}
                  cursor={{ stroke: '#f39c12', strokeWidth: 1, strokeDasharray: '5 5' }}
                />
                <Legend />
                
                <Line
                  type="monotone"
                  dataKey="atr"
                  stroke="#f39c12"
                  strokeWidth={3}
                  dot={false}
                  name="ATR (14)"
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );
      })()}
      
      {/* ATR Info Box */}
      {showATR && (
        <div className="chart-section">
          <div className="atr-info" style={{ 
            padding: '10px', 
            fontSize: '12px', 
            color: '#666',
            backgroundColor: '#f8f9fa',
            borderRadius: '4px',
            margin: '10px 0'
          }}>
            <p style={{ margin: '5px 0' }}>
              💡 <strong>ATR Interpretation:</strong> Höhere Werte = höhere Volatilität
            </p>
            <p style={{ margin: '5px 0' }}>
              🎯 <strong>Stop-Loss Empfehlung:</strong> 1.5-2x ATR unter Einstiegspreis
            </p>
            <p style={{ margin: '5px 0' }}>
              📊 <strong>Position Size:</strong> Bei hohem ATR kleinere Positionen wählen
            </p>
          </div>
        </div>
      )}

      {/* Volume Profile Standalone */}
      {showVolumeProfile && (
        <div className="chart-section">
          <h4 className="chart-subtitle">📊 Volume Profile Analysis</h4>
          <VolumeProfile
            stockId={stock.id}
            period={getPeriodDays(period)}
            numBins={50}
            height={400}
            onLoad={handleProfileLoad}
          />
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

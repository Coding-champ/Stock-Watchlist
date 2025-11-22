import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import '../styles/skeletons.css';
import {
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
  ReferenceLine
} from 'recharts';
import VolumeProfile from './VolumeProfile';
import VolumeProfileOverlay from './VolumeProfileOverlay';
import { StochasticChart } from './AdvancedCharts';
import { RsiChart } from './subcharts/RsiChart';
import { MacdChart } from './subcharts/MacdChart';
import { AtrChart } from './subcharts/AtrChart';
import './StockChart.css';

import { useChartData } from '../hooks/chart/useChartData';
import { useChartEvents } from '../hooks/chart/useChartEvents';
import { useChartIndicators } from '../hooks/chart/useChartIndicators';
import { useChartExport } from '../hooks/chart/useChartExport';
import { useDivergenceMarkers } from '../hooks/chart/useDivergenceMarkers';
import { useCrossoverMarkers } from '../hooks/chart/useCrossoverMarkers';
import { useFibonacciLevels } from '../hooks/chart/useFibonacciLevels';
import { useSupportResistanceLevels } from '../hooks/chart/useSupportResistanceLevels';
import { ChartControls } from './chart/ChartControls';
import { EventMarkers } from './chart/EventMarkers';
import { BollingerSignal } from './chart/BollingerSignal';
import { ChartTooltip } from './chart/ChartTooltip';
import { CandlestickBar } from './chart/CandlestickBar';
import FibonacciLevels from './chart/FibonacciLevels';
import SupportResistanceLevels from './chart/SupportResistanceLevels';
import VolumeProfileLevels from './chart/VolumeProfileLevels';
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
  const [showIchimoku, setShowIchimoku] = useState(false);
  const [showRSI, setShowRSI] = useState(false);
  const [showMACD, setShowMACD] = useState(false);
  const [showStochastic, setShowStochastic] = useState(false);
  const [showBollinger, setShowBollinger] = useState(false);
  const [showATR, setShowATR] = useState(false);
  const [showVWAP, setShowVWAP] = useState(false);
  const [showCrossovers, setShowCrossovers] = useState(false);
  const [showDivergences, setShowDivergences] = useState(false);
  
  // Event marker toggles
  const [showDividends, setShowDividends] = useState(false);
  const [showSplits, setShowSplits] = useState(false);
  const [showEarnings, setShowEarnings] = useState(false);
  
  // Fibonacci toggles
  const [showFibonacci, setShowFibonacci] = useState(false);
  const [fibonacciType, setFibonacciType] = useState('retracement'); // 'retracement' or 'extension'
  const [selectedFibLevels, setSelectedFibLevels] = useState({
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

  // Bollinger Bands signal (display + meta info)
  const [bollingerSignal, setBollingerSignal] = useState(null);

  // Support/Resistance toggles and cached levels
  const [showSupportResistance, setShowSupportResistance] = useState(false);
  const [supportResistanceData, setSupportResistanceData] = useState(null);

  // Volume Profile toggles / shared X axis ticks for synchronized subcharts
  const [showVolumeProfile, setShowVolumeProfile] = useState(false);
  const [showVolumeProfileOverlay, setShowVolumeProfileOverlay] = useState(false);
  const [volumeProfileLevels, setVolumeProfileLevels] = useState(null);
  const [xAxisTicks, setXAxisTicks] = useState(null);

  // Scale and mode toggles (persisted)
  const [isLogScale, setIsLogScale] = useState(() => {
    try { return JSON.parse(localStorage.getItem('chart:isLogScale') || 'false'); } catch { return false; }
  });
  const [isPercentageView, setIsPercentageView] = useState(() => {
    try { return JSON.parse(localStorage.getItem('chart:isPercentageView') || 'false'); } catch { return false; }
  });

  useEffect(() => {
    try { localStorage.setItem('chart:isLogScale', JSON.stringify(!!isLogScale)); } catch {}
  }, [isLogScale]);
  useEffect(() => {
    try { localStorage.setItem('chart:isPercentageView', JSON.stringify(!!isPercentageView)); } catch {}
  }, [isPercentageView]);

  // Snapshot of price overlay toggles for restore after percentage mode
  const overlaysSnapshotRef = useRef(null);
  useEffect(() => {
    if (isPercentageView) {
      // Save current overlay states once
      if (!overlaysSnapshotRef.current) {
        overlaysSnapshotRef.current = {
          sma50: showSMA50,
          sma200: showSMA200,
          bollinger: showBollinger,
          ichimoku: showIchimoku,
          vwap: showVWAP,
          volumeProfileOverlay: showVolumeProfileOverlay
        };
      }
      // Deactivate only price overlays while in percentage mode
      if (showSMA50) setShowSMA50(false);
      if (showSMA200) setShowSMA200(false);
      if (showBollinger) setShowBollinger(false);
      if (showIchimoku) setShowIchimoku(false);
      if (showVWAP) setShowVWAP(false);
      if (showVolumeProfileOverlay) setShowVolumeProfileOverlay(false);
    } else {
      // Restore overlays from snapshot if available
      if (overlaysSnapshotRef.current) {
        const snap = overlaysSnapshotRef.current;
        setShowSMA50(!!snap.sma50);
        setShowSMA200(!!snap.sma200);
        setShowBollinger(!!snap.bollinger);
        setShowIchimoku(!!snap.ichimoku);
        setShowVWAP(!!snap.vwap);
        setShowVolumeProfileOverlay(!!snap.volumeProfileOverlay);
        overlaysSnapshotRef.current = null;
      }
    }
  }, [isPercentageView, showSMA50, showSMA200, showBollinger, showIchimoku, showVWAP, showVolumeProfileOverlay]);

  // Turn off percentage view when switching to candlesticks (not supported for candles)
  useEffect(() => {
    if (chartType === CHART_TYPES.CANDLESTICK && isPercentageView) {
      setIsPercentageView(false);
    }
  }, [chartType, isPercentageView]);

  // Collapsible panel states
  const [fibonacciPanelExpanded, setFibonacciPanelExpanded] = useState(true);
  const [supportResistancePanelExpanded, setSupportResistancePanelExpanded] = useState(true);
  const [volumeProfilePanelExpanded, setVolumeProfilePanelExpanded] = useState(true);
  const [bollingerSignalPanelExpanded, setBollingerSignalPanelExpanded] = useState(true);

  // Memoized callback for Volume Profile data loading
  const handleProfileLoad = useCallback((levels) => {
    setVolumeProfileLevels(levels);
  }, []);


  // New consolidated chart hook (Phase 1 extraction)
  const chartPayload = useChartData({
    assetId: stock.id,
    period,
    customStartDate,
    customEndDate,
    onLatestVwap
  });

  // Lazy indicators hook (Phase 2 extraction)
  useChartIndicators({
    assetId: stock.id,
    period,
    customStartDate,
    customEndDate,
    chartData,
    onChartDataUpdate: setChartData,
    toggles: {
      showSMA50,
      showSMA200,
      showRSI,
      showMACD,
      showStochastic,
      showBollinger,
      showATR,
      showVWAP,
      showIchimoku
    }
  });

  // Separate events fetching with debounce (no full chart refetch)
  useChartEvents({
    assetId: stock.id,
    period,
    customStartDate,
    customEndDate,
    chartData,
    showDividends,
    showSplits,
    showEarnings,
    debounceMs: 350,
    onEventsUpdate: setChartData
  });

  // Sync hook results into existing local state (incremental migration)
  const previousChartPayloadRef = useRef(null);
  useEffect(() => {
    // Only set chartData on initial load or period change, NOT on every chartPayload update
    // This prevents infinite loops where indicators update chartData → triggers this effect → resets chartData
    const isInitialOrPeriodChange = !previousChartPayloadRef.current || 
                                     previousChartPayloadRef.current.loading !== chartPayload.loading;
    
    if (chartPayload.chartData && isInitialOrPeriodChange && !chartPayload.loading) {
      setChartData(chartPayload.chartData);
      previousChartPayloadRef.current = chartPayload;
    }
    
    if (chartPayload.xAxisTicks) setXAxisTicks(chartPayload.xAxisTicks);
    setLoading(chartPayload.loading);
    setError(chartPayload.error);
    setBollingerSignal(chartPayload.bollingerSignal || null);
    setCrossoverData(chartPayload.crossoverData || null);
    setFibonacciData(chartPayload.fibonacciData || null);
    setSupportResistanceData(chartPayload.supportResistanceData || null);
    setDivergenceData(chartPayload.divergenceData || null);
  }, [chartPayload]);

  // Use hooks for rendering analysis overlays
  const divergenceMarkers = useDivergenceMarkers({ 
    showDivergences, 
    divergenceData, 
    chartData, 
    period 
  });

  const crossoverMarkers = useCrossoverMarkers({ 
    showCrossovers, 
    crossoverData, 
    chartData, 
    period, 
    stock 
  });

  const fibonacciLevels = useFibonacciLevels({ 
    showFibonacci, 
    fibonacciData, 
    fibonacciType, 
    selectedFibLevels, 
    selectedExtensionLevels, 
    stock 
  });

  const supportResistanceLevels = useSupportResistanceLevels({ 
    showSupportResistance, 
    supportResistanceData, 
    stock 
  });

  // Helper function to convert period to days (kept for existing downstream logic)
  const getPeriodDays = (p) => {
    const periodMap = { '1d': 1, '5d': 5, '1mo': 30, '3mo': 90, '6mo': 180, '1y': 365, '3y': 1095, '5y': 1825, 'max': 3650 };
    if (p === 'custom' && customStartDate && customEndDate) {
      const start = new Date(customStartDate);
      const end = new Date(customEndDate);
      return Math.ceil(Math.abs(end - start) / (1000 * 60 * 60 * 24));
    }
    return periodMap[p] || 30;
  };

  // Export functionality
  const { chartCaptureRef, exportToPNG, exportToCSV } = useChartExport(stock, period, chartData);



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

  // Derived data for line chart (percentage view support)
  // MUST be called before early returns (React Hooks rule)
  const displayData = useMemo(() => {
    if (!chartData || chartData.length === 0) return chartData;
    if (!isPercentageView || chartType !== CHART_TYPES.LINE) {
      return chartData.map(d => ({ ...d, displayClose: d.close }));
    }
    let baseline = null;
    for (let i = 0; i < chartData.length; i++) {
      const c = chartData[i]?.close;
      if (typeof c === 'number' && isFinite(c) && c > 0) { baseline = c; break; }
    }
    if (!baseline) {
      return chartData.map(d => ({ ...d, displayClose: d.close }));
    }
    return chartData.map(d => {
      const c = d?.close;
      const idx = (typeof c === 'number' && isFinite(c) && c > 0) ? (c / baseline) : null;
      return { ...d, displayClose: idx };
    });
  }, [chartData, isPercentageView, chartType]);

  const displayDomain = useMemo(() => {
    if (!chartData || chartData.length === 0) return [0, 1];
    if (!isPercentageView || chartType !== CHART_TYPES.LINE) return [minPrice, maxPrice];
    // compute domain for index values (>0)
    const values = chartData
      .map(d => d && typeof d.close === 'number' && isFinite(d.close) && d.close > 0 ? d.close : null)
      .filter(v => v != null);
    if (values.length === 0) return [0.5, 1.5];
    const baseline = values[0];
    let minIdx = Infinity, maxIdx = -Infinity;
    for (const v of values) {
      const idx = v / baseline;
      if (isFinite(idx) && idx > 0) {
        if (idx < minIdx) minIdx = idx;
        if (idx > maxIdx) maxIdx = idx;
      }
    }
    if (!isFinite(minIdx) || !isFinite(maxIdx)) return [0.5, 1.5];
    const pad = 0.02;
    return [Math.max(0.01, minIdx * (1 - pad)), maxIdx * (1 + pad)];
  }, [chartData, isPercentageView, chartType, minPrice, maxPrice]);

  // Early returns AFTER all hooks
  if (loading) {
    // Render a skeleton-styled placeholder instead of the global spinner.
    // Uses the central `.skeleton` helper for shimmer effect.
    return (
      <div className="stock-chart-container">
        <div className="chart-controls" aria-hidden style={{ opacity: 0.9 }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <div className="skeleton" style={{ width: 120, height: 36 }} />
            <div className="skeleton" style={{ width: 80, height: 36 }} />
            <div className="skeleton" style={{ width: 160, height: 36 }} />
          </div>
        </div>

        <div className="chart-section" style={{ position: 'relative' }}>
          <div style={{ padding: 16 }}>
            <div className="skeleton" style={{ width: '48%', height: 18, marginBottom: 12 }} />
            <div className="skeleton" style={{ width: '100%', height: 360 }} />
          </div>

          <div style={{ display: 'flex', gap: 12, padding: 16 }}>
            <div className="skeleton" style={{ flex: 1, height: 120 }} />
            <div className="skeleton" style={{ width: 220, height: 120 }} />
          </div>

          <div className="chart-info" style={{ padding: 12 }}>
            <div className="skeleton" style={{ width: 200, height: 12 }} />
          </div>
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
          <button onClick={() => chartPayload?.refetch?.()} className="retry-button">
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
      <ChartControls
        periods={TIME_PERIODS}
        period={period}
        setPeriod={setPeriod}
        showCustomDatePicker={showCustomDatePicker}
        setShowCustomDatePicker={setShowCustomDatePicker}
        customStartDate={customStartDate}
        setCustomStartDate={setCustomStartDate}
        customEndDate={customEndDate}
        setCustomEndDate={setCustomEndDate}
        chartType={chartType}
        setChartType={setChartType}
        CHART_TYPES={CHART_TYPES}
        isLogScale={isLogScale}
        setIsLogScale={setIsLogScale}
        isPercentageView={isPercentageView}
        setIsPercentageView={setIsPercentageView}
        onApplyCustomRange={() => chartPayload?.refetch?.()}
        exportToPNG={exportToPNG}
        exportToCSV={exportToCSV}
      />

      <div className="chart-controls">
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
                checked={showIchimoku}
                onChange={(e) => setShowIchimoku(e.target.checked)}
              />
              <span>Ichimoku Cloud</span>
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
            <label className="checkbox-label" style={{ color: '#3b82f6' }}>
              <input
                type="checkbox"
                checked={showDividends}
                onChange={(e) => setShowDividends(e.target.checked)}
              />
              <span>💰 Dividenden</span>
            </label>
            <label className="checkbox-label" style={{ color: '#f97316' }}>
              <input
                type="checkbox"
                checked={showSplits}
                onChange={(e) => setShowSplits(e.target.checked)}
              />
              <span>✂️ Aktiensplits</span>
            </label>
            <label className="checkbox-label" style={{ color: '#22c55e' }}>
              <input
                type="checkbox"
                checked={showEarnings}
                onChange={(e) => setShowEarnings(e.target.checked)}
              />
              <span>📊 Earnings</span>
            </label>
            
            {/* Fibonacci Controls */}
            <FibonacciLevels
              showFibonacci={showFibonacci}
              setShowFibonacci={setShowFibonacci}
              fibonacciData={fibonacciData}
              fibonacciType={fibonacciType}
              setFibonacciType={setFibonacciType}
              selectedFibLevels={selectedFibLevels}
              setSelectedFibLevels={setSelectedFibLevels}
              selectedExtensionLevels={selectedExtensionLevels}
              setSelectedExtensionLevels={setSelectedExtensionLevels}
              isExpanded={fibonacciPanelExpanded}
              onToggle={() => setFibonacciPanelExpanded(!fibonacciPanelExpanded)}
            />
            
            {/* Support/Resistance Controls */}
            <SupportResistanceLevels
              showSupportResistance={showSupportResistance}
              setShowSupportResistance={setShowSupportResistance}
              supportResistanceData={supportResistanceData}
              isExpanded={supportResistancePanelExpanded}
              onToggle={() => setSupportResistancePanelExpanded(!supportResistancePanelExpanded)}
            />

            {/* Bollinger Bands Signal Info */}
            {showBollinger && (
              <BollingerSignal
                bollingerSignal={bollingerSignal}
                isExpanded={bollingerSignalPanelExpanded}
                onToggle={() => setBollingerSignalPanelExpanded(!bollingerSignalPanelExpanded)}
              />
            )}

            {/* Volume Profile Controls */}
            <VolumeProfileLevels
              showVolumeProfile={showVolumeProfile}
              setShowVolumeProfile={setShowVolumeProfile}
              showVolumeProfileOverlay={showVolumeProfileOverlay}
              setShowVolumeProfileOverlay={setShowVolumeProfileOverlay}
              volumeProfileLevels={volumeProfileLevels}
              stock={stock}
              isExpanded={volumeProfilePanelExpanded}
              onToggle={() => setVolumeProfilePanelExpanded(!volumeProfilePanelExpanded)}
            />
          </div>
        </div>
      </div>

      {/* Main Price Chart */}
      <div className="chart-section" style={{ position: 'relative' }} ref={chartCaptureRef}>
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
            <ComposedChart data={displayData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
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
                domain={displayDomain}
                tick={{ fontSize: 12 }}
                scale={isLogScale ? 'log' : undefined}
                tickFormatter={(value) => isPercentageView
                  ? `${value === 1 ? '0.0%' : `${((value - 1) * 100 > 0 ? '+' : '')}${((value - 1) * 100).toFixed(1)}%`}`
                  : formatPrice(value, stock)}
              />
              <Tooltip 
                content={<ChartTooltip 
                  stock={stock}
                  isPercentageView={isPercentageView}
                  chartType={chartType}
                  showSMA50={showSMA50}
                  showSMA200={showSMA200}
                  showBollinger={showBollinger}
                  showATR={showATR}
                  showVWAP={showVWAP}
                  showIchimoku={showIchimoku}
                  CHART_TYPES={CHART_TYPES}
                />}
                cursor={{ stroke: '#007bff', strokeWidth: 1, strokeDasharray: '5 5' }}
                wrapperStyle={{ pointerEvents: 'none' }}
                isAnimationActive={false}
              />
              <Legend />
              
              {/* Baseline reference line */}
              {isPercentageView ? (
                <ReferenceLine
                  y={1}
                  stroke="#000000"
                  strokeDasharray="5 5"
                  strokeWidth={1.5}
                  label={{ value: '0%', position: 'right', fill: '#000000', fontSize: 10, fontWeight: 'bold' }}
                />
              ) : (
                chartData && chartData.length > 0 && chartData[0].close && (
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
                )
              )}
              
              <Area
                type="monotone"
                dataKey={isPercentageView ? 'displayClose' : 'close'}
                stroke="#007bff"
                strokeWidth={2}
                fill="url(#colorPrice)"
                name={isPercentageView ? 'Price (%)' : 'Price'}
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

              {/* Ichimoku Cloud */}
              {showIchimoku && (
                <>
                  <Area
                    type="monotone"
                    dataKey="ichimoku_span_a"
                    stroke="none"
                    fill="#2ca02c"
                    fillOpacity={0.10}
                    dot={false}
                    name="Ichimoku Span A"
                  />
                  <Area
                    type="monotone"
                    dataKey="ichimoku_span_b"
                    stroke="none"
                    fill="#d62728"
                    fillOpacity={0.08}
                    dot={false}
                    name="Ichimoku Span B"
                  />
                  <Line
                    type="monotone"
                    dataKey="ichimoku_conversion"
                    stroke="#1f77b4"
                    strokeWidth={1.5}
                    dot={false}
                    name="Ichimoku Conversion"
                  />
                  <Line
                    type="monotone"
                    dataKey="ichimoku_base"
                    stroke="#ff7f0e"
                    strokeWidth={1.5}
                    dot={false}
                    name="Ichimoku Base"
                  />
                  <Line
                    type="monotone"
                    dataKey="ichimoku_span_a"
                    stroke="#2ca02c"
                    strokeWidth={1}
                    dot={false}
                    name="Ichimoku Span A (line)"
                  />
                  <Line
                    type="monotone"
                    dataKey="ichimoku_span_b"
                    stroke="#d62728"
                    strokeWidth={1}
                    dot={false}
                    name="Ichimoku Span B (line)"
                  />
                  <Line
                    type="monotone"
                    dataKey="ichimoku_chikou"
                    stroke="#7f7f7f"
                    strokeWidth={1}
                    dot={false}
                    strokeDasharray="4 4"
                    name="Ichimoku Chikou"
                  />
                </>
              )}
              
              {/* Fibonacci Levels */}
              {fibonacciLevels}
              
              {/* Support/Resistance Levels */}
              {supportResistanceLevels}

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
              {crossoverMarkers}
              
              {/* Divergence Markers */}
              {divergenceMarkers}
              
              {/* Event Icons (Dividends, Splits, Earnings) */}
              <EventMarkers 
                chartData={chartData}
                period={period}
                showDividends={showDividends}
                showSplits={showSplits}
                showEarnings={showEarnings}
              />
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
                scale={isLogScale ? 'log' : undefined}
                tickFormatter={(value) => formatPrice(value, stock)}
              />
              <Tooltip 
                content={<ChartTooltip 
                  stock={stock}
                  isPercentageView={isPercentageView}
                  chartType={chartType}
                  showSMA50={showSMA50}
                  showSMA200={showSMA200}
                  showBollinger={showBollinger}
                  showATR={showATR}
                  showVWAP={showVWAP}
                  showIchimoku={showIchimoku}
                  CHART_TYPES={CHART_TYPES}
                />}
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
                shape={<CandlestickBar chartData={chartData} />}
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
              {fibonacciLevels}
              
              {/* Support/Resistance Levels */}
              {supportResistanceLevels}

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
              {crossoverMarkers}
              
              {/* Divergence Markers */}
              {divergenceMarkers}
              
              {/* Event Icons (Dividends, Splits, Earnings) */}
              <EventMarkers
                chartData={chartData}
                period={period}
                showDividends={showDividends}
                showSplits={showSplits}
                showEarnings={showEarnings}
              />
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

      {/* RSI Subchart */}
      {showRSI && <RsiChart data={chartData} ticks={xAxisTicks} />}

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

      {/* MACD Subchart */}
      {showMACD && <MacdChart data={chartData} ticks={xAxisTicks} />}

      {/* ATR Subchart */}
      {showATR && <AtrChart data={chartData} stock={stock} />}

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

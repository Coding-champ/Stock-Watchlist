import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import API_BASE from '../config';

import '../styles/skeletons.css';

const TIMEFRAME_OPTIONS = [
  { key: '7', label: '7T', limit: 7 },
  { key: '30', label: '30T', limit: 30 },
  { key: '90', label: '90T', limit: 90 },
  { key: '180', label: '180T', limit: 180 },
  { key: '365', label: '1J', limit: 365 },
  { key: 'max', label: 'Max', limit: Infinity }
];

const DEFAULT_INDICATORS = {
  sma20: true,
  sma50: false,
  rsi: false
};

const SVG_EXPORT_STYLES = `
  .chart-background {
    fill: rgba(0, 123, 255, 0.04);
    stroke: rgba(0, 123, 255, 0.08);
  }

  .chart-grid-line {
    stroke: rgba(0, 0, 0, 0.08);
    stroke-dasharray: 4 6;
  }

  .chart-axis {
    stroke: rgba(0, 0, 0, 0.35);
    stroke-width: 1.2px;
  }

  .chart-axis-tick {
    stroke: rgba(0, 0, 0, 0.35);
  }

  .chart-axis-label {
    fill: #6c757d;
    font-size: 12px;
    text-anchor: end;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }

  .chart-axis-label.chart-axis-label-x {
    text-anchor: middle;
  }

  .chart-area {
    fill: url(#chartGradient);
    opacity: 0.9;
  }

  .chart-line {
    fill: none;
    stroke: #007bff;
    stroke-width: 2.5px;
    stroke-linecap: round;
  }

  .chart-line-sma20 {
    fill: none;
    stroke: #ff7f0e;
    stroke-width: 2px;
    stroke-linecap: round;
  }

  .chart-line-sma50 {
    fill: none;
    stroke: #6610f2;
    stroke-width: 2px;
    stroke-linecap: round;
  }

  .chart-hover-line {
    stroke: rgba(0, 123, 255, 0.5);
    stroke-width: 1.5px;
    stroke-dasharray: 4 4;
  }

  .chart-hover-dot {
    fill: #ffffff;
    stroke: #007bff;
    stroke-width: 2.5px;
  }

  .chart-hover-dot.sma20 {
    stroke: #ff7f0e;
  }

  .chart-hover-dot.sma50 {
    stroke: #6610f2;
  }
`;

const CHART_WIDTH = 780;
const PRICE_CHART_HEIGHT = 340;
const RSI_CHART_HEIGHT = 200;
const CHART_PADDING = { top: 24, right: 28, bottom: 40, left: 60 };
const RSI_CHART_PADDING = { top: 24, right: 28, bottom: 32, left: 60 };

const computeSMA = (series, windowSize) => {
  if (!Array.isArray(series) || series.length === 0 || windowSize <= 1) {
    return [];
  }

  const result = new Array(series.length).fill(null);
  let rollingSum = 0;

  for (let index = 0; index < series.length; index += 1) {
    const value = series[index]?.price;
    if (typeof value !== 'number' || Number.isNaN(value)) {
      rollingSum = 0;
      continue;
    }

    rollingSum += value;
    if (index >= windowSize) {
      const olderValue = series[index - windowSize]?.price;
      if (typeof olderValue === 'number') {
        rollingSum -= olderValue;
      }
    }

    if (index >= windowSize - 1) {
      result[index] = rollingSum / windowSize;
    }
  }

  return result;
};

const computeRSI = (series, period = 14) => {
  if (!Array.isArray(series) || series.length <= period) {
    return new Array(series.length).fill(null);
  }

  const result = new Array(series.length).fill(null);
  let gainSum = 0;
  let lossSum = 0;

  for (let index = 1; index <= period; index += 1) {
    const change = series[index].price - series[index - 1].price;
    if (change >= 0) {
      gainSum += change;
    } else {
      lossSum -= change;
    }
  }

  let averageGain = gainSum / period;
  let averageLoss = lossSum / period;
  const initialRS = averageLoss === 0 ? Infinity : averageGain / averageLoss;
  result[period] = 100 - 100 / (1 + initialRS);

  for (let index = period + 1; index < series.length; index += 1) {
    const change = series[index].price - series[index - 1].price;
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? -change : 0;

    averageGain = ((averageGain * (period - 1)) + gain) / period;
    averageLoss = ((averageLoss * (period - 1)) + loss) / period;

    if (averageLoss === 0) {
      result[index] = 100;
    } else {
      const relativeStrength = averageGain / averageLoss;
      result[index] = 100 - 100 / (1 + relativeStrength);
    }
  }

  return result;
};

function StockChartModal({ stock, onClose, isEmbedded = false }) {
  const [data, setData] = useState([]);
  const [timeframe, setTimeframe] = useState('90');
  const [indicators, setIndicators] = useState(DEFAULT_INDICATORS);
  const [hoverIndex, setHoverIndex] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const priceChartRef = useRef(null);
  const _timeframeKeyToPeriod = (key) => {
    switch (key) {
      case '7': return '7d';
      case '30': return '1mo';
      case '90': return '3mo';
      case '180': return '6mo';
      case '365': return '1y';
      case 'max': return 'max';
      default: return '3mo';
    }
  };

  const fetchStockData = useCallback(async (signal) => {
    // Fetch chart data (including server-computed indicators) and map to the
    // in-component `chartData` shape. Prefer server-provided indicator values
    // when available, fall back to existing client-side computation.
    setLoading(true);
    setError(null);

    try {
      const period = _timeframeKeyToPeriod(timeframe);
      // Request common indicators. Backend will ignore unknown switches.
      const indicatorParams = new URLSearchParams();
      // Request SMA 20 and 50 and RSI — server may return them or omit if unavailable
      indicatorParams.append('indicators', 'sma_20');
      indicatorParams.append('indicators', 'sma_50');
      indicatorParams.append('indicators', 'rsi');

      const url = `${API_BASE}/stock-data/${stock.id}/chart?period=${encodeURIComponent(period)}&interval=1d&${indicatorParams.toString()}`;
  // Debug: log the exact URL we're requesting so we can verify what the
  // browser actually fetches (helps diagnose caching / wrong-endpoint issues).
  console.debug('[StockChartModal] fetching chart URL:', url);
  const response = await fetch(url, { signal, cache: 'no-store' });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || 'Konnte Kursdaten nicht laden');
      }

      const json = await response.json();

      // Map backend response (dates, close, indicators) into the expected
      // chartData array used throughout this component.
      const dates = Array.isArray(json.dates) ? json.dates : [];
      const closes = Array.isArray(json.close) ? json.close : [];
      const indicatorsResp = json.indicators || {};

      const parsed = [];
      for (let i = 0; i < dates.length; i += 1) {
        try {
          const date = new Date(dates[i]);
          const price = Number.isFinite(Number(closes[i])) ? Number(closes[i]) : null;

          parsed.push({
            date,
            price,
            // Attach server-side indicator values so we can prefer them later
            rsi: Array.isArray(indicatorsResp.rsi) ? (Number.isFinite(Number(indicatorsResp.rsi[i])) ? Number(indicatorsResp.rsi[i]) : null) : null,
            sma20: Array.isArray(indicatorsResp.sma_20) ? (Number.isFinite(Number(indicatorsResp.sma_20[i])) ? Number(indicatorsResp.sma_20[i]) : null) : null,
            sma50: Array.isArray(indicatorsResp.sma_50) ? (Number.isFinite(Number(indicatorsResp.sma_50[i])) ? Number(indicatorsResp.sma_50[i]) : null) : null
          });
        } catch (e) {
          // skip malformed entries
        }
      }

      if (signal?.aborted) {
        return;
      }

      // Filter out invalid rows and sort by date
      const filtered = parsed
        .filter((entry) => entry && entry.price !== null && entry.date instanceof Date && !Number.isNaN(entry.date.getTime()))
        .sort((a, b) => a.date - b.date);

      setData(filtered);
      setHoverIndex(filtered.length ? filtered.length - 1 : null);
    } catch (err) {
      if (signal?.aborted) {
        return;
      }
      console.error('Fehler beim Laden der Kursdaten:', err);
      setError(err.message || 'Unbekannter Fehler beim Laden der Kursdaten');
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, [stock.id, timeframe]);

  useEffect(() => {
    const controller = new AbortController();
    fetchStockData(controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchStockData]);

  const chartData = useMemo(() => {
    if (timeframe === 'max') {
      return data;
    }
    const limit = TIMEFRAME_OPTIONS.find((option) => option.key === timeframe)?.limit ?? data.length;
    return data.slice(-limit);
  }, [data, timeframe]);

  useEffect(() => {
    if (chartData.length) {
      setHoverIndex(chartData.length - 1);
    } else {
      setHoverIndex(null);
    }
  }, [chartData]);

  useEffect(() => {
    if (indicators.rsi && chartData.length < 15) {
      setIndicators((prev) => ({ ...prev, rsi: false }));
    }
  }, [chartData.length, indicators.rsi]);

  const timeframeConfig = useMemo(
    () => TIMEFRAME_OPTIONS.find((option) => option.key === timeframe),
    [timeframe]
  );
  const timeframeLabel = timeframeConfig?.label ?? timeframe;

  const prices = useMemo(() => chartData.map((entry) => entry.price), [chartData]);
  const hasPriceData = prices.length >= 2;

  const minPrice = hasPriceData ? Math.min(...prices) : null;
  const maxPrice = hasPriceData ? Math.max(...prices) : null;
  const valueRange = maxPrice !== null && minPrice !== null
    ? Math.max(maxPrice - minPrice, Math.abs(maxPrice) * 0.005, 1e-6)
    : 1;

  const priceChartAreaWidth = CHART_WIDTH - CHART_PADDING.left - CHART_PADDING.right;
  const priceChartAreaHeight = PRICE_CHART_HEIGHT - CHART_PADDING.top - CHART_PADDING.bottom;

  const getXForIndex = useCallback(
    (index) => {
      if (chartData.length <= 1) {
        return CHART_PADDING.left + priceChartAreaWidth / 2;
      }
      const ratio = index / (chartData.length - 1);
      return CHART_PADDING.left + ratio * priceChartAreaWidth;
    },
    [priceChartAreaWidth, chartData.length]
  );

  const getYForPrice = useCallback(
    (price) => {
      if (!hasPriceData || valueRange === 0) {
        return CHART_PADDING.top + priceChartAreaHeight / 2;
      }
      return (
        CHART_PADDING.top +
        ((maxPrice - price) / valueRange) * priceChartAreaHeight
      );
    },
    [priceChartAreaHeight, hasPriceData, maxPrice, valueRange]
  );

  const buildPriceLinePath = useCallback((values) => {
    if (!hasPriceData || !Array.isArray(values) || values.length === 0) {
      return '';
    }

    let path = '';
    let penDown = false;

    values.forEach((value, index) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        penDown = false;
        return;
      }

      const x = getXForIndex(index);
      const y = getYForPrice(value);
      const command = penDown ? 'L' : 'M';
      path += `${command}${x.toFixed(2)},${y.toFixed(2)} `;
      penDown = true;
    });

    return path.trim();
  }, [getXForIndex, getYForPrice, hasPriceData]);

  const pricePath = useMemo(() => {
    if (!hasPriceData) {
      return '';
    }
    return buildPriceLinePath(prices);
  }, [buildPriceLinePath, hasPriceData, prices]);

  const priceAreaPath = useMemo(() => {
    if (!hasPriceData || !pricePath) {
      return '';
    }

    const lastX = getXForIndex(chartData.length - 1);
    const firstX = getXForIndex(0);
    const baseY = PRICE_CHART_HEIGHT - CHART_PADDING.bottom;

    return `${pricePath} L${lastX.toFixed(2)},${baseY} L${firstX.toFixed(2)},${baseY} Z`;
  }, [chartData.length, getXForIndex, hasPriceData, pricePath]);

  const sma20Values = useMemo(() => {
    // Prefer server-provided SMA values when available
    if (chartData.length && chartData.some((e) => e && typeof e.sma20 === 'number')) {
      return chartData.map((e) => (e && typeof e.sma20 === 'number' ? e.sma20 : null));
    }
    return computeSMA(chartData, 20);
  }, [chartData]);

  const sma50Values = useMemo(() => {
    if (chartData.length && chartData.some((e) => e && typeof e.sma50 === 'number')) {
      return chartData.map((e) => (e && typeof e.sma50 === 'number' ? e.sma50 : null));
    }
    return computeSMA(chartData, 50);
  }, [chartData]);
  const sma20Path = useMemo(() => buildPriceLinePath(sma20Values), [buildPriceLinePath, sma20Values]);
  const sma50Path = useMemo(() => buildPriceLinePath(sma50Values), [buildPriceLinePath, sma50Values]);

  const rsiValues = useMemo(() => {
    // Prefer server-provided RSI values when available
    if (chartData.length && chartData.some((e) => e && typeof e.rsi === 'number')) {
      return chartData.map((entry) => (entry && typeof entry.rsi === 'number' ? entry.rsi : null));
    }
    return computeRSI(chartData, 14);
  }, [chartData]);

  const hasRSIData = useMemo(() => rsiValues.some((value) => value !== null), [rsiValues]);

  const hoveredEntry = hoverIndex !== null && chartData[hoverIndex] ? chartData[hoverIndex] : null;
  const hoverX = hoveredEntry ? getXForIndex(hoverIndex) : null;
  const hoverY = hoveredEntry ? getYForPrice(hoveredEntry.price) : null;

  const priceAxisTicks = useMemo(() => {
    if (!chartData.length) {
      return [];
    }

    const desiredTickCount = chartData.length <= 6 ? chartData.length : 5;
    const step = Math.max(1, Math.floor(chartData.length / desiredTickCount));

    return chartData
      .map((entry, index) => ({ entry, index }))
      .filter(({ index }) => index % step === 0 || index === chartData.length - 1)
      .map(({ entry, index }) => ({
        x: getXForIndex(index),
        lines: [
          entry.date.toLocaleDateString('de-DE'),
          entry.date.toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
          })
        ],
        key: `${entry.date.getTime()}-${index}`
      }));
  }, [chartData, getXForIndex]);

  const priceGridLines = useMemo(() => {
    if (!hasPriceData) {
      return [];
    }

    const segments = 4;
    return Array.from({ length: segments + 1 }, (_, index) => {
      const ratio = index / segments;
      const y = CHART_PADDING.top + ratio * priceChartAreaHeight;
      const priceValue = maxPrice - ratio * valueRange;

      return {
        key: index,
        y,
        priceValue
      };
    });
  }, [priceChartAreaHeight, hasPriceData, maxPrice, valueRange]);

  const handleMouseMove = useCallback(
    (event) => {
      if (!hasPriceData || chartData.length === 0) {
        return;
      }

      const bounds = event.currentTarget.getBoundingClientRect();
      const x = event.clientX - bounds.left;
      const clampedX = Math.min(Math.max(x, CHART_PADDING.left), CHART_WIDTH - CHART_PADDING.right);
      const ratio = (clampedX - CHART_PADDING.left) / Math.max(priceChartAreaWidth, 1);
      const index = Math.round(ratio * (chartData.length - 1));
      setHoverIndex(Math.max(0, Math.min(index, chartData.length - 1)));
    },
    [chartData.length, hasPriceData, priceChartAreaWidth]
  );

  const handleMouseLeave = useCallback(() => {
    if (chartData.length) {
      setHoverIndex(chartData.length - 1);
    }
  }, [chartData.length]);

  const changeInfo = useMemo(() => {
    if (chartData.length < 2) {
      return null;
    }
    const first = chartData[0].price;
    const last = chartData[chartData.length - 1].price;
    const absolute = last - first;
    const relative = first !== 0 ? (absolute / first) * 100 : 0;

    return {
      absolute,
      relative
    };
  }, [chartData]);

  const latestEntry = chartData.length ? chartData[chartData.length - 1] : null;
  const latestSMA20 = chartData.length ? sma20Values[chartData.length - 1] : null;
  const latestSMA50 = chartData.length ? sma50Values[chartData.length - 1] : null;
  const latestRSI = chartData.length ? rsiValues[chartData.length - 1] : null;
  const hoverSMA20 = hoverIndex !== null ? sma20Values[hoverIndex] : null;
  const hoverSMA50 = hoverIndex !== null ? sma50Values[hoverIndex] : null;
  const hoverRSIValue = hoverIndex !== null ? rsiValues[hoverIndex] : null;

  const handleIndicatorToggle = (key) => {
    setIndicators((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const getYForRSI = useCallback((value) => {
    if (value === null || value === undefined) {
      return null;
    }
    const rsiChartHeight = RSI_CHART_HEIGHT - RSI_CHART_PADDING.top - RSI_CHART_PADDING.bottom;
    return RSI_CHART_PADDING.top + ((100 - value) / 100) * rsiChartHeight;
  }, []);

  const rsiPath = useMemo(() => {
    if (!hasRSIData || !indicators.rsi) {
      return '';
    }

    let path = '';
    let penDown = false;

    rsiValues.forEach((value, index) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        penDown = false;
        return;
      }

      const x = getXForIndex(index);
      const y = getYForRSI(value);
      if (y === null) {
        penDown = false;
        return;
      }

      const command = penDown ? 'L' : 'M';
      path += `${command}${x.toFixed(2)},${y.toFixed(2)} `;
      penDown = true;
    });

    return path.trim();
  }, [getXForIndex, getYForRSI, hasRSIData, indicators.rsi, rsiValues]);

  const rsiHoverY = useMemo(() => {
    if (!indicators.rsi || hoverIndex === null) {
      return null;
    }
    const value = rsiValues[hoverIndex];
    return getYForRSI(value);
  }, [getYForRSI, hoverIndex, indicators.rsi, rsiValues]);

  const rsiGuideLines = useMemo(() => {
    if (!indicators.rsi) {
      return [];
    }
    return [70, 50, 30].map((level) => ({
      level,
      y: getYForRSI(level)
    })).filter((line) => line.y !== null);
  }, [getYForRSI, indicators.rsi]);

  const rsiZoneTop = getYForRSI(70);
  const rsiZoneBottom = getYForRSI(30);
  const rsiZoneHeight = rsiZoneTop !== null && rsiZoneBottom !== null
    ? Math.max(rsiZoneBottom - rsiZoneTop, 0)
    : 0;

  const filenameBase = useMemo(() => {
    const base = (stock.ticker_symbol || stock.name || 'stock')
      .toString()
      .trim()
      .replace(/\s+/g, '-')
      .replace(/[^a-zA-Z0-9-_]/g, '')
      .toUpperCase() || 'STOCK';
    const timeframeSlug = (timeframeLabel || 'TIMEFRAME')
      .toString()
      .replace(/\s+/g, '')
      .replace(/[^a-zA-Z0-9]/g, '')
      .toUpperCase() || 'TIMEFRAME';
    return `${base}_${timeframeSlug}`;
  }, [stock.name, stock.ticker_symbol, timeframeLabel]);

  const chartHasData = chartData.length > 0;

  const handleExportCSV = useCallback(() => {
    if (!chartHasData) {
      return;
    }

    const header = ['timestamp', 'price', 'sma20', 'sma50', 'rsi'];
    const rows = chartData.map((entry, index) => {
      const timestamp = entry.date instanceof Date ? entry.date.toISOString() : '';
      const priceValue = Number.isFinite(entry.price) ? entry.price.toFixed(4) : '';
      const sma20Value = Number.isFinite(sma20Values[index]) ? sma20Values[index].toFixed(4) : '';
      const sma50Value = Number.isFinite(sma50Values[index]) ? sma50Values[index].toFixed(4) : '';
      const rsiValue = Number.isFinite(rsiValues[index]) ? rsiValues[index].toFixed(4) : '';
      return [timestamp, priceValue, sma20Value, sma50Value, rsiValue].join(',');
    });

    const csvContent = [header.join(','), ...rows].join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filenameBase}_chart-data.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, [chartData, chartHasData, filenameBase, rsiValues, sma20Values, sma50Values]);

  const handleExportPNG = useCallback(() => {
    if (!chartHasData || !priceChartRef.current) {
      return;
    }

    const svgElement = priceChartRef.current;
    const serializer = new XMLSerializer();
    let svgString = serializer.serializeToString(svgElement);

    if (!svgString.includes('<style')) {
      const styleTag = `<style>${SVG_EXPORT_STYLES}</style>`;
      svgString = svgString.replace(/<svg([^>]*)>/, (match, group) => `<svg${group}>${styleTag}`);
    }

    if (!svgString.match(/^<svg[^>]+xmlns=/)) {
      svgString = svgString.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
    }
    svgString = `<?xml version="1.0" standalone="no"?>\r\n${svgString}`;

    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8;' });
    const url = URL.createObjectURL(svgBlob);

    const image = new Image();
    image.crossOrigin = 'anonymous';
    image.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = CHART_WIDTH;
      canvas.height = PRICE_CHART_HEIGHT;
      const context = canvas.getContext('2d');
      if (!context) {
        URL.revokeObjectURL(url);
        return;
      }
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0);
      URL.revokeObjectURL(url);

      canvas.toBlob((blob) => {
        if (!blob) {
          return;
        }
        const pngUrl = URL.createObjectURL(blob);
        const downloadLink = document.createElement('a');
        downloadLink.href = pngUrl;
        downloadLink.download = `${filenameBase}_chart.png`;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        setTimeout(() => URL.revokeObjectURL(pngUrl), 1000);
      }, 'image/png');
    };
    image.onerror = (error) => {
      console.error('Fehler beim Export des Charts als PNG:', error);
      URL.revokeObjectURL(url);
    };
    image.src = url;
  }, [chartHasData, filenameBase, priceChartRef]);

  // Chart content component (used both in modal and embedded mode)
  const chartContent = (
    <div className="chart-content-wrapper">
      {!isEmbedded && <h2>{stock.name} ({stock.ticker_symbol})</h2>}
      {!isEmbedded && <p className="chart-subtitle">Visualisierung der Kursentwicklung mit technischen Indikatoren</p>}

      <div className="chart-controls">
          <div className="chart-controls-left">
            <div className="timeframe-toggle">
              {TIMEFRAME_OPTIONS.map((option) => (
                <button
                  key={option.key}
                  className={`timeframe-btn ${timeframe === option.key ? 'active' : ''}`}
                  onClick={() => setTimeframe(option.key)}
                  type="button"
                >
                  {option.label}
                </button>
              ))}
            </div>

            <div className="indicator-toggle">
              <span className="indicator-toggle__label">Indikatoren:</span>
              <label className={`indicator-option ${indicators.sma20 ? 'active' : ''}`}>
                <input
                  type="checkbox"
                  checked={indicators.sma20}
                  onChange={() => handleIndicatorToggle('sma20')}
                />
                SMA 20
              </label>
              <label className={`indicator-option ${indicators.sma50 ? 'active' : ''}`}>
                <input
                  type="checkbox"
                  checked={indicators.sma50}
                  onChange={() => handleIndicatorToggle('sma50')}
                />
                SMA 50
              </label>
              <label
                className={`indicator-option ${indicators.rsi ? 'active' : ''} ${chartData.length < 15 ? 'disabled' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={indicators.rsi && chartData.length >= 15}
                  onChange={() => chartData.length >= 15 && handleIndicatorToggle('rsi')}
                  disabled={chartData.length < 15}
                />
                RSI (14)
              </label>
            </div>
          </div>

          <div className="chart-export">
            <button
              type="button"
              className="btn btn-outline"
              onClick={handleExportCSV}
              disabled={!chartHasData}
            >
              <span className="btn-icon" aria-hidden="true">💾</span>
              <span className="btn-label">CSV</span>
            </button>
            <button
              type="button"
              className="btn btn-outline"
              onClick={handleExportPNG}
              disabled={!chartHasData}
            >
              <span className="btn-icon" aria-hidden="true">🖼️</span>
              <span className="btn-label">PNG</span>
            </button>
          </div>
        </div>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        )}

        {!loading && error && (
          <div className="error-state">
            <p>{error}</p>
            <button className="btn" onClick={() => fetchStockData()}>Erneut versuchen</button>
          </div>
        )}

        {!loading && !error && !hasPriceData && (
          <div className="empty-state">
            Leider liegen noch nicht genügend Kursdaten vor, um einen Chart darzustellen.
          </div>
        )}

        {!loading && !error && hasPriceData && (
          <>
            <div className="chart-wrapper">
              <svg
                ref={priceChartRef}
                className="chart-svg"
                viewBox={`0 0 ${CHART_WIDTH} ${PRICE_CHART_HEIGHT}`}
                preserveAspectRatio="none"
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
              >
                <defs>
                  <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="rgba(0, 123, 255, 0.35)" />
                    <stop offset="100%" stopColor="rgba(0, 123, 255, 0)" />
                  </linearGradient>
                </defs>

                <rect
                  x={CHART_PADDING.left}
                  y={CHART_PADDING.top}
                  width={priceChartAreaWidth}
                  height={priceChartAreaHeight}
                  className="chart-background"
                />

                {priceGridLines.map((line) => (
                  <g key={line.key}>
                    <line
                      x1={CHART_PADDING.left}
                      y1={line.y}
                      x2={CHART_WIDTH - CHART_PADDING.right}
                      y2={line.y}
                      className="chart-grid-line"
                    />
                    <text
                      x={CHART_PADDING.left - 12}
                      y={line.y + 4}
                      className="chart-axis-label"
                    >
                      {line.priceValue.toFixed(2)}
                    </text>
                  </g>
                ))}

                <line
                  x1={CHART_PADDING.left}
                  y1={PRICE_CHART_HEIGHT - CHART_PADDING.bottom}
                  x2={CHART_WIDTH - CHART_PADDING.right}
                  y2={PRICE_CHART_HEIGHT - CHART_PADDING.bottom}
                  className="chart-axis"
                />
                <line
                  x1={CHART_PADDING.left}
                  y1={CHART_PADDING.top}
                  x2={CHART_PADDING.left}
                  y2={PRICE_CHART_HEIGHT - CHART_PADDING.bottom}
                  className="chart-axis"
                />

                {priceAxisTicks.map((tick) => (
                  <g key={tick.key}>
                    <line
                      x1={tick.x}
                      y1={PRICE_CHART_HEIGHT - CHART_PADDING.bottom}
                      x2={tick.x}
                      y2={PRICE_CHART_HEIGHT - CHART_PADDING.bottom + 6}
                      className="chart-axis-tick"
                    />
                    <text
                      x={tick.x}
                      y={PRICE_CHART_HEIGHT - CHART_PADDING.bottom + 20}
                      className="chart-axis-label chart-axis-label-x"
                    >
                      {tick.lines.map((line, lineIndex) => (
                        <tspan
                          key={`${tick.key}-line-${lineIndex}`}
                          x={tick.x}
                          dy={lineIndex === 0 ? 0 : 14}
                        >
                          {line}
                        </tspan>
                      ))}
                    </text>
                  </g>
                ))}

                {priceAreaPath && (
                  <path d={priceAreaPath} className="chart-area" />
                )}

                {pricePath && (
                  <path d={pricePath} className="chart-line" />
                )}

                {indicators.sma20 && sma20Path && (
                  <path d={sma20Path} className="chart-line-sma20" />
                )}

                {indicators.sma50 && sma50Path && (
                  <path d={sma50Path} className="chart-line-sma50" />
                )}

                {hoveredEntry && hoverX !== null && hoverY !== null && (
                  <g>
                    <line
                      x1={hoverX}
                      y1={CHART_PADDING.top}
                      x2={hoverX}
                      y2={PRICE_CHART_HEIGHT - CHART_PADDING.bottom}
                      className="chart-hover-line"
                    />
                    <circle
                      cx={hoverX}
                      cy={hoverY}
                      r={5}
                      className="chart-hover-dot"
                    />

                    {indicators.sma20 && hoverSMA20 !== null && typeof hoverSMA20 === 'number' && !Number.isNaN(hoverSMA20) && (
                      <circle
                        cx={hoverX}
                        cy={getYForPrice(hoverSMA20)}
                        r={4}
                        className="chart-hover-dot sma20"
                      />
                    )}

                    {indicators.sma50 && hoverSMA50 !== null && typeof hoverSMA50 === 'number' && !Number.isNaN(hoverSMA50) && (
                      <circle
                        cx={hoverX}
                        cy={getYForPrice(hoverSMA50)}
                        r={4}
                        className="chart-hover-dot sma50"
                      />
                    )}
                  </g>
                )}
              </svg>

              {hoveredEntry && (
                <div className="chart-tooltip">
                  <div>
                    <span className="chart-tooltip-label">Datum:</span>
                    <span>{hoveredEntry.date.toLocaleDateString('de-DE')} {hoveredEntry.date.toLocaleTimeString('de-DE')}</span>
                  </div>
                  <div>
                    <span className="chart-tooltip-label">Kurs:</span>
                    <span>${hoveredEntry.price.toFixed(2)}</span>
                  </div>
                  {indicators.sma20 && hoverSMA20 !== null && typeof hoverSMA20 === 'number' && !Number.isNaN(hoverSMA20) && (
                    <div>
                      <span className="chart-tooltip-label">SMA 20:</span>
                      <span>${hoverSMA20.toFixed(2)}</span>
                    </div>
                  )}
                  {indicators.sma50 && hoverSMA50 !== null && typeof hoverSMA50 === 'number' && !Number.isNaN(hoverSMA50) && (
                    <div>
                      <span className="chart-tooltip-label">SMA 50:</span>
                      <span>${hoverSMA50.toFixed(2)}</span>
                    </div>
                  )}
                  {indicators.rsi && hoverRSIValue !== null && typeof hoverRSIValue === 'number' && !Number.isNaN(hoverRSIValue) && (
                    <div>
                      <span className="chart-tooltip-label">RSI:</span>
                      <span>{hoverRSIValue.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {indicators.rsi && hasRSIData && (
              <div className="chart-wrapper chart-wrapper--rsi">
                <svg
                  className="chart-svg chart-svg-rsi"
                  viewBox={`0 0 ${CHART_WIDTH} ${RSI_CHART_HEIGHT}`}
                  preserveAspectRatio="none"
                  onMouseMove={handleMouseMove}
                  onMouseLeave={handleMouseLeave}
                >
                  <rect
                    x={RSI_CHART_PADDING.left}
                    y={RSI_CHART_PADDING.top}
                    width={CHART_WIDTH - RSI_CHART_PADDING.left - RSI_CHART_PADDING.right}
                    height={RSI_CHART_HEIGHT - RSI_CHART_PADDING.top - RSI_CHART_PADDING.bottom}
                    className="chart-background rsi"
                  />

                  {rsiZoneHeight > 0 && (
                    <rect
                      x={RSI_CHART_PADDING.left}
                      y={rsiZoneTop ?? RSI_CHART_PADDING.top}
                      width={CHART_WIDTH - RSI_CHART_PADDING.left - RSI_CHART_PADDING.right}
                      height={rsiZoneHeight}
                      className="chart-rsi-zone"
                    />
                  )}

                  {rsiGuideLines.map((line) => (
                    <g key={line.level}>
                      <line
                        x1={RSI_CHART_PADDING.left}
                        y1={line.y}
                        x2={CHART_WIDTH - RSI_CHART_PADDING.right}
                        y2={line.y}
                        className="chart-grid-line rsi"
                      />
                      <text
                        x={RSI_CHART_PADDING.left - 12}
                        y={line.y + 4}
                        className="chart-axis-label"
                      >
                        {line.level}
                      </text>
                    </g>
                  ))}

                  <line
                    x1={RSI_CHART_PADDING.left}
                    y1={RSI_CHART_HEIGHT - RSI_CHART_PADDING.bottom}
                    x2={CHART_WIDTH - RSI_CHART_PADDING.right}
                    y2={RSI_CHART_HEIGHT - RSI_CHART_PADDING.bottom}
                    className="chart-axis"
                  />
                  <line
                    x1={RSI_CHART_PADDING.left}
                    y1={RSI_CHART_PADDING.top}
                    x2={RSI_CHART_PADDING.left}
                    y2={RSI_CHART_HEIGHT - RSI_CHART_PADDING.bottom}
                    className="chart-axis"
                  />

                  {priceAxisTicks.map((tick) => (
                    <g key={`rsi-${tick.key}`}>
                      <line
                        x1={tick.x}
                        y1={RSI_CHART_HEIGHT - RSI_CHART_PADDING.bottom}
                        x2={tick.x}
                        y2={RSI_CHART_HEIGHT - RSI_CHART_PADDING.bottom + 6}
                        className="chart-axis-tick"
                      />
                    </g>
                  ))}

                  {rsiPath && (
                    <path d={rsiPath} className="chart-line-rsi" />
                  )}

                  {indicators.rsi && hoverX !== null && rsiHoverY !== null && (
                    <g>
                      <line
                        x1={hoverX}
                        y1={RSI_CHART_PADDING.top}
                        x2={hoverX}
                        y2={RSI_CHART_HEIGHT - RSI_CHART_PADDING.bottom}
                        className="chart-hover-line"
                      />
                      <circle
                        cx={hoverX}
                        cy={rsiHoverY}
                        r={4}
                        className="chart-hover-dot rsi"
                      />
                    </g>
                  )}
                </svg>
              </div>
            )}
          </>
        )}

        {latestEntry && (
          <div className="chart-meta">
            <div>
              <strong>Letzter Kurs:</strong> ${latestEntry.price.toFixed(2)}
            </div>
            <div>
              <strong>Stand:</strong> {latestEntry.date.toLocaleString('de-DE')}
            </div>
            {changeInfo && (
              <div className={`chart-change ${changeInfo.absolute >= 0 ? 'positive' : 'negative'}`}>
                <strong>Veränderung:</strong> {changeInfo.absolute >= 0 ? '+' : ''}{changeInfo.absolute.toFixed(2)} (${changeInfo.relative >= 0 ? '+' : ''}{changeInfo.relative.toFixed(2)}%)
              </div>
            )}
            {indicators.sma20 && latestSMA20 !== null && typeof latestSMA20 === 'number' && !Number.isNaN(latestSMA20) && (
              <div className="chart-meta-indicator">
                <strong>SMA 20:</strong> ${latestSMA20.toFixed(2)}
              </div>
            )}
            {indicators.sma50 && latestSMA50 !== null && typeof latestSMA50 === 'number' && !Number.isNaN(latestSMA50) && (
              <div className="chart-meta-indicator">
                <strong>SMA 50:</strong> ${latestSMA50.toFixed(2)}
              </div>
            )}
            {indicators.rsi && latestRSI !== null && typeof latestRSI === 'number' && !Number.isNaN(latestRSI) && (
              <div className="chart-meta-indicator">
                <strong>RSI 14:</strong> {latestRSI.toFixed(2)}
              </div>
            )}
          </div>
        )}
    </div>
  );

  // Return with or without modal wrapper
  if (isEmbedded) {
    return <div className="chart-embedded">{chartContent}</div>;
  }

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal-content chart-modal" onClick={(event) => event.stopPropagation()}>
        <span className="close" onClick={onClose}>&times;</span>
        {chartContent}
      </div>
    </div>
  );
}

export default StockChartModal;

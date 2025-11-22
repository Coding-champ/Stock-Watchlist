import { useCallback, useEffect, useRef, useState, useMemo } from 'react';
import { useApi } from '../useApi';

/**
 * useChartIndicators
 * Manages lazy-loading of technical indicators (RSI, MACD, Bollinger, ATR, VWAP, Ichimoku, Stochastic)
 * Merges indicator data into chartData rows and tracks cache state.
 * 
 * @param {Object} params
 * @param {number} params.assetId - Stock/asset ID
 * @param {string} params.period - Time period (1d, 1mo, 1y, etc.) or 'custom'
 * @param {string} params.customStartDate - Custom range start (if period='custom')
 * @param {string} params.customEndDate - Custom range end (if period='custom')
 * @param {Array} params.chartData - Current chart data array to merge indicators into
 * @param {Function} params.onChartDataUpdate - Callback to update parent chartData state
 * @param {Object} params.toggles - Indicator visibility toggles
 * @param {boolean} params.toggles.showRSI
 * @param {boolean} params.toggles.showMACD
 * @param {boolean} params.toggles.showBollinger
 * @param {boolean} params.toggles.showATR
 * @param {boolean} params.toggles.showVWAP
 * @param {boolean} params.toggles.showIchimoku
 * @param {boolean} params.toggles.showStochastic
 * @param {boolean} params.toggles.showSMA50
 * @param {boolean} params.toggles.showSMA200
 */
export function useChartIndicators({
  assetId,
  period,
  customStartDate,
  customEndDate,
  chartData,
  onChartDataUpdate,
  toggles
}) {
  const { fetchApi } = useApi();
  const [indicators, setIndicators] = useState({});
  
  // Track in-flight requests to prevent duplicate fetches
  const inFlightIndicatorsRef = useRef(new Set());
  const indicatorsRef = useRef(indicators);
  const chartDataRef = useRef(chartData);
  
  // Cache key for invalidation on period/date change
  // Format: indicator:{assetId}:{period}:{customStart|"-"}:{customEnd|"-"}
  const cacheKey = useMemo(() => {
    const start = period === 'custom' && customStartDate ? customStartDate : '-';
    const end = period === 'custom' && customEndDate ? customEndDate : '-';
    return `indicator:${assetId}:${period}:${start}:${end}`;
  }, [assetId, period, customStartDate, customEndDate]);
  
  const previousCacheKeyRef = useRef(cacheKey);

  // Keep refs in sync with state
  useEffect(() => {
    indicatorsRef.current = indicators;
  }, [indicators]);

  useEffect(() => {
    chartDataRef.current = chartData;
  }, [chartData]);
  
  // Invalidate cache when period/date range changes
  useEffect(() => {
    if (previousCacheKeyRef.current !== cacheKey) {
      console.log(`[useChartIndicators] Cache invalidated: ${previousCacheKeyRef.current} → ${cacheKey}`);
      setIndicators({});
      indicatorsRef.current = {};
      inFlightIndicatorsRef.current.clear();
      previousCacheKeyRef.current = cacheKey;
    }
  }, [cacheKey]);

  // Fetch one or more indicators and merge into chartData
  const fetchIndicators = useCallback(async (indicatorNames, options = {}) => {
    const { force = false } = options;
    if (!indicatorNames || indicatorNames.length === 0) return;
    
    // Check if chartData is available
    const currentChartData = chartDataRef.current;
    if (!currentChartData || currentChartData.length === 0) return;
    
    try {
      // Filter out already-fetched and in-flight indicators
      const toFetch = [];
      indicatorNames.forEach(name => {
        if (!force && indicatorsRef.current && (name in indicatorsRef.current)) return;
        if (inFlightIndicatorsRef.current.has(name)) return;
        toFetch.push(name);
      });
      
      if (toFetch.length === 0) return;

      // Mark as in-flight
      toFetch.forEach(n => inFlightIndicatorsRef.current.add(n));

      // Build endpoint with period or custom range
      let indicatorsEndpoint = `/stock-data/${assetId}/technical-indicators?`;
      if (period === 'custom' && customStartDate && customEndDate) {
        indicatorsEndpoint += `start=${customStartDate}&end=${customEndDate}`;
      } else {
        indicatorsEndpoint += `period=${period}`;
      }
      indicatorsEndpoint += `&${toFetch.map(i => `indicators=${i}`).join('&')}`;
      
      const json = await fetchApi(indicatorsEndpoint);
      const newInd = json?.indicators || {};

      // Update indicators cache
      setIndicators(prev => ({ ...prev, ...newInd }));

      // Merge into chartData rows using callback form to get latest state
      onChartDataUpdate(currentChartData => {
        if (!currentChartData || currentChartData.length === 0) return currentChartData;
        
        return currentChartData.map((row, idx) => {
          const copy = { ...row };
          
          for (const key of Object.keys(newInd)) {
            const val = newInd[key];
            if (val === undefined || val === null) continue;
            
            if (key === 'macd') {
              copy.macd = val.macd?.[idx] ?? copy.macd;
              copy.macdSignal = val.signal?.[idx] ?? copy.macdSignal;
              copy.macdHistogram = val.histogram?.[idx] ?? val.hist?.[idx] ?? copy.macdHistogram;
            } else if (key === 'bollinger') {
              copy.bollingerUpper = val.upper?.[idx] ?? copy.bollingerUpper;
              copy.bollingerMiddle = val.middle?.[idx] ?? val.sma?.[idx] ?? copy.bollingerMiddle;
              copy.bollingerLower = val.lower?.[idx] ?? copy.bollingerLower;
              copy.bollingerPercentB = val.percent_b?.[idx] ?? copy.bollingerPercentB;
              copy.bollingerBandwidth = val.bandwidth?.[idx] ?? copy.bollingerBandwidth;
            } else if (key === 'stochastic') {
              copy.k_percent = val.k_percent?.[idx] ?? copy.k_percent;
              copy.d_percent = val.d_percent?.[idx] ?? copy.d_percent;
            } else if (key === 'ichimoku') {
              copy.ichimoku_conversion = val.conversion?.[idx] ?? copy.ichimoku_conversion;
              copy.ichimoku_base = val.base?.[idx] ?? copy.ichimoku_base;
              copy.ichimoku_span_a = val.span_a?.[idx] ?? copy.ichimoku_span_a;
              copy.ichimoku_span_b = val.span_b?.[idx] ?? copy.ichimoku_span_b;
              copy.ichimoku_chikou = val.chikou?.[idx] ?? copy.ichimoku_chikou;
            } else if (key === 'sma_50') {
              copy.sma50 = Array.isArray(val) ? val[idx] : val;
            } else if (key === 'sma_200') {
              copy.sma200 = Array.isArray(val) ? val[idx] : val;
            } else {
              copy[key] = Array.isArray(val) ? val[idx] : val;
            }
          }
          
          return copy;
        });
      });

      // Clear in-flight markers
      toFetch.forEach(n => inFlightIndicatorsRef.current.delete(n));
    } catch (e) {
      console.warn('Lazy indicators fetch failed', e);
      indicatorNames.forEach(n => inFlightIndicatorsRef.current.delete(n));
    }
  }, [assetId, period, customStartDate, customEndDate, onChartDataUpdate, fetchApi]);

  // Individual toggle watchers - use ref instead of chartData dependency to avoid loops
  useEffect(() => {
    if (!chartDataRef.current || chartDataRef.current.length === 0) return;
    if (toggles.showRSI && !('rsi' in indicatorsRef.current) && !inFlightIndicatorsRef.current.has('rsi')) {
      fetchIndicators(['rsi']);
    }
  }, [toggles.showRSI, fetchIndicators]);

  // SMA50 watcher
  useEffect(() => {
    if (!chartDataRef.current || chartDataRef.current.length === 0) return;
    if (toggles.showSMA50 && !('sma_50' in indicatorsRef.current) && !inFlightIndicatorsRef.current.has('sma_50')) {
      fetchIndicators(['sma_50']);
    }
  }, [toggles.showSMA50, fetchIndicators]);

  // SMA200 watcher
  useEffect(() => {
    if (!chartDataRef.current || chartDataRef.current.length === 0) return;
    if (toggles.showSMA200 && !('sma_200' in indicatorsRef.current) && !inFlightIndicatorsRef.current.has('sma_200')) {
      fetchIndicators(['sma_200']);
    }
  }, [toggles.showSMA200, fetchIndicators]);

  useEffect(() => {
    if (!chartDataRef.current || chartDataRef.current.length === 0) return;
    if (toggles.showIchimoku && !('ichimoku' in indicatorsRef.current) && !inFlightIndicatorsRef.current.has('ichimoku')) {
      fetchIndicators(['ichimoku']);
    }
  }, [toggles.showIchimoku, fetchIndicators]);

  useEffect(() => {
    if (!chartDataRef.current || chartDataRef.current.length === 0) return;
    if (toggles.showMACD && !('macd' in indicatorsRef.current) && !inFlightIndicatorsRef.current.has('macd')) {
      fetchIndicators(['macd']);
    }
  }, [toggles.showMACD, fetchIndicators]);

  useEffect(() => {
    if (!chartDataRef.current || chartDataRef.current.length === 0) return;
    if (toggles.showBollinger && !('bollinger' in indicatorsRef.current) && !inFlightIndicatorsRef.current.has('bollinger')) {
      fetchIndicators(['bollinger']);
    }
  }, [toggles.showBollinger, fetchIndicators]);

  useEffect(() => {
    if (!chartDataRef.current || chartDataRef.current.length === 0) return;
    if (toggles.showATR && !('atr' in indicatorsRef.current) && !inFlightIndicatorsRef.current.has('atr')) {
      fetchIndicators(['atr']);
    }
  }, [toggles.showATR, fetchIndicators]);

  useEffect(() => {
    if (!chartDataRef.current || chartDataRef.current.length === 0) return;
    if (toggles.showVWAP && !('vwap' in indicatorsRef.current) && !inFlightIndicatorsRef.current.has('vwap')) {
      fetchIndicators(['vwap']);
    }
  }, [toggles.showVWAP, fetchIndicators]);

  useEffect(() => {
    if (!chartDataRef.current || chartDataRef.current.length === 0) return;
    if (toggles.showStochastic && !('stochastic' in indicatorsRef.current) && !inFlightIndicatorsRef.current.has('stochastic')) {
      fetchIndicators(['stochastic']);
    }
  }, [toggles.showStochastic, fetchIndicators]);

  return {
    indicators,
    fetchIndicators
  };
}

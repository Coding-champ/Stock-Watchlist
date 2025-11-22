import { useEffect, useRef, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';

/**
 * useChartEvents
 * Separately fetches dividends, splits, earnings when event toggles change, debounced.
 * Merges events into first row of existing chartData without replacing indicator data.
 */
export function useChartEvents({
  assetId,
  period,
  customStartDate,
  customEndDate,
  chartData,
  showDividends,
  showSplits,
  showEarnings,
  debounceMs = 300,
  onEventsUpdate
}) {
  const { fetchApi } = useApi();
  const timerRef = useRef(null);
  const lastRequestPayloadRef = useRef(null);
  const chartDataRef = useRef(chartData);

  // Keep chartData ref in sync
  useEffect(() => {
    chartDataRef.current = chartData;
  }, [chartData]);

  const buildEndpoint = useCallback(() => {
    const periodConfigMap = {
      '1d': '5m', '5d': '15m', '1mo': '1h', '3mo': '1d', '6mo': '1d', '1y': '1d', '3y': '1wk', '5y': '1wk', 'max': '1wk', 'custom': '1d'
    };
    const interval = periodConfigMap[period] || '1d';
    let endpoint = `/stock-data/${assetId}/chart?interval=${interval}`;
    if (period === 'custom' && customStartDate && customEndDate) {
      endpoint += `&start=${customStartDate}&end=${customEndDate}`;
    } else {
      endpoint += `&period=${period}`;
    }
    // We only need events; backend currently returns full chart so we'll ignore price data.
    // Add earnings include if any event toggle active (existing API contract bundles events)
    if (showDividends || showSplits || showEarnings) {
      endpoint += `&include_earnings=true`;
    }
    return endpoint;
  }, [period, customStartDate, customEndDate, assetId, showDividends, showSplits, showEarnings]);

  const fetchEvents = useCallback(async () => {
    const currentChartData = chartDataRef.current;
    if (!currentChartData || currentChartData.length === 0) return; // Need base data first
    
    if (!showDividends && !showSplits && !showEarnings) {
      // Clear events if all toggles off
      const cloned = [...currentChartData];
      const first = { ...cloned[0] };
      first.dividends = [];
      first.dividends_annual = [];
      first.splits = [];
      first.earnings = [];
      cloned[0] = first;
      onEventsUpdate(cloned);
      return;
    }
    try {
      const endpoint = buildEndpoint();
      if (lastRequestPayloadRef.current === endpoint) return; // Prevent duplicate identical request post debounce
      lastRequestPayloadRef.current = endpoint;
      
      const json = await fetchApi(endpoint, { staleTime: 30000 });
      
      // Use callback form to get latest chartData
      onEventsUpdate(latestChartData => {
        if (!latestChartData || latestChartData.length === 0) return latestChartData;
        
        const cloned = [...latestChartData];
        const first = { ...cloned[0] };
        first.dividends_annual = showDividends ? (json.dividends_annual || []) : [];
        first.dividends = showDividends ? (json.dividends || []) : [];
        first.splits = showSplits ? (json.splits || []) : [];
        first.earnings = showEarnings ? (json.earnings || []) : [];
        cloned[0] = first;
        return cloned;
      });
    } catch (e) {
      console.warn('Event fetch failed', e);
    }
  }, [showDividends, showSplits, showEarnings, fetchApi, onEventsUpdate, buildEndpoint]);

  useEffect(() => {
    // Debounce multiple rapid toggle changes
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      fetchEvents();
    }, debounceMs);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [showDividends, showSplits, showEarnings, period, customStartDate, customEndDate, fetchEvents, debounceMs]);
}

export default useChartEvents;

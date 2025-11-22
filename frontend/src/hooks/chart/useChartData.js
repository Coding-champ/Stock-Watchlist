import { useCallback, useEffect, useState, useMemo } from 'react';
import { mergeIndicators, transformChartPayload, ensureVwap, ensureVolumeMovingAverages, computeSharedTicks } from '../../utils/chart/dataTransforms';
import { useApi } from '../../hooks/useApi';

/**
 * useChartData
 * Fetches chart base data + initial indicators + analytics (crossover, fibonacci, support/resistance, divergence)
 * Accepts period or custom range and event toggles. Returns fully transformed series and meta.
 */
export function useChartData({
  assetId,
  period,
  customStartDate,
  customEndDate,
  onLatestVwap
}) {
  const { fetchApi } = useApi();
  const [chartData, setChartData] = useState(null);
  const [xAxisTicks, setXAxisTicks] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [bollingerSignal, setBollingerSignal] = useState(null);
  const [crossoverData, setCrossoverData] = useState(null);
  const [fibonacciData, setFibonacciData] = useState(null);
  const [supportResistanceData, setSupportResistanceData] = useState(null);
  const [divergenceData, setDivergenceData] = useState(null);
  const [seedIndicators, setSeedIndicators] = useState({});

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const periodConfigMap = {
        '1d': '5m', '5d': '15m', '1mo': '1h', '3mo': '1d', '6mo': '1d', '1y': '1d', '3y': '1wk', '5y': '1wk', 'max': '1wk', 'custom': '1d'
      };
      const interval = periodConfigMap[period] || '1d';
      let endpoint = `/stock-data/${assetId}/chart?interval=${interval}&include_volume=true`;
      if (period === 'custom' && customStartDate && customEndDate) {
        endpoint += `&start=${customStartDate}&end=${customEndDate}`;
      } else {
        endpoint += `&period=${period}`;
      }
      const chartJson = await fetchApi(endpoint, { staleTime: 60000 });

      // Initial indicators (SMA only for lean payload)
      const initialIndicatorsList = ['sma_50', 'sma_200'];
      let indicatorsJson = null;
      try {
        let indicatorsEndpoint = `/stock-data/${assetId}/technical-indicators?`;
        if (period === 'custom' && customStartDate && customEndDate) {
          indicatorsEndpoint += `start=${customStartDate}&end=${customEndDate}`;
        } else {
          indicatorsEndpoint += `period=${period}`;
        }
        indicatorsEndpoint += `&${initialIndicatorsList.map(i => `indicators=${i}`).join('&')}`;
        indicatorsJson = await fetchApi(indicatorsEndpoint, { staleTime: 60000 });
      } catch (_) {
        indicatorsJson = null;
      }

      const chartIndicators = chartJson?.indicators || {};
      const fetchedIndicators = indicatorsJson?.indicators || {};
      const sourceIndicators = mergeIndicators(chartIndicators, fetchedIndicators);
      setSeedIndicators(fetchedIndicators); // expose initially fetched indicators for outer merging if needed

      let transformed = transformChartPayload(chartJson, sourceIndicators);
      transformed = ensureVwap(transformed, sourceIndicators);
      transformed = ensureVolumeMovingAverages(transformed);

      // Events intentionally excluded from base fetch now; separate hook merges them later.

      setChartData(transformed);
      const latestVwap = transformed.length ? transformed[transformed.length - 1].vwap : null;
      if (typeof onLatestVwap === 'function') onLatestVwap(latestVwap);

      setXAxisTicks(computeSharedTicks(transformed, 6));

      // Bollinger from indicators response (if present)
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
      } else {
        setBollingerSignal(null);
      }

      // Calculated metrics (fibonacci/support/crossovers)
      try {
        const crossoverJson = await fetchApi(`/stock-data/${assetId}/calculated-metrics`, { staleTime: 60000 });
        const cross = crossoverJson?.metrics?.basic_indicators?.sma_crossovers;
        setCrossoverData(cross && cross.all_crossovers ? cross : null);
        setFibonacciData(crossoverJson?.metrics?.basic_indicators?.fibonacci_levels || null);
        setSupportResistanceData(crossoverJson?.metrics?.basic_indicators?.support_resistance || null);
      } catch (e) {
        setCrossoverData(null);
        setFibonacciData(null);
        setSupportResistanceData(null);
      }

      // Divergence analysis
      try {
        const divergenceJson = await fetchApi(`/stock-data/${assetId}/divergence-analysis`, { staleTime: 60000 });
        if (divergenceJson?.rsi_divergence || divergenceJson?.macd_divergence) {
          setDivergenceData(divergenceJson);
        } else {
          setDivergenceData(null);
        }
      } catch (e) {
        setDivergenceData(null);
      }
    } catch (err) {
      setError(err.message || 'Chart fetch failed');
    } finally {
      setLoading(false);
    }
  }, [assetId, period, customStartDate, customEndDate, onLatestVwap, fetchApi]);

  useEffect(() => { refetch(); }, [refetch]);

  const memoized = useMemo(() => ({
    chartData,
    xAxisTicks,
    loading,
    error,
    refetch,
    bollingerSignal,
    crossoverData,
    fibonacciData,
    supportResistanceData,
    divergenceData,
    seedIndicators
  }), [
    chartData,
    xAxisTicks,
    loading,
    error,
    refetch,
    bollingerSignal,
    crossoverData,
    fibonacciData,
    supportResistanceData,
    divergenceData,
    seedIndicators
  ]);

  return memoized;
}

import { useState } from 'react';
import { calculatePerformance, normalizeSortScore } from '../utils/calculations';
import { PERFORMANCE_SORT_KEYS } from '../constants/stockTable';

export function useStockSorting(sparklineSeries, extendedDataMap) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const getPerformanceScore = (stock, key) => {
    const latestData = stock.latest_data || stock.latestData || {};
    const sparkData = sparklineSeries[stock.id]?.values || [];
    const displayPrice = typeof latestData.current_price === 'number'
      ? latestData.current_price
      : (sparkData.length ? sparkData[sparkData.length - 1] : null);
    if (typeof displayPrice !== 'number') {
      return null;
    }

    const previousPrice = sparkData.length > 1 ? sparkData[sparkData.length - 2] : null;
    const earliestPrice = sparkData.length > 0 ? sparkData[0] : null;
    const priceData = extendedDataMap[stock.id]?.price_data;

    switch (key) {
      case PERFORMANCE_SORT_KEYS.CURRENT: {
        const perf = calculatePerformance(previousPrice, displayPrice);
        return perf ? perf.percent : null;
      }
      case PERFORMANCE_SORT_KEYS.WATCHLIST: {
        const perf = calculatePerformance(earliestPrice, displayPrice);
        return perf ? perf.percent : null;
      }
      case PERFORMANCE_SORT_KEYS.WEEK: {
        if (!priceData || typeof priceData.fifty_two_week_low !== 'number') {
          return null;
        }
        const perf = calculatePerformance(priceData.fifty_two_week_low, displayPrice);
        return perf ? perf.percent : null;
      }
      default:
        return null;
    }
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortedStocks = (stocks) => {
    if (!sortConfig.key) return stocks;

    if (Object.values(PERFORMANCE_SORT_KEYS).includes(sortConfig.key)) {
      const sorted = [...stocks].sort((a, b) => {
        const aScoreRaw = getPerformanceScore(a, sortConfig.key);
        const bScoreRaw = getPerformanceScore(b, sortConfig.key);

        const aScore = normalizeSortScore(aScoreRaw, sortConfig.direction);
        const bScore = normalizeSortScore(bScoreRaw, sortConfig.direction);

        if (aScore < bScore) return -1;
        if (aScore > bScore) return 1;
        return 0;
      });

      return sortConfig.direction === 'asc' ? sorted : sorted.reverse();
    }

    // Fallback to simple property sort
    return [...stocks].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      if (sortConfig.direction === 'asc') {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      }
      return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
    });
  };

  const applySortPreset = (key, direction = 'desc') => {
    setSortConfig({ key, direction });
  };

  const isSortPresetActive = (key, direction = 'desc') => (
    sortConfig.key === key && sortConfig.direction === direction
  );

  return {
    sortConfig,
    setSortConfig,
    handleSort,
    getSortedStocks,
    applySortPreset,
    isSortPresetActive
  };
}

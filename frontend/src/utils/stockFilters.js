/**
 * Check if a stock entry matches the performance filter
 * @param {string} filter - The filter type
 * @param {Object} entry - The enriched stock entry
 * @returns {boolean} True if entry matches filter
 */
export function matchesPerformanceFilter(filter, entry) {
  if (!filter || filter === 'all') {
    return true;
  }

  const { currentPerformance, watchlistPerformance, weekPerformance } = entry;

  switch (filter) {
    case 'current-positive':
      return currentPerformance?.direction === 'positive';
    case 'current-negative':
      return currentPerformance?.direction === 'negative';
    case 'watchlist-positive':
      return watchlistPerformance?.direction === 'positive';
    case 'watchlist-negative':
      return watchlistPerformance?.direction === 'negative';
    case 'week-positive':
      return weekPerformance?.direction === 'positive';
    case 'week-negative':
      return weekPerformance?.direction === 'negative';
    default:
      return true;
  }
}

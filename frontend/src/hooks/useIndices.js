import { useApiQuery } from './useApiQuery';

/**
 * Hook to fetch all indices with optional filtering
 */
export function useIndices(region = null, indexType = null) {
  let url = '/indices';
  const params = [];
  if (region) params.push(`region=${encodeURIComponent(region)}`);
  if (indexType) params.push(`index_type=${encodeURIComponent(indexType)}`);
  if (params.length > 0) url += '?' + params.join('&');

  return useApiQuery(url);
}

/**
 * Hook to fetch details of a specific index
 */
export function useIndexDetails(tickerSymbol) {
  return useApiQuery(tickerSymbol ? `/indices/${tickerSymbol}` : null, {
    enabled: !!tickerSymbol
  });
}

/**
 * Hook to fetch constituents of an index
 */
export function useIndexConstituents(tickerSymbol, includeRemoved = false) {
  const url = tickerSymbol
    ? `/indices/${tickerSymbol}/constituents?include_removed=${includeRemoved}`
    : null;
  
  return useApiQuery(url, {
    enabled: !!tickerSymbol
  });
}

/**
 * Hook to fetch price history for an index
 */
export function useIndexPriceHistory(tickerSymbol, startDate = null, endDate = null, limit = null) {
  let url = tickerSymbol ? `/indices/${tickerSymbol}/price-history` : null;
  
  if (tickerSymbol) {
    const params = [];
    if (startDate) params.push(`start_date=${startDate}`);
    if (endDate) params.push(`end_date=${endDate}`);
    if (limit) params.push(`limit=${limit}`);
    if (params.length > 0) url += '?' + params.join('&');
  }

  return useApiQuery(url, {
    enabled: !!tickerSymbol
  });
}

export default useIndices;

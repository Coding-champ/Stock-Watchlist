import { useQuery } from '@tanstack/react-query';

// Support multiple backend ports; try env first, then common fallbacks.
const API_FALLBACKS = [
  process.env.REACT_APP_API_URL,
  'http://localhost:8000',
  'http://127.0.0.1:8000',
  'http://localhost:8080',
  'http://127.0.0.1:8080'
].filter(Boolean);

/**
 * Fetch comprehensive statistics for an index
 * @param {string} tickerSymbol - Index ticker symbol (e.g., '^GSPC')
 * @param {number} riskFreeRate - Annual risk-free rate (default 0.04 for 4%)
 * @returns {object} Query result with statistics data
 */
export function useIndexStatistics(tickerSymbol, riskFreeRate = 0.04) {
  return useQuery({
    queryKey: ['index-statistics', tickerSymbol, riskFreeRate],
    queryFn: async () => {
      let lastError = null;
      for (const base of API_FALLBACKS) {
        try {
          const url = `${base}/indices/${encodeURIComponent(tickerSymbol)}/statistics?risk_free_rate=${riskFreeRate}`;
          const response = await fetch(url, { cache: 'no-store' });
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            lastError = new Error(errorData.detail || `Request failed (${response.status}) at ${base}`);
            continue;
          }
          return response.json();
        } catch (e) {
          lastError = e;
          continue;
        }
      }
      throw lastError || new Error(`Failed to fetch statistics for ${tickerSymbol}`);
    },
    enabled: !!tickerSymbol,
    retry: 2,
    staleTime: 5 * 60 * 1000, // Statistics are relatively stable, cache for 5 minutes
  });
}

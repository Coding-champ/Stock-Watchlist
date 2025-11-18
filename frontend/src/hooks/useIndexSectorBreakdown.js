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
 * Fetch sector breakdown for an index
 * @param {string} tickerSymbol - Index ticker symbol (e.g., '^GSPC')
 * @returns {object} Query result with sector breakdown data
 */
export function useIndexSectorBreakdown(tickerSymbol) {
  return useQuery({
    queryKey: ['index-sector-breakdown', tickerSymbol],
    queryFn: async () => {
      let lastError = null;
      for (const base of API_FALLBACKS) {
        try {
          const url = `${base}/indices/${encodeURIComponent(tickerSymbol)}/sector-breakdown`;
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
      throw lastError || new Error(`Failed to fetch sector breakdown for ${tickerSymbol}`);
    },
    enabled: !!tickerSymbol,
    retry: 2,
    staleTime: 10 * 60 * 1000, // Sector data is relatively stable, cache for 10 minutes
  });
}

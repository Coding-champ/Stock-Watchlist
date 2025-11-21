import { useQuery } from '@tanstack/react-query';
import API_BASE from '../config';

const PERIOD_OPTIONS = ["1mo","3mo","6mo","1y","2y","5y"];

export function useBenchmarkComparison(stockId, indexSymbol, period = '1y', enabled = true) {
  return useQuery({
    queryKey: ['benchmark-comparison', stockId, indexSymbol, period],
    queryFn: async () => {
      if (!stockId || !indexSymbol) return null;
      const url = `${API_BASE}/stocks/${stockId}/benchmark-comparison?index_symbol=${encodeURIComponent(indexSymbol)}&period=${encodeURIComponent(period)}`;
      const resp = await fetch(url);
      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        throw new Error(errJson.detail || `Request failed (${resp.status})`);
      }
      return resp.json();
    },
    enabled: enabled && !!stockId && !!indexSymbol,
    staleTime: 60 * 60 * 1000, // 1 hour
    retry: 1,
  });
}

export function inferDefaultBenchmark(country) {
  if (!country) return '^GSPC';
  const c = country.toUpperCase();
  if (c === 'US' || c === 'USA') return '^GSPC';
  if (c === 'DE' || c.includes('GERM')) return '^GDAXI';
  if (c === 'GB' || c === 'UK') return '^FTSE';
  if (c === 'JP') return '^N225';
  return '^GSPC';
}

export const BENCHMARK_PERIODS = PERIOD_OPTIONS;

export default useBenchmarkComparison;
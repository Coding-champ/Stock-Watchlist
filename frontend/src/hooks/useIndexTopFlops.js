import { useQuery } from '@tanstack/react-query';
import API_BASE from '../config';

export function useIndexTopFlops(symbol, limit = 5, enabled = true) {
  return useQuery({
    queryKey: ['index-top-flops', symbol, limit],
    queryFn: async () => {
      if (!symbol) return null;
      const url = `${API_BASE}/indices/${encodeURIComponent(symbol)}/top-flops?limit=${limit}`;
      const resp = await fetch(url);
      const text = await resp.text();
      let json = null;
      try { json = text ? JSON.parse(text) : null; } catch { json = null; }
      if (!resp.ok) {
        const detail = json?.detail || text || 'Request failed';
        throw new Error(detail);
      }
      return json;
    },
    enabled: enabled && !!symbol,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export default useIndexTopFlops;

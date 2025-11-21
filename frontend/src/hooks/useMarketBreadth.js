import { useQuery } from '@tanstack/react-query';
import API_BASE from '../config';

export function useBreadthSnapshot(symbol, date = null, enabled = true) {
  return useQuery({
    queryKey: ['breadth-snapshot', symbol, date],
    queryFn: async () => {
      const params = [];
      if (date) params.push(`date_param=${encodeURIComponent(date)}`);
      const qs = params.length ? `?${params.join('&')}` : '';
      const url = `${API_BASE}/indices/${encodeURIComponent(symbol)}/breadth${qs}`;
      const resp = await fetch(url);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Request failed (${resp.status})`);
      }
      return resp.json();
    },
    enabled: enabled && !!symbol,
    staleTime: 5 * 60 * 1000,
  });
}

export function useBreadthHistory(symbol, days = 30, includeMcClellan = false, enabled = true) {
  return useQuery({
    queryKey: ['breadth-history', symbol, days, includeMcClellan],
    queryFn: async () => {
      const url = `${API_BASE}/indices/${encodeURIComponent(symbol)}/breadth/history?days=${days}&include_mcclellan=${includeMcClellan}`;
      const resp = await fetch(url);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Request failed (${resp.status})`);
      }
      return resp.json();
    },
    enabled: enabled && !!symbol,
    staleTime: 5 * 60 * 1000,
  });
}

export default { useBreadthSnapshot, useBreadthHistory };
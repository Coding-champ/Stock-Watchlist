import { useQuery } from '@tanstack/react-query';
import API_BASE from '../config';

export function useBreadthSnapshot(symbol, date = null, enabled = true) {
  return useBreadthSnapshotWithMode(symbol, date, enabled, 'sma200');
}

export function useBreadthSnapshotWithMode(symbol, date = null, enabled = true, mode = 'sma200') {
  return useQuery({
    queryKey: ['breadth-snapshot', symbol, date, mode],
    queryFn: async () => {
      const params = [];
      if (date) params.push(`date_param=${encodeURIComponent(date)}`);
      if (mode) params.push(`mode=${encodeURIComponent(mode)}`);
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
  return useBreadthHistoryWithMode(symbol, days, includeMcClellan, enabled, 'sma200');
}

export function useBreadthHistoryWithMode(symbol, days = 30, includeMcClellan = false, enabled = true, mode = 'sma200') {
  return useQuery({
    queryKey: ['breadth-history', symbol, days, includeMcClellan, mode],
    queryFn: async () => {
      const url = `${API_BASE}/indices/${encodeURIComponent(symbol)}/breadth/history?days=${days}&include_mcclellan=${includeMcClellan}&mode=${encodeURIComponent(mode)}`;
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

const marketBreadthHooks = {
  useBreadthSnapshot,
  useBreadthHistory,
  useBreadthSnapshotWithMode,
  useBreadthHistoryWithMode,
};

export default marketBreadthHooks;
import { useQuery } from '@tanstack/react-query';
import API_BASE from '../config';

export function useCorrelationMatrix(symbols, period = '1y', enabled = true) {
  const symList = Array.isArray(symbols) ? symbols : (typeof symbols === 'string' ? symbols.split(',').map(s => s.trim()).filter(Boolean) : []);
  const queryKey = ['correlation-matrix', symList.sort().join(','), period];
  return useQuery({
    queryKey,
    queryFn: async () => {
      if (!symList.length) return null;
      const joined = symList.join(',');
      const url = `${API_BASE}/indices/correlation-matrix?symbols=${encodeURIComponent(joined)}&period=${encodeURIComponent(period)}`;
      const resp = await fetch(url);
      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        throw new Error(errJson.detail || `Request failed (${resp.status})`);
      }
      return resp.json();
    },
    enabled: enabled && symList.length > 1,
    staleTime: 30 * 60 * 1000, // 30 minutes
    retry: 1,
  });
}

export default useCorrelationMatrix;
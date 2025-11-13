import { useQuery } from '@tanstack/react-query';
import API_BASE from '../config';

async function fetchJson(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

/**
 * Simple wrapper to fetch and cache API responses by URL using React Query.
 * Key is ['api', url] so identical URLs dedupe automatically.
 */
export function useApiQuery(pathOrUrl, options = {}) {
  const url = pathOrUrl && String(pathOrUrl).startsWith('http') ? pathOrUrl : `${API_BASE}${pathOrUrl}`;
  return useQuery(['api', url], () => fetchJson(url), {
    staleTime: 60 * 1000,
    refetchOnWindowFocus: false,
    ...options,
  });
}

export default useApiQuery;

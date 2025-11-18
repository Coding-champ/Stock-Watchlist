import { useApiQuery } from './useApiQuery';

/**
 * Hook to fetch chart data with technical indicators for an index
 */
export function useIndexChart(tickerSymbol, period = '1y', interval = '1d', indicators = []) {
  const hasTicker = !!tickerSymbol;
  const indicatorsStr = indicators && indicators.length > 0 ? indicators.join(',') : '';
  const base = hasTicker ? `/indices/${tickerSymbol}/chart?period=${period}&interval=${interval}` : '';
  const url = indicatorsStr ? `${base}&indicators=${indicatorsStr}` : base;

  const query = useApiQuery(url, {
    enabled: hasTicker,
    staleTime: 5 * 60 * 1000,
    refetchInterval: false,
    retry: 2,
  });

  // Derive friendly status classification
  let friendlyError = null;
  if (query.error) {
    const msg = String(query.error.message || 'Unbekannter Fehler');
    if (/404/.test(msg)) {
      friendlyError = 'Keine Daten für diesen Zeitraum.';
    } else if (/Network|Failed to fetch/i.test(msg)) {
      friendlyError = 'Netzwerkproblem. Bitte Verbindung prüfen.';
    } else {
      friendlyError = 'Fehler beim Laden der Chartdaten.';
    }
  }

  return { ...query, friendlyError };
}

export default useIndexChart;

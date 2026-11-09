export const DISPLAY_LOCALE = 'de-DE';
export const DISPLAY_DECIMAL_PLACES = 2;

function getDecimalPlaces(decimals) {
  return Math.min(DISPLAY_DECIMAL_PLACES, Math.max(0, decimals));
}

/**
 * Zentrale Regeln für Zahlen im Frontend:
 * - Ganze Zahlen: Monate, Zähler, Mengen, Tage und Jahre.
 * - Dezimalzahlen: Messwerte, Quoten und Prozentwerte mit maximal zwei Stellen.
 * - Abgekürzte Zahlen: große Geld- und Mengenwerte ab 1.000 (Tsd., Mio., Mrd., Bio.).
 * - Normale Zahlen verwenden deutsche Schreibweise (12.345,67); Abkürzungen
 *   verwenden keinen Tausendertrenner (12,35 Mrd.).
 *
 * Format a number for normal UI output.
 */
export function formatDisplayNumber(value, decimals = DISPLAY_DECIMAL_PLACES) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';

  return new Intl.NumberFormat(DISPLAY_LOCALE, {
    minimumFractionDigits: getDecimalPlaces(decimals),
    maximumFractionDigits: getDecimalPlaces(decimals)
  }).format(Number(value));
}

/**
 * Format compact values without thousands separators (e.g. 12 Mrd.).
 */
export function formatCompactDisplayNumber(value, decimals = DISPLAY_DECIMAL_PLACES) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';

  const places = getDecimalPlaces(decimals);
  const number = Number(value);
  const compactValue = number >= 1e12
    ? `${number / 1e12} Bio.`
    : number >= 1e9
      ? `${number / 1e9} Mrd.`
    : number >= 1e6
      ? `${number / 1e6} Mio.`
      : number >= 1e3
        ? `${number / 1e3} Tsd.`
        : String(number);

  if (number >= 1e3) {
    const [integer, fraction] = compactValue.split(' ');
    return `${Number(integer).toLocaleString(DISPLAY_LOCALE, {
      minimumFractionDigits: places,
      maximumFractionDigits: places,
      useGrouping: false
    })} ${fraction}`;
  }

  return formatDisplayNumber(number, places);
}

/**
 * Format a named metric according to the central display rules above.
 * Ratio fields such as margins and ROE are returned as percentages.
 */
export function formatMetricValue(key, value) {
  if (typeof value === 'boolean') return value ? 'Ja' : 'Nein';
  if (typeof value !== 'number' || !Number.isFinite(value)) return String(value);

  const normalizedKey = key.toLowerCase();
  if (/(month|months|count|number|observations|quantity|days|years)$/.test(normalizedKey)) {
    return formatDisplayNumber(value, 0);
  }
  if (/(margin|return_on_equity|roe)$/.test(normalizedKey)) {
    return `${formatDisplayNumber(value * 100)} %`;
  }
  if (/(revenue|earnings|cashflow|cash_flow|income|assets|equity|debt|market_cap|volume)$/.test(normalizedKey)) {
    return formatCompactDisplayNumber(value);
  }
  return formatDisplayNumber(value);
}

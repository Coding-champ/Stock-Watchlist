import { formatPrice } from './currencyUtils';

/**
 * Format a timestamp to German locale date and time
 * @param {number|Date|string} timestamp - The timestamp to format
 * @returns {string} Formatted date and time string
 */
export function formatTime(timestamp) {
  if (!timestamp) return '-';

  // Handle numeric epoch seconds
  if (typeof timestamp === 'number') {
    // assume seconds
    const dateNum = new Date(timestamp * 1000);
    if (!isNaN(dateNum.getTime())) {
      return `${dateNum.toLocaleDateString('de-DE')} · ${dateNum.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
    }
  }

  // Handle Date objects
  if (timestamp instanceof Date) {
    const d = timestamp;
    if (Number.isNaN(d.getTime())) return '-';
    return `${d.toLocaleDateString('de-DE')} · ${d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
  }

  // Handle strings
  if (typeof timestamp === 'string') {
    const trimmed = timestamp.trim();
    // Date-only format YYYY-MM-DD -> show only date (no 00:00)
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      try {
        const d = new Date(trimmed + 'T00:00:00');
        if (!isNaN(d.getTime())) return d.toLocaleDateString('de-DE');
      } catch (e) {
        return trimmed;
      }
    }

    // Pure epoch digits in string
    if (/^\d+$/.test(trimmed)) {
      try {
        const sec = parseInt(trimmed, 10);
        const d = new Date(sec * 1000);
        if (!isNaN(d.getTime())) return `${d.toLocaleDateString('de-DE')} · ${d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
      } catch (e) {
        // fallthrough
      }
    }

    // Fallback: let Date parse ISO strings
    const parsed = new Date(trimmed);
    if (!isNaN(parsed.getTime())) {
      return `${parsed.toLocaleDateString('de-DE')} · ${parsed.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
    }

    return trimmed;
  }

  return '-';
}

/**
 * Format a currency value with sign (+ or -)
 * @param {number} value - The currency value
 * @param {Object} stockLike - Stock object for currency detection
 * @returns {string} Formatted signed currency string
 */
export function formatSignedCurrency(value, stockLike) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '-';
  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  // Use formatPrice for localized formatting; strip sign from formatted and prepend our sign
  const formatted = formatPrice(Math.abs(value), stockLike);
  return `${sign}${formatted}`;
}

/**
 * Format a percentage value with sign
 * @param {number} value - The percentage value
 * @returns {string} Formatted percentage string
 */
export function formatPercent(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '-';
  }

  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  const formatted = new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(Math.abs(value));

  return `${sign}${formatted} %`;
}

/**
 * Format watchlist duration in days
 * @param {string|Date} createdAt - The creation timestamp
 * @returns {string|null} Formatted duration string or null
 */
export function formatWatchlistDuration(createdAt) {
  if (!createdAt) {
    return null;
  }

  const created = new Date(createdAt);
  if (Number.isNaN(created.getTime())) {
    return null;
  }

  const diffMs = Date.now() - created.getTime();
  const diffDays = Math.max(0, Math.floor(diffMs / (1000 * 60 * 60 * 24)));

  if (diffDays === 0) {
    return 'Heute hinzugefügt';
  }

  return `${diffDays} ${diffDays === 1 ? 'Tag' : 'Tage'}`;
}

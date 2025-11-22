/**
 * Get initials from stock name or ticker symbol
 * @param {Object} stock - Stock object with name or ticker_symbol
 * @returns {string} Two-letter initials in uppercase
 */
export function getInitials(stock) {
  const source = stock.name || stock.ticker_symbol || '';
  const parts = source.trim().split(/\s+/);
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }

  return (parts[0][0] + parts[1][0]).toUpperCase();
}

// Centralized metric label utility
export function metricLabel(key) {
  switch (key) {
    case 'market_cap':
      return 'Marktkapitalisierung';
    case 'pe_ratio':
      return 'KGV (P/E)';
    case 'price_to_sales':
      return 'P/S';
    case 'ev_ebit':
      return 'EV/EBIT';
    case 'price_to_book':
      return 'P/B';
    default:
      // Replace underscores with spaces and capitalize first letter
      const human = String(key).replace(/_/g, ' ');
      return human.charAt(0).toUpperCase() + human.slice(1);
  }
}

export default metricLabel;

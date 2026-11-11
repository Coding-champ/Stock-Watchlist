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
    case 'revenue':
      return 'Umsatz';
    case 'earnings':
      return 'Nettogewinn';
    case 'operating_income':
      return 'Betriebsergebnis (EBIT)';
    case 'gross_profit':
      return 'Bruttogewinn';
    case 'ebitda':
      return 'EBITDA';
    case 'total_assets':
      return 'Bilanzsumme';
    case 'total_liabilities':
      return 'Verbindlichkeiten';
    case 'shareholders_equity':
      return 'Eigenkapital';
    case 'operating_cashflow':
      return 'Operativer Cashflow';
    case 'free_cashflow':
      return 'Free Cashflow';
    default:
      // Replace underscores with spaces and capitalize first letter
      const human = String(key).replace(/_/g, ' ');
      return human.charAt(0).toUpperCase() + human.slice(1);
  }
}

export default metricLabel;

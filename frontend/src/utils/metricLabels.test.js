import metricLabel from './metricLabels';

describe('metricLabel utility', () => {
  test('returns german label for market_cap', () => {
    expect(metricLabel('market_cap')).toBe('Marktkapitalisierung');
  });

  test('returns KGV (P/E) for pe_ratio', () => {
    expect(metricLabel('pe_ratio')).toBe('KGV (P/E)');
  });

  test('returns P/S for price_to_sales', () => {
    expect(metricLabel('price_to_sales')).toBe('P/S');
  });

  test('returns EV/EBIT for ev_ebit', () => {
    expect(metricLabel('ev_ebit')).toBe('EV/EBIT');
  });

  test('returns P/B for price_to_book', () => {
    expect(metricLabel('price_to_book')).toBe('P/B');
  });

  test('humanizes unknown keys by replacing underscores and capitalizing', () => {
    expect(metricLabel('net_income_margin')).toBe('Net income margin');
    expect(metricLabel('total_assets')).toBe('Total assets');
  });

  test('handles non-string input by stringifying and humanizing', () => {
    // null -> 'Null'
    expect(metricLabel(null)).toBe('Null');
    // number -> '123'
    expect(metricLabel(123)).toBe('123');
  });
});

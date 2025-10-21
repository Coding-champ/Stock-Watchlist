// Map yfinance 'quote_type' values to German labels
const QUOTE_TYPE_MAP = {
  EQUITY: 'Aktie',
  STOCK: 'Aktie',
  ETF: 'ETF',
  MUTUALFUND: 'Fond',
  FUND: 'Fond',
  CRYPTO: 'Krypto',
  CRYPTOCURRENCY: 'Krypto',
  OPTION: 'Option',
  FUTURE: 'Future',
  CURRENCY: 'Währung',
  INDEX: 'Index'
};

export function getLocalizedQuoteType(raw) {
  if (!raw && raw !== 0) return 'Aktie'; // default

  const value = String(raw).trim().toUpperCase();
  if (!value) return 'Aktie';

  return QUOTE_TYPE_MAP[value] || 'Instrument';
}

export default getLocalizedQuoteType;

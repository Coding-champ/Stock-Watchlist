/**
 * Utility-Funktionen für Währungen und Formatierung
 */

/**
 * Format a number with specified decimals
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @param {string} suffix - Optional suffix to append (e.g., '%')
 * @returns {string} Formatted number or '-' if value is null/undefined
 */
export const formatNumber = (value, decimals = 2, suffix = '') => {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') {
    return value.toFixed(decimals) + suffix;
  }
  return '-';
};

// Währungszuordnung nach Land/Region (symbol)
const CURRENCY_MAP = {
  // Nordamerika
  'USA': '$',
  'United States': '$',
  'US': '$',
  'Kanada': 'C$',
  'Canada': 'C$',
  
  // Europa (Euro)
  'Deutschland': '€',
  'Germany': '€',
  'Österreich': '€',
  'Austria': '€',
  'Frankreich': '€',
  'France': '€',
  'Italien': '€',
  'Italy': '€',
  'Spanien': '€',
  'Spain': '€',
  'Niederlande': '€',
  'Netherlands': '€',
  'Belgien': '€',
  'Belgium': '€',
  'Portugal': '€',
  'Griechenland': '€',
  'Greece': '€',
  'Irland': '€',
  'Ireland': '€',
  'Finnland': '€',
  'Finland': '€',
  
  // Andere Europa
  'Schweiz': 'CHF',
  'Switzerland': 'CHF',
  'Großbritannien': '£',
  'United Kingdom': '£',
  'UK': '£',
  'England': '£',
  'Norwegen': 'kr',
  'Norway': 'kr',
  'Schweden': 'kr',
  'Sweden': 'kr',
  'Dänemark': 'kr',
  'Denmark': 'kr',
  
  // Asien
  'Japan': '¥',
  'China': '¥',
  'Indien': '₹',
  'India': '₹',
  'Südkorea': '₩',
  'South Korea': '₩',
  
  // Ozeanien
  'Australien': 'A$',
  'Australia': 'A$',
  'Neuseeland': 'NZ$',
  'New Zealand': 'NZ$',
};

// ISO currency codes mapping for key countries / exchanges
const CURRENCY_CODE_MAP = {
  'Germany': 'EUR', 'Deutschland': 'EUR',
  'France': 'EUR', 'Frankreich': 'EUR',
  'Italy': 'EUR', 'Italien': 'EUR',
  'Spain': 'EUR', 'Spanien': 'EUR',
  'Netherlands': 'EUR', 'Niederlande': 'EUR',
  'Belgium': 'EUR', 'Belgien': 'EUR',
  'Portugal': 'EUR',
  'Greece': 'EUR', 'Griechenland': 'EUR',
  'Ireland': 'EUR', 'Irland': 'EUR',
  'Finland': 'EUR', 'Finnland': 'EUR',
  'Austria': 'EUR', 'Österreich': 'EUR',
  'United States': 'USD', 'USA': 'USD', 'US': 'USD',
  'Canada': 'CAD', 'Kanada': 'CAD',
  'United Kingdom': 'GBP', 'UK': 'GBP', 'Großbritannien': 'GBP',
  'Switzerland': 'CHF', 'Schweiz': 'CHF',
  'Japan': 'JPY',
  'China': 'CNY',
  'India': 'INR', 'Indien': 'INR',
  'South Korea': 'KRW', 'Südkorea': 'KRW',
  'Australia': 'AUD', 'Australien': 'AUD',
  'New Zealand': 'NZD', 'Neuseeland': 'NZD',
  'Hong Kong': 'HKD'
};

// Börsen-Suffix zu Währung Mapping
const EXCHANGE_SUFFIX_MAP = {
  '.DE': 'EUR',    // Xetra (Frankfurt)
  '.F': 'EUR',     // Frankfurt
  '.DU': 'EUR',    // Düsseldorf
  '.MU': 'EUR',    // München
  '.BE': 'EUR',    // Berlin
  '.HM': 'EUR',    // Hamburg
  '.HA': 'EUR',    // Hannover
  '.STU': 'EUR',   // Stuttgart
  '.PA': 'EUR',    // Paris
  '.MI': 'EUR',    // Mailand
  '.AS': 'EUR',    // Amsterdam
  '.BR': 'EUR',    // Brüssel
  '.LS': 'EUR',    // Lissabon
  '.MC': 'EUR',    // Madrid
  '.L': 'GBP',     // London
  '.SW': 'CHF',    // Schweiz (SIX)
  '.VX': 'CHF',    // Schweiz (Virt-X)
  '.TO': 'CAD',    // Toronto
  '.V': 'CAD',     // TSX Venture
  '.AX': 'AUD',    // Australian Securities Exchange
  '.NZ': 'NZD',    // New Zealand Stock Exchange
  '.T': 'JPY',     // Tokyo
  '.HK': 'HKD',    // Hong Kong
  '.SS': 'CNY',    // Shanghai
  '.SZ': 'CNY',    // Shenzhen
  '.KS': 'KRW',    // Korea Stock Exchange
  '.BO': 'INR',    // Bombay Stock Exchange
  '.NS': 'INR',    // National Stock Exchange of India
  '.OL': 'NOK',    // Oslo
  '.ST': 'SEK',    // Stockholm
  '.CO': 'DKK',    // Copenhagen
};

// Map symbol fallback for backward compatibility (used by getCurrencyForStock)
const EXCHANGE_SUFFIX_SYMBOL_MAP = {
  '.DE': '€', '.F': '€', '.DU': '€', '.MU': '€', '.BE': '€', '.HM': '€', '.HA': '€', '.STU': '€', '.PA': '€', '.MI': '€', '.AS': '€', '.BR': '€', '.LS': '€', '.MC': '€',
  '.L': '£', '.SW': 'CHF', '.VX': 'CHF', '.TO': 'C$', '.V': 'C$', '.AX': 'A$', '.NZ': 'NZ$', '.T': '¥', '.HK': 'HK$', '.SS': '¥', '.SZ': '¥', '.KS': '₩', '.BO': '₹', '.NS': '₹', '.OL': 'kr', '.ST': 'kr', '.CO': 'kr'
};

/**
 * Ermittelt die Währung für eine Aktie basierend auf Land und Ticker-Symbol
 * @param {Object} stock - Das Stock-Objekt mit country und ticker_symbol
 * @returns {string} Das Währungssymbol (z.B. '$', '€', '£')
 */
export function getCurrencyForStock(stock) {
  if (!stock) return '$'; // Fallback zu USD
  
  // 1. Prüfe nach Land
  if (stock.country && CURRENCY_MAP[stock.country]) {
    return CURRENCY_MAP[stock.country];
  }
  
  // 2. Prüfe nach Ticker-Symbol Suffix (Börsen-Kürzel)
  if (stock.ticker_symbol) {
    const ticker = stock.ticker_symbol.toUpperCase();
    
    // Suche nach bekannten Börsen-Suffixen
    for (const suffix of Object.keys(EXCHANGE_SUFFIX_MAP)) {
        if (ticker.endsWith(suffix)) {
          // return symbol mapping for backward compatibility
          return EXCHANGE_SUFFIX_SYMBOL_MAP[suffix] || CURRENCY_MAP[stock.country] || '$';
        }
      }
  }
  
  // 3. Fallback zu USD (Standard für US-Aktien und unbekannte)
  return '$';
}

/**
 * Determine ISO currency code for stock (e.g., 'EUR', 'USD')
 * @param {Object} stock
 * @returns {string} ISO currency (defaults to 'USD')
 */
export function getCurrencyCodeForStock(stock) {
  if (!stock) return 'USD';

  // 1. country mapping
  if (stock.country && CURRENCY_CODE_MAP[stock.country]) return CURRENCY_CODE_MAP[stock.country];

  // 2. explicit currency code in stock object (common in extended data)
  if (stock.currency && typeof stock.currency === 'string' && /^[A-Za-z]{3}$/.test(stock.currency)) {
    return stock.currency.toUpperCase();
  }

  // 3. ticker suffix mapping
  if (stock.ticker_symbol) {
    const ticker = stock.ticker_symbol.toUpperCase();
    for (const [suffix, iso] of Object.entries(EXCHANGE_SUFFIX_MAP)) {
      if (ticker.endsWith(suffix)) return iso;
    }
  }

  // 4. exchange field heuristic
  if (stock.exchange && typeof stock.exchange === 'string') {
    const e = stock.exchange.toUpperCase();
    if (e.includes('DE') || e === 'XETRA' || e === 'FRA') return 'EUR';
    if (['NASDAQ','NMS','NYSE','AMEX','ARCA'].includes(e)) return 'USD';
  }

  return 'USD';
}

/**
 * Formatiert einen Preis mit der richtigen Währung
 * @param {number} value - Der Preis
 * @param {Object} stock - Das Stock-Objekt
 * @param {number} decimals - Anzahl Dezimalstellen (Standard: 2)
 * @returns {string} Formatierter Preis mit Währung (z.B. "$150.00", "€45.50")
 */
export function formatPrice(value, stock, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) return '-';

  // Determine ISO currency code and use Intl for German localization
  const iso = getCurrencyCodeForStock(stock);
  try {
    const nf = new Intl.NumberFormat('de-DE', { style: 'currency', currency: iso, minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    return nf.format(Number(value));
  } catch (e) {
    // Fallback: symbol based formatting
    const symbol = getCurrencyForStock(stock) || '$';
    const formattedValue = Number(value).toFixed(decimals);
    if (symbol === '€' || symbol === 'CHF' || symbol === 'kr') return `${formattedValue} ${symbol}`;
    return `${symbol}${formattedValue}`;
  }
}

/**
 * Gibt das Alarm-Typen-Array mit der richtigen Währung zurück
 * @param {Object} stock - Das Stock-Objekt
 * @returns {Array} Array von Alarm-Typen mit Labels und Einheiten
 */
export function getAlertTypesForStock(stock) {
  return [
    { value: 'price', label: 'Preis', unit: getCurrencyForStock(stock) },
    { value: 'pe_ratio', label: 'KGV (P/E Ratio)', unit: '' },
    { value: 'rsi', label: 'RSI', unit: '' },
    { value: 'volatility', label: 'Volatilität', unit: '%' },
    { value: 'price_change_percent', label: 'Prozentuale Änderung', unit: '%' },
    { value: 'ma_cross', label: 'MA Cross (50/200)', unit: '' },
    { value: 'volume_spike', label: 'Volumen-Spike', unit: 'x' }
  ];
}

/**
 * Gibt eine menschenlesbare Bezeichnung für einen Alarm-Typ zurück
 * @param {string} alertType - Der Typ des Alarms
 * @returns {string} Die lesbare Bezeichnung
 */
export function getAlertTypeLabel(alertType) {
  const labels = {
    'price': 'Preis',
    'pe_ratio': 'KGV',
    'rsi': 'RSI',
    'volatility': 'Volatilität',
    'price_change_percent': 'Preis-Änderung %',
    'ma_cross': 'MA Cross',
    'volume_spike': 'Volumen-Spike'
  };
  return labels[alertType] || alertType;
}

/**
 * Gibt eine menschenlesbare Bezeichnung für eine Bedingung zurück
 * @param {string} condition - Die Bedingung
 * @returns {string} Die lesbare Bezeichnung
 */
export function getConditionLabel(condition) {
  const labels = {
    'above': 'über',
    'below': 'unter',
    'equals': 'gleich',
    'cross_above': 'kreuzt nach oben',
    'cross_below': 'kreuzt nach unten',
    'before': 'vor'
  };
  return labels[condition] || condition;
}

/**
 * Gibt die Einheit für einen bestimmten Alarm-Typ zurück
 * @param {string} alertType - Der Typ des Alarms ('price', 'pe_ratio', etc.)
 * @param {Object} stock - Das Stock-Objekt
 * @returns {string} Die Einheit (z.B. '$', '%', '')
 */
export function getUnitForAlertType(alertType, stock) {
  switch (alertType) {
    case 'price':
      return getCurrencyForStock(stock);
    case 'volatility':
    case 'price_change_percent':
      return '%';
    case 'volume_spike':
      return 'x';
    case 'earnings':
      return 'Tage';
    case 'pe_ratio':
    case 'rsi':
    case 'ma_cross':
    case 'composite':
    default:
      return '';
  }
}

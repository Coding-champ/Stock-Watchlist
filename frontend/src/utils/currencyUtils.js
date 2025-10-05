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

// Währungszuordnung nach Land/Region
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

// Börsen-Suffix zu Währung Mapping
const EXCHANGE_SUFFIX_MAP = {
  '.DE': '€',    // Xetra (Frankfurt)
  '.F': '€',     // Frankfurt
  '.DU': '€',    // Düsseldorf
  '.MU': '€',    // München
  '.BE': '€',    // Berlin
  '.HM': '€',    // Hamburg
  '.HA': '€',    // Hannover
  '.STU': '€',   // Stuttgart
  '.PA': '€',    // Paris
  '.MI': '€',    // Mailand
  '.AS': '€',    // Amsterdam
  '.BR': '€',    // Brüssel
  '.LS': '€',    // Lissabon
  '.MC': '€',    // Madrid
  '.L': '£',     // London
  '.SW': 'CHF',  // Schweiz (SIX)
  '.VX': 'CHF',  // Schweiz (Virt-X)
  '.TO': 'C$',   // Toronto
  '.V': 'C$',    // TSX Venture
  '.AX': 'A$',   // Australian Securities Exchange
  '.NZ': 'NZ$',  // New Zealand Stock Exchange
  '.T': '¥',     // Tokyo
  '.HK': 'HK$',  // Hong Kong
  '.SS': '¥',    // Shanghai
  '.SZ': '¥',    // Shenzhen
  '.KS': '₩',    // Korea Stock Exchange
  '.BO': '₹',    // Bombay Stock Exchange
  '.NS': '₹',    // National Stock Exchange of India
  '.OL': 'kr',   // Oslo
  '.ST': 'kr',   // Stockholm
  '.CO': 'kr',   // Copenhagen
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
    for (const [suffix, currency] of Object.entries(EXCHANGE_SUFFIX_MAP)) {
      if (ticker.endsWith(suffix)) {
        return currency;
      }
    }
  }
  
  // 3. Fallback zu USD (Standard für US-Aktien und unbekannte)
  return '$';
}

/**
 * Formatiert einen Preis mit der richtigen Währung
 * @param {number} value - Der Preis
 * @param {Object} stock - Das Stock-Objekt
 * @param {number} decimals - Anzahl Dezimalstellen (Standard: 2)
 * @returns {string} Formatierter Preis mit Währung (z.B. "$150.00", "€45.50")
 */
export function formatPrice(value, stock, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) {
    return '-';
  }
  
  const currency = getCurrencyForStock(stock);
  const formattedValue = Number(value).toFixed(decimals);
  
  // Bei Euro und anderen europäischen Währungen: Währung hinten
  if (currency === '€' || currency === 'kr' || currency === 'CHF') {
    return `${formattedValue} ${currency}`;
  }
  
  // Bei Dollar, Pfund, Yen etc.: Währung vorne
  return `${currency}${formattedValue}`;
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

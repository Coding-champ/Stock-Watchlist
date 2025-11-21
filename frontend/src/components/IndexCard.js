import React from 'react';
import './IndexCard.css';

function IndexCard({ index, onClick }) {
  const latestPrice = index.latest_price;
  
  // Calculate change (if we have enough data)
  const change = latestPrice ? calculateChange(latestPrice) : null;
  const changePercent = change ? change.percent : null;
  const isPositive = changePercent && changePercent > 0;
  const isNegative = changePercent && changePercent < 0;

  return (
    <div className="index-card" onClick={onClick}>
      <div className="index-card-header">
        <div className="index-name">{index.name}</div>
        <div className="index-symbol">{index.ticker_symbol}</div>
      </div>
      
      <div className="index-card-body">
        {latestPrice ? (
          <>
            <div className="index-price">
              {formatPrice(latestPrice.close, latestPrice.currency, index.ticker_symbol)}
            </div>
            {changePercent !== null && (
              <div className={`index-change ${isPositive ? 'positive' : isNegative ? 'negative' : ''}`}>
                {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
              </div>
            )}
            <div className="index-date">
              {new Date(latestPrice.date).toLocaleDateString('de-DE')}
            </div>
          </>
        ) : (
          <div className="no-data">Keine Kursdaten</div>
        )}
      </div>

      <div className="index-card-footer">
        <div className="index-type">{index.index_type || 'Index'}</div>
      </div>
    </div>
  );
}

// Helper function to calculate change (simplified - assumes we have open/close)
function calculateChange(priceData) {
  // For daily change, compare close to open
  if (priceData.open && priceData.close) {
    const change = priceData.close - priceData.open;
    const percent = (change / priceData.open) * 100;
    return { absolute: change, percent };
  }
  return null;
}

function formatPrice(price, currency = 'USD', tickerSymbol = '') {
  if (price == null) return '-';
  const formatted = new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price);
  const t = (tickerSymbol || '').toUpperCase();
  if (t.startsWith('^')) {
    return `${formatted} Punkte`;
  }
  return `${formatted} ${currency || ''}`.trim();
}

export default IndexCard;

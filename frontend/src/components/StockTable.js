import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function StockTable({ stocks, watchlists, currentWatchlistId, onStockClick, onDeleteStock, onMoveStock }) {
  const [stocksWithData, setStocksWithData] = useState([]);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const loadStockData = useCallback(async () => {
    const stocksData = await Promise.all(
      stocks.map(async (stock) => {
        try {
          const response = await fetch(`${API_BASE}/stock-data/?stock_id=${stock.id}&limit=1`);
          const data = await response.json();
          return {
            ...stock,
            latestData: data.length > 0 ? data[0] : {}
          };
        } catch (error) {
          console.error(`Error loading data for stock ${stock.id}:`, error);
          return { ...stock, latestData: {} };
        }
      })
    );
    setStocksWithData(stocksData);
  }, [stocks]);

  useEffect(() => {
    loadStockData();
  }, [loadStockData]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortedStocks = () => {
    if (!sortConfig.key) return stocksWithData;

    const sorted = [...stocksWithData].sort((a, b) => {
      let aValue, bValue;

      if (sortConfig.key === 'current_price' || sortConfig.key === 'pe_ratio' || 
          sortConfig.key === 'rsi' || sortConfig.key === 'volatility') {
        aValue = a.latestData[sortConfig.key] || 0;
        bValue = b.latestData[sortConfig.key] || 0;
      } else {
        aValue = a[sortConfig.key] || '';
        bValue = b[sortConfig.key] || '';
      }

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  };

  const handleMoveClick = (stockId) => {
    const otherWatchlists = watchlists.filter(wl => wl.id !== currentWatchlistId);
    
    if (otherWatchlists.length === 0) {
      alert('Keine anderen Watchlists verfügbar');
      return;
    }

    const targetWatchlistId = prompt(
      `Verschieben zu:\n${otherWatchlists.map((wl, i) => `${i + 1}. ${wl.name}`).join('\n')}\n\nGeben Sie die Nummer ein:`
    );

    if (targetWatchlistId) {
      const index = parseInt(targetWatchlistId) - 1;
      if (index >= 0 && index < otherWatchlists.length) {
        onMoveStock(stockId, otherWatchlists[index].id);
      }
    }
  };

  if (stocks.length === 0) {
    return (
      <div className="empty-state">
        Keine Aktien in dieser Watchlist. Fügen Sie eine Aktie hinzu.
      </div>
    );
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th onClick={() => handleSort('isin')}>ISIN</th>
            <th onClick={() => handleSort('ticker_symbol')}>Ticker</th>
            <th onClick={() => handleSort('name')}>Name</th>
            <th onClick={() => handleSort('current_price')}>Aktueller Preis</th>
            <th onClick={() => handleSort('country')}>Land</th>
            <th onClick={() => handleSort('industry')}>Branche</th>
            <th onClick={() => handleSort('sector')}>Sektor</th>
            <th onClick={() => handleSort('pe_ratio')}>KGV</th>
            <th onClick={() => handleSort('rsi')}>RSI</th>
            <th onClick={() => handleSort('volatility')}>Volatilität</th>
            <th>Aktionen</th>
          </tr>
        </thead>
        <tbody>
          {getSortedStocks().map((stock) => (
            <tr key={stock.id} className="stock-row" onClick={() => onStockClick(stock)}>
              <td>{stock.isin}</td>
              <td>{stock.ticker_symbol}</td>
              <td>{stock.name}</td>
              <td>
                {stock.latestData.current_price
                  ? stock.latestData.current_price.toFixed(2) + ' €'
                  : '-'}
              </td>
              <td>{stock.country || '-'}</td>
              <td>{stock.industry || '-'}</td>
              <td>{stock.sector || '-'}</td>
              <td>
                {stock.latestData.pe_ratio ? stock.latestData.pe_ratio.toFixed(2) : '-'}
              </td>
              <td>{stock.latestData.rsi ? stock.latestData.rsi.toFixed(2) : '-'}</td>
              <td>
                {stock.latestData.volatility
                  ? stock.latestData.volatility.toFixed(2) + '%'
                  : '-'}
              </td>
              <td onClick={(e) => e.stopPropagation()}>
                <div className="actions">
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleMoveClick(stock.id)}
                  >
                    Verschieben
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={() => onDeleteStock(stock.id)}
                  >
                    Löschen
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default StockTable;

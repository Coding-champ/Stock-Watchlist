import React, { useState, useEffect, useCallback } from 'react';
import StockTable from './StockTable';
import StockModal from './StockModal';
import StockDetailModal from './StockDetailModal';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function StocksSection({ watchlist, watchlists }) {
  const [stocks, setStocks] = useState([]);
  const [filteredStocks, setFilteredStocks] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadStocks = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/stocks/?watchlist_id=${watchlist.id}`);
      const data = await response.json();
      setStocks(data);
    } catch (error) {
      console.error('Error loading stocks:', error);
      alert('Fehler beim Laden der Aktien');
    } finally {
      setLoading(false);
    }
  }, [watchlist.id]);

  const filterStocks = useCallback(() => {
    if (!searchTerm) {
      setFilteredStocks(stocks);
      return;
    }

    const term = searchTerm.toLowerCase();
    const filtered = stocks.filter(stock =>
      stock.name.toLowerCase().includes(term) ||
      stock.isin.toLowerCase().includes(term) ||
      stock.ticker_symbol.toLowerCase().includes(term)
    );
    setFilteredStocks(filtered);
  }, [stocks, searchTerm]);

  useEffect(() => {
    if (watchlist) {
      loadStocks();
    }
  }, [watchlist, loadStocks]);

  useEffect(() => {
    filterStocks();
  }, [filterStocks]);

  const handleAddStock = () => {
    setShowAddModal(true);
  };

  const handleStockAdded = () => {
    setShowAddModal(false);
    loadStocks();
  };

  const handleStockClick = (stock) => {
    setSelectedStock(stock);
  };

  const handleDeleteStock = async (stockId) => {
    if (!window.confirm('Möchten Sie diese Aktie wirklich löschen?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/stocks/${stockId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        loadStocks();
      } else {
        alert('Fehler beim Löschen der Aktie');
      }
    } catch (error) {
      console.error('Error deleting stock:', error);
      alert('Fehler beim Löschen der Aktie');
    }
  };

  const handleMoveStock = async (stockId, targetWatchlistId) => {
    try {
      const response = await fetch(`${API_BASE}/stocks/${stockId}/move`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_watchlist_id: targetWatchlistId })
      });

      if (response.ok) {
        loadStocks();
      } else {
        alert('Fehler beim Verschieben der Aktie');
      }
    } catch (error) {
      console.error('Error moving stock:', error);
      alert('Fehler beim Verschieben der Aktie');
    }
  };

  return (
    <div className="section">
      <h2>Aktien in {watchlist.name}</h2>
      <button className="btn" onClick={handleAddStock}>
        + Aktie hinzufügen
      </button>

      <input
        type="text"
        className="search-box"
        placeholder="Suche nach Name, ISIN oder Ticker..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
        </div>
      ) : (
        <StockTable
          stocks={filteredStocks}
          watchlists={watchlists}
          currentWatchlistId={watchlist.id}
          onStockClick={handleStockClick}
          onDeleteStock={handleDeleteStock}
          onMoveStock={handleMoveStock}
        />
      )}

      {showAddModal && (
        <StockModal
          watchlistId={watchlist.id}
          onClose={() => setShowAddModal(false)}
          onStockAdded={handleStockAdded}
        />
      )}

      {selectedStock && (
        <StockDetailModal
          stock={selectedStock}
          onClose={() => setSelectedStock(null)}
        />
      )}
    </div>
  );
}

export default StocksSection;

import React, { useState, useEffect } from 'react';
import './App.css';
import WatchlistSection from './components/WatchlistSection';
import StocksSection from './components/StocksSection';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function App() {
  const [watchlists, setWatchlists] = useState([]);
  const [currentWatchlist, setCurrentWatchlist] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadWatchlists();
  }, []);

  const loadWatchlists = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/watchlists/`);
      const data = await response.json();
      setWatchlists(data);
    } catch (error) {
      console.error('Error loading watchlists:', error);
      alert('Fehler beim Laden der Watchlists');
    } finally {
      setLoading(false);
    }
  };

  const handleWatchlistSelect = (watchlist) => {
    setCurrentWatchlist(watchlist);
  };

  return (
    <div className="container">
      <h1>📊 Stock Watchlist</h1>
      
      {loading && (
        <div className="loading">
          <div className="spinner"></div>
        </div>
      )}

      <WatchlistSection
        watchlists={watchlists}
        currentWatchlist={currentWatchlist}
        onWatchlistSelect={handleWatchlistSelect}
        onWatchlistsChange={loadWatchlists}
      />

      {currentWatchlist && (
        <StocksSection
          watchlist={currentWatchlist}
          watchlists={watchlists}
        />
      )}
    </div>
  );
}

export default App;

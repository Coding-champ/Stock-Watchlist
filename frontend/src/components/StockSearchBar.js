import React, { useState, useEffect, useRef } from 'react';
import API_BASE from '../config';
import './StockSearchBar.css';

/**
 * StockSearchBar Component
 * 
 * Provides a search interface for finding stocks in the database
 * by name, ticker symbol, ISIN, or WKN.
 * 
 * Features:
 * - Real-time search with debouncing
 * - Dropdown results list
 * - Keyboard navigation
 * - Click outside to close
 */
function StockSearchBar({ onStockSelect, placeholder = "Aktie suchen..." }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef(null);
  const resultsRef = useRef(null);
  const inputRef = useRef(null);

  // Debounce search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    setIsSearching(true);
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(
          `${API_BASE}/stocks/search-db/?q=${encodeURIComponent(searchQuery)}&limit=10`
        );
        
        if (response.ok) {
          const data = await response.json();
          setSearchResults(data);
          setShowResults(data.length > 0);
        } else {
          setSearchResults([]);
          setShowResults(false);
        }
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
        setShowResults(false);
      } finally {
        setIsSearching(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Close results when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowResults(false);
        setSelectedIndex(-1);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (!showResults || searchResults.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => 
          prev < searchResults.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && searchResults[selectedIndex]) {
          handleSelectStock(searchResults[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowResults(false);
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  };

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && resultsRef.current) {
      const selectedElement = resultsRef.current.children[selectedIndex];
      if (selectedElement) {
        selectedElement.scrollIntoView({
          block: 'nearest',
          behavior: 'smooth'
        });
      }
    }
  }, [selectedIndex]);

  const handleSelectStock = (stock) => {
    if (onStockSelect) {
      onStockSelect(stock);
    }
    setSearchQuery('');
    setShowResults(false);
    setSelectedIndex(-1);
    inputRef.current?.blur();
  };

  const handleInputChange = (e) => {
    setSearchQuery(e.target.value);
    setSelectedIndex(-1);
  };

  const highlightMatch = (text, query) => {
    if (!text || !query) return text;
    
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === query.toLowerCase() ? 
        <mark key={index}>{part}</mark> : part
    );
  };

  return (
    <div className="stock-search" ref={searchRef}>
      <div className="stock-search__input-wrapper">
        <svg 
          className="stock-search__icon" 
          width="18" 
          height="18" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        
        <input
          ref={inputRef}
          type="text"
          className="stock-search__input"
          placeholder={placeholder}
          value={searchQuery}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => searchResults.length > 0 && setShowResults(true)}
          aria-label="Aktien durchsuchen"
          aria-autocomplete="list"
          aria-controls="search-results"
          aria-expanded={showResults}
        />
        
        {isSearching && (
          <div className="stock-search__spinner">
            <div className="spinner spinner--small"></div>
          </div>
        )}
        
        {searchQuery && !isSearching && (
          <button
            type="button"
            className="stock-search__clear"
            onClick={() => {
              setSearchQuery('');
              setSearchResults([]);
              setShowResults(false);
              inputRef.current?.focus();
            }}
            aria-label="Suche löschen"
          >
            ×
          </button>
        )}
      </div>

      {showResults && searchResults.length > 0 && (
        <ul 
          id="search-results"
          className="stock-search__results" 
          ref={resultsRef}
          role="listbox"
        >
          {searchResults.map((stock, index) => (
            <li
              key={stock.id}
              className={`stock-search__result-item ${
                index === selectedIndex ? 'is-selected' : ''
              }`}
              onClick={() => handleSelectStock(stock)}
              role="option"
              aria-selected={index === selectedIndex}
            >
              <div className="stock-search__result-main">
                <span className="stock-search__result-ticker">
                  {highlightMatch(stock.ticker_symbol, searchQuery)}
                </span>
                <span className="stock-search__result-name">
                  {highlightMatch(stock.name, searchQuery)}
                </span>
              </div>
              <div className="stock-search__result-meta">
                {stock.isin && (
                  <span className="stock-search__result-isin">
                    ISIN: {highlightMatch(stock.isin, searchQuery)}
                  </span>
                )}
                {stock.wkn && (
                  <span className="stock-search__result-wkn">
                    WKN: {highlightMatch(stock.wkn, searchQuery)}
                  </span>
                )}
                {stock.sector && (
                  <span className="stock-search__result-sector">
                    {stock.sector}
                  </span>
                )}
              </div>
              {stock.latest_data && stock.latest_data.current_price && (
                <div className="stock-search__result-price">
                  {new Intl.NumberFormat('de-DE', {
                    style: 'currency',
                    currency: stock.currency || 'USD'
                  }).format(stock.latest_data.current_price)}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {showResults && searchQuery && !isSearching && searchResults.length === 0 && (
        <div className="stock-search__no-results">
          <p>Keine Aktien gefunden für "{searchQuery}"</p>
        </div>
      )}
    </div>
  );
}

export default StockSearchBar;

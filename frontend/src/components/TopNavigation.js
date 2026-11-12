import React from 'react';
import StockSearchBar from './StockSearchBar';

function TopNavigation({ activeView, onNavigate, onStockSelect, onOpenGallery }) {
  return (
    <nav className="topnav" aria-label="Hauptnavigation">
      <div className="topnav__search">
        <StockSearchBar onStockSelect={onStockSelect} placeholder="Aktie suchen..." />
      </div>
      <div className="topnav__items">
        <button className={`topnav__item ${activeView === 'overview' ? 'is-active' : ''}`} onClick={() => onNavigate('overview')} type="button">
          Übersicht
        </button>
        <button className={`topnav__item ${activeView === 'portfolio' ? 'is-active' : ''}`} onClick={() => onNavigate('portfolio')} type="button">
          Portfolio
        </button>
        <button className={`topnav__item ${activeView === 'watchlist' ? 'is-active' : ''}`} onClick={() => onNavigate('watchlist')} type="button">
          Watchlist
        </button>
        <button className={`topnav__item ${activeView === 'screener' ? 'is-active' : ''}`} onClick={() => onNavigate('screener')} type="button">
          Screener
        </button>
        <button className={`topnav__item ${activeView === 'indices' ? 'is-active' : ''}`} onClick={() => onNavigate('indices')} type="button">
          Indizes
        </button>
        <button
          className={`topnav__item topnav__item--icon ${activeView === 'earnings' ? 'is-active' : ''}`}
          onClick={() => onNavigate('earnings')}
          title="Earnings"
          aria-label="Earnings öffnen"
          type="button"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <rect x="3" y="5" width="18" height="16" rx="2" />
            <path d="M7 3v4M17 3v4M3 10h18M7 14h3M14 14h3M7 17h3" />
          </svg>
        </button>
        <button
          className={`topnav__item topnav__item--icon ${activeView === 'alerts' ? 'is-active' : ''}`}
          onClick={() => onNavigate('alerts')}
          title="Alerts"
          aria-label="Alerts öffnen"
          type="button"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4" />
          </svg>
        </button>
        <button
          className={`topnav__item topnav__item--icon ${activeView === 'investment-check' ? 'is-active' : ''}`}
          onClick={() => onNavigate('investment-check')}
          title="Investitions-Check"
          aria-label="Investitions-Check öffnen"
          type="button"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M8 3h8a2 2 0 0 1 2 2v16H6V5a2 2 0 0 1 2-2ZM9 3v3h6V3M9 13l2 2 4-4" />
          </svg>
        </button>
        <button
          className="topnav__item topnav__item--icon"
          onClick={onOpenGallery}
          title="Quick Insights Gallery"
          aria-label="Quick Insights Gallery öffnen"
          type="button"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <rect x="3" y="3" width="7" height="7" rx="1" fill="currentColor" />
            <rect x="14" y="3" width="7" height="7" rx="1" fill="currentColor" />
            <rect x="3" y="14" width="7" height="7" rx="1" fill="currentColor" />
            <rect x="14" y="14" width="7" height="7" rx="1" fill="currentColor" />
          </svg>
        </button>
      </div>
    </nav>
  );
}

export default TopNavigation;

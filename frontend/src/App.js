import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import WatchlistSection from './components/WatchlistSection';
import StocksSection from './components/StocksSection';
import AlertDashboard from './components/AlertDashboard';
import { useAlerts } from './hooks/useAlerts';
import ScreenerView from './components/screener/ScreenerView';
import EarningsView from './components/earnings/EarningsView';
import StockDetailPage from './components/StockDetailPage';

import API_BASE from './config';

function App() {
  const [watchlists, setWatchlists] = useState([]);
  const [currentWatchlist, setCurrentWatchlist] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [showAlertDashboard, setShowAlertDashboard] = useState(false);
  const [activeView, setActiveView] = useState('watchlist');
  const [selectedStock, setSelectedStock] = useState(null);
  const toastTimeoutRef = useRef(null);

  const showToast = useCallback((message, appearance = 'info') => {
    if (!message) {
      setToast(null);
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current);
        toastTimeoutRef.current = null;
      }
      return;
    }

    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }

    setToast({ message, appearance });
    toastTimeoutRef.current = setTimeout(() => {
      setToast(null);
      toastTimeoutRef.current = null;
    }, 4000);
  }, []);

  // Use the alerts hook for background checking (after showToast is defined)
  const { checkAllAlerts } = useAlerts(null, showToast);

  useEffect(() => () => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }
  }, []);

  const loadWatchlists = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/watchlists/`);
      const data = await response.json();
      setWatchlists(data);
    } catch (error) {
      console.error('Error loading watchlists:', error);
      showToast('Laden fehlgeschlagen · Watchlists konnten nicht geladen werden', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadWatchlists();
    
    // Check alerts every 15 minutes (matching backend scheduler)
    const checkAlerts = async () => {
      try {
        const result = await checkAllAlerts();
        
        // Show toast notifications for triggered alerts
        if (result.triggered_count > 0 && result.triggered_alerts) {
          result.triggered_alerts.forEach((triggered) => {
            const message = `🔔 Alert: ${triggered.stock_name} (${triggered.ticker_symbol})`;
            showToast(message, 'warning');
          });
        }
      } catch (error) {
        console.error('Background alert check failed:', error);
      }
    };
    
    // Initial check after 1 minute
    const initialTimer = setTimeout(checkAlerts, 60000);
    
    // Then check every 15 minutes
    const interval = setInterval(checkAlerts, 15 * 60 * 1000);
    
    return () => {
      clearTimeout(initialTimer);
      clearInterval(interval);
    };
  }, [loadWatchlists, showToast, checkAllAlerts]);

  const handleWatchlistSelect = (watchlist) => {
    setCurrentWatchlist(watchlist);
    // Always navigate to the watchlist view when a list is selected
    setActiveView('watchlist');
    if (watchlist?.name) {
      showToast(`Watchlist geöffnet · ${watchlist.name}`, 'info');
    }
  };

  // Collapsed sidebar state: when true the sidebar shows a compact placeholder
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);

  const handleWatchlistSelectAndCollapse = (watchlist) => {
    handleWatchlistSelect(watchlist);
    // Collapse sidebar on select
    setSidebarCollapsed(true);
    // Ensure we navigate to the watchlist view so the stocks panel is shown
    setActiveView('watchlist');
  };

  return (
    <div className="app-shell">
      {toast && typeof document !== 'undefined' && (
        <div className="toast-container" role="status" aria-live="polite">
          <div className={`toast toast--${toast.appearance}`}>
            <span className="toast__message">{toast.message}</span>
            <button
              type="button"
              className="toast__close"
              onClick={() => showToast(null)}
              aria-label="Hinweis schließen"
            >
              ×
            </button>
          </div>
        </div>
      )}
      <div className="container">
        <header className="app-header">
          <div className="app-header__title-group">
            <span className="app-header__eyebrow">Dein Marktüberblick</span>
            <h1>Stock Watchlist</h1>
          </div>
          <p className="app-header__subtitle">
            Synchronisiere deine Watchlists mit aktuellen Kursen und behalte Chancen im Blick.
          </p>
          
          {/* Alert Dashboard Button */}
          <button
            onClick={() => setShowAlertDashboard(true)}
            style={{
              marginTop: '12px',
              padding: '10px 20px',
              background: 'linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: '600',
              boxShadow: '0 4px 12px rgba(124, 58, 237, 0.2)',
              transition: 'all var(--motion-short)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-1px)';
              e.target.style.boxShadow = '0 6px 16px rgba(124, 58, 237, 0.3)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 12px rgba(124, 58, 237, 0.2)';
            }}
          >
            📊 Alarm-Dashboard
          </button>
        </header>

        {/* Top Navigation */}
        <nav className="topnav" aria-label="Hauptnavigation">
          <button
            className={`topnav__item ${activeView === 'overview' ? 'is-active' : ''}`}
            onClick={() => setActiveView('overview')}
            type="button"
          >
            Übersicht
          </button>
          <button
            className={`topnav__item ${activeView === 'watchlist' ? 'is-active' : ''}`}
            onClick={() => setActiveView('watchlist')}
            type="button"
          >
            Watchlist
          </button>
          <button
            className={`topnav__item ${activeView === 'screener' ? 'is-active' : ''}`}
            onClick={() => setActiveView('screener')}
            type="button"
          >
            Screener
          </button>
          <button
            className={`topnav__item ${activeView === 'earnings' ? 'is-active' : ''}`}
            onClick={() => setActiveView('earnings')}
            type="button"
          >
            Earnings
          </button>
          <button
            className="topnav__item"
            onClick={() => setShowAlertDashboard(true)}
            type="button"
            aria-haspopup="dialog"
            aria-controls="alert-dashboard"
          >
            Alerts
          </button>
        </nav>

        {loading && (
          <div className="loading-overlay" role="status" aria-live="polite">
            <div className="spinner"></div>
          </div>
        )}

        {activeView === 'screener' && (
          <div className={`layout ${sidebarCollapsed ? 'layout--sidebar-collapsed' : ''}`}>
            <aside className={`layout__sidebar ${sidebarCollapsed ? 'layout__sidebar--collapsed' : ''}`}>
              <button
                type="button"
                className="sidebar-toggle"
                aria-label={sidebarCollapsed ? 'Sidebar ausklappen' : 'Sidebar einklappen'}
                onClick={() => setSidebarCollapsed((s) => !s)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" fill="currentColor" />
                </svg>
              </button>
              <WatchlistSection
                watchlists={watchlists}
                currentWatchlist={currentWatchlist}
                onWatchlistSelect={handleWatchlistSelectAndCollapse}
                onWatchlistsChange={loadWatchlists}
                onShowToast={showToast}
                collapsed={sidebarCollapsed}
                onToggleCollapsed={() => setSidebarCollapsed((s) => !s)}
              />
            </aside>
            <main className="layout__content">
              <ScreenerView />
            </main>
          </div>
        )}

        {activeView === 'earnings' && (
          <div className={`layout ${sidebarCollapsed ? 'layout--sidebar-collapsed' : ''}`}>
            <aside className={`layout__sidebar ${sidebarCollapsed ? 'layout__sidebar--collapsed' : ''}`}>
              <button
                type="button"
                className="sidebar-toggle"
                aria-label={sidebarCollapsed ? 'Sidebar ausklappen' : 'Sidebar einklappen'}
                onClick={() => setSidebarCollapsed((s) => !s)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" fill="currentColor" />
                </svg>
              </button>
              <WatchlistSection
                watchlists={watchlists}
                currentWatchlist={currentWatchlist}
                onWatchlistSelect={handleWatchlistSelectAndCollapse}
                onWatchlistsChange={loadWatchlists}
                onShowToast={showToast}
                collapsed={sidebarCollapsed}
                onToggleCollapsed={() => setSidebarCollapsed((s) => !s)}
              />
            </aside>
            <main className="layout__content">
              <EarningsView />
            </main>
          </div>
        )}

        {activeView === 'watchlist' && (
          <div className={`layout ${sidebarCollapsed ? 'layout--sidebar-collapsed' : ''}`}>
            <aside className={`layout__sidebar ${sidebarCollapsed ? 'layout__sidebar--collapsed' : ''}`}>
              <button
                type="button"
                className="sidebar-toggle"
                aria-label={sidebarCollapsed ? 'Sidebar ausklappen' : 'Sidebar einklappen'}
                onClick={() => setSidebarCollapsed((s) => !s)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" fill="currentColor" />
                </svg>
              </button>
              <WatchlistSection
                watchlists={watchlists}
                currentWatchlist={currentWatchlist}
                onWatchlistSelect={handleWatchlistSelectAndCollapse}
                onWatchlistsChange={loadWatchlists}
                onShowToast={showToast}
                collapsed={sidebarCollapsed}
                onToggleCollapsed={() => setSidebarCollapsed((s) => !s)}
              />
            </aside>
            <main className="layout__content">
              {currentWatchlist ? (
                <StocksSection
                  watchlist={currentWatchlist}
                  watchlists={watchlists}
                  onShowToast={showToast}
                  onOpenStock={(stock) => { setSelectedStock(stock); setActiveView('stock'); }}
                />
              ) : (
                <div className="empty-state empty-state--hero">
                  <h2>Wähle eine Watchlist aus</h2>
                  <p>
                    Markiere eine Watchlist auf der linken Seite, um Kursverläufe, Kennzahlen und Performance-Insights zu sehen.
                  </p>
                  <p className="empty-state__hint">
                    Du kannst jederzeit neue Watchlists anlegen oder bestehende anpassen.
                  </p>
                </div>
              )}
            </main>
          </div>
        )}

        {activeView === 'stock' && (
          <div className={`layout ${sidebarCollapsed ? 'layout--sidebar-collapsed' : ''}`}>
            <aside className={`layout__sidebar ${sidebarCollapsed ? 'layout__sidebar--collapsed' : ''}`}>
              <button
                type="button"
                className="sidebar-toggle"
                aria-label={sidebarCollapsed ? 'Sidebar ausklappen' : 'Sidebar einklappen'}
                onClick={() => setSidebarCollapsed((s) => !s)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" fill="currentColor" />
                </svg>
              </button>
              <WatchlistSection
                watchlists={watchlists}
                currentWatchlist={currentWatchlist}
                onWatchlistSelect={handleWatchlistSelectAndCollapse}
                onWatchlistsChange={loadWatchlists}
                onShowToast={showToast}
                collapsed={sidebarCollapsed}
                onToggleCollapsed={() => setSidebarCollapsed((s) => !s)}
              />
            </aside>
            <main className="layout__content">
              {selectedStock ? (
                <StockDetailPage stock={selectedStock} onBack={() => { setActiveView('watchlist'); setSelectedStock(null); }} />
              ) : (
                <div className="empty-state empty-state--hero">
                  <h2>Keine Aktie ausgewählt</h2>
                  <p>Wähle eine Aktie aus der Watchlist aus, um Details zu sehen.</p>
                </div>
              )}
            </main>
          </div>
        )}

        {activeView === 'overview' && (
          <main className="layout__content">
            <div className="panel">
              <div className="panel__title-group">
                <div className="panel__eyebrow">Überblick</div>
                <div className="panel__title">Marktübersicht</div>
                <div className="panel__subtitle">Kommende Kacheln: Marktbreite, Top Gainer/Loser, Sektor-Heatmap …</div>
              </div>
              <div style={{marginTop: '16px', color: 'var(--text-muted)'}}>Kommt bald.</div>
            </div>
          </main>
        )}
      </div>
      
      {/* Alert Dashboard Modal */}
      {showAlertDashboard && (
        <AlertDashboard 
          onClose={() => setShowAlertDashboard(false)}
          showToast={showToast}
        />
      )}
    </div>
  );
}

export default App;

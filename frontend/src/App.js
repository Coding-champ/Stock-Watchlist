import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import WatchlistSection from './components/WatchlistSection';
import StocksSection from './components/StocksSection';
import StockSearchBar from './components/StockSearchBar';
import { useAlerts } from './hooks/useAlerts';
import ScreenerView from './components/screener/ScreenerView';
import EarningsView from './components/earnings/EarningsView';
import AlertsView from './components/alerts/AlertsView';
import StockDetailPage from './components/StockDetailPage';
import IndexOverview from './components/IndexOverview';
import IndexDetailPage from './components/IndexDetailPage';

import API_BASE from './config';
import { useQueryClient } from '@tanstack/react-query';

function App() {
  const [watchlists, setWatchlists] = useState([]);
  const [currentWatchlist, setCurrentWatchlist] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [activeView, setActiveView] = useState('watchlist');
  const [selectedStock, setSelectedStock] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);
  // Default period changed to 1y per user request
  const [galleryPeriod, setGalleryPeriod] = useState('1y');
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
  const queryClient = useQueryClient();

  useEffect(() => () => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }
  }, []);

  const loadWatchlists = useCallback(async () => {
    try {
      setLoading(true);
      const url = `${API_BASE}/watchlists/`;
      const data = await queryClient.fetchQuery(['api', url], async () => {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      }, { staleTime: 60 * 1000 });
      setWatchlists(data);
    } catch (error) {
      console.error('Error loading watchlists:', error);
      showToast('Laden fehlgeschlagen · Watchlists konnten nicht geladen werden', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast, queryClient]);

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
        </header>

        {/* Top Navigation */}
        <nav className="topnav" aria-label="Hauptnavigation">
          <div className="topnav__search">
            <StockSearchBar 
              onStockSelect={(stock) => {
                setSelectedStock(stock);
                setActiveView('stock');
                showToast(`Aktie geöffnet · ${stock.name}`, 'info');
              }}
              placeholder="Aktie suchen..."
            />
          </div>
          <div className="topnav__items">
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
              className={`topnav__item ${activeView === 'alerts' ? 'is-active' : ''}`}
              onClick={() => setActiveView('alerts')}
              type="button"
            >
              Alerts
            </button>
            <button
              className={`topnav__item ${activeView === 'indices' ? 'is-active' : ''}`}
              onClick={() => setActiveView('indices')}
              type="button"
            >
              Indizes
            </button>
            {/* Gallery trigger icon at the far right */}
            <button
              className="topnav__item topnav__item--icon"
              onClick={() => setIsGalleryOpen(true)}
              title="Quick Insights Gallery"
              aria-label="Quick Insights Gallery öffnen"
              type="button"
              style={{ marginLeft: 'auto' }}
            >
              {/* simple grid icon */}
              <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <rect x="3" y="3" width="7" height="7" rx="1" fill="currentColor"/>
                <rect x="14" y="3" width="7" height="7" rx="1" fill="currentColor"/>
                <rect x="3" y="14" width="7" height="7" rx="1" fill="currentColor"/>
                <rect x="14" y="14" width="7" height="7" rx="1" fill="currentColor"/>
              </svg>
            </button>
          </div>
        </nav>

        {isGalleryOpen && (
          <div 
            className="drawer-overlay" 
            role="dialog" 
            aria-modal="true" 
            aria-label="Quick Insights Gallery"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setIsGalleryOpen(false);
              }
            }}
          >
            <div className="drawer drawer--right">
              <div className="drawer__header">
                <div className="drawer__title-group">
                  <div className="drawer__eyebrow">Quick Insights</div>
                  <div className="drawer__title">Performance-Gallery</div>
                </div>
                <div className="drawer__actions">
                  <div className="segmented">
                    {['6m','1y','3y'].map((p) => (
                      <button key={p} className={`segmented__btn ${galleryPeriod===p?'is-active':''}`} onClick={() => setGalleryPeriod(p)}>{p}</button>
                    ))}
                  </div>
                  <button className="drawer__close" onClick={() => setIsGalleryOpen(false)} aria-label="Schließen">
                    ×
                  </button>
                </div>
              </div>
              <div className="drawer__body">
                {/* Lazy import kept simple to avoid bundler churn; inline component below */}
                <PerformanceGallery period={galleryPeriod} onToast={showToast} />
              </div>
            </div>
          </div>
        )}

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

        {activeView === 'alerts' && (
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
              <AlertsView showToast={showToast} />
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

        {activeView === 'indices' && (
          <main className="layout__content">
            <IndexOverview 
              onIndexClick={(index) => {
                setSelectedIndex(index);
                setActiveView('index-detail');
                showToast(`Index geöffnet · ${index.name}`, 'info');
              }}
            />
          </main>
        )}

        {activeView === 'index-detail' && selectedIndex && (
          <main className="layout__content">
            <IndexDetailPage 
              index={selectedIndex}
              onBack={() => {
                setActiveView('indices');
                setSelectedIndex(null);
              }}
            />
          </main>
        )}
      </div>
    </div>
  );
}

export default App;

// Minimal inline gallery (keeps patch tight). Consider moving to separate files later.
// Duplicate import removed: React, useEffect, useState already imported at top
function PerformanceGallery({ period, onToast }) {
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);
  const [quickWatchlistId, setQuickWatchlistId] = useState(null);
  const [busyTicker, setBusyTicker] = useState(null);
  const [favoritedTickers, setFavoritedTickers] = useState(new Set());
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false); // initial load
  const [loadingMore, setLoadingMore] = useState(false); // pagination
  const containerRef = useRef(null);
  const loadMoreRef = useRef(null);
  const PAGE_LIMIT = 60;

  const fetchPage = useCallback(async (targetPage, replace = false) => {
    const isFirst = targetPage === 1 && replace;
    if (isFirst) setLoading(true); else setLoadingMore(true);
    try {
      setError(null);
      const url = `${API_BASE}/stocks/performance?period=${encodeURIComponent(period)}&points=24&sort=desc&page=${targetPage}&limit=${PAGE_LIMIT}&includeSignals=true`;
      const res = await fetch(url);
      const text = await res.text();
      if (!res.ok) {
        console.error('Performance fetch failed', res.status, text);
        throw new Error(`HTTP ${res.status} ${text?.slice(0,180)}`);
      }
      const json = text ? JSON.parse(text) : { items: [] };
      const newItems = Array.isArray(json.items) ? json.items : [];
      setHasMore(newItems.length === PAGE_LIMIT);
      setItems((prev) => replace ? newItems : prev.concat(newItems));
    } catch (e) {
      setError('Konnte Performance nicht laden');
    } finally {
      if (isFirst) setLoading(false); else setLoadingMore(false);
    }
  }, [period]);

  // Reset and load first page whenever period changes
  useEffect(() => {
    setItems([]);
    setPage(1);
    setHasMore(true);
    fetchPage(1, true);
  }, [period, fetchPage]);

  useEffect(() => {
    let cancel = false;
    async function loadFavorites() {
      try {
        const listRes = await fetch(`${API_BASE}/watchlists/`);
        if (!listRes.ok) return;
        const lists = await listRes.json();
        const quickList = Array.isArray(lists) ? lists.find((wl) => (wl.name || '').toLowerCase() === 'quick insights') : null;
        if (!quickList?.id) return;
        setQuickWatchlistId(quickList.id);
        
        const stocksRes = await fetch(`${API_BASE}/stocks/?watchlist_id=${quickList.id}`);
        if (!stocksRes.ok) return;
        const stocks = await stocksRes.json();
        if (!cancel && Array.isArray(stocks)) {
          setFavoritedTickers(new Set(stocks.map(s => s.ticker_symbol)));
        }
      } catch (e) {
        console.error('Load favorites error', e);
      }
    }
    loadFavorites();
    return () => { cancel = true; };
  }, []);

  // IntersectionObserver to trigger loading more when sentinel enters view
  useEffect(() => {
    if (!hasMore) return;
    const rootEl = containerRef.current ? containerRef.current.closest('.drawer__body') : null;
    const sentinel = loadMoreRef.current;
    if (!sentinel) return;
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !loading && !loadingMore && hasMore) {
          const next = page + 1;
          setPage(next);
          fetchPage(next);
        }
      });
    }, { root: rootEl || null, rootMargin: '200px', threshold: 0 });
    obs.observe(sentinel);
    return () => { obs.disconnect(); };
  }, [page, hasMore, loading, loadingMore, fetchPage]);

  const ensureQuickInsightsWatchlist = useCallback(async () => {
    if (quickWatchlistId) return quickWatchlistId;
    // Try to find existing
    const listRes = await fetch(`${API_BASE}/watchlists/`);
    if (listRes.ok) {
      const lists = await listRes.json();
      const found = Array.isArray(lists) ? lists.find((wl) => (wl.name || '').toLowerCase() === 'quick insights') : null;
      if (found?.id) {
        setQuickWatchlistId(found.id);
        return found.id;
      }
    }
    // Create if missing
    const createRes = await fetch(`${API_BASE}/watchlists/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Quick Insights', description: 'Auto-created for Quick Insights' })
    });
    if (!createRes.ok) {
      const t = await createRes.text();
      throw new Error(`Watchlist erstellen fehlgeschlagen: ${createRes.status} ${t}`);
    }
    const created = await createRes.json();
    setQuickWatchlistId(created.id);
    return created.id;
  }, [quickWatchlistId]);

  const handleFavorite = useCallback(async (ticker, stockId) => {
    try {
      setBusyTicker(ticker);
      const wlId = await ensureQuickInsightsWatchlist();
      const already = favoritedTickers.has(ticker);
      if (already) {
        const del = await fetch(`${API_BASE}/stocks/${stockId}?watchlist_id=${wlId}`, { method: 'DELETE' });
        if (del.status === 204) {
          setFavoritedTickers(prev => { const next = new Set(prev); next.delete(ticker); return next; });
          onToast?.(`Entfernt · ${ticker} aus Quick Insights`, 'info');
        } else {
          const txt = await del.text();
          onToast?.(`Konnte ${ticker} nicht entfernen`, 'error');
          console.error('Unfavorite failed', del.status, txt);
        }
      } else {
        const res = await fetch(`${API_BASE}/stocks/add-by-ticker`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticker_symbol: ticker, watchlist_id: wlId })
        });
        if (res.status === 201) {
          setFavoritedTickers(prev => new Set([...prev, ticker]));
          onToast?.(`✓ Hinzugefügt · ${ticker} → Quick Insights`, 'info');
        } else {
          const txt = await res.text();
          if (txt && /exists|already/i.test(txt)) {
            setFavoritedTickers(prev => new Set([...prev, ticker]));
            onToast?.(`Bereits vorhanden · ${ticker} in Quick Insights`, 'info');
          } else {
            onToast?.(`Fehler beim Hinzufügen · ${ticker}`, 'error');
            console.error('Favorite failed', res.status, txt);
          }
        }
      }
    } catch (e) {
      console.error('Favorite error', e);
      onToast?.('Aktion fehlgeschlagen · Quick Insights', 'error');
    } finally {
      setBusyTicker(null);
    }
  }, [ensureQuickInsightsWatchlist, onToast, favoritedTickers]);

  if (loading && !items.length) return <div className="loading">Lade…</div>;
  if (error && !items.length) return <div className="empty-state">{error}</div>;
  if (!items.length) return <div className="empty-state">Keine Daten</div>;

  return (
    <div ref={containerRef}>
      <div className="gallery-grid">
      {items.map((it) => {
        const isFavorited = favoritedTickers.has(it.ticker);
        const isBusy = busyTicker === it.ticker;
        return (
          <div key={it.id} className={`gallery-card ${isFavorited ? 'gallery-card--favorited' : ''}`}>
            <div className="gallery-card__header">
              <div style={{display:'flex', flexDirection:'column'}}>
                <div className="gallery-card__title">{it.name}</div>
                <div className="gallery-card__subtitle">{it.ticker}</div>
              </div>
              <button
                type="button"
                className={`icon-btn ${isFavorited ? 'icon-btn--active' : ''}`}
                title={isFavorited ? 'In Quick Insights' : 'Zu Quick Insights hinzufügen'}
                onClick={() => handleFavorite(it.ticker, it.id)}
                disabled={isBusy}
              >
                {isBusy ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" className="icon-spinner" aria-hidden>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" opacity="0.25"/>
                    <path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" strokeWidth="3" fill="none"/>
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden>
                    <path d="M12 21s-6.716-3.868-9.193-6.346C.761 12.61.5 9.5 2.318 7.682 4.136 5.864 7.246 6.125 9.654 8.533L12 10.879l2.346-2.346c2.408-2.408 5.518-2.669 7.336-.851 1.818 1.818 1.557 4.928-.489 6.972C18.716 17.132 12 21 12 21z" fill="currentColor"/>
                  </svg>
                )}
              </button>
            </div>
            <MiniSparkline data={(it.price_series||[]).map(p=>p.close)} />
            <div className="gallery-card__footer">
              <span className="perf">{it.performance_pct!=null ? `${it.performance_pct.toFixed(2)}%` : '-'}</span>
              <div className="badges">
                <Badge label="RSI" value={it.signals?.rsi?.signal || '–'} />
                <Badge label="MACD" value={it.signals?.macd?.trend || '–'} />
              </div>
            </div>
          </div>
        );
      })}
      </div>
      {hasMore && (
        <>
          <div ref={loadMoreRef} className="infinite-sentinel" />
          {loadingMore && (
            <div className="infinite-loader" role="status" aria-live="polite">
              <div className="spinner" style={{ width: 24, height: 24, borderWidth: 3 }} />
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MiniSparkline({ data, w=140, h=48, color='#7c3aed' }){
  if (!data || data.length < 2) return <div className="sparkline sparkline--empty">–</div>;
  const min = Math.min(...data), max = Math.max(...data), range = max-min || 1;
  const pts = data.map((v,i)=>({ x: (i/(data.length-1))*w, y: h-((v-min)/range)*h }));
  const path = pts.reduce((a,p,i)=> i? `${a} L ${p.x},${p.y}`: `M ${p.x},${p.y}`,'');
  const area = `${path} L ${w},${h} L 0,${h} Z`;
  const last = pts[pts.length-1];
  const gid = `g${Math.random().toString(36).slice(2)}`;
  return (
    <div className="sparkline" aria-hidden="true">
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
        <defs><linearGradient id={gid} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity="0.35"/><stop offset="100%" stopColor={color} stopOpacity="0"/></linearGradient></defs>
        <path d={area} fill={`url(#${gid})`} className="sparkline__area"/>
        <path d={path} stroke={color} strokeWidth="2" className="sparkline__line"/>
        <circle cx={last.x} cy={last.y} r="3.5" fill={color} className="sparkline__dot"/>
      </svg>
    </div>
  );
}

function Badge({ label, value }){
  const tone = value==='bullish' ? 'success' : (value==='bearish' || value==='overbought') ? 'warning' : 'neutral';
  return <span className={`badge badge--${tone}`} title={`${label}: ${value}`}>{label}: {value}</span>;
}

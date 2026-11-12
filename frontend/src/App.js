import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import AppSidebar from './components/AppSidebar';
import SidebarLayout from './components/SidebarLayout';
import AppHeader from './components/AppHeader';
import TopNavigation from './components/TopNavigation';
import StocksSection from './components/StocksSection';
import { useAlerts } from './hooks/useAlerts';
import ScreenerView from './components/screener/ScreenerView';
import EarningsView from './components/earnings/EarningsView';
import AlertsView from './components/alerts/AlertsView';
import StockDetailPage from './components/StockDetailPage';
import IndexOverview from './components/IndexOverview';
import IndexDetailPage from './components/IndexDetailPage';
import CorrelationHeatmap from './components/CorrelationHeatmap';
import PortfolioView from './components/portfolio/PortfolioView';
import InvestmentCheckView from './components/investment-check/InvestmentCheckView';
import AdminView from './components/AdminView';
import PerformanceGallery from './components/PerformanceGallery';

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
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [settings, setSettings] = useState({ display_mode: 'compact', default_page: 'overview', theme: 'default' });
  const [themes, setThemes] = useState([]);
  // TODO: Apply different layouts and visible features when expert mode is implemented.
  // Default period changed to 1y per user request
  const [galleryPeriod, setGalleryPeriod] = useState('1y');
  const toastTimeoutRef = useRef(null);
  const settingsRef = useRef(null);

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

  const saveSettings = useCallback(async (patch) => {
    try {
      const response = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const saved = await response.json();
      setSettings(saved);
      if (patch.default_page) setActiveView(patch.default_page);
    } catch (error) {
      console.error('Error saving application settings:', error);
      showToast('Einstellungen konnten nicht gespeichert werden', 'error');
    }
  }, [showToast]);

  // Use the alerts hook for background checking (after showToast is defined)
  const { checkAllAlerts } = useAlerts(null, showToast);
  const queryClient = useQueryClient();

  useEffect(() => () => {
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
      toastTimeoutRef.current = null;
    }
  }, []);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const [settingsResponse, themesResponse] = await Promise.all([
          fetch(`${API_BASE}/settings`),
          fetch(`${API_BASE}/settings/themes`),
        ]);
        if (!settingsResponse.ok || !themesResponse.ok) throw new Error('Settings API unavailable');
        const loadedSettings = await settingsResponse.json();
        setSettings(loadedSettings);
        setActiveView(loadedSettings.default_page);
        setThemes(await themesResponse.json());
      } catch (error) {
        console.error('Error loading application settings:', error);
      }
    };
    loadSettings();
  }, []);

  useEffect(() => {
    const selectedTheme = themes.find((theme) => theme.id === settings.theme);
    selectedTheme?.variables && Object.entries(selectedTheme.variables).forEach(([name, value]) => {
      document.documentElement.style.setProperty(name, value);
    });
  }, [settings.theme, themes]);

  useEffect(() => {
    const handleDocumentClick = (event) => {
      if (settingsRef.current && !settingsRef.current.contains(event.target)) {
        setIsSettingsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleDocumentClick);
    return () => document.removeEventListener('mousedown', handleDocumentClick);
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

  const openInvestmentCheck = (identifier = '') => {
    setSelectedStock(identifier ? { ticker_symbol: identifier, name: identifier } : null);
    setActiveView('investment-check');
  };

  const sidebar = (
    <AppSidebar
      watchlists={watchlists}
      currentWatchlist={currentWatchlist}
      sidebarCollapsed={sidebarCollapsed}
      onToggleCollapsed={() => setSidebarCollapsed((s) => !s)}
      onWatchlistSelect={handleWatchlistSelectAndCollapse}
      onWatchlistsChange={loadWatchlists}
      onShowToast={showToast}
    />
  );

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
        <AppHeader
          isSettingsOpen={isSettingsOpen}
          settings={settings}
          themes={themes}
          settingsRef={settingsRef}
          onToggleSettings={() => setIsSettingsOpen((open) => !open)}
          onOpenAdmin={() => {
            setIsSettingsOpen(false);
            setActiveView('admin');
          }}
          onSaveSettings={saveSettings}
        />

        <TopNavigation
          activeView={activeView}
          onNavigate={setActiveView}
          onStockSelect={(stock) => {
            setSelectedStock(stock);
            setActiveView('stock');
            showToast(`Aktie geöffnet · ${stock.name}`, 'info');
          }}
          onOpenGallery={() => setIsGalleryOpen(true)}
        />

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
          <SidebarLayout sidebarCollapsed={sidebarCollapsed} sidebar={sidebar}>
            <ScreenerView />
          </SidebarLayout>
        )}

        {activeView === 'earnings' && (
          <SidebarLayout sidebarCollapsed={sidebarCollapsed} sidebar={sidebar}>
            <EarningsView />
          </SidebarLayout>
        )}

        {activeView === 'alerts' && (
          <SidebarLayout sidebarCollapsed={sidebarCollapsed} sidebar={sidebar}>
            <AlertsView showToast={showToast} />
          </SidebarLayout>
        )}

        {activeView === 'watchlist' && (
          <SidebarLayout sidebarCollapsed={sidebarCollapsed} sidebar={sidebar}>
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
          </SidebarLayout>
        )}

        {activeView === 'stock' && (
          <SidebarLayout sidebarCollapsed={sidebarCollapsed} sidebar={sidebar}>
            {selectedStock ? (
              <StockDetailPage
                stock={selectedStock}
                watchlistId={currentWatchlist?.id}
                onShowToast={showToast}
                onOpenInvestmentCheck={openInvestmentCheck}
                onBack={() => { setActiveView('watchlist'); setSelectedStock(null); }}
              />
            ) : (
              <div className="empty-state empty-state--hero">
                <h2>Keine Aktie ausgewählt</h2>
                <p>Wähle eine Aktie aus der Watchlist aus, um Details zu sehen.</p>
              </div>
            )}
          </SidebarLayout>
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

        {activeView === 'portfolio' && (
          <PortfolioView
            showToast={showToast}
            onOpenInvestmentCheck={openInvestmentCheck}
            onOpenStock={(stock) => {
              setSelectedStock(stock);
              setActiveView('stock');
            }}
          />
        )}

        {activeView === 'investment-check' && (
          <InvestmentCheckView
            showToast={showToast}
            initialIdentifier={selectedStock?.ticker_symbol || ''}
            onOpenPortfolio={() => setActiveView('portfolio')}
          />
        )}

        {activeView === 'admin' && <AdminView showToast={showToast} />}

        {activeView === 'indices' && (
          <main className="layout__content">
            <IndexOverview 
              onIndexClick={(index) => {
                setSelectedIndex(index);
                setActiveView('index-detail');
                showToast(`Index geöffnet · ${index.name}`, 'info');
              }}
            />
            {/* Korrelationsmatrix unterhalb der Indizes-Übersicht */}
            <div style={{ marginTop: '32px' }}>
              <div className="panel">
                <div className="panel__title-group">
                  <div className="panel__eyebrow">Analyse</div>
                  <div className="panel__title">Index-Korrelationen</div>
                  <div className="panel__subtitle">Vergleich der täglichen Renditen wichtiger Leitindizes</div>
                </div>
              </div>
              <CorrelationHeatmap />
            </div>
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
              onOpenStock={(stock) => { 
                setSelectedStock(stock); 
                setActiveView('stock'); 
              }}
            />
          </main>
        )}
      </div>
    </div>
  );
}

export default App;

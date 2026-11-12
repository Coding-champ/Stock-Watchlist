import React, { useCallback, useEffect, useRef, useState } from 'react';
import API_BASE from '../config';
import { formatDisplayNumber } from '../utils/numberFormatting';

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
                <div style={{ display: 'flex', flexDirection: 'column' }}>
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
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" opacity="0.25" />
                      <path d="M22 12a10 10 0 0 1-10 10" stroke="currentColor" strokeWidth="3" fill="none" />
                    </svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden>
                      <path d="M12 21s-6.716-3.868-9.193-6.346C.761 12.61.5 9.5 2.318 7.682 4.136 5.864 7.246 6.125 9.654 8.533L12 10.879l2.346-2.346c2.408-2.408 5.518-2.669 7.336-.851 1.818 1.818 1.557 4.928-.489 6.972C18.716 17.132 12 21 12 21z" fill="currentColor" />
                    </svg>
                  )}
                </button>
              </div>
              <MiniSparkline data={(it.price_series || []).map(p => p.close)} />
              <div className="gallery-card__footer">
                <span className="perf">{it.performance_pct != null ? `${formatDisplayNumber(it.performance_pct)}%` : '-'}</span>
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

function MiniSparkline({ data, w = 140, h = 48, color = 'var(--brand-primary)' }) {
  if (!data || data.length < 2) return <div className="sparkline sparkline--empty">–</div>;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => ({ x: (i / (data.length - 1)) * w, y: h - ((v - min) / range) * h }));
  const path = pts.reduce((a, p, i) => i ? `${a} L ${p.x},${p.y}` : `M ${p.x},${p.y}`, '');
  const area = `${path} L ${w},${h} L 0,${h} Z`;
  const last = pts[pts.length - 1];
  const gid = `g${Math.random().toString(36).slice(2)}`;
  return (
    <div className="sparkline" aria-hidden="true">
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.35" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={area} fill={`url(#${gid})`} className="sparkline__area" />
        <path d={path} stroke={color} strokeWidth="2" className="sparkline__line" />
        <circle cx={last.x} cy={last.y} r="3.5" fill={color} className="sparkline__dot" />
      </svg>
    </div>
  );
}

function Badge({ label, value }) {
  // Treat 'oversold' as a positive (green) signal similar to 'bullish'
  const tone = (value === 'bullish' || value === 'oversold')
    ? 'success'
    : (value === 'bearish' || value === 'overbought')
      ? 'warning'
      : 'neutral';
  const displayValue = value === 'bullish'
    ? '↑ bullish'
    : value === 'bearish'
      ? '↓ bearish'
      : value;
  return <span className={`badge badge--${tone}`} title={`${label}: ${value}`}>{label}: {displayValue}</span>;
}

export default PerformanceGallery;

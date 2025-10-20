import React, { useEffect, useMemo, useRef, useState } from 'react';
import API_BASE from '../../config';

const ScreenerView = () => {
  const [facets, setFacets] = useState({ countries: [], sectors: [], industries: [] });
  const [filters, setFilters] = useState({
    q: '',
    country: '',
    sector: '',
    industry: '',
    // technical
    price_vs_sma50: '', // above|below
    price_vs_sma200: '', // above|below
    // beta
    beta_min: '',
    beta_max: '',
    // fundamentals
    profit_margin_min: '',
    roe_min: '',
    current_ratio_min: '',
    quick_ratio_min: '',
    operating_cashflow_min: '',
    free_cashflow_min: '',
    shareholders_equity_min: '',
    total_assets_min: '',
    debt_to_equity_max: '',
    total_liabilities_max: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [sort, setSort] = useState('ticker_symbol');
  const [order, setOrder] = useState('asc');
  const [filtersOpen, setFiltersOpen] = useState(false);
  const scrollRef = useRef(null);
  const [hasLeftShadow, setHasLeftShadow] = useState(false);
  const [hasRightShadow, setHasRightShadow] = useState(false);

  // Load facets
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/screener/filters`);
        const data = await res.json();
        if (!cancelled) setFacets(data);
      } catch (e) {
        // ignore silently for facets
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    const setIf = (key, val) => {
      if (val !== '' && val !== null && val !== undefined) params.set(key, String(val));
    };
    setIf('q', filters.q);
    setIf('country', filters.country);
    setIf('sector', filters.sector);
    setIf('industry', filters.industry);
    // technical
    setIf('price_vs_sma50', filters.price_vs_sma50);
    setIf('price_vs_sma200', filters.price_vs_sma200);
    // beta
    setIf('beta_min', filters.beta_min);
    setIf('beta_max', filters.beta_max);
    // fundamentals
    setIf('profit_margin_min', filters.profit_margin_min);
    setIf('roe_min', filters.roe_min);
    setIf('current_ratio_min', filters.current_ratio_min);
    setIf('quick_ratio_min', filters.quick_ratio_min);
    setIf('operating_cashflow_min', filters.operating_cashflow_min);
    setIf('free_cashflow_min', filters.free_cashflow_min);
    setIf('shareholders_equity_min', filters.shareholders_equity_min);
    setIf('total_assets_min', filters.total_assets_min);
    setIf('debt_to_equity_max', filters.debt_to_equity_max);
    setIf('total_liabilities_max', filters.total_liabilities_max);
    params.set('page', String(page));
    params.set('page_size', String(pageSize));
    params.set('sort', sort);
    params.set('order', order);
    return params.toString();
  }, [filters, page, pageSize, sort, order]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/screener/run?${queryString}`);
        const data = await res.json();
        if (!cancelled) {
          setResults(data.results || []);
          setTotal(data.total || 0);
        }
      } catch (e) {
        if (!cancelled) setError('Screener konnte nicht geladen werden');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [queryString]);

  // Scroll shadow updater
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const update = () => {
      const max = el.scrollWidth - el.clientWidth;
      const left = el.scrollLeft > 0;
      const right = el.scrollLeft < max - 1; // tolerance
      setHasLeftShadow(left);
      setHasRightShadow(right);
    };
    update();
    el.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    return () => {
      el.removeEventListener('scroll', update);
      window.removeEventListener('resize', update);
    };
  }, [results, page, pageSize, filtersOpen]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const toggleSort = (key) => {
    if (sort === key) {
      setOrder(order === 'asc' ? 'desc' : 'asc');
    } else {
      setSort(key);
      setOrder('asc');
    }
  };

  const clearFilters = () => {
    setFilters({
      q: '', country: '', sector: '', industry: '',
      price_vs_sma50: '', price_vs_sma200: '', beta_min: '', beta_max: '',
      profit_margin_min: '', roe_min: '', current_ratio_min: '', quick_ratio_min: '',
      operating_cashflow_min: '', free_cashflow_min: '', shareholders_equity_min: '',
      total_assets_min: '', debt_to_equity_max: '', total_liabilities_max: '',
    });
    setPage(1);
  };

  const fmtNum = (v, digits = 2) => {
    if (v === null || v === undefined || isNaN(v)) return '—';
    const n = Number(v);
    return Number.isFinite(n) ? n.toFixed(digits) : '—';
  };

  return (
    <div className="panel">
      <div className="panel__title-group">
        <div className="panel__eyebrow">Screener</div>
        <div className="panel__title">Aktien-Screener</div>
        <div className="panel__subtitle">Filtere nach Stammdaten, Technik (SMA) und Kennzahlen.</div>
      </div>
      <div className="panel__body" style={{marginTop: '12px'}}>
        <div className="panel__toolbar">
          <div className="panel__toolbar-row">
            <div className="search-field" style={{flex: 1}}>
              <span className="search-field__icon">🔎</span>
              <input
                className="search-field__input"
                placeholder="Suche Ticker oder Name"
                value={filters.q}
                onChange={(e) => { setPage(1); setFilters({ ...filters, q: e.target.value }); }}
              />
            </div>
            <select value={filters.country} onChange={(e) => { setPage(1); setFilters({ ...filters, country: e.target.value }); }}>
              <option value="">Land</option>
              {facets.countries.map((c) => (<option key={c} value={c}>{c}</option>))}
            </select>
            <select value={filters.sector} onChange={(e) => { setPage(1); setFilters({ ...filters, sector: e.target.value }); }}>
              <option value="">Sektor</option>
              {facets.sectors.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={filters.industry} onChange={(e) => { setPage(1); setFilters({ ...filters, industry: e.target.value }); }}>
              <option value="">Industrie</option>
              {facets.industries.map((i) => (<option key={i} value={i}>{i}</option>))}
            </select>
          </div>
          <div className="panel__toolbar-row">
            <button className="btn btn--ghost" type="button" onClick={()=> setFiltersOpen(o => !o)}>
              {filtersOpen ? '▾ Filter ausblenden' : '▸ Filter anzeigen'}
            </button>
          </div>

          {filtersOpen && (
            <div className="filter-collapse" style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
              <div className="panel__toolbar-row">
                <select value={filters.price_vs_sma50} onChange={(e)=>{ setPage(1); setFilters({ ...filters, price_vs_sma50: e.target.value }); }}>
                  <option value="">Preis vs SMA50</option>
                  <option value="above">Über SMA50</option>
                  <option value="below">Unter SMA50</option>
                </select>
                <select value={filters.price_vs_sma200} onChange={(e)=>{ setPage(1); setFilters({ ...filters, price_vs_sma200: e.target.value }); }}>
                  <option value="">Preis vs SMA200</option>
                  <option value="above">Über SMA200</option>
                  <option value="below">Unter SMA200</option>
                </select>
                <input type="number" inputMode="decimal" step="0.1" placeholder="β min" value={filters.beta_min}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, beta_min: e.target.value }); }} style={{maxWidth: 120}} />
                <input type="number" inputMode="decimal" step="0.1" placeholder="β max" value={filters.beta_max}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, beta_max: e.target.value }); }} style={{maxWidth: 120}} />
              </div>

              <div className="panel__toolbar-row">
                <input type="number" inputMode="decimal" step="0.1" placeholder="Profit Margin ≥" value={filters.profit_margin_min}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, profit_margin_min: e.target.value }); }} style={{maxWidth: 180}} />
                <input type="number" inputMode="decimal" step="0.1" placeholder="ROE ≥" value={filters.roe_min}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, roe_min: e.target.value }); }} style={{maxWidth: 140}} />
                <input type="number" inputMode="decimal" step="0.01" placeholder="Current Ratio ≥" value={filters.current_ratio_min}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, current_ratio_min: e.target.value }); }} style={{maxWidth: 180}} />
                <input type="number" inputMode="decimal" step="0.01" placeholder="Quick Ratio ≥" value={filters.quick_ratio_min}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, quick_ratio_min: e.target.value }); }} style={{maxWidth: 160}} />
              </div>

              <div className="panel__toolbar-row">
                <input type="number" inputMode="decimal" step="1000000" placeholder="Oper. Cashflow ≥" value={filters.operating_cashflow_min}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, operating_cashflow_min: e.target.value }); }} style={{maxWidth: 200}} />
                <input type="number" inputMode="decimal" step="1000000" placeholder="Free Cashflow ≥" value={filters.free_cashflow_min}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, free_cashflow_min: e.target.value }); }} style={{maxWidth: 200}} />
                <input type="number" inputMode="decimal" step="1000000" placeholder="Eigenkapital ≥" value={filters.shareholders_equity_min}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, shareholders_equity_min: e.target.value }); }} style={{maxWidth: 200}} />
                <input type="number" inputMode="decimal" step="1000000" placeholder="Vermögenswerte ≥" value={filters.total_assets_min}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, total_assets_min: e.target.value }); }} style={{maxWidth: 200}} />
                <input type="number" inputMode="decimal" step="0.01" placeholder="Debt/Equity ≤" value={filters.debt_to_equity_max}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, debt_to_equity_max: e.target.value }); }} style={{maxWidth: 160}} />
                <input type="number" inputMode="decimal" step="1000000" placeholder="Verbindlichkeiten ≤" value={filters.total_liabilities_max}
                  onChange={(e)=>{ setPage(1); setFilters({ ...filters, total_liabilities_max: e.target.value }); }} style={{maxWidth: 200}} />
              </div>
            </div>
          )}
          <div className="panel__toolbar-row">
            <button className="btn btn--ghost" onClick={clearFilters}>Zurücksetzen</button>
          </div>
        </div>

        <div className="panel" style={{marginTop: '12px'}}>
          <div className="panel__title">Ergebnisse</div>
          {error && <div style={{ color: '#b91c1c', marginTop: '8px' }}>{error}</div>}
          {loading ? (
            <div style={{ padding: '16px', color: 'var(--text-muted)' }}>Laden …</div>
          ) : (
            <div
              ref={scrollRef}
              className={`scroll-shadow${hasLeftShadow ? ' has-left' : ''}${hasRightShadow ? ' has-right' : ''}`}
              style={{ overflowX: 'auto', marginTop: '12px' }}
            >
              <table className="table">
                <thead>
                  <tr>
                    <th role="button" onClick={() => toggleSort('ticker_symbol')}>Ticker {sort==='ticker_symbol' ? (order==='asc'?'▲':'▼') : ''}</th>
                    <th role="button" onClick={() => toggleSort('name')}>Name {sort==='name' ? (order==='asc'?'▲':'▼') : ''}</th>
                    <th role="button" onClick={() => toggleSort('country')}>Land {sort==='country' ? (order==='asc'?'▲':'▼') : ''}</th>
                    <th role="button" onClick={() => toggleSort('sector')}>Sektor {sort==='sector' ? (order==='asc'?'▲':'▼') : ''}</th>
                    <th role="button" onClick={() => toggleSort('industry')}>Industrie {sort==='industry' ? (order==='asc'?'▲':'▼') : ''}</th>
                    <th role="button" onClick={() => toggleSort('e_beta')}>β {sort==='e_beta' ? (order==='asc'?'▲':'▼') : ''}</th>
                    <th role="button" onClick={() => toggleSort('lf_profit_margin')}>Profit Margin {sort==='lf_profit_margin' ? (order==='asc'?'▲':'▼') : ''}</th>
                    <th role="button" onClick={() => toggleSort('lf_return_on_equity')}>ROE {sort==='lf_return_on_equity' ? (order==='asc'?'▲':'▼') : ''}</th>
                    <th role="button" onClick={() => toggleSort('lf_current_ratio')}>Current Ratio {sort==='lf_current_ratio' ? (order==='asc'?'▲':'▼') : ''}</th>
                  </tr>
                </thead>
                <tbody>
                  {results.length === 0 ? (
                    <tr><td colSpan={9} style={{ color: 'var(--text-muted)', padding: '16px' }}>Keine Ergebnisse</td></tr>
                  ) : (
                    results.map(row => (
                      <tr key={row.id}>
                        <td>{row.ticker_symbol}</td>
                        <td>{row.name}</td>
                        <td>{row.country || '-'}</td>
                        <td>{row.sector || '-'}</td>
                        <td>{row.industry || '-'}</td>
                        <td>{fmtNum(row.e_beta, 2)}</td>
                        <td>{fmtNum(row.lf_profit_margin, 2)}</td>
                        <td>{fmtNum(row.lf_return_on_equity, 2)}</td>
                        <td>{fmtNum(row.lf_current_ratio, 2)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button className="btn btn--ghost" disabled={page<=1} onClick={() => setPage(1)}>«</button>
                  <button className="btn btn--ghost" disabled={page<=1} onClick={() => setPage(p => Math.max(1, p-1))}>‹</button>
                  <span style={{ color: 'var(--text-muted)' }}>Seite {page} / {totalPages}</span>
                  <button className="btn btn--ghost" disabled={page>=totalPages} onClick={() => setPage(p => Math.min(totalPages, p+1))}>›</button>
                  <button className="btn btn--ghost" disabled={page>=totalPages} onClick={() => setPage(totalPages)}>»</button>
                </div>
                <div>
                  <select value={pageSize} onChange={(e)=>{ setPage(1); setPageSize(parseInt(e.target.value, 10)); }}>
                    {[10,25,50,100].map(ps => (<option key={ps} value={ps}>{ps} / Seite</option>))}
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScreenerView;

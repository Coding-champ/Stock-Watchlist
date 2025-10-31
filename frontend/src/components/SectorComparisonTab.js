import React, { useEffect, useState } from 'react';
import './SectorComparisonTab.css';
import API_BASE from '../config';
import { metricLabel } from '../utils/metricLabels';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, LineChart, Line } from 'recharts';

// helper to format large numbers in German style (use billions as default unit)
const formatLargeNumber = (value) => {
  if (value === null || value === undefined) return '-';
  const n = Number(value);
  if (!isFinite(n)) return '-';
  if (Math.abs(n) >= 1e9) {
    return (n / 1e9).toFixed(2) + ' Mrd.';
  }
  if (Math.abs(n) >= 1e6) {
    return (n / 1e6).toFixed(1) + ' Mio.';
  }
  return new Intl.NumberFormat('de-DE').format(n);
};

function PeersTooltip({ active, payload, label, metric }) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload || {};
  return (
    <div style={{ background: '#fff', padding: 8, border: '1px solid #e2e8f0', fontSize: 12 }}>
      <div style={{ fontWeight: 700 }}>{data.name}</div>
      <div>{metricLabel(metric)}: {metric === 'market_cap' ? formatLargeNumber(data.value) : (data.value == null ? '-' : data.value)}</div>
    </div>
  );
}



// Sector / industry comparison tab. Fetches peer group data and shows bar charts.
function SectorComparisonTab({ stockId }) {
  const [metric, setMetric] = useState('market_cap');
  const [by, setBy] = useState('sector');
  const [limit, setLimit] = useState(8);
  const [peers, setPeers] = useState(null);
  const [usedMock, setUsedMock] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [perfPeriod, setPerfPeriod] = useState('1m');
  const [compareMode, setCompareMode] = useState('absolute');
  const [stockPerf, setStockPerf] = useState(null);
  
  // fetch peers when inputs change
  useEffect(() => {
    if (!stockId) return;
    let mounted = true;
    setLoading(true);
    setError(null);
    const url = `${API_BASE}/stocks/${stockId}/peers?perf_period=${encodeURIComponent(perfPeriod)}&limit=${encodeURIComponent(limit)}&by=${encodeURIComponent(by)}&metric=${encodeURIComponent(metric)}`;
    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error('network');
        return r.json();
      })
      .then(data => {
        if (!mounted) return;
        setPeers(data.peers || []);
        setUsedMock(Boolean(data.mock));
      })
      .catch(err => {
        if (!mounted) return;
        setError('Fehler beim Laden der Vergleichsdaten');
        setPeers([]);
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });
    return () => { mounted = false; };
  }, [stockId, perfPeriod, limit, by, metric]);

  // compute selected stock performance for the chosen period (used by relative mode)
  useEffect(() => {
    if (!stockId) return;
    let mounted = true;
    setStockPerf(null);

    const now = new Date();
    const start = new Date(now.getTime());
    switch (perfPeriod) {
      case '1m': start.setMonth(start.getMonth() - 1); break;
      case '3m': start.setMonth(start.getMonth() - 3); break;
      case '6m': start.setMonth(start.getMonth() - 6); break;
      case '1y': start.setFullYear(start.getFullYear() - 1); break;
      case '3y': start.setFullYear(start.getFullYear() - 3); break;
      default: start.setMonth(start.getMonth() - 1); break;
    }
    const yyyy = start.getFullYear();
    const mm = String(start.getMonth() + 1).padStart(2, '0');
    const dd = String(start.getDate()).padStart(2, '0');
    const startDate = `${yyyy}-${mm}-${dd}`;

    const url = `${API_BASE}/stocks/${stockId}/price-history?start_date=${encodeURIComponent(startDate)}`;
    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error('network');
        return r.json();
      })
      .then(data => {
        if (!mounted) return;
        const series = data.price_series || data || [];
        if (!series || series.length < 2) {
          setStockPerf(null);
          return;
        }
        const first = Number(series[0].close);
        const last = Number(series[series.length - 1].close);
        if (!isFinite(first) || !isFinite(last) || first === 0) {
          setStockPerf(null);
          return;
        }
        const perf = ((last / first) - 1) * 100;
        setStockPerf(Number(perf.toFixed(2)));
      })
      .catch(() => {
        if (!mounted) return;
        setStockPerf(null);
      });
    return () => { mounted = false; };
  }, [stockId, perfPeriod]);

  // if user selected relative mode but we couldn't compute stockPerf, fallback to absolute
  useEffect(() => {
    if (compareMode === 'relative' && stockPerf == null) {
      setCompareMode('absolute');
    }
  }, [stockPerf, compareMode]);
 

  return (
    <div className="sector-comparison-tab">
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center', justifyContent: 'space-between' }}>
        <label>Vergleichsmetrik:</label>
        <select value={metric} onChange={(e) => setMetric(e.target.value)}>
          <option value="market_cap">Marktkapitalisierung</option>
          <option value="pe_ratio">KGV (P/E)</option>
          <option value="price_to_sales">P/S</option>
        </select>
        <label style={{ marginLeft: '8px' }}>Gruppieren nach:</label>
        <select value={by} onChange={(e) => setBy(e.target.value)}>
          <option value="sector">Sektor (Standard)</option>
          <option value="industry">Branche</option>
        </select>
        <label style={{ marginLeft: '8px' }}>Anzahl:</label>
        <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
          <option value={5}>5</option>
          <option value={8}>8</option>
          <option value={10}>10</option>
        </select>
        
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginLeft: 12 }}>
          <label>Zeitraum:</label>
          <select value={perfPeriod} onChange={(e) => setPerfPeriod(e.target.value)}>
            <option value="1m">1 Monat</option>
            <option value="3m">3 Monate</option>
            <option value="6m">6 Monate</option>
            <option value="1y">1 Jahr</option>
            <option value="3y">3 Jahre</option>
          </select>
          <label style={{ marginLeft: 8 }}>Vergleichsmodus:</label>
          <select value={compareMode} onChange={(e) => setCompareMode(e.target.value)}>
            <option value="absolute">Absolute Performance</option>
            <option value="relative" disabled={stockPerf == null}>Relativ zur Aktie</option>
          </select>
        </div>
      </div>
        </div>
        <div>
          {usedMock && <span className="mock-badge">Mockdaten</span>}
        </div>
      {loading && <div className="loading">Lade Vergleichsdaten...</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && peers && peers.length === 0 && (
        <div className="no-data">Keine Vergleichsdaten verfügbar.</div>
      )}
      {/* Performance line below chart */}
      {!loading && !error && peers && peers.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
            <div style={{ fontSize: 13, color: '#333', fontWeight: 600 }}>Peer Performance ({perfPeriod})</div>
            {compareMode === 'relative' && stockPerf == null && (
              <div style={{ fontSize: 12, color: '#666', marginLeft: 8 }}>Relativer Vergleich: Referenz-Performance nicht verfügbar</div>
            )}
          </div>
          <PerformanceLine peers={peers} mode={compareMode} stockPerf={stockPerf} perfPeriod={perfPeriod} />
        </div>
      )}

      {!loading && !error && peers && peers.length > 0 && (
        <div style={{ height: 320, display: 'flex', gap: 48, marginTop: 16 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={peers} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => metric === 'market_cap' ? formatLargeNumber(v) : v} />
                <YAxis type="category" dataKey="name" width={170} />
                <Tooltip content={<PeersTooltip metric={metric} />} />
                <Legend formatter={(v) => (metric === 'market_cap' ? 'Marktkapitalisierung' : v)} />
                <Bar dataKey="value" name={metricLabel(metric)} fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ width: 280, overflowY: 'auto' }} className="peer-list">
            {peers.map((p, idx) => {
              const perf = p.performance;
              const perfSign = perf == null ? null : (perf > 0 ? 'positive' : (perf < 0 ? 'negative' : 'neutral'));
              const stroke = perf > 0 ? '#2ecc71' : (perf < 0 ? '#e74c3c' : '#8884d8');
              return (
                <div key={p.ticker + idx} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '10px 8px', borderBottom: '1px solid #f0f0f0' }}>
                  <div style={{ flex: '0 0 140px' }}>
                    <div style={{ fontSize: 12, fontWeight: 600 }}>{p.name}</div>
                    <div style={{ fontSize: 11, color: '#666' }}>{p.ticker}</div>
                  </div>
                  <div style={{ flex: '1 1 auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ fontSize: 12, color: perfSign === 'positive' ? '#2ecc71' : (perfSign === 'negative' ? '#e74c3c' : '#333'), fontWeight: 700 }}>
                        {perf == null ? '-' : (perf > 0 ? `+${perf}%` : `${perf}%`)}
                      </div>
                    </div>
                    <div style={{ height: 48 }}>
                      {p.price_series && p.price_series.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={p.price_series} margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
                                <Line type="monotone" dataKey="close" stroke={stroke} dot={false} strokeWidth={2} />
                                <Tooltip content={<SparklineTooltip start={p.price_series[0]} end={p.price_series[p.price_series.length-1]} perf={p.performance} />} />
                              </LineChart>
                            </ResponsiveContainer>
                      ) : (
                        <div style={{ height: '100%', background: '#fafafa' }} />
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
    </div>
  );
}

function SparklineTooltip({ active, payload, label, start, end, perf }) {
  // Note: Recharts will pass in tooltip props; we also accept start/end/perf as props
  if (!active) return null;
  const startVal = start && start.close != null ? Number(start.close).toFixed(2) : '-';
  const endVal = end && end.close != null ? Number(end.close).toFixed(2) : '-';
  const perfVal = perf == null ? '-' : (perf > 0 ? `+${perf}%` : `${perf}%`);
  return (
    <div style={{ background: '#fff', padding: 8, border: '1px solid #e2e8f0', fontSize: 12 }}>
      <div>Start: {startVal}</div>
      <div>End: {endVal}</div>
      <div style={{ fontWeight: 700, marginTop: 4 }}>Perf: {perfVal}</div>
    </div>
  );
}

function PerformanceLine({ peers, mode = 'absolute', stockPerf = null }) {
  // Build items with performance values depending on mode; extract date range if available
  const items = (peers || []).map((p, i) => {
    const basePerf = p.performance != null ? Number(p.performance) : null;
    let perf = basePerf;
    if (mode === 'relative') {
      if (basePerf != null && stockPerf != null) {
        perf = Number((basePerf - stockPerf).toFixed(2));
      } else {
        perf = null;
      }
    }
    const firstDate = p.price_series && p.price_series.length ? p.price_series[0].date : null;
    const lastDate = p.price_series && p.price_series.length ? p.price_series[p.price_series.length - 1].date : null;
    return { id: `${p.ticker}-${i}`, ticker: p.ticker, name: p.name, perf, firstDate, lastDate };
  });
    const measured = items.filter(i => i.perf != null);
    // hover state for tooltip (must be declared unconditionally to satisfy hooks rule)
    const [hoverId, setHoverId] = useState(null);
    const wrapperRef = React.useRef(null);
    const labelRefs = React.useRef({});
    const [labelSideMap, setLabelSideMap] = useState({}); // id -> 'top'|'bottom'

    // compute clustered positions and maxAbs with useMemo so dependencies are stable
    const { clusters, maxAbs } = React.useMemo(() => {
      const vals = measured.map(i => i.perf);
      if (!vals.length) return { clusters: [], maxAbs: 0 };
      const min = Math.min(...vals);
      const max = Math.max(...vals);
      const _maxAbs = Math.max(Math.abs(min), Math.abs(max));
      const withPos = measured.map(i => ({ ...i, left: _maxAbs === 0 ? 50 : (50 + (i.perf / _maxAbs) * 50) }));
      const thresholdPercent = 3; // markers within 3% will cluster
      const sorted = withPos.slice().sort((a, b) => a.left - b.left);
      const _clusters = [];
      let current = null;
      for (const itm of sorted) {
        if (!current) {
          current = { lefts: [itm.left], items: [itm] };
          continue;
        }
        const lastLeft = current.lefts[current.lefts.length - 1];
        if (Math.abs(itm.left - lastLeft) <= thresholdPercent) {
          current.lefts.push(itm.left);
          current.items.push(itm);
        } else {
          _clusters.push(current);
          current = { lefts: [itm.left], items: [itm] };
        }
      }
      if (current) _clusters.push(current);
      return { clusters: _clusters, maxAbs: _maxAbs };
    }, [measured]);

    // After render, decide labelSides based on actual label widths and proximity to other labels
    React.useEffect(() => {
      try {
        const container = wrapperRef.current;
        if (!container) return;
        const cw = container.clientWidth || 1;

        // build display items corresponding to clusters
        const displays = clusters.map((c, ci) => {
          const clusterLeft = c.lefts.reduce((s, v) => s + v, 0) / c.lefts.length;
          const id = c.items.length === 1 ? c.items[0].id : `cluster-${ci}`;
          const el = labelRefs.current[id];
          let lw = 0;
          if (el && el.offsetWidth) lw = el.offsetWidth;
          else {
            const labelText = c.items.length === 1 ? `${c.items[0].name}` : `${c.items.length}×`;
            lw = Math.min(200, Math.max(40, labelText.length * 7 + 16));
          }
          const leftPx = (clusterLeft / 100) * cw;
          return { id, leftPx, lw };
        }).sort((a,b) => a.leftPx - b.leftPx);

        const occupiedTop = [];
        const occupiedBottom = [];
        const sides = {};

        function intersects(intervals, a,b) {
          for (const iv of intervals) {
            if (!(b < iv[0] || a > iv[1])) return true;
          }
          return false;
        }

        for (const d of displays) {
          const a = d.leftPx - d.lw/2;
          const b = d.leftPx + d.lw/2;
          const clampedA = Math.max(0, a);
          const clampedB = Math.min(cw, b);
          const topConflict = intersects(occupiedTop, clampedA, clampedB);
          const bottomConflict = intersects(occupiedBottom, clampedA, clampedB);
          if (!topConflict) {
            sides[d.id] = 'top';
            occupiedTop.push([clampedA, clampedB]);
          } else if (!bottomConflict) {
            sides[d.id] = 'bottom';
            occupiedBottom.push([clampedA, clampedB]);
          } else {
            const topOverlap = occupiedTop.reduce((s, iv) => s + Math.max(0, Math.min(iv[1], clampedB) - Math.max(iv[0], clampedA)), 0);
            const bottomOverlap = occupiedBottom.reduce((s, iv) => s + Math.max(0, Math.min(iv[1], clampedB) - Math.max(iv[0], clampedA)), 0);
            if (topOverlap <= bottomOverlap) {
              sides[d.id] = 'top';
              occupiedTop.push([clampedA, clampedB]);
            } else {
              sides[d.id] = 'bottom';
              occupiedBottom.push([clampedA, clampedB]);
            }
          }
        }

        setLabelSideMap(sides);
      } catch (e) {
        // ignore layout errors
      }
    }, [clusters]);

  if (!measured.length) {
    return <div className="performance-line-wrapper">Keine Performance-Daten für den ausgewählten Zeitraum.</div>;
  }

  return (
    <div ref={wrapperRef} className="performance-line-wrapper">
      <div className="performance-axis" />
      <div className="performance-markers">
        {clusters.map((c, ci) => {
          const clusterLeft = c.lefts.reduce((s, v) => s + v, 0) / c.lefts.length;
          const id = c.items.length === 1 ? c.items[0].id : `cluster-${ci}`;
          const labelTop = (labelSideMap[id] || 'bottom') === 'top';
          if (c.items.length === 1) {
            const it = c.items[0];
            const color = it.perf > 0 ? '#16a34a' : (it.perf < 0 ? '#dc2626' : '#374151');
            return (
              <div key={it.id} className={`perf-marker ${labelTop ? 'label-top' : ''}`} style={{ left: `${clusterLeft}%` }}
                onMouseEnter={() => setHoverId(it.id)} onMouseLeave={() => setHoverId(null)} title={`${it.name} (${it.ticker})`}>
                <div className="perf-dot" style={{ background: color }} />
                <div ref={el => labelRefs.current[it.id] = el} className="perf-label" style={{ color }}>{it.name} {it.perf > 0 ? `+${it.perf}%` : `${it.perf}%`}</div>
                {hoverId === it.id && (
                  <div className="perf-tooltip">
                    <div style={{ fontWeight: 700 }}>{it.name} ({it.ticker})</div>
                    <div>Performance: {it.perf > 0 ? `+${it.perf}%` : `${it.perf}%`}</div>
                    {(it.firstDate || it.lastDate) && <div style={{ fontSize: 12, color: '#666' }}>{it.firstDate || '-'} → {it.lastDate || '-'}</div>}
                  </div>
                )}
              </div>
            );
          }

          // cluster rendering
          const key = `cluster-${ci}`;
          const count = c.items.length;
          const averagePerf = (c.items.reduce((s, x) => s + x.perf, 0) / count).toFixed(2);
          return (
            <div key={key} className={`perf-cluster ${labelTop ? 'label-top' : ''}`} style={{ left: `${clusterLeft}%` }}
              onMouseEnter={() => setHoverId(key)} onMouseLeave={() => setHoverId(null)}>
              <div className="perf-dot" style={{ background: '#2563eb', width: 18, height: 18 }} />
              <div ref={el => labelRefs.current[key] = el} className="perf-label">{count}×</div>
              {hoverId === key && (
                <div className="perf-tooltip">
                  <div style={{ fontWeight: 700 }}>Cluster ({count}) — Ø {averagePerf}%</div>
                  <div style={{ marginTop: 6 }}>
                    {c.items.map(it => (
                      <div key={it.id} style={{ fontSize: 12, marginBottom: 4 }}>
                        <strong>{it.name}</strong> ({it.ticker}) — {it.perf > 0 ? `+${it.perf}%` : `${it.perf}%`}
                        {(it.firstDate || it.lastDate) && <div style={{ fontSize: 11, color: '#666' }}>{it.firstDate || '-'} → {it.lastDate || '-'}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div style={{ fontSize: 12, color: '#666', marginTop: 8 }}>Skala: -{maxAbs}% — +{maxAbs}%</div>
    </div>
  );
}

export default SectorComparisonTab;

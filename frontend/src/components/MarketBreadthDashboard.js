import React, { useMemo, useState } from 'react';
import { useBreadthSnapshot, useBreadthHistory } from '../hooks/useMarketBreadth';
import { AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar, Legend, BarChart, Bar } from 'recharts';

function MarketBreadthDashboard({ symbol, days: initialDays = 30 }) {
  const [historyDays, setHistoryDays] = useState(initialDays);
  const { data: snapshot, isLoading: snapLoading, error: snapError } = useBreadthSnapshot(symbol);
  const { data: history, isLoading: histLoading, error: histError } = useBreadthHistory(symbol, historyDays, true);

  const adSeries = useMemo(() => {
    const recs = history?.records || [];
    let cum = 0;
    return recs.map((r) => {
      const diff = (r.advancing || 0) - (r.declining || 0);
      cum += diff;
      return {
        date: r.date,
        adv: r.advancing,
        dec: r.declining,
        pctAdv: r.percentage_advancing,
        cumADLine: cum,
        newHighs: r.new_highs,
        newLows: r.new_lows,
      };
    });
  }, [history]);

  const gaugeValue = snapshot?.advance_decline?.percentage_advancing ?? null;
  const highs = snapshot?.new_highs_lows?.new_highs ?? null;
  const lows = snapshot?.new_highs_lows?.new_lows ?? null;

  return (
    <div className="breadth-dashboard" style={{ display:'grid', gridTemplateColumns:'1fr', gap: '16px' }}>
      {(snapLoading || histLoading) && <div>Lade Marktbreite…</div>}
      {(snapError || histError) && <div style={{ color:'var(--danger-color)' }}>Fehler beim Laden der Marktbreite.</div>}

      {/* Days selector */}
      <div style={{ display:'flex', gap:'8px', flexWrap:'wrap', marginBottom:'8px' }}>
        <div style={{ fontSize:'0.7rem', fontWeight:600, letterSpacing:'0.05em', textTransform:'uppercase' }}>Zeitraum:</div>
        {[30,60,90].map(d => (
          <button
            key={d}
            onClick={() => setHistoryDays(d)}
            style={{
              padding:'6px 12px',
              border:'1px solid var(--border-color)',
              background: historyDays === d ? 'var(--brand-primary-fade)' : 'var(--panel-bg)',
              color: historyDays === d ? 'var(--brand-primary-dark)' : 'inherit',
              borderRadius:6,
              cursor:'pointer',
              fontSize:'0.75rem',
              fontWeight: historyDays === d ? 600 : 400
            }}
          >{d} Tage</button>
        ))}
      </div>

      {/* A/D Line (cumulative) */}
      <div className="panel">
        <div className="panel__title-group">
          <div className="panel__eyebrow">Advance/Decline</div>
          <div className="panel__title">A/D-Linie (kumuliert · {historyDays} Tage)</div>
        </div>
        <div className="panel__body" style={{ height: 260 }}>
          <ResponsiveContainer>
            <AreaChart data={adSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#eee" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
              <YAxis tick={{ fontSize: 12 }} domain={['auto','auto']} />
              <Tooltip />
              <Area type="monotone" dataKey="cumADLine" stroke="#2563eb" fill="#bfdbfe" name="A/D kumuliert" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Current A/D Ratio Gauge */}
      <div className="panel">
        <div className="panel__title-group">
          <div className="panel__eyebrow">Aktuell</div>
          <div className="panel__title">A/D Verhältnis</div>
        </div>
        <div className="panel__body" style={{ display:'flex', alignItems:'center', gap:'24px' }}>
          <div style={{ width: 260, height: 200 }}>
            <ResponsiveContainer>
              <RadialBarChart innerRadius="60%" outerRadius="100%" data={[{ name: 'Adv', value: gaugeValue || 0 }]} startAngle={180} endAngle={0}>
                <RadialBar minAngle={15} clockWise dataKey="value" fill="#16a34a" background cornerRadius={6} />
                <Legend verticalAlign="bottom" height={36} formatter={() => `Advancing: ${gaugeValue != null ? gaugeValue.toFixed(1) + '%' : '—'}`} />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(2, minmax(120px, 1fr))', gap:'12px', flex: 1 }}>
            <div className="stat-card">
              <div className="stat-label">Steigend</div>
              <div className="stat-value">{snapshot?.advance_decline?.advancing ?? '—'}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Fallend</div>
              <div className="stat-value">{snapshot?.advance_decline?.declining ?? '—'}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Unverändert</div>
              <div className="stat-value">{snapshot?.advance_decline?.unchanged ?? '—'}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Abgedeckt</div>
              <div className="stat-value">{snapshot?.advance_decline?.total_count ?? '—'}</div>
            </div>
          </div>
        </div>
      </div>

      {/* New Highs vs Lows (multi-day history) */}
      <div className="panel">
        <div className="panel__title-group">
          <div className="panel__eyebrow">52W Extrema Verlauf</div>
          <div className="panel__title">Neue Hochs vs. Tiefs (letzte {historyDays} Tage)</div>
        </div>
        <div className="panel__body" style={{ height: 260 }}>
          <ResponsiveContainer>
            <BarChart data={adSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="newHighs" name="Neue Hochs" fill="#16a34a" stackId="extrema" />
              <Bar dataKey="newLows" name="Neue Tiefs" fill="#dc2626" stackId="extrema" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default MarketBreadthDashboard;
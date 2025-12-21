import React, { useMemo, useState } from 'react';
import { useBreadthSnapshotWithMode, useBreadthHistoryWithMode } from '../hooks/useMarketBreadth';
import { AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar, Legend, BarChart, Bar } from 'recharts';

function MarketBreadthDashboard({ symbol, days: initialDays = 30 }) {
  const [historyDays, setHistoryDays] = useState(initialDays);
  const [breadthMode, setBreadthMode] = useState('sma200');

  // McClellan is derived from the classic (close-to-close) A/D series.
  // We always fetch a dedicated classic+McClellan history for the oscillator chart,
  // while the rest of the section is driven by the selected mode.
  const mainMode = breadthMode === 'mcclellan' ? 'classic' : breadthMode;

  const { data: snapshot, isLoading: snapLoading, error: snapError } = useBreadthSnapshotWithMode(symbol, null, true, mainMode);
  const { data: history, isLoading: histLoading, error: histError } = useBreadthHistoryWithMode(symbol, historyDays, false, true, mainMode);
  const { data: mcclellanHistory, isLoading: mccLoading, error: mccError } = useBreadthHistoryWithMode(symbol, historyDays, true, true, 'classic');

  const recordsSeries = useMemo(() => {
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
        advDecDiff: diff,
      };
    });
  }, [history]);

  const mcclellanSeries = useMemo(() => {
    const recs = mcclellanHistory?.mcclellan_oscillator || [];
    return recs.map((r) => ({
      date: r.date,
      oscillator: r.oscillator,
      ema19: r.ema19,
      ema39: r.ema39,
      advDecDiff: r.adv_dec_diff,
    }));
  }, [mcclellanHistory]);

  const chartMode = mainMode;
  const topEyebrow = chartMode === 'sma200' ? 'Marktbreite (SMA200)' : 'A/D (klassisch)';
  const topTitle = chartMode === 'classic'
    ? `A/D-Linie (kumuliert ${historyDays} Tage)`
    : `Netto über SMA200 (kumuliert ${historyDays} Tage)`;

  const chartStroke = 'var(--brand-primary)';
  const chartFill = 'var(--brand-primary-light)';
  const chartGrid = 'var(--brand-border)';

  const gaugeTitle = chartMode === 'sma200' ? 'Anteil über SMA200' : 'A/D Verhältnis';

  const statLabels = chartMode === 'sma200'
    ? { adv: 'Über SMA200', dec: 'Unter SMA200', unch: 'Gleich SMA200', total: 'Abgedeckt' }
    : { adv: 'Steigend', dec: 'Fallend', unch: 'Unverändert', total: 'Abgedeckt' };

  const gaugeValue = snapshot?.advance_decline?.percentage_advancing ?? null;

  return (
    <div className="breadth-dashboard" style={{ display:'grid', gridTemplateColumns:'1fr', gap: '16px' }}>
      {(snapLoading || histLoading || mccLoading) && <div>Lade Marktbreite…</div>}
      {(snapError || histError || mccError) && <div style={{ color:'var(--danger-color)' }}>Fehler beim Laden der Marktbreite.</div>}

      {/* Controls */}
      <div style={{ display:'flex', gap:'12px', flexWrap:'wrap', marginBottom:'8px', alignItems:'center' }}>
        <div style={{ display:'flex', gap:'8px', flexWrap:'wrap', alignItems:'center' }}>
          <div style={{ fontSize:'0.7rem', fontWeight:600, letterSpacing:'0.05em', textTransform:'uppercase' }}>Modus:</div>
          {[{ key:'sma200', label:'SMA200-Breite' }, { key:'classic', label:'A/D (klassisch)' }].map(m => (
            <button
              key={m.key}
              onClick={() => setBreadthMode(m.key)}
              style={{
                padding:'6px 12px',
                border:'1px solid var(--brand-border)',
                background: breadthMode === m.key ? 'var(--brand-surface-muted)' : 'var(--brand-surface)',
                color: breadthMode === m.key ? 'var(--brand-primary-dark)' : 'inherit',
                borderRadius:6,
                cursor:'pointer',
                fontSize:'0.75rem',
                fontWeight: breadthMode === m.key ? 600 : 400
              }}
            >{m.label}</button>
          ))}
        </div>

        <div style={{ display:'flex', gap:'8px', flexWrap:'wrap', alignItems:'center' }}>
          <div style={{ fontSize:'0.7rem', fontWeight:600, letterSpacing:'0.05em', textTransform:'uppercase' }}>Zeitraum:</div>
          {[30,60,90].map(d => (
            <button
              key={d}
              onClick={() => setHistoryDays(d)}
              style={{
                padding:'6px 12px',
                border:'1px solid var(--brand-border)',
                background: historyDays === d ? 'var(--brand-surface-muted)' : 'var(--brand-surface)',
                color: historyDays === d ? 'var(--brand-primary-dark)' : 'inherit',
                borderRadius:6,
                cursor:'pointer',
                fontSize:'0.75rem',
                fontWeight: historyDays === d ? 600 : 400
              }}
            >{d} Tage</button>
          ))}
        </div>
      </div>

      {/* McClellan oscillator (separate top chart, always visible) */}
      <div className="panel">
        <div className="panel__title-group">
          <div className="panel__eyebrow">McClellan</div>
          <div className="panel__title">{`McClellan-Oszillator (${historyDays} Tage)`}</div>
        </div>
        <div className="panel__body" style={{ height: 260 }}>
          <ResponsiveContainer>
            <AreaChart
              data={mcclellanSeries}
              margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
            >
              <CartesianGrid stroke={chartGrid} strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
              <YAxis tick={{ fontSize: 12 }} domain={['auto','auto']} />
              <Tooltip />
              <Area type="monotone" dataKey="oscillator" stroke={chartStroke} fill={chartFill} name="McClellan" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Main breadth chart */}
      <div className="panel">
        <div className="panel__title-group">
          <div className="panel__eyebrow">{topEyebrow}</div>
          <div className="panel__title">{topTitle}</div>
        </div>
        <div className="panel__body" style={{ height: 260 }}>
          <ResponsiveContainer>
            <AreaChart
              data={recordsSeries}
              margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
            >
              <CartesianGrid stroke={chartGrid} strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
              <YAxis tick={{ fontSize: 12 }} domain={['auto','auto']} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="cumADLine"
                stroke={chartStroke}
                fill={chartFill}
                name={chartMode === 'classic' ? 'A/D kumuliert' : 'Kumuliert (Über − Unter SMA200)'}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Current A/D Ratio Gauge */}
      <div className="panel">
        <div className="panel__title-group">
          <div className="panel__eyebrow">Aktuell</div>
          <div className="panel__title">{gaugeTitle}</div>
        </div>
        <div className="panel__body" style={{ display:'flex', alignItems:'center', gap:'24px' }}>
          <div style={{ width: 260, height: 200 }}>
            <ResponsiveContainer>
              <RadialBarChart innerRadius="60%" outerRadius="100%" data={[{ name: 'Adv', value: gaugeValue || 0 }]} startAngle={180} endAngle={0}>
                <RadialBar minAngle={15} clockWise dataKey="value" fill="var(--brand-primary)" background cornerRadius={6} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={() => {
                    const pct = gaugeValue != null ? gaugeValue.toFixed(1) + '%' : '—';
                    return chartMode === 'sma200' ? `Über SMA200: ${pct}` : `Steigend: ${pct}`;
                  }}
                />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(2, minmax(120px, 1fr))', gap:'12px', flex: 1 }}>
            <div className="stat-card">
              <div className="stat-label">{statLabels.adv}</div>
              <div className="stat-value">{snapshot?.advance_decline?.advancing ?? '—'}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">{statLabels.dec}</div>
              <div className="stat-value">{snapshot?.advance_decline?.declining ?? '—'}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">{statLabels.unch}</div>
              <div className="stat-value">{snapshot?.advance_decline?.unchanged ?? '—'}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">{statLabels.total}</div>
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
            <BarChart data={recordsSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="newHighs" name="Neue Hochs" fill="var(--brand-primary)" stackId="extrema" />
              <Bar dataKey="newLows" name="Neue Tiefs" fill="var(--brand-secondary)" stackId="extrema" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default MarketBreadthDashboard;
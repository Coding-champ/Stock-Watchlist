import React, { useState, useMemo } from 'react';
import { useCorrelationMatrix } from '../hooks/useCorrelationMatrix';

// Simple continuous color scale from -1 (red) -> 0 (white) -> +1 (green)
function getColor(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '#ccc';
  const v = Math.max(-1, Math.min(1, value));
  if (v === 0) return '#ffffff';
  if (v < 0) {
    // interpolate red (#dc2626) -> white
    const t = (v + 1); // v=-1 => 0, v=0 => 1
    const r = Math.round(0xdc * t + 0xff * (1 - t));
    const g = Math.round(0x26 * t + 0xff * (1 - t));
    const b = Math.round(0x26 * t + 0xff * (1 - t));
    return `rgb(${r},${g},${b})`;
  }
  // v>0 interpolate white -> green (#16a34a)
  const t = v; // 0->0, 1->1
  const r = Math.round(0xff * (1 - t) + 0x16 * t);
  const g = Math.round(0xff * (1 - t) + 0xa3 * t);
  const b = Math.round(0xff * (1 - t) + 0x4a * t);
  return `rgb(${r},${g},${b})`;
}

function CorrelationHeatmap({ defaultSymbols = ['^GSPC','^IXIC','^GDAXI','^FTSE','^N225'], defaultPeriod='1y' }) {
  const [symbolsInput, setSymbolsInput] = useState(defaultSymbols.join(','));
  const [period, setPeriod] = useState(defaultPeriod);
  const symbols = useMemo(() => symbolsInput.split(',').map(s => s.trim()).filter(Boolean), [symbolsInput]);
  const { data, isLoading, error } = useCorrelationMatrix(symbols, period, true);

  const matrix = data?.matrix || [];
  const labels = data?.symbols || symbols;

  return (
    <div className="panel panel--heatmap">
      <div className="panel__header">
        <div className="panel__title-group">
          <h2 className="panel__title">Korrelationsmatrix</h2>
          <p className="panel__subtitle">Tägliche Rendite-Korrelationen · Zeitraum: {period}</p>
        </div>
      </div>
      <div className="panel__body">
        <div style={{ display:'flex', gap:'16px', flexWrap:'wrap', marginBottom:'16px' }}>
          <div style={{ flex:'1 1 260px', minWidth:220 }}>
            <label style={{ fontSize:'0.7rem', fontWeight:600, textTransform:'uppercase', letterSpacing:'0.05em' }}>Indizes (Komma-getrennt)</label>
            <input
              value={symbolsInput}
              onChange={e => setSymbolsInput(e.target.value)}
              style={{ width:'100%', padding:'8px 10px', border:'1px solid var(--border-color)', borderRadius:6 }}
              placeholder="^GSPC,^IXIC,^GDAXI"
            />
          </div>
          <div style={{ width:140 }}>
            <label style={{ fontSize:'0.7rem', fontWeight:600, textTransform:'uppercase', letterSpacing:'0.05em' }}>Zeitraum</label>
            <select
              value={period}
              onChange={e => setPeriod(e.target.value)}
              style={{ width:'100%', padding:'8px 10px', border:'1px solid var(--border-color)', borderRadius:6 }}
            >
              {['1mo','3mo','6mo','1y','2y','5y'].map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>

        {isLoading && <div>Lade Korrelationsdaten…</div>}
        {error && <div style={{ color:'var(--danger-color)' }}>Fehler: {String(error.message || error)}</div>}
        {data?.error && <div style={{ color:'var(--danger-color)' }}>{data.error}</div>}

        {!isLoading && !error && matrix.length > 0 && (
          <div style={{ overflowX:'auto' }}>
            <table style={{ borderCollapse:'collapse', minWidth: labels.length * 70 }}>
              <thead>
                <tr>
                  <th style={{ textAlign:'left', padding:'6px 8px', fontSize:'0.75rem' }}>Index</th>
                  {labels.map(l => (
                    <th key={l} style={{ padding:'6px 8px', fontSize:'0.7rem', writingMode:'vertical-rl', transform:'rotate(180deg)', whiteSpace:'nowrap' }}>{l}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {labels.map((rowLabel, i) => (
                  <tr key={rowLabel}>
                    <th style={{ textAlign:'left', padding:'6px 8px', fontSize:'0.7rem', whiteSpace:'nowrap' }}>{rowLabel}</th>
                    {labels.map((colLabel, j) => {
                      const val = matrix[i][j];
                      const color = getColor(val);
                      return (
                        <td
                          key={colLabel}
                          title={`${rowLabel} vs ${colLabel}: ${val?.toFixed(3)}`}
                          style={{
                            padding:0,
                            width:50,
                            height:50,
                            background: color,
                            border:'1px solid #fff',
                            position:'relative',
                            fontSize:'0.65rem',
                            textAlign:'center',
                            color: Math.abs(val) > 0.75 ? '#fff' : '#222',
                            fontWeight: Math.abs(val) > 0.85 ? 600 : 400
                          }}
                        >
                          {i===j ? '1.00' : (val!=null ? val.toFixed(2) : '—')}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ marginTop:'12px', fontSize:'0.7rem', color:'var(--text-muted)' }}>Grün = hohe positive Korrelation · Rot = hohe negative Korrelation · Weiß = neutral</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CorrelationHeatmap;
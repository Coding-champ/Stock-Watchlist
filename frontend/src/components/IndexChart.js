import React, { useState, useMemo, useRef, useEffect } from 'react';
import { useIndexChart } from '../hooks/useIndexChart';
import './IndexChart.css';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
  Area,
  ReferenceLine
} from 'recharts';

const PERIOD_OPTIONS = ['1M','3M','6M','1Y','3Y','5Y','MAX'];
const INTERVAL_OPTIONS = ['1d','1wk','1mo'];
const DEFAULT_INDICATORS = ['sma_50','sma_200','rsi','macd','bollinger'];
const BENCHMARK_OPTIONS = [
  { value: '', label: 'Kein Benchmark' },
  { value: '^GSPC', label: 'S&P 500 (^GSPC)' },
  { value: '^NDX', label: 'NASDAQ 100 (^NDX)' },
  { value: '^DJI', label: 'Dow Jones (^DJI)' },
  { value: '^GDAXI', label: 'DAX (^GDAXI)' }
];

function IndexChart({ tickerSymbol }) {
  const [period, setPeriod] = useState('1Y');
  const [interval, setInterval] = useState('1d');
  const [indicators, setIndicators] = useState(DEFAULT_INDICATORS);
  const [benchmarkOpen, setBenchmarkOpen] = useState(false);
  const [benchmark, setBenchmark] = useState(BENCHMARK_OPTIONS[0].value);
  const [showOutperformance, setShowOutperformance] = useState(true);
  const dropdownRef = useRef(null);

  // Map UI period to backend expected (lowercase, max etc.)
  const backendPeriod = useMemo(() => {
    const p = period.toLowerCase();
    if (p === 'max') return 'max';
    return p.replace('y','y').replace('m','mo'); // 1M->1mo, 3M->3mo etc.
  }, [period]);

  const { data, isLoading, error, friendlyError } = useIndexChart(tickerSymbol, backendPeriod, interval, indicators);
  const { data: benchmarkData, isLoading: benchmarkLoading, friendlyError: benchmarkError } = useIndexChart(
    benchmark || null,
    backendPeriod,
    interval,
    [] // no indicators for benchmark to save bandwidth
  );

  const chartRows = useMemo(() => {
    if (!data || !data.dates) return [];

    // Helper to canonicalize date (strip time/timezone) for alignment across feeds
    const canonicalDate = (raw) => {
      if (!raw) return raw;
      // Accept ISO, space-separated, etc. Take first 10 chars if possible
      if (typeof raw === 'string') {
        if (raw.length >= 10) return raw.slice(0,10);
        return raw;
      }
      return raw;
    };

    // Build benchmark map by canonical date if available
    const benchmarkMap = new Map();
    if (benchmark && benchmarkData && benchmarkData.dates && benchmarkData.close) {
      benchmarkData.dates.forEach((d, i) => {
        const key = canonicalDate(d);
        benchmarkMap.set(key, benchmarkData.close[i]);
      });
    }

    // Normalize both series for comparison (base to first value = 100)
    const primaryFirst = data.close[0];
    let benchmarkFirst = null;
    if (benchmark && benchmarkData && benchmarkData.close && benchmarkData.close.length > 0) {
      benchmarkFirst = benchmarkData.close[0];
    }

    return data.dates.map((d, i) => {
      const canon = canonicalDate(d);
      const row = {
        date: d, // keep original for tooltip
        open: data.open[i],
        high: data.high[i],
        low: data.low[i],
        close: data.close[i],
        volume: data.volume[i],
        sma_50: data.indicators?.sma_50 ? data.indicators.sma_50[i] : null,
        sma_200: data.indicators?.sma_200 ? data.indicators.sma_200[i] : null,
        rsi: data.indicators?.rsi ? data.indicators.rsi[i] : null,
        macd: data.indicators?.macd ? data.indicators.macd.macd[i] : null,
        macd_signal: data.indicators?.macd ? data.indicators.macd.signal[i] : null,
        macd_hist: data.indicators?.macd ? data.indicators.macd.hist[i] : null,
        bb_upper: data.indicators?.bollinger ? data.indicators.bollinger.upper[i] : null,
        bb_middle: data.indicators?.bollinger ? data.indicators.bollinger.middle[i] : null,
        bb_lower: data.indicators?.bollinger ? data.indicators.bollinger.lower[i] : null,
      };

      if (benchmark && benchmarkFirst) {
        let benchVal = null;
        if (benchmarkMap.has(canon)) {
          benchVal = benchmarkMap.get(canon);
        } else if (benchmarkData && benchmarkData.close && benchmarkData.close[i] != null) {
          // Fallback positional match if date strings differ (timezone / format discrepancies)
          benchVal = benchmarkData.close[i];
        }
        if (benchVal != null) {
          row.benchmark_normalized = (benchVal / benchmarkFirst) * 100;
          row.primary_normalized = (data.close[i] / primaryFirst) * 100;
          // Outperformance (Spread): positive => primary outperforms benchmark
          row.outperformance = row.primary_normalized - row.benchmark_normalized;
        }
      }
      return row;
    });
  }, [data, benchmark, benchmarkData]);

  const toggleIndicator = (name) => {
    setIndicators(prev => prev.includes(name) ? prev.filter(i => i !== name) : [...prev, name]);
  };
  
  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setBenchmarkOpen(false);
      }
    };
    if (benchmarkOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [benchmarkOpen]);

  return (
    <div className="index-chart-wrapper">
      <div className="index-chart-controls">
        <div className="segmented">
          {PERIOD_OPTIONS.map(p => (
            <button key={p} className={`segmented__btn ${period===p?'is-active':''}`} onClick={() => setPeriod(p)}>{p}</button>
          ))}
        </div>
        <div className="segmented" style={{marginLeft: '12px'}}>
          {INTERVAL_OPTIONS.map(iv => (
            <button key={iv} className={`segmented__btn ${interval===iv?'is-active':''}`} onClick={() => setInterval(iv)}>{iv}</button>
          ))}
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div className="custom-dropdown-container" style={{ minWidth: 220 }} ref={dropdownRef}>
            <button
              type="button"
              className={`custom-dropdown-toggle ${benchmarkOpen ? 'open' : ''}`}
              onClick={() => setBenchmarkOpen(!benchmarkOpen)}
            >
              <span className="dropdown-text">
                {BENCHMARK_OPTIONS.find(o => o.value === benchmark)?.label || 'Benchmark auswählen'}
              </span>
              <span className="dropdown-arrow">{benchmarkOpen ? '▲' : '▼'}</span>
            </button>
            {benchmarkOpen && (
              <div className="custom-dropdown-menu">
                {BENCHMARK_OPTIONS.map(opt => (
                  <div
                    key={opt.value || 'none'}
                    className="dropdown-item"
                    onClick={() => { setBenchmark(opt.value); setBenchmarkOpen(false); }}
                  >
                    <span>{opt.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="indicator-toggles" style={{ marginLeft: 0 }}>
            {['sma_50','sma_200','bollinger','rsi','macd'].map(ind => (
              <label key={ind} className={`indicator-toggle ${indicators.includes(ind)?'is-active':''}`}> 
                <input
                  type="checkbox"
                  checked={indicators.includes(ind)}
                  onChange={() => toggleIndicator(ind)}
                /> {ind.toUpperCase()}
              </label>
            ))}
            {benchmark && (
              <label className={`indicator-toggle ${showOutperformance ? 'is-active':''}`}> 
                <input
                  type="checkbox"
                  checked={showOutperformance}
                  onChange={() => setShowOutperformance(v => !v)}
                /> OUTPERF
              </label>
            )}
          </div>
        </div>
      </div>

      {(isLoading || (benchmark && benchmarkLoading)) && (
        <div className="chart-loading-skeleton">
          <div className="skeleton-bar" style={{width:'35%'}}></div>
          <div className="skeleton-bar" style={{width:'55%'}}></div>
          <div className="skeleton-rect" style={{height:160}}></div>
          <div className="skeleton-rect" style={{height:80}}></div>
        </div>
      )}
      {(friendlyError || benchmarkError) && !isLoading && !benchmarkLoading && (
        <div className="chart-error">
          {friendlyError || benchmarkError}
          <button className="retry-btn" onClick={() => window.location.reload()}>
            Neu laden
          </button>
        </div>
      )}

      {!isLoading && !friendlyError && chartRows.length > 0 && (
        <div className="chart-panels">
          {/* Price Panel */}
          <div className="chart-panel chart-panel--price">
            <ResponsiveContainer width="100%" height={360}>
              <LineChart data={chartRows} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" hide={chartRows.length > 120} />
                {/* Use normalized axis when benchmark is active */}
                {benchmark ? (
                  <>
                    <YAxis yAxisId="normalized" domain={['auto','auto']} label={{ value: 'Normalisiert (Basis=100)', angle: -90, position: 'insideLeft' }} />
                    <YAxis yAxisId="spread" orientation="right" domain={['auto','auto']} label={{ value: 'Outperformance %', angle: -90, position: 'insideRight' }} />
                  </>
                ) : (
                  <YAxis domain={['auto','auto']} />
                )}
                <Tooltip formatter={(v, n) => [v, n]} labelFormatter={(l) => l} />
                {/* Show normalized comparison if benchmark selected */}
                {benchmark ? (
                  <>
                    <ReferenceLine yAxisId={showOutperformance ? "spread" : "normalized"} y={showOutperformance ? 0 : 100} stroke="#000" strokeWidth={1} strokeOpacity={0.5} />
                    <Line 
                      yAxisId="normalized" 
                      type="monotone" 
                      dataKey="primary_normalized" 
                      stroke="#2563eb" 
                      dot={false} 
                      name={tickerSymbol} 
                      strokeWidth={2}
                      strokeDasharray={showOutperformance ? "5 3" : undefined}
                    />
                    <Line 
                      yAxisId="normalized" 
                      type="monotone" 
                      dataKey="benchmark_normalized" 
                      stroke="#dc2626" 
                      dot={false} 
                      name={BENCHMARK_OPTIONS.find(o => o.value === benchmark)?.label || 'Benchmark'} 
                      strokeWidth={2} 
                      strokeDasharray={showOutperformance ? "5 3" : "5 5"}
                    />
                    {showOutperformance && (
                      <>
                        <Area yAxisId="spread" type="monotone" dataKey="outperformance" name="Outperformance %" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.18} strokeWidth={3} />
                        <Line yAxisId="spread" type="monotone" dataKey="outperformance" stroke="#7c3aed" dot={false} name="Outperformance %" strokeWidth={3} />
                      </>
                    )}
                  </>
                ) : (
                  <>
                    <Line type="monotone" dataKey="close" stroke="#2563eb" dot={false} name="Close" />
                    {indicators.includes('sma_50') && <Line type="monotone" dataKey="sma_50" stroke="#16a34a" dot={false} name="SMA50" />}
                    {indicators.includes('sma_200') && <Line type="monotone" dataKey="sma_200" stroke="#9333ea" dot={false} name="SMA200" />}
                    {indicators.includes('bollinger') && (
                      <>
                        <Line type="monotone" dataKey="bb_upper" stroke="#f59e0b" dot={false} name="BB Upper" />
                        <Line type="monotone" dataKey="bb_middle" stroke="#fbbf24" dot={false} name="BB Mid" />
                        <Line type="monotone" dataKey="bb_lower" stroke="#f59e0b" dot={false} name="BB Lower" />
                      </>
                    )}
                  </>
                )}
                <Legend />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Volume Panel */}
          <div className="chart-panel chart-panel--volume">
            <ResponsiveContainer width="100%" height={120}>
              <BarChart data={chartRows}>
                <XAxis dataKey="date" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="volume" fill="#94a3b8" name="Vol" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* RSI Panel */}
            {indicators.includes('rsi') && (
              <div className="chart-panel chart-panel--rsi">
                <ResponsiveContainer width="100%" height={120}>
                  <LineChart data={chartRows}>
                    <XAxis dataKey="date" hide />
                    <YAxis domain={[0,100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="rsi" stroke="#dc2626" dot={false} name="RSI" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

          {/* MACD Panel */}
            {indicators.includes('macd') && (
              <div className="chart-panel chart-panel--macd">
                <ResponsiveContainer width="100%" height={160}>
                  <LineChart data={chartRows}>
                    <XAxis dataKey="date" hide />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="macd" stroke="#0d9488" dot={false} name="MACD" />
                    <Line type="monotone" dataKey="macd_signal" stroke="#0891b2" dot={false} name="Signal" />
                  </LineChart>
                </ResponsiveContainer>
                <ResponsiveContainer width="100%" height={80}>
                  <BarChart data={chartRows}>
                    <XAxis dataKey="date" hide />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="macd_hist" fill="#64748b" name="Histogram" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
        </div>
      )}

      {!isLoading && !friendlyError && chartRows.length === 0 && (
        <div className="chart-empty">Keine Chartdaten verfügbar.</div>
      )}
    </div>
  );
}

export default IndexChart;

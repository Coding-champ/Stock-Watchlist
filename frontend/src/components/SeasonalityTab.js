import React, { useEffect, useState, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import PropTypes from 'prop-types';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Legend
} from 'recharts';
import './SeasonalityTab.css';
import '../styles/skeletons.css';
import API_BASE from '../config';

function SeasonalityTab({ stockId }) {
  const [seasonality, setSeasonality] = useState([]);
  const [series, setSeries] = useState([]); // per-year series for plotting
  const [visibleSeriesKeys, setVisibleSeriesKeys] = useState(new Set()); // which year_{YYYY} keys are visible (also controls 'avg_trend')
  const [showLines, setShowLines] = useState(true);
  // Always hide future months by default; no toggle control required
  const hideFutureMonths = true;
  // current year daily OHLC kept server-side but not used in main chart currently
  const [selectedPeriod, setSelectedPeriod] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [availableYears, setAvailableYears] = useState(null);
  const [availableRange, setAvailableRange] = useState(null);
  const queryClient = useQueryClient();
  // when we detect the server has less history than 'all' default (15y), we may
  // force a one-time refetch using the actual available years to surface per-year series
  const [forcedYearsBack, setForcedYearsBack] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
  // Always send a valid years_back value; for 'all', use a sensible default (e.g., 15)
  // If forcedYearsBack is set we use that to trigger a single refetch with the
  // exact number of available years (so include_series can be true for <=10 years).
  const yearsBack = forcedYearsBack ? String(forcedYearsBack) : (selectedPeriod === 'all' ? '15' : selectedPeriod.replace('y', ''));
    const includeSeries = Number(yearsBack) <= 10;
    const url = `${API_BASE}/stocks/${stockId}/seasonality?years_back=${yearsBack}${includeSeries ? '&include_series=true' : ''}`;
    queryClient.fetchQuery(['api', url], async () => {
      const res = await fetch(url);
      if (!res.ok) {
        console.error('Seasonality fetch failed', { url, status: res.status });
        throw new Error(`API response not OK: ${res.status}`);
      }
      return res.json();
    }, { staleTime: 60000 })
    .then(data => {
        // Support two response shapes:
        // 1) { seasonality: [...], series: [...] }
        // 2) [...] (legacy)
        // If the API returns an object with metadata, capture it for UI hints
        if (!Array.isArray(data) && data) {
          if (Array.isArray(data.available_years)) setAvailableYears(data.available_years);
          if (data.available_range) setAvailableRange(data.available_range);
        }

        if (Array.isArray(data)) {
          setSeasonality(data);
          setSeries([]);
        } else if (data && Array.isArray(data.seasonality)) {
          setSeasonality(data.seasonality);
          setSeries(Array.isArray(data.series) ? data.series : []);
        } else {
          setSeasonality([]);
          setSeries([]);
          setError('Ungültige Saisonalitätsdaten vom Server');
        }
        setLoading(false);

        // If we requested the 'all' default but the server reports fewer available years
        // and those years are <= 10, force a one-time refetch using that exact years_back
        // so the per-year series can be included and plotted. Use forcedYearsBack to avoid loops.
        try {
          if (!forcedYearsBack && selectedPeriod === 'all' && data && Array.isArray(data.available_years)) {
            const availCount = data.available_years.length;
            if (availCount > 0 && availCount <= 10 && String(availCount) !== yearsBack) {
              // schedule a one-time refetch
              setForcedYearsBack(String(availCount));
            }
          }
        } catch (e) {
          // ignore any safety errors here
        }
      })
      .catch(err => {
        console.error('Error loading seasonality for', stockId, err);
        setError('Fehler beim Laden der Saisonalitätsdaten');
        setLoading(false);
      });
  }, [stockId, selectedPeriod, forcedYearsBack]);

  // initialize visible series keys whenever series updates
  useEffect(() => {
    const keys = new Set();
    if (Array.isArray(series) && series.length > 0) {
      series.slice(0, 10).forEach(s => keys.add(`year_${s.year}`));
    }
    // show average trend by default and control it via the legend like other series
    keys.add('avg_trend');
    setVisibleSeriesKeys(keys);
  }, [series]);

  // Format numbers as percent strings like +2.5% or -1.2% with locale awareness
  const formatPercent = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
    const num = Number(value);
    const sign = num > 0 ? '+' : '';
    // Use two decimal places for clarity
    return sign + new Intl.NumberFormat(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 }).format(num) + '%';
  };

  // Ensure chart data has numeric avg_return for recharts and keep month_name
  const chartData = useMemo(() => {
    if (!Array.isArray(seasonality)) return [];

    // map seasonality rows by month for quick lookup
    const byMonth = (seasonality || []).reduce((acc, row) => {
      acc[row.month] = row;
      return acc;
    }, {});

    // Build base chartData with avg_return and placeholders for year series
    const base = [];
    for (let m = 1; m <= 12; m++) {
      const row = byMonth[m] || {};
      base.push({
        month: m,
        month_name: row.month_name || new Date(0, m - 1).toLocaleString(undefined, { month: 'short' }),
        avg_return: row.avg_return === null || row.avg_return === undefined ? 0 : Number(row.avg_return),
        median_return: row.median_return === null || row.median_return === undefined ? null : Number(row.median_return),
        win_rate: row.win_rate === null || row.win_rate === undefined ? null : Number(row.win_rate),
        total_count: row.total_count === null || row.total_count === undefined ? null : row.total_count
      });
    }

    // If series available (per-year monthly closes), normalize and add year_{YYYY} fields
    if (Array.isArray(series) && series.length > 0) {
      const limited = series.slice(0, 10);
      const currentYear = new Date().getFullYear();
      const currentMonth = new Date().getMonth() + 1; // 1-12
      limited.forEach(s => {
        const yearKey = `year_${s.year}`;
        if (Array.isArray(s.monthly_closes) && s.monthly_closes.length >= 1) {
          const start = Number(s.monthly_closes[0]) || 0;
          for (let i = 0; i < 12; i++) {
            // For the current year, optionally hide future months (they haven't occurred yet)
            const monthIndex = i + 1;
            if (hideFutureMonths && Number(s.year) === currentYear && monthIndex > currentMonth) {
              base[i][yearKey] = null;
              continue;
            }

            const close = s.monthly_closes[i] === undefined || s.monthly_closes[i] === null ? null : Number(s.monthly_closes[i]);
            const norm = (start === 0 || close === null) ? null : ((close / start) - 1) * 100;
            base[i][yearKey] = Number.isFinite(norm) ? Number(norm.toFixed(2)) : null;
          }
        } else {
          for (let i = 0; i < 12; i++) base[i][yearKey] = null;
        }
      });
    }

    // If current year series with monthly_ohlc exists, add normalized OHLC fields to chartData
    if (Array.isArray(series) && series.length > 0) {
      const currentYear = new Date().getFullYear();
      const curr = series.find(s => Number(s.year) === currentYear) || null;
      if (curr && Array.isArray(curr.monthly_ohlc) && curr.monthly_ohlc.length >= 1) {
        const startClose = (curr.monthly_ohlc[0] && curr.monthly_ohlc[0].close) ? Number(curr.monthly_ohlc[0].close) : (curr.monthly_closes && curr.monthly_closes[0] ? Number(curr.monthly_closes[0]) : 0);
        for (let i = 0; i < 12; i++) {
          const mo = curr.monthly_ohlc[i] || { open: null, high: null, low: null, close: null };
          const o = mo.open === null || mo.open === undefined ? null : Number(mo.open);
          const h = mo.high === null || mo.high === undefined ? null : Number(mo.high);
          const l = mo.low === null || mo.low === undefined ? null : Number(mo.low);
          const c = mo.close === null || mo.close === undefined ? null : Number(mo.close);
          const norm = v => (startClose === 0 || v === null) ? null : ((v / startClose) - 1) * 100;
          base[i].current_open = Number.isFinite(norm(o)) ? Number(norm(o).toFixed(2)) : null;
          base[i].current_high = Number.isFinite(norm(h)) ? Number(norm(h).toFixed(2)) : null;
          base[i].current_low = Number.isFinite(norm(l)) ? Number(norm(l).toFixed(2)) : null;
          base[i].current_close = Number.isFinite(norm(c)) ? Number(norm(c).toFixed(2)) : null;
        }
      }
    }

    // compute avg_trend as cumulative average_return for display
    let cum = 0;
    base.forEach((b) => {
      cum += Number(b.avg_return) || 0;
      b.avg_trend = Number(cum.toFixed(2));
    });

    return base;
  }, [seasonality, series, hideFutureMonths]);

  // Compute Y axis domains and align zero position between left (bars) and right (lines)
  const { leftDomain, rightDomain, leftTicks, rightTicks } = useMemo(() => {
    // collect left values (avg_return) and right values (all year_*, current_*, avg_trend)
    const leftVals = [];
    const rightVals = [];
    chartData.forEach(row => {
      if (row.avg_return !== null && row.avg_return !== undefined && !Number.isNaN(Number(row.avg_return))) leftVals.push(Number(row.avg_return));
      Object.keys(row).forEach(k => {
        if (k === 'avg_return' || k === 'median_return' || k === 'month' || k === 'month_name' || k === 'win_rate' || k === 'total_count') return;
        const v = row[k];
        if (v !== null && v !== undefined && !Number.isNaN(Number(v))) {
          // treat year_*, avg_trend, current_* as right-axis values
          rightVals.push(Number(v));
        }
      });
    });

    const safeExtents = (arr) => {
      if (!arr || arr.length === 0) return [0, 1];
      let min = Math.min(...arr);
      let max = Math.max(...arr);
      if (min === max) {
        // expand a tiny bit
        const pad = Math.abs(min) * 0.05 || 1;
        min = min - pad;
        max = max + pad;
      }
      return [min, max];
    };

    let [lMin, lMax] = safeExtents(leftVals);
    let [rMin, rMax] = safeExtents(rightVals);

    // ensure zero is within each domain
    lMin = Math.min(lMin, 0);
    lMax = Math.max(lMax, 0);
    rMin = Math.min(rMin, 0);
    rMax = Math.max(rMax, 0);

    const frac = (min, max) => {
      if (max === min) return 0.5;
      return (0 - min) / (max - min);
    };

    const lFrac = frac(lMin, lMax);
    const rFrac = frac(rMin, rMax);

    // Try to expand right to match left fraction (so zero aligns)
    let newLMin = lMin, newLMax = lMax, newRMin = rMin, newRMax = rMax;
    if (lFrac > 0 && lFrac < 1) {
      // desired right max so that right fraction equals lFrac: (0 - rMin)/(newRMax - rMin) = lFrac
      const desiredRMax = rMin + (0 - rMin) / lFrac;
      if (desiredRMax >= rMax) {
        newRMax = desiredRMax;
      } else {
        // else expand left to match right fraction
        if (rFrac > 0 && rFrac < 1) {
          const desiredLMax = lMin + (0 - lMin) / rFrac;
          if (desiredLMax >= lMax) newLMax = desiredLMax;
          else {
            // fallback: symmetric around zero using max absolute
            const maxAbs = Math.max(Math.abs(lMin), Math.abs(lMax), Math.abs(rMin), Math.abs(rMax)) || 1;
            newLMin = -maxAbs; newLMax = maxAbs; newRMin = -maxAbs; newRMax = maxAbs;
          }
        } else {
          const maxAbs = Math.max(Math.abs(lMin), Math.abs(lMax), Math.abs(rMin), Math.abs(rMax)) || 1;
          newLMin = -maxAbs; newLMax = maxAbs; newRMin = -maxAbs; newRMax = maxAbs;
        }
      }
    } else {
      // if lFrac is 0 or 1 (zero at edge), fallback to symmetric padding
      const maxAbs = Math.max(Math.abs(lMin), Math.abs(lMax), Math.abs(rMin), Math.abs(rMax)) || 1;
      newLMin = -maxAbs; newLMax = maxAbs; newRMin = -maxAbs; newRMax = maxAbs;
    }

    // add small padding so lines don't sit on chart bounds
    const padDomain = (min, max) => {
      const range = max - min || Math.abs(min) || 1;
      const pad = range * 0.06; // 6% padding
      return [min - pad, max + pad];
    };

    const [finalLMin, finalLMax] = padDomain(newLMin, newLMax);
    const [finalRMin, finalRMax] = padDomain(newRMin, newRMax);

    // compute ticks ensuring 0 is present
    const computeTicks = (min, max, count = 5) => {
      if (min === max) return [min];

      // helper: choose a "nice" step ~ raw
      const niceStep = (raw) => {
        if (!isFinite(raw) || raw === 0) return 1;
        const p = Math.pow(10, Math.floor(Math.log10(raw)));
        const d = raw / p;
        let m = 1;
        if (d <= 1) m = 1;
        else if (d <= 2) m = 2;
        else if (d <= 2.5) m = 2.5;
        else if (d <= 5) m = 5;
        else m = 10;
        return m * p;
      };

      // If range does not cross zero, create ticks from min..max using nice step
      if (min >= 0 || max <= 0) {
        const rawStep = (max - min) / Math.max(1, count - 1);
        const step = niceStep(rawStep);
        // align start to multiple of step
        const start = Math.floor(min / step) * step;
        const ticks = [];
        for (let t = start; t <= max + 1e-12 && ticks.length < count + 2; t += step) {
          ticks.push(Number(t.toFixed(2)));
        }
        // trim or pad to count elements
        if (ticks.length > count) ticks.length = count;
        while (ticks.length < count) ticks.push(Number((ticks[ticks.length - 1] + step).toFixed(2)));
        return ticks;
      }

      // Range crosses zero: prefer symmetric ticks around zero and always include 0 explicitly
      const half = Math.floor((count - 1) / 2);
      const maxAbs = Math.max(Math.abs(min), Math.abs(max));
      const raw = maxAbs / Math.max(1, half);
      const step = niceStep(raw);
      const ticks = [];
      // build symmetric ticks centered on zero
      for (let i = -half; i <= half; i++) {
        ticks.push(Number((i * step).toFixed(2)));
      }
      // if we need one more tick (odd/even count), add on the positive side
      if (ticks.length < count) ticks.push(Number(((half + 1) * step).toFixed(2)));
      return ticks;
    };

  const TICK_COUNT = 9;
  let leftTicks = computeTicks(finalLMin, finalLMax, TICK_COUNT);
  let rightTicks = computeTicks(finalRMin, finalRMax, TICK_COUNT);

  // clamp ticks to domain bounds to avoid drawing ticks outside chart area
  leftTicks = leftTicks.filter(t => t >= finalLMin - 1e-8 && t <= finalLMax + 1e-8);
  rightTicks = rightTicks.filter(t => t >= finalRMin - 1e-8 && t <= finalRMax + 1e-8);

    return { leftDomain: [finalLMin, finalLMax], rightDomain: [finalRMin, finalRMax], leftTicks, rightTicks };
  }, [chartData]);

  // Daily chart data (kept for future Variante A); not currently used in the main chart.
  // If you later enable daily candles, re-enable this memo and the CustomCandle renderer.

  // helper: generate distinct, muted colors for year lines
  const colorForIndex = (i) => {
    const hue = (i * 40) % 360; // spread hues
    return `hsl(${hue} 60% 40%)`; // slightly darker
  };

  // Custom tooltip that hides values for series that are not visible
  const CustomTooltip = ({ active, payload, label, visibleSeriesKeys: visibleKeys }) => {
    if (!active || !payload || payload.length === 0) return null;

    // Filter payload: always show avg_return, show avg_trend only if it's visible in legend, show year_* only if visible
    const visibleItems = payload.filter(item => {
      const key = item.dataKey;
      // skip null/undefined values (e.g., future months)
      if (item.value === null || item.value === undefined) return false;
      if (!key) return true;
      if (key === 'avg_return') return true;
      if (key === 'avg_trend') return visibleKeys && visibleKeys.has('avg_trend');
      return visibleKeys && visibleKeys.has(key);
    });

    if (visibleItems.length === 0) return null;

    return (
      <div className="custom-tooltip">
        <div className="tooltip-label">{label}</div>
        <div className="tooltip-items">
          {visibleItems.map((it) => (
            <div key={it.dataKey || it.name} className="tooltip-row">
              <div className="tooltip-name" style={{ color: it.color || '#000' }}>{it.name || it.dataKey}</div>
              <div className="tooltip-value">{formatPercent(it.value)}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const periods = [
    { key: 'all', label: 'Gesamt' },
    { key: '5y', label: '5 Jahre' },
    { key: '10y', label: '10 Jahre' },
    { key: '15y', label: '15 Jahre' }
  ];

  // UI styles to approximate the design in the screenshot
  // Styles moved to SeasonalityTab.css

  // Defensive: only use reduce if seasonality is array and not empty
  const bestMonth = Array.isArray(seasonality) && seasonality.length > 0
    ? seasonality.reduce((prev, curr) => curr.avg_return > prev.avg_return ? curr : prev, seasonality[0])
    : null;
  const worstMonth = Array.isArray(seasonality) && seasonality.length > 0
    ? seasonality.reduce((prev, curr) => curr.avg_return < prev.avg_return ? curr : prev, seasonality[0])
    : null;

  return (
    <div className="seasonality-tab">
    <div className="periods-container">
        {periods.map(period => (
          <button
            key={period.key}
            onClick={() => setSelectedPeriod(period.key)}
            aria-pressed={selectedPeriod === period.key}
            aria-label={`Periode ${period.label} auswählen`}
            className={`btn ${selectedPeriod === period.key ? 'btn-active' : ''}`}
          >
            {period.label}
          </button>
        ))}
      </div>
      {/* show available history range if backend provided it */}
      {availableRange && (
        <div className="available-range" style={{ marginTop: 8, marginBottom: 8, fontSize: '0.9rem', color: '#555' }}>
          Verfügbare Historie: {availableRange.start} — {availableRange.end}
        </div>
      )}
      {forcedYearsBack && (
        <div className="available-range" style={{ marginTop: 4, marginBottom: 8, fontSize: '0.85rem', color: '#b07200' }}>
          Hinweis: Darstellung auf die vorhandenen {forcedYearsBack} Jahr(e) angepasst, damit Jahresreihen angezeigt werden.
        </div>
      )}
      {loading ? (
        <div className="loading" role="status" aria-live="polite">Lade Saisonalitätsdaten...</div>
      ) : error ? (
        <div className="error" role="alert" aria-live="assertive">{error}</div>
      ) : (
        <>
          <div className="summary-container">
            <div className="card best-card">
              <div className="small-label"><span className="emoji">↗️</span><div>Bester Monat</div></div>
              <div className="month">{bestMonth ? bestMonth.month_name : 'Keine Daten'}</div>
              <div className="avg">Durchschnitt: {bestMonth ? formatPercent(bestMonth.avg_return) : '-'}</div>
            </div>
            <div className="card worst-card">
              <div className="small-label"><span className="emoji">↘️</span><div>Schlechtester Monat</div></div>
              <div className="month">{worstMonth ? worstMonth.month_name : 'Keine Daten'}</div>
              <div className="avg">Durchschnitt: {worstMonth ? formatPercent(worstMonth.avg_return) : '-'}</div>
            </div>
          </div>

          {/* Chart showing average return per month */}
          <div className="seasonality-chart" aria-label="Saisonalität durchschnittliche Rendite pro Monat">
              <div className="chart-controls">
              {/* Average trend is toggled via the legend (avg_trend) like other series */}
              <button
                onClick={() => setShowLines(v => !v)}
                className={`btn ${showLines ? 'btn-active' : ''}`}
                aria-pressed={showLines}
              >
                {showLines ? 'Linien ausblenden' : 'Linien einblenden'}
              </button>
              {/* Future months are hidden by default (no toggle) */}
              {/* Candlestick toggle removed for now */}
            </div>
            <ResponsiveContainer width="100%" height={480}>
              <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 50 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month_name" angle={-40} textAnchor="end" interval={0} />
                {/* Left axis for bars (monthly returns) */}
                <YAxis yAxisId="left" domain={leftDomain} ticks={leftTicks} tickFormatter={val => formatPercent(val)} />
                {/* Right axis for lines (normalized series / avg trend) */}
                <YAxis yAxisId="right" domain={rightDomain} ticks={rightTicks} orientation="right" tickFormatter={val => formatPercent(val)} />
                {/* Bold zero reference line (same pixel Y for both axes because domains were aligned) */}
                <ReferenceLine y={0} stroke="#222" strokeWidth={3} strokeOpacity={0.95} />
                <Tooltip content={<CustomTooltip visibleSeriesKeys={visibleSeriesKeys} />} />
                <Legend verticalAlign="top" onClick={(evt) => {
                  // evt has payload.dataKey or payload.value depending on context
                  let key = null;
                  if (!evt) return;
                  if (evt.dataKey) key = evt.dataKey;
                  else if (evt.value) {
                    // legend value for year lines will be a string year; map to year_{YYYY}
                    if (evt.value === 'Durchschnitt' || evt.value === 'Average' || evt.value === 'avg_trend') key = 'avg_trend';
                    else key = `year_${evt.value}`;
                  }
                  if (!key) return;
                  setVisibleSeriesKeys(prev => {
                    const next = new Set(prev);
                    if (next.has(key)) next.delete(key); else next.add(key);
                    return next;
                  });
                }} />

                <Bar dataKey="avg_return" barSize={18} yAxisId="left">
                  {chartData.map((entry, idx) => (
                    <Cell key={`cell-${idx}`} fill={Number(entry.avg_return) > 0 ? '#4caf50' : '#e53935'} />
                  ))}
                </Bar>

                {/* Candles are temporarily removed */}

                {/* render up to 10 per-year lines if series present; highlight current year
                    Lines are always rendered; visibility is controlled via color/opactiy/dash so legend remains */}
                {showLines && Array.isArray(series) && series.slice(0, 10).map((s, i) => {
                  const key = `year_${s.year}`;
                  const visible = visibleSeriesKeys.has(key);
                  const currentYear = new Date().getFullYear();
                  const isCurrent = Number(s.year) === currentYear;
                  const baseStroke = isCurrent ? '#1565c0' : colorForIndex(i); // slightly darker blue for current year
                  const stroke = visible ? baseStroke : '#9e9e9e';
                  const strokeWidth = isCurrent ? (visible ? 3 : 1.5) : (visible ? 1.5 : 1.25);
                  const opacity = visible ? (isCurrent ? 0.95 : 0.45) : 0.28;
                  const dash = visible ? undefined : '4 4';

                  return (
                    <Line
                      key={`line-${s.year}`}
                      type="monotone"
                      dataKey={key}
                      stroke={stroke}
                      strokeWidth={strokeWidth}
                      opacity={opacity}
                      dot={false}
                      name={isCurrent ? `${s.year} (aktuell)` : String(s.year)}
                      yAxisId="right"
                      strokeDasharray={dash}
                    />
                  );
                })}

                {/* average trend line: always render but hide/grey via legend state so the legend entry remains */}
                <Line
                  type="monotone"
                  dataKey="avg_trend"
                  stroke={visibleSeriesKeys.has('avg_trend') ? '#111' : '#9e9e9e'}
                  strokeWidth={visibleSeriesKeys.has('avg_trend') ? 3 : 1.5}
                  dot={false}
                  name="Durchschnitt"
                  yAxisId="right"
                  opacity={visibleSeriesKeys.has('avg_trend') ? 1 : 0.28}
                  strokeDasharray={visibleSeriesKeys.has('avg_trend') ? undefined : '4 4'}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="table-container">
            <table className="seasonality-table">
              <thead>
                <tr>
                  <th>Monat</th>
                  <th>Ø Return</th>
                  <th>Median</th>
                  <th>Win Rate</th>
                  <th>Anzahl</th>
                </tr>
              </thead>
              <tbody>
                {seasonality.map((row, idx) => (
                  <tr key={row.month}>
                    <td className="month-name">{row.month_name}</td>
                    {/* Emphasize large moves (abs >= 5%) */}
                    {(() => {
                      // Determine numeric values; treat null/undefined/NaN as missing
                      const avgRaw = row.avg_return;
                      const medRaw = row.median_return;

                      const avg = (avgRaw === null || avgRaw === undefined || Number.isNaN(Number(avgRaw))) ? null : Number(avgRaw);
                      const med = (medRaw === null || medRaw === undefined || Number.isNaN(Number(medRaw))) ? null : Number(medRaw);

                      const avgEmph = avg !== null && Math.abs(avg) >= 5;
                      const medEmph = med !== null && Math.abs(med) >= 5;

                      const avgPolarity = avg === null ? 'value-neutral' : (avg > 0 ? 'value-pos' : (avg < 0 ? 'value-neg' : 'value-neutral'));
                      const medPolarity = med === null ? 'value-neutral' : (med > 0 ? 'value-pos' : (med < 0 ? 'value-neg' : 'value-neutral'));

                      const avgClass = `value-cell ${avgPolarity} ${avgEmph ? 'value-emph' : ''}`;
                      const medClass = `value-cell ${medPolarity} ${medEmph ? 'value-emph' : ''}`;

                      return (
                        <>
                          <td className={avgClass}>{avg === null ? '-' : formatPercent(avg)}</td>
                          <td className={medClass}>{med === null ? '-' : formatPercent(med)}</td>
                        </>
                      );
                    })()}
                    <td>
                      {row.win_rate === null || row.win_rate === undefined ? '-' : (
                        (() => {
                          const wr = Number(row.win_rate);
                          const cls = wr >= 70 ? 'win-pill win-pill--high' : wr >= 50 ? 'win-pill win-pill--mid' : 'win-pill win-pill--low';
                          return <span className={cls}>{`${wr}%`}</span>;
                        })()
                      )}
                    </td>
                    <td className="count-cell">{row.total_count ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

SeasonalityTab.propTypes = {
  stockId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired
};

export default SeasonalityTab;

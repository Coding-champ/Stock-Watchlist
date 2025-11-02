import React, { useEffect, useState } from 'react';
import './FundamentalsTimeSeriesTab.css';
import '../styles/skeletons.css';
import API_BASE from '../config';
import { formatNumber } from '../utils/currencyUtils';
import { metricLabel } from '../utils/metricLabels';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine
} from 'recharts';

// Human-readable metric labels
  

// Simple fundamentals time series tab.
// Fetches time-series for selected metric and renders a line chart.
function FundamentalsTimeSeriesTab({ stockId }) {
  const [metric, setMetric] = useState('pe_ratio');
  const [period, setPeriod] = useState('3y');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [usedMock, setUsedMock] = useState(false);

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Endpoint to be implemented on backend. For now the UI expects an array of { date, value }
        const resp = await fetch(`${API_BASE}/stocks/${stockId}/fundamentals/timeseries?metric=${metric}&period=${period}`);
        if (!resp.ok) {
          throw new Error('Fehler beim Laden der Zeitreihe');
        }
        const json = await resp.json();
        // Expecting { series: [{ date: 'YYYY-MM-DD', value: 12.3 }, ...], used_mock: bool }
        const rawSeries = json.series || [];
        // Format dates similar to StockChart (locale de-DE)
        const formatDateLabel = (dateStr) => {
          try {
            const d = new Date(dateStr);
            const includeYear = period === '1y' || period === '3y' || period === '5y';
            return d.toLocaleDateString('de-DE', { month: 'short', day: 'numeric', ...(includeYear ? { year: '2-digit' } : {}) });
          } catch (e) {
            return dateStr;
          }
        };

        const mapped = rawSeries.map((r) => ({ date: formatDateLabel(r.date), value: r.value }));
        if (mounted) {
          setData(mapped);
          setUsedMock(Boolean(json.used_mock));
        }
      } catch (e) {
        console.error('FundamentalsTimeSeriesTab fetch error', e);
        if (mounted) setError(e.message || 'Fehler');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchData();
    return () => { mounted = false; };
  }, [stockId, metric, period]);

  

  return (
    <div className="fundamentals-timeseries-tab">
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <label>Kennzahl:</label>
        <select value={metric} onChange={(e) => setMetric(e.target.value)}>
          <option value="pe_ratio">KGV (P/E)</option>
          <option value="price_to_sales">P/S</option>
          <option value="ev_ebit">EV/EBIT</option>
          <option value="price_to_book">P/B</option>
        </select>

        <label style={{ marginLeft: '12px' }}>Zeitraum:</label>
        <select value={period} onChange={(e) => setPeriod(e.target.value)}>
          <option value="1y">1 Jahr</option>
          <option value="3y">3 Jahre</option>
          <option value="5y">5 Jahre</option>
        </select>
        </div>
        <div>
          {usedMock && <span className="mock-badge">Mockdaten</span>}
        </div>
      </div>

  {loading && <div className="loading">Lade Daten...</div>}
  {error && <div className="error">{error}</div>}

      {!loading && !error && data && data.length === 0 && (
        <div className="no-data">Keine Daten für die gewählte Kennzahl verfügbar.</div>
      )}

      {!loading && !error && data && data.length > 0 && (
        <div style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={true} />
              <Tooltip content={<CustomTooltip metric={metric} />} />
              <Legend />
              {(() => {
                // compute mean of numeric values (always visible)
                const nums = data.map(d => Number(d.value)).filter(v => !Number.isNaN(v) && isFinite(v));
                const mean = nums.length ? nums.reduce((a,b) => a + b, 0) / nums.length : null;
                return mean !== null ? <ReferenceLine y={mean} stroke="#ff9800" strokeDasharray="3 3" label={{ value: 'Mittelwert', position: 'right' }} /> : null;
              })()}
              <Line type="monotone" dataKey="value" name={metricLabel(metric)} stroke="#2a6edb" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function CustomTooltip({ active, payload, label, metric }) {
  if (!active || !payload || !payload.length) return null;
  const val = payload[0].value;
  return (
    <div className="recharts-tooltip-wrapper" style={{ background: '#fff', padding: 8, border: '1px solid #e2e8f0' }}>
      <div style={{ fontSize: '0.9rem', marginBottom: 4 }}>{label}</div>
      <div style={{ fontWeight: 600 }}>{metricLabel(metric)}: {formatNumber(Number(val), 2)}</div>
    </div>
  );
}

export default FundamentalsTimeSeriesTab;

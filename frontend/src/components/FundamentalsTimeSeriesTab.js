import React, { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import './FundamentalsTimeSeriesTab.css';
import API_BASE from '../config';
import { formatNumber } from '../utils/currencyUtils';
import { metricLabel } from '../utils/metricLabels';
import {
  Bar,
  BarChart,
  Legend,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

const FINANCIAL_GROUPS = [
  {
    key: 'income',
    label: 'GuV',
    metrics: ['revenue', 'operating_income', 'earnings', 'gross_profit', 'ebitda']
  },
  {
    key: 'balance',
    label: 'Bilanz',
    metrics: ['total_assets', 'shareholders_equity', 'total_liabilities']
  },
  {
    key: 'cashflow',
    label: 'Cashflow',
    metrics: ['operating_cashflow', 'free_cashflow']
  }
];

const DEFAULT_FINANCIAL_METRICS = 
      ['revenue', 'operating_income', 'earnings',
        'total_assets', 'shareholders_equity', 'total_liabilities',
        'operating_cashflow', 'free_cashflow'];
const BAR_COLORS = ['#2a6edb', '#e67e22', '#2ca02c', '#9467bd', '#d62728'];

function FundamentalsTimeSeriesTab({ stockId }) {
  const [valuationMetric, setValuationMetric] = useState('pe_ratio');
  const [valuationPeriod, setValuationPeriod] = useState('5y');
  const [valuationData, setValuationData] = useState(null);
  const [valuationLoading, setValuationLoading] = useState(false);
  const [valuationError, setValuationError] = useState(null);
  const [financialFrequency, setFinancialFrequency] = useState('annual');
  const [financialPeriod, setFinancialPeriod] = useState('5y');
  const [selectedMetrics, setSelectedMetrics] = useState(DEFAULT_FINANCIAL_METRICS);
  const [financialData, setFinancialData] = useState(null);
  const [financialLoading, setFinancialLoading] = useState(false);
  const [financialError, setFinancialError] = useState(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    let mounted = true;
    const fetchValuationData = async () => {
      setValuationLoading(true);
      setValuationError(null);
      try {
        const params = new URLSearchParams({
          metric: valuationMetric,
          period: valuationPeriod
        });
        const url = `${API_BASE}/stocks/${stockId}/fundamentals/timeseries?${params}`;
        const json = await queryClient.fetchQuery(['api', url], async () => {
          const response = await fetch(url);
          if (!response.ok) throw new Error('Fehler beim Laden der Bewertungszeitreihe');
          return response.json();
        }, { staleTime: 60000 });
        if (mounted) {
          setValuationData((json.series || []).map((item) => ({
            date: formatDate(item.date, valuationPeriod),
            value: item.value
          })));
        }
      } catch (error) {
        if (mounted) setValuationError(error.message || 'Fehler');
      } finally {
        if (mounted) setValuationLoading(false);
      }
    };

    fetchValuationData();
    return () => { mounted = false; };
  }, [stockId, valuationMetric, valuationPeriod, queryClient]);

  useEffect(() => {
    let mounted = true;
    const fetchFinancialData = async () => {
      if (!selectedMetrics.length) {
        setFinancialData({ series: [] });
        return;
      }
      setFinancialLoading(true);
      setFinancialError(null);
      try {
        const params = new URLSearchParams({
          metrics: selectedMetrics.join(','),
          frequency: financialFrequency,
          period: financialPeriod
        });
        const url = `${API_BASE}/stocks/${stockId}/fundamentals/timeseries?${params}`;
        const json = await queryClient.fetchQuery(['api', url], async () => {
          const response = await fetch(url);
          if (!response.ok) throw new Error('Fehler beim Laden der Finanzkennzahlen');
          return response.json();
        }, { staleTime: 60000 });
        if (mounted) setFinancialData(json);
      } catch (error) {
        if (mounted) setFinancialError(error.message || 'Fehler');
      } finally {
        if (mounted) setFinancialLoading(false);
      }
    };

    fetchFinancialData();
    return () => { mounted = false; };
  }, [stockId, financialFrequency, financialPeriod, selectedMetrics, queryClient]);

  const financialSeries = useMemo(
    () => (financialData?.series || []).map((item) => ({
      ...item.values,
      date: formatDate(item.date, financialFrequency === 'annual' ? '5y' : '1y')
    })),
    [financialData, financialFrequency]
  );

  const toggleMetric = (metric) => {
    setSelectedMetrics((current) => (
      current.includes(metric)
        ? current.filter((item) => item !== metric)
        : [...current, metric]
    ));
  };

  return (
    <div className="fundamentals-timeseries-tab">
      <section className="fundamentals-timeseries-section">
        <h3>Bewertungskennzahlen</h3>
        <div className="timeseries-controls">
          <label>Kennzahl:</label>
          <select value={valuationMetric} onChange={(event) => setValuationMetric(event.target.value)}>
            <option value="pe_ratio">KGV (P/E)</option>
            <option value="price_to_sales">P/S</option>
            <option value="ev_ebit">EV/EBIT</option>
            <option value="price_to_book">P/B</option>
          </select>
          <label>Zeitraum:</label>
          <select value={valuationPeriod} onChange={(event) => setValuationPeriod(event.target.value)}>
            <option value="3y">3 Jahre</option>
            <option value="5y">5 Jahre</option>
            <option value="10y">10 Jahre</option>
          </select>
        </div>
        <ValuationChart data={valuationData} metric={valuationMetric} loading={valuationLoading} error={valuationError} />
      </section>

      <section className="fundamentals-timeseries-section">
        <h3>Finanzkennzahlen</h3>
        <div className="timeseries-controls">
          <label>Darstellung:</label>
          <select value={financialFrequency} onChange={(event) => setFinancialFrequency(event.target.value)}>
            <option value="annual">Jährlich</option>
            <option value="quarterly">Quartal</option>
          </select>
          <label>Zeitraum:</label>
          <select
            value={financialPeriod}
            onChange={(event) => setFinancialPeriod(event.target.value)}
            disabled={financialFrequency === 'quarterly'}
          >
            <option value="3y">3 Jahre</option>
            <option value="5y">5 Jahre</option>
            <option value="10y">10 Jahre</option>
          </select>
          {financialFrequency === 'quarterly' && <span className="control-hint">letzte 5 Quartale</span>}
        </div>

        <div className="metric-selection">
          {FINANCIAL_GROUPS.map((group) => (
            <fieldset key={group.key}>
              <legend>{group.label}</legend>
              {group.metrics.map((metric) => (
                <label key={metric}>
                  <input
                    type="checkbox"
                    checked={selectedMetrics.includes(metric)}
                    onChange={() => toggleMetric(metric)}
                  />
                  {metricLabel(metric)}
                </label>
              ))}
            </fieldset>
          ))}
        </div>

        {financialLoading && <div className="loading">Lade Finanzkennzahlen...</div>}
        {financialError && <div className="error">{financialError}</div>}
        {!financialLoading && !financialError && !financialSeries.length && (
          <div className="no-data">
            Keine Finanzkennzahlen für die gewählte Darstellung verfügbar.
          </div>
        )}
        {!financialLoading && !financialError && financialSeries.length > 0 && (
          <div className="financial-charts">
            {FINANCIAL_GROUPS.map((group) => {
              const metrics = group.metrics.filter((metric) => selectedMetrics.includes(metric));
              if (!metrics.length) return null;
              return (
                <FinancialChart
                  key={group.key}
                  title={group.label}
                  data={financialSeries}
                  metrics={metrics}
                />
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function ValuationChart({ data, metric, loading, error }) {
  if (loading) return <div className="loading">Lade Daten...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!data || !data.length) return <div className="no-data">Keine Bewertungsdaten verfügbar.</div>;
  return (
    <div className="timeseries-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="date" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
          <YAxis />
          <Tooltip content={<ValueTooltip metrics={[metric]} />} />
          <Legend />
          <Line type="monotone" dataKey="value" name={metricLabel(metric)} stroke="#2a6edb" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function FinancialChart({ title, data, metrics }) {
  return (
    <div className="financial-chart">
      <h4>{title}</h4>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={data}
          barGap={8}
          barCategoryGap="10%"
          barSize={55}
          margin={{ top: 28, right: 12, bottom: 8, left: 12 }}
        >
          <XAxis dataKey="date" tick={{ fontSize: 13 }} axisLine={false} tickLine={false} />
          <Tooltip content={<ValueTooltip metrics={metrics} />} />
          <Legend itemSorter={(item) => metrics.indexOf(item.dataKey)} />
          {metrics.map((metric, index) => (
            <Bar
              key={metric}
              dataKey={metric}
              name={metricLabel(metric)}
              fill={BAR_COLORS[index % BAR_COLORS.length]}
              radius={[6, 6, 0, 0]}
            >
              <LabelList
                dataKey={metric}
                position="top"
                formatter={formatCompactValue}
                style={{ fontSize: 12, fill: '#334155' }}
              />
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function ValueTooltip({ active, payload, label, metrics }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip__date">{label}</div>
      {metrics.map((metric) => {
        const item = payload.find((entry) => entry.dataKey === metric);
        return item && item.value !== null && item.value !== undefined ? (
          <div key={metric}>{metricLabel(metric)}: {formatNumber(Number(item.value), 2)}</div>
        ) : null;
      })}
    </div>
  );
}

function formatDate(dateString, period) {
  const date = new Date(dateString);
  return date.toLocaleDateString('de-DE', {
    year: 'numeric',
    ...(period === '1y' ? { month: 'short', day: 'numeric' } : {})
  });
}

function formatCompactValue(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '';
  const absolute = Math.abs(number);
  if (absolute >= 1e9) return `${(number / 1e9).toFixed(1)} Mrd.`;
  if (absolute >= 1e6) return `${(number / 1e6).toFixed(1)} Mio.`;
  return number.toLocaleString('de-DE', { maximumFractionDigits: 0 });
}

export default FundamentalsTimeSeriesTab;

import React, { useEffect, useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

function SeasonalityTab({ stockId }) {
  const [seasonality, setSeasonality] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    // Always send a valid years_back value; for 'all', use a sensible default (e.g., 15)
    const yearsBack = selectedPeriod === 'all' ? '15' : selectedPeriod.replace('y', '');
    fetch(`/api/stocks/${stockId}/seasonality?years_back=${yearsBack}`)
      .then(res => {
        if (!res.ok) {
          throw new Error('API response not OK');
        }
        return res.json();
      })
      .then(data => {
        // Defensive: ensure data is array
        if (Array.isArray(data)) {
          setSeasonality(data);
        } else {
          setSeasonality([]);
          setError('Ungültige Saisonalitätsdaten vom Server');
        }
        setLoading(false);
      })
      .catch(err => {
        setError('Fehler beim Laden der Saisonalitätsdaten');
        setLoading(false);
      });
  }, [stockId, selectedPeriod]);

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
    return seasonality.map(row => ({
      ...row,
      avg_return: row.avg_return === null || row.avg_return === undefined ? 0 : Number(row.avg_return)
    }));
  }, [seasonality]);

  const periods = [
    { key: 'all', label: 'Gesamt' },
    { key: '5y', label: '5 Jahre' },
    { key: '10y', label: '10 Jahre' },
    { key: '15y', label: '15 Jahre' }
  ];

  // Defensive: only use reduce if seasonality is array and not empty
  const bestMonth = Array.isArray(seasonality) && seasonality.length > 0
    ? seasonality.reduce((prev, curr) => curr.avg_return > prev.avg_return ? curr : prev, seasonality[0])
    : null;
  const worstMonth = Array.isArray(seasonality) && seasonality.length > 0
    ? seasonality.reduce((prev, curr) => curr.avg_return < prev.avg_return ? curr : prev, seasonality[0])
    : null;

  return (
    <div className="seasonality-tab">
      <div className="period-selector">
        {periods.map(period => (
          <button
            key={period.key}
            className={`period-btn${selectedPeriod === period.key ? ' active' : ''}`}
            onClick={() => setSelectedPeriod(period.key)}
            aria-pressed={selectedPeriod === period.key}
            aria-label={`Periode ${period.label} auswählen`}
          >
            {period.label}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="loading" role="status" aria-live="polite">Lade Saisonalitätsdaten...</div>
      ) : error ? (
        <div className="error" role="alert" aria-live="assertive">{error}</div>
      ) : (
        <>
          <div className="summary-cards">
            <div className="summary-card best">
              <span role="img" aria-label="Bester Monat">📈</span>
              <div>Bester Monat: <strong>{bestMonth ? bestMonth.month_name : 'Keine Daten'}</strong></div>
              <div>Ø Return: {bestMonth ? formatPercent(bestMonth.avg_return) : '-'}</div>
            </div>
            <div className="summary-card worst">
              <span role="img" aria-label="Schlechtester Monat">📉</span>
              <div>Schlechtester Monat: <strong>{worstMonth ? worstMonth.month_name : 'Keine Daten'}</strong></div>
              <div>Ø Return: {worstMonth ? formatPercent(worstMonth.avg_return) : '-'}</div>
            </div>
          </div>

          {/* Chart showing average return per month */}
          <div className="seasonality-chart" aria-label="Saisonalität durchschnittliche Rendite pro Monat">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month_name" />
                <YAxis tickFormatter={val => formatPercent(val)} />
                <Tooltip formatter={(value) => formatPercent(value)} />
                <Bar dataKey="avg_return" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="seasonality-table-wrapper">
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
                {seasonality.map(row => (
                  <tr key={row.month}>
                    <td>{row.month_name}</td>
                    <td className={Number(row.avg_return) > 0 ? 'pos' : 'neg'}>{formatPercent(row.avg_return)}</td>
                    <td>{row.median_return === null || row.median_return === undefined ? '-' : formatPercent(row.median_return)}</td>
                    <td>{row.win_rate === null || row.win_rate === undefined ? '-' : `${Number(row.win_rate).toFixed(1)}%`}</td>
                    <td>{row.total_count ?? '-'}</td>
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

import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

function SeasonalityTab({ stockId }) {
  const [seasonality, setSeasonality] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/stocks/${stockId}/seasonality?years_back=${selectedPeriod === 'all' ? '' : selectedPeriod.replace('y','')}`)
      .then(res => res.json())
      .then(data => {
        setSeasonality(data);
        setLoading(false);
      })
      .catch(err => {
        setError('Fehler beim Laden der Saisonalitätsdaten');
        setLoading(false);
      });
  }, [stockId, selectedPeriod]);

  const periods = [
    { key: 'all', label: 'Gesamt' },
    { key: '5y', label: '5 Jahre' },
    { key: '10y', label: '10 Jahre' },
    { key: '15y', label: '15 Jahre' }
  ];

  const bestMonth = seasonality.reduce((prev, curr) => curr.avg_return > prev.avg_return ? curr : prev, seasonality[0] || {});
  const worstMonth = seasonality.reduce((prev, curr) => curr.avg_return < prev.avg_return ? curr : prev, seasonality[0] || {});

  return (
    <div className="seasonality-tab">
      <div className="period-selector">
        {periods.map(period => (
          <button
            key={period.key}
            className={`period-btn${selectedPeriod === period.key ? ' active' : ''}`}
            onClick={() => setSelectedPeriod(period.key)}
          >
            {period.label}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="loading">Lade Saisonalitätsdaten...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <>
          <div className="summary-cards">
            <div className="summary-card best">
              <span role="img" aria-label="Bester Monat">📈</span>
              <div>Bester Monat: <strong>{bestMonth.month_name}</strong></div>
              <div>Ø Return: {bestMonth.avg_return}%</div>
            </div>
            <div className="summary-card worst">
              <span role="img" aria-label="Schlechtester Monat">📉</span>
              <div>Schlechtester Monat: <strong>{worstMonth.month_name}</strong></div>
              <div>Ø Return: {worstMonth.avg_return}%</div>
            </div>
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
                    <td className={row.avg_return > 0 ? 'pos' : 'neg'}>{row.avg_return}%</td>
                    <td>{row.median_return}%</td>
                    <td>{row.win_rate}%</td>
                    <td>{row.total_count}</td>
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

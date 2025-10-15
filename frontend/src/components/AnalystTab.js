import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';

function AnalystTab({ stockId }) {
  const [analystData, setAnalystData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`/api/stocks/${stockId}/analyst-ratings`)
      .then(res => res.json())
      .then(data => {
        setAnalystData(data);
        setLoading(false);
      })
      .catch(err => {
        setError('Fehler beim Laden der Analystendaten');
        setLoading(false);
      });
  }, [stockId]);

  return (
    <div className="analyst-tab">
      {loading ? (
        <div className="loading">Lade Analystendaten...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : analystData ? (
        <>
          {analystData.price_targets && (
            <div className="summary-cards">
              <div className="summary-card price">
                <span role="img" aria-label="Kursziel">🎯</span>
                <div>Ø Kursziel: <strong>{analystData.price_targets.target_mean} €</strong></div>
                <div>Potential: {analystData.price_targets.upside_mean}%</div>
              </div>
              <div className="summary-card analysts">
                <span role="img" aria-label="Analysten">🧑‍💼</span>
                <div>Anzahl Analysten: <strong>{analystData.price_targets.num_analysts}</strong></div>
              </div>
            </div>
          )}
          {analystData.price_targets && (
            <div className="analyst-table-wrapper">
              <table className="analyst-table">
                <thead>
                  <tr>
                    <th>Kursziel Hoch</th>
                    <th>Kursziel Ø</th>
                    <th>Kursziel Median</th>
                    <th>Kursziel Tief</th>
                    <th>Spread</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{analystData.price_targets.target_high} €</td>
                    <td>{analystData.price_targets.target_mean} €</td>
                    <td>{analystData.price_targets.target_median} €</td>
                    <td>{analystData.price_targets.target_low} €</td>
                    <td>{analystData.price_targets.target_spread} €</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
          {analystData.recommendations && analystData.recommendations.current && (
            <div className="recommendations-section">
              <h3>Empfehlungen</h3>
              <table className="recommendations-table">
                <thead>
                  <tr>
                    <th>Strong Buy</th>
                    <th>Buy</th>
                    <th>Hold</th>
                    <th>Sell</th>
                    <th>Strong Sell</th>
                    <th>Konsens</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{analystData.recommendations.current.strong_buy}</td>
                    <td>{analystData.recommendations.current.buy}</td>
                    <td>{analystData.recommendations.current.hold}</td>
                    <td>{analystData.recommendations.current.sell}</td>
                    <td>{analystData.recommendations.current.strong_sell}</td>
                    <td>{analystData.recommendations.current.consensus_rating}</td>
                    <td>{analystData.recommendations.current.consensus_score}</td>
                  </tr>
                </tbody>
              </table>
              <div className="revision-info">
                <div>Revisionen (1 Monat): {analystData.recommendations.revisions_1m}</div>
                <div>Revisionen (3 Monate): {analystData.recommendations.revisions_3m}</div>
                <div>Stand: {analystData.recommendations.latest_date}</div>
              </div>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}

AnalystTab.propTypes = {
  stockId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired
};

export default AnalystTab;

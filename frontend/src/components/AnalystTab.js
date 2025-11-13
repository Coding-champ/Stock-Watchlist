import React, { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import API_BASE from '../config';
import PropTypes from 'prop-types';
import './AnalystTab.css';
import '../styles/skeletons.css';

function AnalystTab({ stockId }) {
  const [analystData, setAnalystData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    setLoading(true);
    setError(null);
    const url = `${API_BASE}/stocks/${stockId}/analyst-ratings`;
    queryClient.fetchQuery(['api', url], async () => {
      const r = await fetch(url);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    }, { staleTime: 60000 })
    .then(data => {
      setAnalystData(data);
      setLoading(false);
    })
    .catch(err => {
      console.error('AnalystTab fetch error', err);
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
          {/* Kursziele Cards */}
          {analystData.price_targets && (
            <div className="analyst-cards">
              <div className="analyst-card current">
                <div className="analyst-card__title">Aktueller Kurs</div>
                <div className="analyst-card__value">{analystData.price_targets.current_price} €</div>
              </div>
              <div className="analyst-card mean">
                <div className="analyst-card__title">Ø Kursziel</div>
                <div className="analyst-card__value">{analystData.price_targets.target_mean} €</div>
                <div className="analyst-card__potential" style={{color: analystData.price_targets.upside_mean >= 0 ? '#22c55e' : '#ef4444'}}>
                  {analystData.price_targets.upside_mean >= 0 ? '+' : ''}{analystData.price_targets.upside_mean}% Potential
                </div>
              </div>
              <div className="analyst-card high">
                <div className="analyst-card__title">Höchstes Ziel</div>
                <div className="analyst-card__value">{analystData.price_targets.target_high} €</div>
                <div className="analyst-card__potential" style={{color: '#7c3aed'}}>
                  +{analystData.price_targets.upside_high}% Potential
                </div>
              </div>
              <div className="analyst-card low">
                <div className="analyst-card__title">Niedrigstes Ziel</div>
                <div className="analyst-card__value">{analystData.price_targets.target_low} €</div>
                <div className="analyst-card__potential" style={{color: '#ef4444'}}>
                  {analystData.price_targets.upside_low}% Potential
                </div>
              </div>
              <div className="analyst-card spread">
                <div className="analyst-card__title">Spread</div>
                <div className="analyst-card__value">{analystData.price_targets.target_spread} €</div>
                <div className="analyst-card__meta">{analystData.price_targets.target_spread_pct}%</div>
              </div>
              <div className="analyst-card analysts">
                <div className="analyst-card__title">Anzahl Analysten</div>
                <div className="analyst-card__value">{analystData.price_targets.num_analysts}</div>
              </div>
            </div>
          )}

          {/* Empfehlungen */}
          {analystData.recommendations && analystData.recommendations.current && (
            <div className="analyst-recommendations">
              <div className="analyst-recommendations__header">
                <div className={`analyst-recommendations__rating analyst-recommendations__rating--${analystData.recommendations.current.consensus_rating.toLowerCase()}`}
                  style={{fontSize: '2.6rem', fontWeight: 800}}>
                  {analystData.recommendations.current.consensus_rating}
                </div>
                <div className="analyst-recommendations__score">
                  Score: <strong>{analystData.recommendations.current.consensus_score}</strong>/5.0
                </div>
                <div className="analyst-recommendations__meta">
                  <span><strong>{analystData.price_targets.num_analysts}</strong> Analysten</span>
                </div>
              </div>
              <div className="analyst-recommendations__bar-vertical">
                {[
                  {label: 'Strong Buy', value: analystData.recommendations.current.strong_buy, class: 'strong-buy', color: '#22c55e'},
                  {label: 'Buy', value: analystData.recommendations.current.buy, class: 'buy', color: '#4ade80'},
                  {label: 'Hold', value: analystData.recommendations.current.hold, class: 'hold', color: '#facc15', textColor: '#7c3aed'},
                  {label: 'Sell', value: analystData.recommendations.current.sell, class: 'sell', color: '#f87171'},
                  {label: 'Strong Sell', value: analystData.recommendations.current.strong_sell, class: 'strong-sell', color: '#ef4444'}
                ].map((seg, idx) => {
                  const pct = Math.round(seg.value / analystData.price_targets.num_analysts * 100);
                  return (
                    <div key={seg.label} className="analyst-bar-row">
                      <div className="analyst-bar-label">{seg.label}</div>
                      <div className="analyst-bar-track">
                        <div
                          className={`analyst-bar-fill analyst-bar-${seg.class}`}
                          style={{width: `${pct}%`, background: seg.color, color: seg.textColor || '#fff'}}>
                          {seg.value > 0 && <span className="analyst-bar-value">{seg.value}</span>}
                        </div>
                      </div>
                      <div className="analyst-bar-percent">{pct}%</div>
                    </div>
                  );
                })}
              </div>
              <div className="analyst-recommendations__revisions">
                <span className="analyst-recommendations__revision-box analyst-recommendations__revision-box--blue">Revisionen (1 Monat): <strong>{analystData.recommendations.revisions_1m}</strong></span>
                <span className="analyst-recommendations__revision-box analyst-recommendations__revision-box--purple">Revisionen (3 Monate): <strong>{analystData.recommendations.revisions_3m}</strong></span>
              </div>
              <div className="analyst-recommendations__date analyst-recommendations__revision-box analyst-recommendations__revision-box--gray">
                {(() => {
                  const rawDate = analystData.recommendations.latest_date;
                  if (!rawDate || rawDate === '1970-01-01') return null;
                  const dateObj = new Date(rawDate);
                  if (isNaN(dateObj.getTime())) return null;
                  return `Stand: ${dateObj.toLocaleDateString('de-DE')}`;
                })()}
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

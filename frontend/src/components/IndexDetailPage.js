import React from 'react';
import { useIndexDetails, useIndexConstituents } from '../hooks/useIndices';
import { useIndexStatistics } from '../hooks/useIndexStatistics';
import { useApi } from '../hooks/useApi';
import IndexChart from './IndexChart';
import SectorBreakdown from './SectorBreakdown';
import TopFlopsPanel from './TopFlopsPanel';
import MarketBreadthDashboard from './MarketBreadthDashboard';
import './IndexDetailPage.css';

function IndexDetailPage({ index, onBack, onOpenStock }) {
  const { data: indexDetails, isLoading: detailsLoading, error: detailsError } = useIndexDetails(index.ticker_symbol);
  const { data: constituentsData, isLoading: constituentsLoading, error: constituentsError } = useIndexConstituents(index.ticker_symbol);
  const { data: statistics, isLoading: statsLoading, error: statsError } = useIndexStatistics(index.ticker_symbol);
  const { fetchApi } = useApi();

  if (detailsLoading) {
    return (
      <div className="index-detail-page">
        <div className="detail-skeleton">
          <div className="skeleton-title" />
          <div className="skeleton-meta" />
          <div className="skeleton-cards">
            <div className="skeleton-card" />
            <div className="skeleton-card" />
            <div className="skeleton-card" />
          </div>
        </div>
      </div>
    );
  }

  if (detailsError) {
    return (
      <div className="index-detail-page">
        <div className="error-state">
          Fehler beim Laden der Index-Details.
          <button onClick={() => window.location.reload()} className="retry-btn">Neu laden</button>
        </div>
      </div>
    );
  }

  const details = indexDetails || index;
  const constituents = constituentsData?.constituents || [];

  const handleStockClick = async (ticker) => {
    if (!onOpenStock) return;
    try {
      const stocks = await fetchApi(`/stocks/search-db/?q=${encodeURIComponent(ticker)}&limit=1`);
      if (stocks && stocks.length > 0) {
        onOpenStock(stocks[0]);
      }
    } catch (err) {
      console.error('Failed to fetch stock:', err);
    }
  };

  return (
    <div className="index-detail-page">
      {/* Header */}
      <div className="index-detail-header">
        <button className="back-button" onClick={onBack}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          Zurück
        </button>
        
        <div className="index-header-content">
          <div className="index-title-section">
            <h1>{details.name}</h1>
            <div className="index-meta">
              <span className="index-symbol">{details.ticker_symbol}</span>
              {details.region && <span className="index-region">{details.region}</span>}
              {details.index_type && <span className="index-type">{details.index_type}</span>}
            </div>
          </div>

          {details.latest_price && (
            <div className="index-price-section">
              <div className="current-price">
                {formatPrice(details.latest_price.close, details.latest_price.currency, details.ticker_symbol)}
              </div>
              <div className="price-date">
                {new Date(details.latest_price.date).toLocaleDateString('de-DE')}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Description */}
      {details.description && (
        <div className="index-description">
          <p>{details.description}</p>
        </div>
      )}

      {/* Stats Cards */}
      <div className="index-stats-grid">
        <div className="stat-card">
          <div className="stat-label">Bestandteile</div>
          <div className="stat-value">{details.constituent_count || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Berechnungsmethode</div>
          <div className="stat-value">{details.calculation_method || '-'}</div>
        </div>
        {details.benchmark_index && (
          <div className="stat-card">
            <div className="stat-label">Benchmark</div>
            <div className="stat-value">{details.benchmark_index}</div>
          </div>
        )}
      </div>

      <div className="index-chart-section">
        <h2>Chart</h2>
        <IndexChart tickerSymbol={details.ticker_symbol} />
      </div>

      {/* Performance Statistics */}
      <div className="index-statistics-section">
        <h2>Performance & Risiko-Statistiken</h2>
        {statsLoading ? (
          <div className="stats-loading">
            <div className="skeleton-cards">
              <div className="skeleton-card" />
              <div className="skeleton-card" />
              <div className="skeleton-card" />
              <div className="skeleton-card" />
            </div>
          </div>
        ) : statsError ? (
          <div className="error-inline">
            Statistiken konnten nicht geladen werden.
          </div>
        ) : statistics ? (
          <>
            {/* Returns Grid */}
            <div className="stats-category">
              <h3>Renditen</h3>
              <div className="stats-grid">
                {statistics.ytd_return !== null && (
                  <div className="stat-card">
                    <div className="stat-label">YTD</div>
                    <div className={`stat-value ${statistics.ytd_return >= 0 ? 'positive' : 'negative'}`}>
                      {statistics.ytd_return >= 0 ? '+' : ''}{statistics.ytd_return}%
                    </div>
                  </div>
                )}
                {statistics.return_1y !== null && (
                  <div className="stat-card">
                    <div className="stat-label">1 Jahr</div>
                    <div className={`stat-value ${statistics.return_1y >= 0 ? 'positive' : 'negative'}`}>
                      {statistics.return_1y >= 0 ? '+' : ''}{statistics.return_1y}%
                    </div>
                  </div>
                )}
                {statistics.return_3y !== null && (
                  <div className="stat-card">
                    <div className="stat-label">3 Jahre (p.a.)</div>
                    <div className={`stat-value ${statistics.return_3y >= 0 ? 'positive' : 'negative'}`}>
                      {statistics.return_3y >= 0 ? '+' : ''}{statistics.return_3y}%
                    </div>
                  </div>
                )}
                {statistics.return_5y !== null && (
                  <div className="stat-card">
                    <div className="stat-label">5 Jahre (p.a.)</div>
                    <div className={`stat-value ${statistics.return_5y >= 0 ? 'positive' : 'negative'}`}>
                      {statistics.return_5y >= 0 ? '+' : ''}{statistics.return_5y}%
                    </div>
                  </div>
                )}
                {statistics.return_10y !== null && (
                  <div className="stat-card">
                    <div className="stat-label">10 Jahre (p.a.)</div>
                    <div className={`stat-value ${statistics.return_10y >= 0 ? 'positive' : 'negative'}`}>
                      {statistics.return_10y >= 0 ? '+' : ''}{statistics.return_10y}%
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Risk Metrics Grid */}
            <div className="stats-category">
              <h3>Risiko-Kennzahlen</h3>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Volatilität (p.a.)</div>
                  <div className="stat-value">{statistics.volatility_annual}%</div>
                </div>
                {statistics.sharpe_ratio !== null && (
                  <div className="stat-card">
                    <div className="stat-label">Sharpe Ratio</div>
                    <div className="stat-value">{statistics.sharpe_ratio}</div>
                  </div>
                )}
                <div className="stat-card">
                  <div className="stat-label">Max. Drawdown</div>
                  <div className="stat-value negative">{statistics.max_drawdown}%</div>
                  {statistics.max_drawdown_period && (
                    <div className="stat-meta">
                      {new Date(statistics.max_drawdown_period.peak_date).toLocaleDateString('de-DE')} - {new Date(statistics.max_drawdown_period.trough_date).toLocaleDateString('de-DE')}
                    </div>
                  )}
                  {statistics.max_drawdown_recovery_days != null && (
                    <div className="stat-meta">
                      {statistics.max_drawdown_recovery_days === null ? 'Noch keine Erholung' : `Erholung: ${statistics.max_drawdown_recovery_days} Tage${statistics.max_drawdown_recovery_date ? ' (bis ' + new Date(statistics.max_drawdown_recovery_date).toLocaleDateString('de-DE') + ')' : ''}`}
                    </div>
                  )}
                </div>
                <div className="stat-card">
                  <div className="stat-label">Aktueller Drawdown</div>
                  <div className={`stat-value ${statistics.current_drawdown >= 0 ? 'positive' : 'negative'}`}>
                    {statistics.current_drawdown}%
                  </div>
                  {statistics.current_drawdown_period && (
                    <div className="stat-meta">
                      {new Date(statistics.current_drawdown_period.start_date).toLocaleDateString('de-DE')} - {new Date(statistics.current_drawdown_period.end_date).toLocaleDateString('de-DE')}
                    </div>
                  )}
                  {statistics.current_drawdown_duration_days != null && statistics.current_drawdown_duration_days > 0 && (
                    <div className="stat-meta">Dauer: {statistics.current_drawdown_duration_days} Tage</div>
                  )}
                </div>
              </div>
            </div>

            {/* Additional Metrics */}
            <div className="stats-category">
              <h3>Weitere Kennzahlen</h3>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Bester Tag</div>
                  <div className="stat-value positive">+{statistics.best_day}%</div>
                  {statistics.best_day_date && (
                    <div className="stat-meta">{new Date(statistics.best_day_date).toLocaleDateString('de-DE')}</div>
                  )}
                </div>
                <div className="stat-card">
                  <div className="stat-label">Schlechtester Tag</div>
                  <div className="stat-value negative">{statistics.worst_day}%</div>
                  {statistics.worst_day_date && (
                    <div className="stat-meta">{new Date(statistics.worst_day_date).toLocaleDateString('de-DE')}</div>
                  )}
                </div>
                {statistics.positive_days_pct !== null && (
                  <div className="stat-card">
                    <div className="stat-label">Positive Tage</div>
                    <div className="stat-value">{statistics.positive_days_pct}%</div>
                  </div>
                )}
                {statistics.up_down_ratio !== null && (
                  <div className="stat-card">
                    <div className="stat-label">Up/Down Ratio</div>
                    <div className="stat-value">{statistics.up_down_ratio}</div>
                  </div>
                )}
                <div className="stat-card">
                  <div className="stat-label">Allzeithoch</div>
                  <div className="stat-value">{statistics.all_time_high?.toFixed(2)}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Allzeittief</div>
                  <div className="stat-value">{statistics.all_time_low?.toFixed(2)}</div>
                </div>
                {statistics.average_volume && (
                  <div className="stat-card">
                    <div className="stat-label">Ø Volumen</div>
                    <div className="stat-value">{formatVolume(statistics.average_volume)}</div>
                  </div>
                )}
                {statistics.new_aths_ytd != null && (
                  <div className="stat-card">
                    <div className="stat-label">Neue ATHs (YTD)</div>
                    <div className="stat-value">{statistics.new_aths_ytd}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Data Info */}
            <div className="stats-info">
              Datenbasis: {new Date(statistics.data_start_date).toLocaleDateString('de-DE')} bis {new Date(statistics.data_end_date).toLocaleDateString('de-DE')} ({statistics.total_trading_days} Handelstage)
            </div>
          </>
        ) : null}
      </div>

      {/* Sector Breakdown */}
      <SectorBreakdown tickerSymbol={details.ticker_symbol} />

      {/* Constituents Table */}
      {constituentsError && (
        <div className="error-inline">
          Bestandteile konnten nicht geladen werden.
          <button onClick={() => window.location.reload()} className="retry-btn">Neu laden</button>
        </div>
      )}
      {(!constituentsError && constituents.length > 0) && (
        <div className="constituents-section">
          <h2>Bestandteile ({constituents.length})</h2>
          {constituentsLoading ? (
            <div className="loading-state">Lade Bestandteile...</div>
          ) : (
            <div className="constituents-table-wrapper">
              <table className="constituents-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Name</th>
                    <th>Gewichtung</th>
                    <th>Status</th>
                    <th>Hinzugefügt</th>
                  </tr>
                </thead>
                <tbody>
                  {constituents.map((constituent, idx) => (
                    <tr 
                      key={idx}
                      onClick={() => handleStockClick(constituent.ticker_symbol)}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--hover-bg, #f8f9fa)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <td className="ticker">{constituent.ticker_symbol}</td>
                      <td className="name">{constituent.name}</td>
                      <td className="weight">
                        {constituent.weight ? `${constituent.weight.toFixed(2)}%` : '-'}
                      </td>
                      <td>
                        <span className={`status-badge status-${constituent.status}`}>
                          {constituent.status}
                        </span>
                      </td>
                      <td className="date">
                        {new Date(constituent.date_added).toLocaleDateString('de-DE')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tops / Flops des Tages: direkt vor Marktbreite */}
      <TopFlopsPanel symbol={details.ticker_symbol} onOpenStock={onOpenStock} />

      {/* Marktbreite separat unterhalb der Bestandteile */}
      <div className="market-breadth-section" style={{ marginTop: '32px' }}>
        <h2>Marktbreite</h2>
        <MarketBreadthDashboard symbol={details.ticker_symbol} days={30} />
      </div>
    </div>
  );
}

function formatPrice(price, currency = 'USD', tickerSymbol = '') {
  if (price == null) return '-';
  const formatted = new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price);
  const t = (tickerSymbol || '').toUpperCase();
  if (t.startsWith('^')) {
    return `${formatted} Punkte`;
  }
  return `${formatted} ${currency || ''}`.trim();
}

function formatVolume(volume) {
  if (volume == null) return '-';
  
  if (volume >= 1e9) {
    return `${(volume / 1e9).toFixed(2)}B`;
  } else if (volume >= 1e6) {
    return `${(volume / 1e6).toFixed(2)}M`;
  } else if (volume >= 1e3) {
    return `${(volume / 1e3).toFixed(2)}K`;
  }
  return volume.toLocaleString('de-DE');
}

export default IndexDetailPage;

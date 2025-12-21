import React, { useState } from 'react';
import { ResponsiveContainer, Treemap } from 'recharts';
import { useIndexSectorBreakdown } from '../hooks/useIndexSectorBreakdown';
import './SectorBreakdown.css';

const COLORS = [
  '#2563eb', '#7c3aed', '#dc2626', '#16a34a', '#ea580c',
  '#0891b2', '#4f46e5', '#db2777', '#65a30d', '#ca8a04',
  '#0d9488', '#7e22ce', '#be123c', '#059669', '#b45309'
];

function TreemapContent(props) {
  const { x, y, width, height, index, name, percentage } = props;
  const fill = COLORS[index % COLORS.length];
  const pad = 6;

  // Avoid rendering labels when tiles are too small
  const canRenderLabel = width > 80 && height > 36;

  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill={fill} opacity={0.9} stroke="rgba(255,255,255,0.8)" />
      {canRenderLabel && (
        <>
          <text x={x + pad} y={y + pad + 12} fill="#ffffff" fontSize={12} fontWeight={700}>
            {name}
          </text>
          <text x={x + pad} y={y + pad + 28} fill="rgba(255,255,255,0.92)" fontSize={11}>
            {Number.isFinite(percentage) ? `${percentage.toFixed(1)}%` : ''}
          </text>
        </>
      )}
    </g>
  );
}

function SectorBreakdown({ tickerSymbol }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const { data, isLoading, error } = useIndexSectorBreakdown(tickerSymbol);

  if (isLoading) {
    return (
      <div className="sector-breakdown">
        <div className="sector-header">
          <h2>Sektor-Analyse</h2>
        </div>
        <div className="sector-loading">
          <div className="skeleton-bar" style={{width:'60%', height:24}}></div>
          <div className="skeleton-rect" style={{height:280, marginTop:16}}></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="sector-breakdown">
        <div className="sector-header">
          <h2>Sektor-Analyse</h2>
        </div>
        <div className="error-inline">
          Sektor-Daten konnten nicht geladen werden.
        </div>
      </div>
    );
  }

  if (!data || !data.sectors || data.sectors.length === 0) {
    return null;
  }

  const treemapData = data.sectors.map((s) => ({
    name: s.sector,
    size: s.percentage,
    percentage: s.percentage,
    weight: s.weight,
    count: s.count,
  }));

  return (
    <div className="sector-breakdown">
      <div className="sector-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h2>Sektor-Analyse</h2>
        <button className="collapse-toggle" aria-label={isExpanded ? 'Zuklappen' : 'Aufklappen'}>
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {isExpanded && (
        <div className="sector-content">
          <div className="sector-summary">
            <span className="summary-item">
              <strong>{data.sectors.length}</strong> Sektoren
            </span>
            <span className="summary-item">
              <strong>{data.total_constituents}</strong> Unternehmen
            </span>
          </div>

          <div className="sector-visuals">
            {/* Treemap (tree chart) */}
            <div className="sector-chart">
              <h3>Sektor-Verteilung</h3>
              <ResponsiveContainer width="100%" height={300}>
                <Treemap
                  data={treemapData}
                  dataKey="size"
                  nameKey="name"
                  aspectRatio={4 / 3}
                  isAnimationActive={false}
                  content={<TreemapContent />}
                />
              </ResponsiveContainer>
            </div>

            {/* Table + mini-bars (replaced bar chart) */}
            <div className="sector-chart">
              <h3>Sektoren</h3>
              <div className="sector-table-wrapper">
                <table className="sector-table">
                  <thead>
                    <tr>
                      <th>Sektor</th>
                      <th>Anzahl</th>
                      <th>Gewichtung</th>
                      <th>Top Aktien</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.sectors.map((sector, idx) => (
                      <tr key={idx}>
                        <td>
                          <span className="sector-color-dot" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></span>
                          {sector.sector}
                        </td>
                        <td className="center">{sector.count}</td>
                        <td className="right">
                          <div className="mini-bar-cell">
                            <div className="mini-bar" aria-hidden="true">
                              <div
                                className="mini-bar__fill"
                                style={{
                                  width: `${Math.max(0, Math.min(100, sector.percentage || 0))}%`,
                                  backgroundColor: COLORS[idx % COLORS.length]
                                }}
                              />
                            </div>
                            <span className="mini-bar__value">{sector.percentage.toFixed(2)}%</span>
                          </div>
                        </td>
                        <td className="top-stocks">
                          {sector.top_stocks.slice(0, 3).map((stock, i) => (
                            <span key={i} className="stock-chip" title={stock.name}>
                              {stock.ticker_symbol}
                            </span>
                          ))}
                          {sector.top_stocks.length > 3 && (
                            <span className="stock-chip more">+{sector.top_stocks.length - 3}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SectorBreakdown;

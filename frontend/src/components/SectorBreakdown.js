import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useIndexSectorBreakdown } from '../hooks/useIndexSectorBreakdown';
import './SectorBreakdown.css';

const COLORS = [
  '#2563eb', '#7c3aed', '#dc2626', '#16a34a', '#ea580c',
  '#0891b2', '#4f46e5', '#db2777', '#65a30d', '#ca8a04',
  '#0d9488', '#7e22ce', '#be123c', '#059669', '#b45309'
];

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

  const topSectors = data.sectors.slice(0, 5);

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
            {/* Pie Chart */}
            <div className="sector-chart">
              <h3>Sektor-Verteilung</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data.sectors}
                    dataKey="percentage"
                    nameKey="sector"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ sector, percentage }) => `${sector}: ${percentage}%`}
                  >
                    {data.sectors.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `${value}%`} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Top Sectors Bar Chart */}
            <div className="sector-chart">
              <h3>Top 5 Sektoren (Gewichtung)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topSectors} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" unit="%" />
                  <YAxis dataKey="sector" type="category" width={120} />
                  <Tooltip formatter={(value) => `${value}%`} />
                  <Bar dataKey="percentage" fill="#2563eb">
                    {topSectors.map((entry, index) => (
                      <Cell key={`bar-${index}`} fill={COLORS[index]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Sector Table */}
          <div className="sector-table-wrapper">
            <table className="sector-table">
              <thead>
                <tr>
                  <th>Sektor</th>
                  <th>Anzahl</th>
                  <th>Gewichtung</th>
                  <th>%</th>
                  <th>Top Aktien</th>
                </tr>
              </thead>
              <tbody>
                {data.sectors.map((sector, idx) => (
                  <tr key={idx}>
                    <td>
                      <span className="sector-color-dot" style={{backgroundColor: COLORS[idx % COLORS.length]}}></span>
                      {sector.sector}
                    </td>
                    <td className="center">{sector.count}</td>
                    <td className="right">{sector.weight.toFixed(2)}</td>
                    <td className="right">{sector.percentage.toFixed(2)}%</td>
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
      )}
    </div>
  );
}

export default SectorBreakdown;

import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area } from 'recharts';
import API_BASE from '../config';

/**
 * DrawdownChartTooltip Component
 * Displays a small drawdown chart in a tooltip when hovering over Max Drawdown
 */
function DrawdownChartTooltip({ stockId, maxDrawdown, children }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [drawdownData, setDrawdownData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (showTooltip && !drawdownData && !loading) {
      loadDrawdownData();
    }
  }, [showTooltip, drawdownData, loading]);

  const loadDrawdownData = async () => {
    setLoading(true);
    try {
      // Fetch 1-year chart data to match calculated-metrics default period
      const response = await fetch(`${API_BASE}/stock-data/${stockId}/chart?period=1y&interval=1d`);
      if (!response.ok) throw new Error('Failed to fetch chart data');
      
      const chartData = await response.json();
      console.log('Chart data received:', chartData);
      
      if (chartData && chartData.close && chartData.close.length > 0) {
        // Calculate drawdown series
        const closes = chartData.close;
        const dates = chartData.dates || [];
        let cumMax = -Infinity;
        
        const drawdownSeries = [];
        
        for (let idx = 0; idx < closes.length; idx++) {
          const close = closes[idx];
          
          if (close == null || isNaN(close)) continue;
          
          cumMax = Math.max(cumMax, close);
          const drawdown = cumMax > 0 ? ((close - cumMax) / cumMax) * 100 : 0;
          
          // Format date with year
          let displayDate = '';
          if (dates[idx]) {
            try {
              const d = new Date(dates[idx]);
              displayDate = d.toLocaleDateString('de-DE', { year: 'numeric', month: 'short', day: 'numeric' });
            } catch {
              displayDate = String(dates[idx]);
            }
          } else {
            displayDate = `Day ${idx}`;
          }
          
          drawdownSeries.push({
            date: displayDate,
            drawdown: drawdown,
            price: close
          });
        }
        
        console.log('Drawdown series calculated:', drawdownSeries.slice(0, 5), '...', drawdownSeries.slice(-5));
        setDrawdownData(drawdownSeries);
      } else {
        console.error('No chart data available');
      }
    } catch (error) {
      console.error('Error loading drawdown data:', error);
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltipContent = ({ active, payload }) => {
    if (!active || !payload || payload.length === 0) return null;
    const data = payload[0].payload;
    
    return (
      <div style={{
        background: 'white',
        border: '1px solid #ddd',
        borderRadius: '4px',
        padding: '8px',
        fontSize: '12px'
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{data.date}</div>
        <div style={{ color: data.drawdown < 0 ? '#ef4444' : '#666' }}>
          Drawdown: {data.drawdown.toFixed(2)}%
        </div>
      </div>
    );
  };

  return (
    <div
      className="metric-tooltip-container has-chart-tooltip"
      style={{ position: 'relative', display: 'inline-block' }}
    >
      <span 
        className="metric-tooltip-trigger"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {children}
      </span>
      
      {showTooltip && (
        <div 
          className="drawdown-chart-tooltip-popup"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <div className="metric-tooltip-header">
            <span className="metric-tooltip-icon">📉</span>
            <span>Drawdown Chart (1 Jahr)</span>
          </div>
          
          {loading ? (
            <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
              Lädt...
            </div>
          ) : drawdownData && drawdownData.length > 0 ? (
            <>
              <div style={{ marginBottom: '10px', fontSize: '12px', color: '#666' }}>
                Maximum Drawdown: <strong style={{ color: '#ef4444' }}>{maxDrawdown?.toFixed(2)}%</strong>
              </div>
              
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={drawdownData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ef4444" stopOpacity={0.1}/>
                      <stop offset="100%" stopColor="#ef4444" stopOpacity={0.3}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 10 }}
                    interval="preserveStartEnd"
                    minTickGap={50}
                  />
                  <YAxis 
                    tick={{ fontSize: 10 }}
                    tickFormatter={(value) => `${value.toFixed(0)}%`}
                  />
                  <Tooltip content={<CustomTooltipContent />} />
                  <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" strokeWidth={1.5} label={{ value: '0%', position: 'right' }} />
                  <Line
                    type="monotone"
                    dataKey="drawdown"
                    stroke="#ef4444"
                    strokeWidth={2.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Area
                    type="monotone"
                    dataKey="drawdown"
                    stroke="none"
                    fill="url(#drawdownGradient)"
                    fillOpacity={1}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
              
              <div style={{ fontSize: '11px', color: '#666', marginTop: '8px', lineHeight: '1.4' }}>
                Der Chart zeigt den prozentualen Rückgang vom jeweiligen Höchststand. 
                Negative Werte bedeuten, dass der Kurs unter dem bisherigen Maximum liegt.
              </div>
            </>
          ) : (
            <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
              Keine Daten verfügbar
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default DrawdownChartTooltip;

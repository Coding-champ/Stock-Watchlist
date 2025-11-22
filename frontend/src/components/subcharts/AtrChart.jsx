import React, { useMemo } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { formatPrice } from '../../utils/currencyUtils';

export const AtrChart = ({ data, stock }) => {
  // Always call hooks; compute derived values with safe fallbacks
  const atrValues = useMemo(() => {
    if (!data || data.length === 0) return [];
    return data.map(d => d.atr).filter(v => v != null);
  }, [data]);
  const hasData = data && data.length > 0 && atrValues.length > 0;
  const minATR = hasData ? Math.min(...atrValues) : 0;
  const maxATR = hasData ? Math.max(...atrValues) : 0;
  const padding = hasData ? (maxATR - minATR) * 0.1 : 0;
  const atrDomain = hasData ? [Math.max(0, minATR - padding), maxATR + padding] : [0, 1];
  if (!hasData) return null;

  return (
    <div className="chart-section">
      <h4 className="chart-subtitle">ATR (14) - Average True Range</h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="atrGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f39c12" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#f39c12" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 9, angle: -45, textAnchor: 'end' }}
            height={60}
            interval="preserveStartEnd"
            minTickGap={40}
          />
          <YAxis 
            tick={{ fontSize: 10 }}
            tickFormatter={(value) => formatPrice(value, stock)}
            domain={atrDomain}
          />
          <Tooltip 
            formatter={(value, name) => [formatPrice(value, stock), name]}
            contentStyle={{ 
              backgroundColor: 'rgba(255, 255, 255, 0.98)', 
              border: '1px solid #ddd',
              borderRadius: '6px',
              padding: '10px'
            }}
            labelStyle={{ fontWeight: 'bold', color: '#333' }}
            cursor={{ stroke: '#f39c12', strokeWidth: 1, strokeDasharray: '5 5' }}
          />
          <Legend />
          <Line type="monotone" dataKey="atr" stroke="#f39c12" strokeWidth={3} dot={false} name="ATR (14)" isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
      <div className="atr-info" style={{ 
        padding: '10px', 
        fontSize: '12px', 
        color: '#666',
        backgroundColor: '#f8f9fa',
        borderRadius: '4px',
        margin: '10px 0'
      }}>
        <p style={{ margin: '5px 0' }}>
          💡 <strong>ATR Interpretation:</strong> Höhere Werte = höhere Volatilität
        </p>
        <p style={{ margin: '5px 0' }}>
          🎯 <strong>Stop-Loss Empfehlung:</strong> 1.5-2x ATR unter Einstiegspreis
        </p>
        <p style={{ margin: '5px 0' }}>
          📊 <strong>Position Size:</strong> Bei hohem ATR kleinere Positionen wählen
        </p>
      </div>
    </div>
  );
};

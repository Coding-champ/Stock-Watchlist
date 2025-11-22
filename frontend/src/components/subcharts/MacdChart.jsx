import React from 'react';
import { ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ReferenceLine, Bar, Line } from 'recharts';

export const MacdChart = ({ data, ticks }) => {
  if (!data || data.length === 0) return null;
  return (
    <div className="chart-section">
      <h4 className="chart-subtitle">MACD</h4>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 9, angle: -45, textAnchor: 'end' }}
            height={60}
            interval="preserveStartEnd"
            minTickGap={40}
            ticks={ticks}
          />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'rgba(255, 255, 255, 0.98)', 
              border: '1px solid #ddd',
              borderRadius: '6px',
              padding: '10px'
            }}
            labelStyle={{ fontWeight: 'bold', color: '#333' }}
            cursor={{ stroke: '#3498db', strokeWidth: 1, strokeDasharray: '5 5' }}
          />
          <Legend />
          <ReferenceLine y={0} stroke="#000" />
          <Bar dataKey="macdHistogram" fill="#3498db" opacity={0.6} name="Histogram" />
          <Line type="monotone" dataKey="macd" stroke="#e74c3c" strokeWidth={2} dot={false} name="MACD" />
          <Line type="monotone" dataKey="macdSignal" stroke="#27ae60" strokeWidth={2} dot={false} name="Signal" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

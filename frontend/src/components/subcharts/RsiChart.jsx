import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceArea, ReferenceLine } from 'recharts';

// Small colored dot to indicate RSI zones
const RsiCustomDot = ({ cx, cy, payload }) => {
  if (!payload || payload.rsi == null) return null;
  let fill = '#8e44ad';
  if (payload.rsi >= 70) fill = '#e74c3c';
  else if (payload.rsi <= 30) fill = '#27ae60';
  return <circle cx={cx} cy={cy} r={1} fill={fill} />;
};

export const RsiChart = ({ data, ticks }) => {
  if (!data || data.length === 0) return null;
  return (
    <div className="chart-section">
      <h4 className="chart-subtitle">RSI (14)</h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="overboughtGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#e74c3c" stopOpacity={0.15}/>
              <stop offset="100%" stopColor="#e74c3c" stopOpacity={0.05}/>
            </linearGradient>
            <linearGradient id="oversoldGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#27ae60" stopOpacity={0.05}/>
              <stop offset="100%" stopColor="#27ae60" stopOpacity={0.15}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 9, angle: -45, textAnchor: 'end' }}
            height={60}
            interval="preserveStartEnd"
            minTickGap={40}
            ticks={ticks}
          />
          <YAxis 
            domain={[0, 100]}
            tick={{ fontSize: 10 }}
            ticks={[0, 30, 50, 70, 100]}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'rgba(255, 255, 255, 0.98)', 
              border: '1px solid #ddd',
              borderRadius: '6px',
              padding: '10px'
            }}
            labelStyle={{ fontWeight: 'bold', color: '#333' }}
            cursor={{ stroke: '#6c63ff', strokeWidth: 1, strokeDasharray: '5 5' }}
          />
          <Legend />
          <ReferenceArea y1={70} y2={100} fill="url(#overboughtGradient)" fillOpacity={1} />
          <ReferenceArea y1={0} y2={30} fill="url(#oversoldGradient)" fillOpacity={1} />
          <ReferenceLine y={70} stroke="#e74c3c" strokeDasharray="3 3" strokeWidth={1.5} label={{ value: 'Overbought (70)', position: 'right', fill: '#e74c3c', fontSize: 11 }} />
          <ReferenceLine y={30} stroke="#27ae60" strokeDasharray="3 3" strokeWidth={1.5} label={{ value: 'Oversold (30)', position: 'right', fill: '#27ae60', fontSize: 11 }} />
          <ReferenceLine y={50} stroke="#95a5a6" strokeDasharray="2 2" strokeWidth={1} />
          <Line
            type="monotone"
            dataKey="rsi"
            stroke="#8e44ad"
            strokeWidth={2.5}
            dot={RsiCustomDot}
            name="RSI"
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

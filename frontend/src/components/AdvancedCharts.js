import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart
} from 'recharts';

/**
 * MACD Chart Component
 * Zeigt MACD Line, Signal Line und Histogram
 */
export const MACDChart = ({ data, macd, signal }) => {
  if (!data || data.length === 0) {
    return <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>Keine Daten verfügbar</div>;
  }

  // Prepare chart data
  const chartData = data.map((point, index) => ({
    date: new Date(point.date).toLocaleDateString('de-DE', { month: 'short', day: 'numeric' }),
    macd: point.macd || null,
    signal: point.signal || null,
    histogram: point.histogram || null
  }));

  // Determine signal
  const latestMacd = macd || 0;
  const latestSignal = signal || 0;
  const signalType = latestMacd > latestSignal ? 'BUY' : latestMacd < latestSignal ? 'SELL' : 'NEUTRAL';
  const signalColor = signalType === 'BUY' ? '#22c55e' : signalType === 'SELL' ? '#ef4444' : '#6c757d';
  const signalIcon = signalType === 'BUY' ? '↑' : signalType === 'SELL' ? '↓' : '→';

  return (
    <div style={{ marginBottom: '30px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '12px',
        padding: '12px',
        background: '#f8f9fa',
        borderRadius: '6px'
      }}>
        <div style={{ fontSize: '16px', fontWeight: '600', color: '#333' }}>
          📊 MACD Indicator
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '14px', color: '#666' }}>
            MACD: <strong>{latestMacd.toFixed(2)}</strong> | Signal: <strong>{latestSignal.toFixed(2)}</strong>
          </span>
          <span style={{ 
            padding: '4px 12px',
            borderRadius: '12px',
            fontSize: '13px',
            fontWeight: '600',
            background: signalColor,
            color: 'white'
          }}>
            {signalType} {signalIcon}
          </span>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 11, fill: '#666' }}
            tickLine={{ stroke: '#666' }}
          />
          <YAxis 
            tick={{ fontSize: 11, fill: '#666' }}
            tickLine={{ stroke: '#666' }}
          />
          <Tooltip 
            contentStyle={{ 
              background: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '12px'
            }}
          />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />
          <ReferenceLine y={0} stroke="#999" strokeDasharray="3 3" />
          
          {/* Histogram */}
          <Bar 
            dataKey="histogram" 
            fill="#82ca9d" 
            name="Histogram"
            opacity={0.6}
          />
          
          {/* MACD Line */}
          <Line 
            type="monotone" 
            dataKey="macd" 
            stroke="#007bff" 
            strokeWidth={2}
            name="MACD"
            dot={false}
          />
          
          {/* Signal Line */}
          <Line 
            type="monotone" 
            dataKey="signal" 
            stroke="#ff7f0e" 
            strokeWidth={2}
            name="Signal"
            dot={false}
            strokeDasharray="5 5"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};


/**
 * Stochastic Oscillator Chart
 * Zeigt %K und %D Linien mit Overbought/Oversold Zonen
 */
export const StochasticChart = ({ data, kPercent, dPercent }) => {
  if (!data || data.length === 0) {
    return <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>Keine Daten verfügbar</div>;
  }

  // Prepare chart data
  const chartData = data.map((point) => ({
    date: new Date(point.date).toLocaleDateString('de-DE', { month: 'short', day: 'numeric' }),
    k: point.k_percent !== undefined ? point.k_percent : null,
    d: point.d_percent !== undefined ? point.d_percent : null
  }));

  // Determine zone
  const latestK = kPercent || 0;
  const zone = latestK > 80 ? 'Overbought' : latestK < 20 ? 'Oversold' : 'Neutral';
  const zoneColor = latestK > 80 ? '#ef4444' : latestK < 20 ? '#22c55e' : '#6c757d';

  return (
    <div style={{ marginBottom: '30px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '12px',
        padding: '12px',
        background: '#f8f9fa',
        borderRadius: '6px'
      }}>
        <div style={{ fontSize: '16px', fontWeight: '600', color: '#333' }}>
          📉 Stochastic Oscillator
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '14px', color: '#666' }}>
            %K: <strong>{latestK.toFixed(1)}%</strong>
          </span>
          <span style={{ 
            padding: '4px 12px',
            borderRadius: '12px',
            fontSize: '13px',
            fontWeight: '600',
            background: zoneColor,
            color: 'white'
          }}>
            {zone}
          </span>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 11, fill: '#666' }}
            tickLine={{ stroke: '#666' }}
          />
          <YAxis 
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: '#666' }}
            tickLine={{ stroke: '#666' }}
          />
          <Tooltip 
            contentStyle={{ 
              background: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '12px'
            }}
          />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />
          
          {/* Overbought Line */}
          <ReferenceLine 
            y={80} 
            stroke="#ef4444" 
            strokeDasharray="5 5" 
            label={{ value: 'Overbought', position: 'right', fontSize: 10, fill: '#ef4444' }}
          />
          
          {/* Oversold Line */}
          <ReferenceLine 
            y={20} 
            stroke="#22c55e" 
            strokeDasharray="5 5"
            label={{ value: 'Oversold', position: 'right', fontSize: 10, fill: '#22c55e' }}
          />
          
          {/* %K Line */}
          <Line 
            type="monotone" 
            dataKey="k" 
            stroke="#007bff" 
            strokeWidth={2}
            name="%K"
            dot={false}
          />
          
          {/* %D Line */}
          <Line 
            type="monotone" 
            dataKey="d" 
            stroke="#6610f2" 
            strokeWidth={2}
            name="%D"
            dot={false}
            strokeDasharray="5 5"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};


/**
 * Price Chart with SMA50 and SMA200
 * Erweiterte Version mit Moving Averages
 */
export const PriceChartWithSMA = ({ data, showSMA50 = true, showSMA200 = true }) => {
  if (!data || data.length === 0) {
    return <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>Keine Daten verfügbar</div>;
  }

  // Prepare chart data
  const chartData = data.map((point) => ({
    date: new Date(point.date).toLocaleDateString('de-DE', { month: 'short', day: 'numeric' }),
    price: point.close || point.price,
    sma50: point.sma50 || null,
    sma200: point.sma200 || null
  }));

  return (
    <div style={{ marginBottom: '30px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '12px',
        padding: '12px',
        background: '#f8f9fa',
        borderRadius: '6px'
      }}>
        <div style={{ fontSize: '16px', fontWeight: '600', color: '#333' }}>
          📈 Preis mit Moving Averages
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 11, fill: '#666' }}
            tickLine={{ stroke: '#666' }}
          />
          <YAxis 
            tick={{ fontSize: 11, fill: '#666' }}
            tickLine={{ stroke: '#666' }}
            domain={['auto', 'auto']}
          />
          <Tooltip 
            contentStyle={{ 
              background: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '12px'
            }}
          />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />
          
          {/* Price Line */}
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#007bff" 
            strokeWidth={2.5}
            name="Preis"
            dot={false}
          />
          
          {/* SMA50 */}
          {showSMA50 && (
            <Line 
              type="monotone" 
              dataKey="sma50" 
              stroke="#ff7f0e" 
              strokeWidth={2}
              name="SMA 50"
              dot={false}
              connectNulls
            />
          )}
          
          {/* SMA200 */}
          {showSMA200 && (
            <Line 
              type="monotone" 
              dataKey="sma200" 
              stroke="#6610f2" 
              strokeWidth={2}
              name="SMA 200"
              dot={false}
              connectNulls
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

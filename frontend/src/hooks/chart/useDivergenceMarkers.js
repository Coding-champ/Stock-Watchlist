import { useMemo } from 'react';
import { ReferenceLine } from 'recharts';

/**
 * Hook to generate divergence markers for RSI and MACD indicators
 * @param {Object} params - Hook parameters
 * @param {boolean} params.showDivergences - Whether to show divergence markers
 * @param {Object} params.divergenceData - Divergence data from API
 * @param {Array} params.chartData - Chart data array
 * @param {string} params.period - Current time period
 * @returns {Array|null} Array of ReferenceLine components or null
 */
export const useDivergenceMarkers = ({ showDivergences, divergenceData, chartData, period }) => {
  return useMemo(() => {
    if (!showDivergences || !divergenceData || !chartData) return null;
    
    const markers = [];
    
    // RSI Divergences
    if (divergenceData.rsi_divergence) {
      const rsiDiv = divergenceData.rsi_divergence;
      
      // Bullish divergence
      if (rsiDiv.bullish_divergence && rsiDiv.divergence_points?.bullish) {
        rsiDiv.divergence_points.bullish.forEach((point, index) => {
          const pointDate = new Date(point.date).toLocaleDateString('de-DE', { 
            month: 'short', 
            day: 'numeric',
            ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
          });
          
          const dataIndex = chartData.findIndex(d => d.date === pointDate);
          if (dataIndex === -1) return;
          
          markers.push(
            <ReferenceLine
              key={`rsi-bullish-${index}`}
              x={pointDate}
              stroke="#27ae60"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: `🔺 RSI Bull (${Math.round(rsiDiv.confidence * 100)}%)`,
                position: 'top',
                fill: '#27ae60',
                fontSize: 10,
                fontWeight: 'bold'
              }}
            />
          );
        });
      }
      
      // Bearish divergence
      if (rsiDiv.bearish_divergence && rsiDiv.divergence_points?.bearish) {
        rsiDiv.divergence_points.bearish.forEach((point, index) => {
          const pointDate = new Date(point.date).toLocaleDateString('de-DE', { 
            month: 'short', 
            day: 'numeric',
            ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
          });
          
          const dataIndex = chartData.findIndex(d => d.date === pointDate);
          if (dataIndex === -1) return;
          
          markers.push(
            <ReferenceLine
              key={`rsi-bearish-${index}`}
              x={pointDate}
              stroke="#e74c3c"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: `🔻 RSI Bear (${Math.round(rsiDiv.confidence * 100)}%)`,
                position: 'top',
                fill: '#e74c3c',
                fontSize: 10,
                fontWeight: 'bold'
              }}
            />
          );
        });
      }
    }
    
    // MACD Divergences
    if (divergenceData.macd_divergence) {
      const macdDiv = divergenceData.macd_divergence;
      
      // Bullish divergence
      if (macdDiv.bullish_divergence && macdDiv.divergence_points?.bullish) {
        macdDiv.divergence_points.bullish.forEach((point, index) => {
          const pointDate = new Date(point.date).toLocaleDateString('de-DE', { 
            month: 'short', 
            day: 'numeric',
            ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
          });
          
          const dataIndex = chartData.findIndex(d => d.date === pointDate);
          if (dataIndex === -1) return;
          
          markers.push(
            <ReferenceLine
              key={`macd-bullish-${index}`}
              x={pointDate}
              stroke="#3498db"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: `🔺 MACD Bull (${Math.round(macdDiv.confidence * 100)}%)`,
                position: 'bottom',
                fill: '#3498db',
                fontSize: 10,
                fontWeight: 'bold'
              }}
            />
          );
        });
      }
      
      // Bearish divergence
      if (macdDiv.bearish_divergence && macdDiv.divergence_points?.bearish) {
        macdDiv.divergence_points.bearish.forEach((point, index) => {
          const pointDate = new Date(point.date).toLocaleDateString('de-DE', { 
            month: 'short', 
            day: 'numeric',
            ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
          });
          
          const dataIndex = chartData.findIndex(d => d.date === pointDate);
          if (dataIndex === -1) return;
          
          markers.push(
            <ReferenceLine
              key={`macd-bearish-${index}`}
              x={pointDate}
              stroke="#e67e22"
              strokeWidth={2}
              strokeDasharray="5 5"
              label={{
                value: `🔻 MACD Bear (${Math.round(macdDiv.confidence * 100)}%)`,
                position: 'bottom',
                fill: '#e67e22',
                fontSize: 10,
                fontWeight: 'bold'
              }}
            />
          );
        });
      }
    }
    
    return markers;
  }, [showDivergences, divergenceData, chartData, period]);
};

import { useMemo } from 'react';
import { ReferenceLine } from 'recharts';
import { formatPrice } from '../../utils/currencyUtils';

/**
 * Hook to generate crossover markers (Golden Cross / Death Cross)
 * @param {Object} params - Hook parameters
 * @param {boolean} params.showCrossovers - Whether to show crossover markers
 * @param {Object} params.crossoverData - Crossover data from API
 * @param {Array} params.chartData - Chart data array
 * @param {string} params.period - Current time period
 * @param {Object} params.stock - Stock object for price formatting
 * @returns {Array|null} Array of ReferenceLine components or null
 */
export const useCrossoverMarkers = ({ showCrossovers, crossoverData, chartData, period, stock }) => {
  return useMemo(() => {
    if (!showCrossovers || !crossoverData || !crossoverData.all_crossovers || !chartData) {
      return null;
    }
    
    return crossoverData.all_crossovers.map((crossover, index) => {
      // Find the matching date in chartData
      const crossoverDate = new Date(crossover.date).toLocaleDateString('de-DE', { 
        month: 'short', 
        day: 'numeric',
        ...(period === 'max' || period === '1y' ? { year: '2-digit' } : {})
      });
      
      const dataIndex = chartData.findIndex(d => d.date === crossoverDate);
      if (dataIndex === -1) return null; // Date not in visible range
      
      // Dynamic positioning: if crossover is in the right half of chart, position label on left
      const positionPercent = (dataIndex / chartData.length) * 100;
      const isRightSide = positionPercent > 50;
      
      const isGolden = crossover.type === 'golden_cross';
      const color = isGolden ? '#4caf50' : '#f44336';
      const price = crossover.price ? formatPrice(crossover.price, stock) : '';
      const emoji = isGolden ? '🌟' : '💀';
      const label = isGolden ? 'Golden Cross' : 'Death Cross';
      
      return (
        <ReferenceLine
          key={`crossover-${index}`}
          x={crossoverDate}
          stroke={color}
          strokeWidth={2}
          strokeDasharray="3 3"
          label={{
            value: `${emoji} ${label}${price ? ' @ ' + price : ''}`,
            position: 'top',
            fill: color,
            fontSize: 10,
            fontWeight: 'bold',
            dx: isRightSide ? -50 : 10,
            dy: 5
          }}
        />
      );
    });
  }, [showCrossovers, crossoverData, chartData, period, stock]);
};

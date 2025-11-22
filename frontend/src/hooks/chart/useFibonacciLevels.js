import { useMemo } from 'react';
import { ReferenceLine } from 'recharts';
import { formatPrice } from '../../utils/currencyUtils';

/**
 * Hook to generate Fibonacci retracement/extension level markers
 * @param {Object} params - Hook parameters
 * @param {boolean} params.showFibonacci - Whether to show Fibonacci levels
 * @param {Object} params.fibonacciData - Fibonacci data from API
 * @param {string} params.fibonacciType - 'retracement' or 'extension'
 * @param {Object} params.selectedFibLevels - Selected retracement levels
 * @param {Object} params.selectedExtensionLevels - Selected extension levels
 * @param {Object} params.stock - Stock object for price formatting
 * @returns {Array|null} Array of ReferenceLine components or null
 */
export const useFibonacciLevels = ({ 
  showFibonacci, 
  fibonacciData, 
  fibonacciType, 
  selectedFibLevels, 
  selectedExtensionLevels,
  stock 
}) => {
  return useMemo(() => {
    if (!showFibonacci || !fibonacciData) return null;
    
    const levels = fibonacciType === 'retracement' ? fibonacciData.retracement : fibonacciData.extension;
    if (!levels) return null;
    
    // Farben für Fibonacci Levels (Blautöne)
    const fibColors = {
      '0.0': '#1e88e5',
      '23.6': '#42a5f5',
      '38.2': '#64b5f6',
      '50.0': '#90caf9',
      '61.8': '#64b5f6',
      '78.6': '#42a5f5',
      '100.0': '#1e88e5',
      '127.2': '#1565c0',
      '161.8': '#0d47a1',
      '200.0': '#0d47a1',
      '261.8': '#01579b'
    };
    
    return Object.entries(levels).map(([level, price]) => {
      // Check if this level should be displayed
      if (fibonacciType === 'retracement') {
        // Skip 0% and 100% for retracement, always show swing high/low
        if (level !== '0.0' && level !== '100.0' && !selectedFibLevels[level]) {
          return null;
        }
      } else {
        // Extension: Skip 0% and 100%, check selectedExtensionLevels
        if (level !== '0.0' && level !== '100.0' && !selectedExtensionLevels[level]) {
          return null;
        }
      }
      
      const color = fibColors[level] || '#2196f3';
      const labelText = fibonacciType === 'retracement'
        ? `Fib ${level}% - ${price != null ? formatPrice(price, stock) : 'N/A'}`
        : `Fib Ext ${level}% - ${price != null ? formatPrice(price, stock) : 'N/A'}`;
      
      return (
        <ReferenceLine
          key={`fib-${fibonacciType}-${level}`}
          y={price}
          stroke={color}
          strokeWidth={1.5}
          strokeDasharray="5 5"
          label={{
            value: labelText,
            position: 'right',
            fill: color,
            fontSize: 9,
            fontWeight: 'bold'
          }}
        />
      );
    }).filter(Boolean);
  }, [showFibonacci, fibonacciData, fibonacciType, selectedFibLevels, selectedExtensionLevels, stock]);
};

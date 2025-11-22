import { useMemo } from 'react';
import { ReferenceLine } from 'recharts';
import { formatPrice } from '../../utils/currencyUtils';

/**
 * Hook to generate Support and Resistance level markers
 * @param {Object} params - Hook parameters
 * @param {boolean} params.showSupportResistance - Whether to show S/R levels
 * @param {Object} params.supportResistanceData - S/R data from API
 * @param {Object} params.stock - Stock object for price formatting
 * @returns {Array|null} Array of ReferenceLine components or null
 */
export const useSupportResistanceLevels = ({ 
  showSupportResistance, 
  supportResistanceData,
  stock 
}) => {
  return useMemo(() => {
    if (!showSupportResistance || !supportResistanceData) return null;
    
    const allLevels = [
      ...supportResistanceData.support.map(level => ({ ...level, type: 'support' })),
      ...supportResistanceData.resistance.map(level => ({ ...level, type: 'resistance' }))
    ];
    
    return allLevels.map((level, index) => {
      const color = level.type === 'support' ? '#27ae60' : '#e74c3c';
      const icon = level.type === 'support' ? '🟢' : '🔴';
      const labelText = `${icon} ${level.type === 'support' ? 'Support' : 'Resistance'} - ${level.price ? formatPrice(level.price, stock) : 'N/A'} (${level.strength}× getestet)`;
      
      // Linienstärke basierend auf Stärke (1-3px)
      const strokeWidth = Math.min(level.strength, 3);
      
      return (
        <ReferenceLine
          key={`sr-${level.type}-${index}`}
          y={level.price}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray="0"
          label={{
            value: labelText,
            position: 'right',
            fill: color,
            fontSize: 9,
            fontWeight: 'bold'
          }}
        />
      );
    });
  }, [showSupportResistance, supportResistanceData, stock]);
};

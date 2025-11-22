import React from 'react';

/**
 * Custom candlestick shape component for recharts Bar
 * Renders OHLC candles with proper positioning
 */
export const CandlestickBar = (props) => {
  const { x, y, width, height, chartData, index } = props;
  
  // Get the data item for this bar
  if (!chartData || !chartData[index]) return null;
  
  const item = chartData[index];
  
  if (!item.open || !item.high || !item.low || !item.close) return null;

  // Determine color based on price movement
  const isGreen = item.close >= item.open;
  const color = isGreen ? '#26a69a' : '#ef5350';

  // When Y-axis starts at 0, the Bar component gives us:
  // - y: pixel position for 'high' value
  // - height: pixel height from 'high' to 0
  // We need to calculate positions for open, close, and low
  
  // The key insight: if high is at 'y' and 0 is at 'y + height',
  // then the scale is: pixels_per_dollar = height / high
  const pixelsPerDollar = height / item.high;
  
  // Calculate Y positions for each price point
  // For a price P: its Y position = y + (high - P) * pixelsPerDollar
  const highY = y;
  const lowY = y + (item.high - item.low) * pixelsPerDollar;
  const openY = y + (item.high - item.open) * pixelsPerDollar;
  const closeY = y + (item.high - item.close) * pixelsPerDollar;
  
  // Body dimensions
  const bodyTop = Math.min(openY, closeY);
  const bodyHeight = Math.abs(closeY - openY) || 1; // Minimum 1px for doji
  
  // Candlestick width
  const candleWidth = Math.min(width * 0.8, 10);
  const wickX = x + width / 2;

  return (
    <g>
      {/* Wick line (from high to low) */}
      <line
        x1={wickX}
        y1={highY}
        x2={wickX}
        y2={lowY}
        stroke={color}
        strokeWidth={1}
      />
      {/* Body rectangle */}
      <rect
        x={x + (width - candleWidth) / 2}
        y={bodyTop}
        width={candleWidth}
        height={bodyHeight}
        fill={color}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  );
};

export default CandlestickBar;

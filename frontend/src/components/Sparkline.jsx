import React from 'react';

function Sparkline({ data, id, width = 140, height = 48, color = '#7c3aed' }) {
  if (!data || data.length < 2) {
    return <div className="sparkline sparkline--empty">Keine Daten</div>;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return { x, y };
  });

  const pathD = points.reduce((acc, point, index) => (
    index === 0 ? `M ${point.x},${point.y}` : `${acc} L ${point.x},${point.y}`
  ), '');

  const closedPathD = `${pathD} L ${width},${height} L 0,${height} Z`;

  return (
    <svg
      className="sparkline"
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id={`gradient-${id}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0.05" />
        </linearGradient>
      </defs>
      <path
        d={closedPathD}
        fill={`url(#gradient-${id})`}
        stroke="none"
      />
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth="2"
      />
    </svg>
  );
}

export default Sparkline;

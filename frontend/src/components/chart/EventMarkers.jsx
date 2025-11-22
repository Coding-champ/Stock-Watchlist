import React, { useMemo } from 'react';
import { ReferenceLine } from 'recharts';

/**
 * EventMarkers
 * Renders dividend, split, and earnings markers as stacked circular icons along X-axis.
 * Logic extracted from StockChart for modularity and performance.
 */
export const EventMarkers = ({ chartData, period, showDividends, showSplits, showEarnings }) => {
  const markers = useMemo(() => {
    if (!chartData || chartData.length === 0) return null;

    const events = [];

    const formatEventDate = (dateStr) => {
      const datePart = dateStr.split('T')[0];
      const date = new Date(datePart + 'T12:00:00Z');
      const options = { month: 'short', day: 'numeric', year: '2-digit', timeZone: 'UTC' };
      return date.toLocaleDateString('de-DE', options);
    };

    const availableDates = new Set(chartData.map(d => d.date));

    // Dividends
    if (showDividends) {
      const shortPeriods = new Set(['1d','5d','1mo','3mo','6mo','6m','ytd','1y']);
      const useQuarterly = shortPeriods.has(period);
      const dividendData = useQuarterly ? chartData[0]?.dividends : chartData[0]?.dividends_annual;
      if (dividendData?.length) {
        dividendData.forEach(div => {
          const eventDate = formatEventDate(div.date);
          const rawDate = new Date(div.date);
          if (!availableDates.has(eventDate)) {
            const targetTime = rawDate.getTime();
            const closestDate = chartData.reduce((closest, point) => {
              const pointDate = new Date(point.fullDate);
              const diff = Math.abs(pointDate.getTime() - targetTime);
              const closestDiff = closest ? Math.abs(new Date(closest.fullDate).getTime() - targetTime) : Infinity;
              return diff < closestDiff ? point : closest;
            }, null);
            if (closestDate) {
              const closestDiff = Math.abs(new Date(closestDate.fullDate).getTime() - targetTime);
              const daysDiff = closestDiff / (1000 * 60 * 60 * 24);
              if (daysDiff <= 7) {
                events.push({ date: closestDate.date, fullDate: div.date, type: 'dividend', data: div, priority: 3, isQuarterly: useQuarterly });
              }
            }
          } else {
            events.push({ date: eventDate, fullDate: div.date, type: 'dividend', data: div, priority: 3, isQuarterly: useQuarterly });
          }
        });
      }
    }

    // Splits
    if (showSplits && chartData[0]?.splits?.length) {
      chartData[0].splits.forEach(split => {
        const eventDate = formatEventDate(split.date);
        const rawDate = new Date(split.date);
        if (!availableDates.has(eventDate)) {
          const targetTime = rawDate.getTime();
            const closestDate = chartData.reduce((closest, point) => {
              const pointDate = new Date(point.fullDate);
              const diff = Math.abs(pointDate.getTime() - targetTime);
              const closestDiff = closest ? Math.abs(new Date(closest.fullDate).getTime() - targetTime) : Infinity;
              return diff < closestDiff ? point : closest;
            }, null);
            if (closestDate) {
              const closestDiff = Math.abs(new Date(closestDate.fullDate).getTime() - targetTime);
              const daysDiff = closestDiff / (1000 * 60 * 60 * 24);
              if (daysDiff <= 7) {
                events.push({ date: closestDate.date, fullDate: split.date, type: 'split', data: split, priority: 2 });
              }
            }
        } else {
          events.push({ date: eventDate, fullDate: split.date, type: 'split', data: split, priority: 2 });
        }
      });
    }

    // Earnings
    if (showEarnings && chartData[0]?.earnings?.length) {
      chartData[0].earnings.forEach(earning => {
        const eventDate = formatEventDate(earning.date);
        const rawDate = new Date(earning.date);
        if (!availableDates.has(eventDate)) {
          const targetTime = rawDate.getTime();
          const closestDate = chartData.reduce((closest, point) => {
            const pointDate = new Date(point.fullDate);
            const diff = Math.abs(pointDate.getTime() - targetTime);
            const closestDiff = closest ? Math.abs(new Date(closest.fullDate).getTime() - targetTime) : Infinity;
            return diff < closestDiff ? point : closest;
          }, null);
          if (closestDate) {
            const closestDiff = Math.abs(new Date(closestDate.fullDate).getTime() - targetTime);
            const daysDiff = closestDiff / (1000 * 60 * 60 * 24);
            if (daysDiff <= 7) {
              events.push({ date: closestDate.date, fullDate: earning.date, type: 'earnings', data: earning, priority: 1 });
            }
          }
        } else {
          events.push({ date: eventDate, fullDate: earning.date, type: 'earnings', data: earning, priority: 1 });
        }
      });
    }

    if (events.length === 0) return null;

    // Deduplicate earnings by original calendar day
    const earningsDedup = new Map();
    events.forEach(event => {
      if (event.type === 'earnings') {
        const key = (event.fullDate?.split?.('T')?.[0]) || event.date;
        if (!earningsDedup.has(key)) earningsDedup.set(key, event);
        else {
          const existing = earningsDedup.get(key);
          const hasEstAndAct = event.data.eps_estimate != null && event.data.eps_actual != null;
          const existingHasEstAndAct = existing.data.eps_estimate != null && existing.data.eps_actual != null;
          if (hasEstAndAct && !existingHasEstAndAct) earningsDedup.set(key, event);
        }
      }
    });
    const dedupedEvents = events.filter(e => e.type !== 'earnings');
    earningsDedup.forEach(e => dedupedEvents.push(e));

    const eventsByDate = dedupedEvents.reduce((acc, event) => {
      const key = event.fullDate;
      if (!acc[key]) acc[key] = [];
      acc[key].push(event);
      return acc;
    }, {});

    const iconSize = 20;
    const spacing = 4;
    const markersLocal = [];

    Object.entries(eventsByDate).forEach(([fullDate, dateEvents]) => {
      dateEvents.sort((a, b) => a.priority - b.priority);
      dateEvents.forEach((event, stackIndex) => {
        const originalEventDate = formatEventDate(event.fullDate);
        let color = '#9ca3af';
        let letter = '?';
        let tooltipText = '';
        if (event.type === 'earnings') {
          letter = 'E';
          const { eps_estimate, eps_actual } = event.data;
          if (eps_estimate != null && eps_actual != null) {
            color = eps_actual >= eps_estimate ? '#22c55e' : '#ef4444';
            tooltipText = `Est: $${eps_estimate.toFixed(2)} / Act: $${eps_actual.toFixed(2)}`;
          } else if (eps_actual != null) {
            tooltipText = `EPS: $${eps_actual.toFixed(2)}`;
          } else tooltipText = 'Earnings';
        } else if (event.type === 'split') {
          letter = 'S';
          color = '#f97316';
          tooltipText = `Split ${event.data.ratio}:1`;
        } else if (event.type === 'dividend') {
          letter = 'D';
          color = '#3b82f6';
          if (event.isQuarterly) tooltipText = `Dividend: $${event.data.amount.toFixed(2)}`;
          else {
            const year = event.data.year;
            const total = event.data.total_amount;
            const count = event.data.count;
            tooltipText = `Jahresdividende ${year}: $${total.toFixed(2)}${count ? ` aus ${count} Zahlungen` : ''}`;
          }
        }
        markersLocal.push(
          <ReferenceLine
            key={`event-${event.type}-${fullDate}-${stackIndex}`}
            x={event.date}
            stroke={color}
            strokeWidth={0}
            label={{
              value: letter,
              position: 'bottom',
              fill: 'white',
              fontSize: 12,
              fontWeight: 'bold',
              offset: 15 + (stackIndex * (iconSize + spacing)),
              content: (props) => {
                const { viewBox } = props;
                if (!viewBox || !viewBox.x) return null;
                const cx = viewBox.x;
                const cy = viewBox.y + viewBox.height - 2 - (stackIndex * (iconSize + spacing));
                return (
                  <g>
                    <circle cx={cx} cy={cy} r={iconSize / 2} fill={color} stroke="white" strokeWidth={2} />
                    <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central" fill="white" fontSize={12} fontWeight="bold">{letter}</text>
                    <title>{originalEventDate + '\n' + tooltipText}</title>
                  </g>
                );
              }
            }}
          />
        );
      });
    });

    return markersLocal;
  }, [chartData, showDividends, showSplits, showEarnings, period]);

  return markers;
};

export default EventMarkers;

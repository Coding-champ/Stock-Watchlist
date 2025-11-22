// Basic data transformation utilities extracted from StockChart.js
// Focus: chart payload shaping, indicator merging, tick calculation.

export function mergeIndicators(primary = {}, secondary = {}) {
  return { ...secondary, ...primary };
}

export function transformChartPayload(chartJson, sourceIndicators) {
  if (!chartJson || !chartJson.dates) return [];
  return chartJson.dates.map((date, index) => {
    const datePart = date.split('T')[0];
    const dateObj = new Date(datePart + 'T12:00:00Z');
    return {
      date: dateObj.toLocaleDateString('de-DE', {
        month: 'short',
        day: 'numeric',
        year: '2-digit',
        timeZone: 'UTC'
      }),
      fullDate: date,
      open: chartJson.open[index],
      high: chartJson.high[index],
      low: chartJson.low[index],
      close: chartJson.close[index],
      volume: chartJson.volume ? chartJson.volume[index] : null,
      sma50: sourceIndicators?.sma_50?.[index],
      sma200: sourceIndicators?.sma_200?.[index],
      rsi: sourceIndicators?.rsi?.[index],
      k_percent: sourceIndicators?.stochastic?.k_percent?.[index],
      d_percent: sourceIndicators?.stochastic?.d_percent?.[index],
      macd: sourceIndicators?.macd?.macd?.[index] ?? sourceIndicators?.macd?.macd?.[index],
      macdSignal: sourceIndicators?.macd?.signal?.[index] ?? sourceIndicators?.macd?.signal?.[index],
      macdHistogram: sourceIndicators?.macd?.histogram?.[index] ?? sourceIndicators?.macd?.hist?.[index],
      bollingerUpper: sourceIndicators?.bollinger?.upper?.[index],
      bollingerMiddle: sourceIndicators?.bollinger?.middle?.[index] ?? sourceIndicators?.bollinger?.sma?.[index],
      bollingerLower: sourceIndicators?.bollinger?.lower?.[index],
      bollingerPercentB: sourceIndicators?.bollinger?.percent_b?.[index],
      bollingerBandwidth: sourceIndicators?.bollinger?.bandwidth?.[index],
      atr: sourceIndicators?.atr?.[index],
      vwap: sourceIndicators?.vwap?.[index],
      volumeMA10: sourceIndicators?.volumeMA10?.[index],
      volumeMA20: sourceIndicators?.volumeMA20?.[index],
      ichimoku_conversion: sourceIndicators?.ichimoku?.conversion?.[index],
      ichimoku_base: sourceIndicators?.ichimoku?.base?.[index],
      ichimoku_span_a: sourceIndicators?.ichimoku?.span_a?.[index],
      ichimoku_span_b: sourceIndicators?.ichimoku?.span_b?.[index],
      ichimoku_chikou: sourceIndicators?.ichimoku?.chikou?.[index]
    };
  });
}

export function ensureVwap(transformed, sourceIndicators) {
  const hasVwap = !!(sourceIndicators && Array.isArray(sourceIndicators.vwap) && sourceIndicators.vwap.some(v => v !== null && v !== undefined));
  if (hasVwap) return transformed;
  const windowSize = 20;
  for (let i = 0; i < transformed.length; i++) {
    let volSum = 0, pvSum = 0;
    for (let j = Math.max(0, i - (windowSize - 1)); j <= i; j++) {
      const rec = transformed[j];
      if (typeof rec?.close === 'number' && typeof rec?.volume === 'number' && rec.volume > 0) {
        pvSum += rec.close * rec.volume;
        volSum += rec.volume;
      }
    }
    transformed[i].vwap = volSum > 0 ? (pvSum / volSum) : transformed[i].vwap ?? null;
  }
  return transformed;
}

export function ensureVolumeMovingAverages(transformed) {
  const needVolMA10 = !transformed.some(d => d.volumeMA10 !== undefined && d.volumeMA10 !== null);
  const needVolMA20 = !transformed.some(d => d.volumeMA20 !== undefined && d.volumeMA20 !== null);
  if (needVolMA10) {
    const volumeMA10 = transformed.map((item, index) => {
      if (index < 9) return null;
      let sum = 0;
      for (let i = 0; i < 10; i++) sum += transformed[index - i].volume || 0;
      return sum / 10;
    });
    transformed.forEach((item, index) => { if (item.volumeMA10 == null) item.volumeMA10 = volumeMA10[index]; });
  }
  if (needVolMA20) {
    const volumeMA20 = transformed.map((item, index) => {
      if (index < 19) return null;
      let sum = 0;
      for (let i = 0; i < 20; i++) sum += transformed[index - i].volume || 0;
      return sum / 20;
    });
    transformed.forEach((item, index) => { if (item.volumeMA20 == null) item.volumeMA20 = volumeMA20[index]; });
  }
  return transformed;
}

export function computeSharedTicks(data, targetCount = 6) {
  if (!data || data.length === 0) return null;
  const n = Math.min(targetCount, data.length);
  const ticks = [];
  for (let i = 0; i < n; i++) {
    const idx = Math.round(i * (data.length - 1) / (n - 1));
    ticks.push(data[idx].date);
  }
  return ticks;
}

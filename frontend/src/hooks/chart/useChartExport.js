import { useRef, useCallback } from 'react';

/**
 * Custom hook for chart export functionality
 * Provides PNG and CSV export capabilities
 * 
 * @param {Object} stock - Stock object with ticker_symbol
 * @param {string} period - Current time period
 * @param {Array} chartData - Chart data array
 * @returns {Object} Export functions and ref
 */
export const useChartExport = (stock, period, chartData) => {
  const chartCaptureRef = useRef(null);

  /**
   * Export chart as PNG image using html2canvas
   */
  const exportToPNG = useCallback(async () => {
    try {
      const html2canvas = (await import('html2canvas')).default;
      const node = chartCaptureRef.current;
      if (!node) return;
      
      const canvas = await html2canvas(node, { 
        backgroundColor: '#ffffff', 
        scale: 2, 
        useCORS: true 
      });
      
      const dataUrl = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      a.href = dataUrl;
      a.download = `${stock.ticker_symbol}_${period}_chart.png`;
      a.click();
    } catch (e) {
      console.error('PNG export failed', e);
      alert('PNG Export fehlgeschlagen. Bitte Abhängigkeit html2canvas installieren.');
    }
  }, [stock.ticker_symbol, period]);

  /**
   * Export chart data as CSV file
   */
  const exportToCSV = useCallback(() => {
    if (!chartData) return;

    const headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'];
    const csvContent = [
      headers.join(','),
      ...chartData.map(row => [
        row.fullDate,
        row.open,
        row.high,
        row.low,
        row.close,
        row.volume || ''
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${stock.ticker_symbol}_${period}_chart_data.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  }, [chartData, stock.ticker_symbol, period]);

  return {
    chartCaptureRef,
    exportToPNG,
    exportToCSV
  };
};

export default useChartExport;

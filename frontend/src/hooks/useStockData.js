import { useState, useEffect, useRef } from 'react';
import API_BASE from '../config';
import { SPARKLINE_POINT_LIMIT } from '../constants/stockTable';

export function useStockData(stocks) {
  const [sparklineSeries, setSparklineSeries] = useState({});
  const [extendedDataMap, setExtendedDataMap] = useState({});
  const fetchedExtendedIdsRef = useRef(new Set());
  const fetchedSparklineIdsRef = useRef(new Set());

  useEffect(() => {
    const fetchSparklineData = async () => {
      const stocksToFetch = stocks.filter(stock => !fetchedSparklineIdsRef.current.has(stock.id));
      if (stocksToFetch.length === 0) {
        return;
      }

      for (const stock of stocksToFetch) {
        fetchedSparklineIdsRef.current.add(stock.id);
        try {
          const resp = await fetch(`${API_BASE}/stocks/${stock.id}/price-history?limit=${SPARKLINE_POINT_LIMIT}`, {
            headers: { Accept: 'application/json' },
          });

          if (!resp.ok) {
            console.warn(`Failed to fetch sparkline for stock ${stock.id}:`, resp.status);
            continue;
          }

          const data = await resp.json();
          const values = Array.isArray(data) && data.length > 0
            ? data.map(item => item.price).filter(p => typeof p === 'number')
            : [];

          setSparklineSeries(prev => ({
            ...prev,
            [stock.id]: { values }
          }));
        } catch (error) {
          console.error(`Error fetching sparkline for stock ${stock.id}:`, error);
        }
      }
    };

    fetchSparklineData();
  }, [stocks]);

  useEffect(() => {
    const fetchExtendedData = async () => {
      const stocksToFetch = stocks.filter(stock => !fetchedExtendedIdsRef.current.has(stock.id));
      if (stocksToFetch.length === 0) {
        return;
      }

      for (const stock of stocksToFetch) {
        fetchedExtendedIdsRef.current.add(stock.id);
        try {
          const resp = await fetch(`${API_BASE}/stocks/${stock.id}/extended-data`, {
            headers: { Accept: 'application/json' },
          });

          if (!resp.ok) {
            console.warn(`Failed to fetch extended data for stock ${stock.id}:`, resp.status);
            continue;
          }

          const data = await resp.json();
          setExtendedDataMap(prev => ({
            ...prev,
            [stock.id]: data
          }));
        } catch (error) {
          console.error(`Error fetching extended data for stock ${stock.id}:`, error);
        }
      }
    };

    fetchExtendedData();
  }, [stocks]);

  return {
    sparklineSeries,
    extendedDataMap
  };
}

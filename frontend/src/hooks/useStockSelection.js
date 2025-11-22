import { useState } from 'react';

export function useStockSelection() {
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedStockIds, setSelectedStockIds] = useState(new Set());

  const toggleSelectionMode = () => {
    setSelectionMode(!selectionMode);
    setSelectedStockIds(new Set());
  };

  const toggleStockSelection = (stockId) => {
    setSelectedStockIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(stockId)) {
        newSet.delete(stockId);
      } else {
        newSet.add(stockId);
      }
      return newSet;
    });
  };

  const selectAll = (stocks) => {
    const allIds = new Set(stocks.map(s => s.id));
    setSelectedStockIds(allIds);
  };

  const clearSelection = () => {
    setSelectedStockIds(new Set());
  };

  return {
    selectionMode,
    setSelectionMode,
    selectedStockIds,
    setSelectedStockIds,
    toggleSelectionMode,
    toggleStockSelection,
    selectAll,
    clearSelection
  };
}

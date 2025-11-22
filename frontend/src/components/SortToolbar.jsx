import React from 'react';
import { PERFORMANCE_SORT_KEYS } from '../constants/stockTable';

function SortToolbar({ sortConfig, applySortPreset, isSortPresetActive, setSortConfig }) {
  return (
    <div className="stock-table__toolbar">
      <span className="stock-table__toolbar-label">Sortierung</span>
      <div className="stock-table__toolbar-group">
        <button
          type="button"
          className={`sort-chip ${isSortPresetActive(PERFORMANCE_SORT_KEYS.CURRENT) ? 'sort-chip--active' : ''}`}
          onClick={() => applySortPreset(PERFORMANCE_SORT_KEYS.CURRENT, 'desc')}
        >
          Aktuelle Gewinner
        </button>
        <button
          type="button"
          className={`sort-chip ${isSortPresetActive(PERFORMANCE_SORT_KEYS.WATCHLIST) ? 'sort-chip--active' : ''}`}
          onClick={() => applySortPreset(PERFORMANCE_SORT_KEYS.WATCHLIST, 'desc')}
        >
          Watchlist-Gewinner
        </button>
        <button
          type="button"
          className={`sort-chip ${isSortPresetActive(PERFORMANCE_SORT_KEYS.WEEK) ? 'sort-chip--active' : ''}`}
          onClick={() => applySortPreset(PERFORMANCE_SORT_KEYS.WEEK, 'desc')}
        >
          52-Wochen-Gewinner
        </button>
        <button
          type="button"
          className={`sort-chip ${sortConfig.key === null ? 'sort-chip--active' : (!Object.values(PERFORMANCE_SORT_KEYS).includes(sortConfig.key) && sortConfig.key ? 'sort-chip--muted' : '')}`}
          onClick={() => setSortConfig({ key: null, direction: 'asc' })}
        >
          Standard
        </button>
      </div>
    </div>
  );
}

export default SortToolbar;

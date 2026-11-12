import React from 'react';
import WatchlistSection from './WatchlistSection';

function AppSidebar({
  watchlists,
  currentWatchlist,
  sidebarCollapsed,
  onToggleCollapsed,
  onWatchlistSelect,
  onWatchlistsChange,
  onShowToast,
}) {
  return (
    <aside className={`layout__sidebar ${sidebarCollapsed ? 'layout__sidebar--collapsed' : ''}`}>
      <button
        type="button"
        className="sidebar-toggle"
        aria-label={sidebarCollapsed ? 'Sidebar ausklappen' : 'Sidebar einklappen'}
        onClick={onToggleCollapsed}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" fill="currentColor" />
        </svg>
      </button>
      <WatchlistSection
        watchlists={watchlists}
        currentWatchlist={currentWatchlist}
        onWatchlistSelect={onWatchlistSelect}
        onWatchlistsChange={onWatchlistsChange}
        onShowToast={onShowToast}
        collapsed={sidebarCollapsed}
        onToggleCollapsed={onToggleCollapsed}
      />
    </aside>
  );
}

export default AppSidebar;

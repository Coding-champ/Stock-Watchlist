import React from 'react';

function AppHeader({
  isSettingsOpen,
  settings,
  themes,
  settingsRef,
  onToggleSettings,
  onOpenAdmin,
  onSaveSettings,
}) {
  return (
    <header className="app-header">
      <div className="app-header__actions" ref={settingsRef}>
        <button
          className="app-header__action"
          type="button"
          onClick={onOpenAdmin}
          aria-label="Admin Panel öffnen"
          title="Admin Panel"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 3 4 6v5c0 5 3.4 8.7 8 10 4.6-1.3 8-5 8-10V6l-8-3Zm0 4 4 1.5V11c0 2.8-1.7 5.2-4 6.3-2.3-1.1-4-3.5-4-6.3V8.5L12 7Zm-1 2v3h-2l3 3 3-3h-2V9h-2Z" />
          </svg>
          <span>Admin</span>
        </button>
        <button
          className={`app-header__action ${isSettingsOpen ? 'is-active' : ''}`}
          type="button"
          onClick={onToggleSettings}
          aria-expanded={isSettingsOpen}
          aria-haspopup="dialog"
          aria-label="Einstellungsmenü öffnen"
          title="Einstellungen"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m19.4 13.5 1.6 1.2-1.8 3.1-1.9-.8a7.3 7.3 0 0 1-1.7 1l-.3 2h-3.6l-.3-2a7.3 7.3 0 0 1-1.7-1l-1.9.8L6 14.7l1.6-1.2a7.1 7.1 0 0 1 0-2L6 10.3l1.8-3.1 1.9.8a7.3 7.3 0 0 1 1.7-1l.3-2h3.6l.3 2a7.3 7.3 0 0 1 1.7 1l1.9-.8 1.8 3.1-1.6 1.2a7.1 7.1 0 0 1 0 2ZM13.5 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
          </svg>
          <span>Einstellungen</span>
        </button>
        {isSettingsOpen && (
          <div className="settings-popover" role="dialog" aria-label="Einstellungen">
            <strong>Einstellungen</strong>
            <label className="settings-popover__field">
              <span>Ansichtsmodus</span>
              <button
                type="button"
                className={`settings-toggle ${settings.display_mode === 'expert' ? 'is-on' : ''}`}
                role="switch"
                aria-checked={settings.display_mode === 'expert'}
                onClick={() => onSaveSettings({ display_mode: settings.display_mode === 'expert' ? 'compact' : 'expert' })}
              >
                <span className="settings-toggle__thumb" />
                <span>{settings.display_mode === 'expert' ? 'Experte' : 'Kompakt'}</span>
              </button>
            </label>
            <label className="settings-popover__field">
              <span>Startseite</span>
              <select value={settings.default_page} onChange={(event) => onSaveSettings({ default_page: event.target.value })}>
                <option value="overview">Übersicht</option>
                <option value="portfolio">Portfolio</option>
                <option value="watchlist">Watchlist</option>
                <option value="screener">Screener</option>
                <option value="indices">Indizes</option>
                <option value="earnings">Earnings</option>
                <option value="alerts">Alerts</option>
                <option value="investment-check">Investitions-Check</option>
              </select>
            </label>
            <label className="settings-popover__field">
              <span>Theme</span>
              <select value={settings.theme} onChange={(event) => onSaveSettings({ theme: event.target.value })}>
                {themes.map((theme) => <option key={theme.id} value={theme.id}>{theme.name}</option>)}
              </select>
            </label>
            <p className="settings-popover__hint">Der Expertenmodus ist gespeichert und wird später mit einer eigenen Ansicht aktiviert.</p>
          </div>
        )}
      </div>
      <div className="app-header__title-group">
        <span className="app-header__eyebrow">Dein Marktüberblick</span>
        <h1>Stock Watchlist</h1>
      </div>
    </header>
  );
}

export default AppHeader;

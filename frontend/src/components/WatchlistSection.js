import React, { useState } from 'react';
import '../styles/skeletons.css';
import API_BASE from '../config';

const getInitials = (name = '') => {
  const trimmed = (name || '').trim();
  if (!trimmed) {
    return 'WL';
  }

  const parts = trimmed.split(/\s+/).slice(0, 2);
  const initials = parts
    .map((part) => part.charAt(0).toUpperCase())
    .join('');

  return initials || trimmed.slice(0, 2).toUpperCase();
};

function WatchlistSection({ watchlists, currentWatchlist, onWatchlistSelect, onWatchlistsChange, onShowToast, collapsed = false, onToggleCollapsed = () => {} }) {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/watchlists/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const created = await response.json();
        setShowModal(false);
        setFormData({ name: '', description: '' });
        onWatchlistsChange();
        if (onShowToast) {
          onShowToast(`Watchlist erstellt · ${created?.name || formData.name}`, 'success');
        }
      } else {
        let message = 'Fehler beim Erstellen der Watchlist';
        try {
          const errorBody = await response.json();
          if (errorBody?.detail) {
            message = errorBody.detail;
          }
        } catch (parseError) {
          console.warn('Watchlist create: konnte Fehlermeldung nicht parsen', parseError);
        }

        if (onShowToast) {
          onShowToast(`Erstellung fehlgeschlagen · ${message}`, 'error');
        } else {
          alert(message);
        }
      }
    } catch (error) {
      console.error('Error creating watchlist:', error);
      if (onShowToast) {
        onShowToast('Erstellung fehlgeschlagen · Bitte erneut versuchen', 'error');
      } else {
        alert('Fehler beim Erstellen der Watchlist');
      }
    }
  };

  return (
    <section className="panel panel--watchlists" aria-label="Watchlists">
      {collapsed && (
        <div className="sidebar-mini" aria-hidden={false}>
          <button
            type="button"
            className="watchlist-mini-toggle"
            onClick={onToggleCollapsed}
            title="Sidebar öffnen"
            aria-label="Sidebar öffnen"
          >
            ‹
          </button>

          <div className="watchlist-mini-list" role="list" aria-label="Watchlists">
            {watchlists.map((wl) => {
              const initials = getInitials(wl.name);
              const isActive = currentWatchlist?.id === wl.id;

              return (
                <button
                  key={wl.id}
                  type="button"
                  role="listitem"
                  title={wl.name}
                  aria-label={`Öffne Watchlist ${wl.name}`}
                  className={`watchlist-mini-card ${isActive ? 'active' : ''}`}
                  onClick={() => onWatchlistSelect(wl)}
                >
                  <span className="watchlist-mini-card__icon">{initials}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
      <div className="panel__header">
        <div className="panel__title-group">
          <span className="panel__eyebrow">Listen</span>
          <h2 className="panel__title">Meine Watchlists</h2>
          <p className="panel__subtitle">
            Strukturiere deine Marktbeobachtung in fokussierten Sammlungen.
          </p>
        </div>
        <button type="button" className="btn" onClick={() => setShowModal(true)}>
          <span className="btn__icon" aria-hidden="true">＋</span>
          <span>Neue Watchlist</span>
        </button>
      </div>

      <div className="watchlist-container">
        {watchlists.length === 0 ? (
          <div className="empty-state empty-state--card">
            <h3>Leg direkt los</h3>
            <p>Erstelle deine erste Watchlist und sammle spannende Titel an einem Ort.</p>
            <button type="button" className="btn btn--ghost" onClick={() => setShowModal(true)}>
              <span className="btn__icon" aria-hidden="true">＋</span>
              <span>Watchlist anlegen</span>
            </button>
          </div>
        ) : (
          watchlists.map((wl) => {
            const initials = getInitials(wl.name);
            const isActive = currentWatchlist?.id === wl.id;

            return (
              <button
                key={wl.id}
                type="button"
                className={`watchlist-card ${isActive ? 'active' : ''}`}
                onClick={() => onWatchlistSelect(wl)}
                aria-pressed={isActive}
              >
                <span className="watchlist-card__icon" aria-hidden="true">{initials}</span>
                <div className="watchlist-card__body">
                  <span className="watchlist-card__badge">Watchlist</span>
                  <h3 className="watchlist-card__title">{wl.name}</h3>
                  <p className="watchlist-card__description">{wl.description || 'Keine Beschreibung hinterlegt.'}</p>
                </div>
                <span className="watchlist-card__chevron" aria-hidden="true">›</span>
              </button>
            );
          })
        )}
      </div>

      {showModal && (
        <div className="modal" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <span className="close" onClick={() => setShowModal(false)}>&times;</span>
            <h2>Neue Watchlist erstellen</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Beschreibung</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <button type="submit" className="btn">Erstellen</button>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}

export default WatchlistSection;

import React, { useState } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function WatchlistSection({ watchlists, currentWatchlist, onWatchlistSelect, onWatchlistsChange }) {
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
        setShowModal(false);
        setFormData({ name: '', description: '' });
        onWatchlistsChange();
      } else {
        alert('Fehler beim Erstellen der Watchlist');
      }
    } catch (error) {
      console.error('Error creating watchlist:', error);
      alert('Fehler beim Erstellen der Watchlist');
    }
  };

  return (
    <div className="section">
      <h2>Meine Watchlists</h2>
      <button className="btn" onClick={() => setShowModal(true)}>
        + Neue Watchlist
      </button>

      <div className="watchlist-container">
        {watchlists.length === 0 ? (
          <div className="empty-state">
            Keine Watchlists vorhanden. Erstellen Sie eine neue Watchlist.
          </div>
        ) : (
          watchlists.map((wl) => (
            <div
              key={wl.id}
              className={`watchlist-card ${currentWatchlist?.id === wl.id ? 'active' : ''}`}
              onClick={() => onWatchlistSelect(wl)}
            >
              <h3>{wl.name}</h3>
              <p>{wl.description || 'Keine Beschreibung'}</p>
            </div>
          ))
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
    </div>
  );
}

export default WatchlistSection;

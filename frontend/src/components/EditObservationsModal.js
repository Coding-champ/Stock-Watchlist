import React, { useState, useEffect, useRef } from 'react';
import API_BASE from '../config';

const OBSERVATION_REASON_OPTIONS = [
  { value: 'chart_technical', label: 'Charttechnische Indikatoren' },
  { value: 'fundamentals', label: 'Fundamentaldaten' },
  { value: 'industry', label: 'Branchendaten' },
  { value: 'economics', label: 'Wirtschaftsdaten' }
];

function EditObservationsModal({ stock, watchlistId, onClose, onSaved, onShowToast }) {
  const [observationReasons, setObservationReasons] = useState([]);
  const [observationNotes, setObservationNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [showReasonsDropdown, setShowReasonsDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Initialisierung mit den aktuellen Werten
  useEffect(() => {
    if (stock) {
      setObservationReasons(Array.isArray(stock.observation_reasons) ? [...stock.observation_reasons] : []);
      setObservationNotes(stock.observation_notes || '');
    }
  }, [stock]);

  // Dropdown schließen bei Klick außerhalb
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowReasonsDropdown(false);
      }
    };

    if (showReasonsDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showReasonsDropdown]);

  const handleObservationReasonsChange = (value) => {
    if (observationReasons.includes(value)) {
      // Entfernen wenn bereits ausgewählt
      setObservationReasons(observationReasons.filter(r => r !== value));
    } else {
      // Hinzufügen wenn noch nicht ausgewählt
      setObservationReasons([...observationReasons, value]);
    }
  };

  const handleClearAll = () => {
    setObservationReasons([]);
    setObservationNotes('');
  };

  const handleSave = async (e) => {
    e.preventDefault();
    
    if (!stock || !watchlistId) {
      if (onShowToast) {
        onShowToast('Fehler: Stock oder Watchlist-ID fehlt', 'error');
      }
      return;
    }

    setSaving(true);

    try {
      const trimmedNotes = observationNotes.trim();
      
      const payload = {
        observation_reasons: observationReasons,
        observation_notes: trimmedNotes || null
      };

      const response = await fetch(`${API_BASE}/stocks/${stock.id}?watchlist_id=${watchlistId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        if (onShowToast) {
          onShowToast(`Beobachtungen aktualisiert · ${stock.name}`, 'success');
        }
        if (onSaved) {
          onSaved();
        }
        onClose();
      } else {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || 'Fehler beim Speichern';
        if (onShowToast) {
          onShowToast(errorMessage, 'error');
        }
      }
    } catch (error) {
      console.error('Error updating observations:', error);
      if (onShowToast) {
        onShowToast('Fehler beim Speichern der Beobachtungen', 'error');
      }
    } finally {
      setSaving(false);
    }
  };

  if (!stock) return null;

  return (
    <div className="modal modal--overlay" onClick={onClose}>
      <div className="modal-content modal-content--medium" onClick={(e) => e.stopPropagation()}>
        <span className="close" onClick={onClose}>&times;</span>
        <h2>Beobachtungen bearbeiten</h2>
        <p className="modal-subtitle">{stock.name} ({stock.ticker_symbol})</p>

        <form onSubmit={handleSave}>
          {/* Beobachtungsgründe */}
          <div className="form-group observation-section__reasons">
            <label htmlFor="observation-reasons-edit">
              Beobachtungsgründe
            </label>
            
            <div className="custom-dropdown" ref={dropdownRef}>
              <button
                type="button"
                className="dropdown-trigger"
                onClick={() => setShowReasonsDropdown(!showReasonsDropdown)}
              >
                {observationReasons.length > 0 
                  ? `${observationReasons.length} ausgewählt` 
                  : 'Kategorien auswählen'}
                <span className="dropdown-arrow">▼</span>
              </button>
              
              {showReasonsDropdown && (
                <div className="dropdown-menu">
                  {OBSERVATION_REASON_OPTIONS.map((option) => (
                    <label key={option.value} className="dropdown-item">
                      <input
                        type="checkbox"
                        checked={observationReasons.includes(option.value)}
                        onChange={() => handleObservationReasonsChange(option.value)}
                      />
                      <span>{option.label}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
            
            {/* Ausgewählte Kategorien anzeigen */}
            {observationReasons.length > 0 && (
              <div className="selected-tags">
                {observationReasons.map((reason) => {
                  const option = OBSERVATION_REASON_OPTIONS.find(opt => opt.value === reason);
                  return option ? (
                    <span key={reason} className="tag">
                      {option.label}
                      <button
                        type="button"
                        className="tag-remove"
                        onClick={() => handleObservationReasonsChange(reason)}
                      >
                        ×
                      </button>
                    </span>
                  ) : null;
                })}
              </div>
            )}
          </div>

          {/* Bemerkungen */}
          <div className="form-group observation-section__notes">
            <label htmlFor="observation-notes-edit">
              Bemerkungen
            </label>
            <textarea
              id="observation-notes-edit"
              placeholder="z.B. Beobachte starkes Momentum nach dem Earnings Call, Setup läuft gut..."
              value={observationNotes}
              onChange={(e) => setObservationNotes(e.target.value)}
              rows={4}
            />
            <small className="form-hint">
              Notiere hier deine persönlichen Einschätzungen, Setups oder wichtige Beobachtungen zu dieser Aktie.
            </small>
          </div>

          {/* Buttons */}
          <div className="modal-actions">
            <button
              type="button"
              className="btn btn--ghost"
              onClick={handleClearAll}
              disabled={saving}
            >
              Alle löschen
            </button>
            <div className="modal-actions-right">
              <button
                type="button"
                className="btn btn--secondary"
                onClick={onClose}
                disabled={saving}
              >
                Abbrechen
              </button>
              <button
                type="submit"
                className="btn"
                disabled={saving}
              >
                {saving ? 'Speichern...' : 'Speichern'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default EditObservationsModal;

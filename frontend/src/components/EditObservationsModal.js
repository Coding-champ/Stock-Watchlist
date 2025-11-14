import React, { useState, useEffect } from 'react';
import ObservationFields from './ObservationFields';
import { useApi } from '../hooks/useApi';

function EditObservationsModal({ stock, watchlistId, onClose, onSaved, onShowToast }) {
  const [observationReasons, setObservationReasons] = useState([]);
  const [observationNotes, setObservationNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const { fetchApi } = useApi();
  
  // Initialisierung mit den aktuellen Werten
  useEffect(() => {
    if (stock) {
      setObservationReasons(Array.isArray(stock.observation_reasons) ? [...stock.observation_reasons] : []);
      setObservationNotes(stock.observation_notes || '');
    }
  }, [stock]);

  // Note: ObservationFields uses setObservationReasons directly; no local handler required

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

      await fetchApi(`/stocks/${stock.id}?watchlist_id=${watchlistId}`, {
        method: 'PUT',
        body: payload,
        onError: (err) => {
          if (onShowToast) {
            onShowToast(err.message || 'Fehler beim Speichern', 'error');
          }
        }
      });

      if (onShowToast) {
        onShowToast(`Beobachtungen aktualisiert · ${stock.name}`, 'success');
      }
      if (onSaved) {
        onSaved();
      }
      onClose();
    } catch (error) {
      console.error('Error updating observations:', error);
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
          <ObservationFields
            reasons={observationReasons}
            setReasons={setObservationReasons}
            notes={observationNotes}
            setNotes={setObservationNotes}
            reasonsLabel="Beobachtungsgründe"
            notesLabel="Bemerkungen"
            notesPlaceholder="z.B. Beobachte starkes Momentum nach dem Earnings Call, Setup läuft gut..."
          />

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

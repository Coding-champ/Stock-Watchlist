import React, { useState } from 'react';
import { useAlerts } from '../hooks/useAlerts';

const API_BASE = process.env.REACT_APP_API_BASE || '';

// Funktion zum Ermitteln der Währung
function getCurrencyForStock(stock) {
  if (!stock) return '$'; // Fallback

  // Nach Ticker-Symbol (Suffix)
  if (stock.ticker_symbol) {
    if (stock.ticker_symbol.endsWith('.DE') || 
        stock.ticker_symbol.endsWith('.F') || 
        stock.ticker_symbol.endsWith('.DU')) {
      return '€'; // Deutsche Börsen
    }
    if (stock.ticker_symbol.endsWith('.L')) {
      return '£'; // London
    }
    if (stock.ticker_symbol.endsWith('.TO')) {
      return 'C$'; // Toronto
    }
    if (stock.ticker_symbol.endsWith('.AX')) {
      return 'A$'; // Australien
    }
    if (stock.ticker_symbol.endsWith('.T')) {
      return '¥'; // Tokyo
    }
    if (stock.ticker_symbol.endsWith('.SW')) {
      return 'CHF'; // Schweiz
    }
  }
  
  // 3. Fallback zu USD
  return '$';
}

// Alarm-Typen mit deutschen Bezeichnungen
const getAlertTypes = (stock) => [
  { value: 'price', label: 'Preis', unit: getCurrencyForStock(stock), needsTimeframe: false },
  { value: 'pe_ratio', label: 'KGV (P/E Ratio)', unit: '', needsTimeframe: false },
  { value: 'rsi', label: 'RSI', unit: '', needsTimeframe: false },
  { value: 'volatility', label: 'Volatilität', unit: '%', needsTimeframe: false },
  { value: 'price_change_percent', label: 'Prozentuale Preisänderung', unit: '%', needsTimeframe: true },
  { value: 'ma_cross', label: 'Moving Average Cross (50/200)', unit: '', needsTimeframe: false, specialConditions: true },
  { value: 'volume_spike', label: 'Volumen-Spike', unit: 'x', needsTimeframe: false },
  { value: 'earnings', label: 'Earnings-Termin', unit: 'Tage', needsTimeframe: true, earningsAlert: true },
  { value: 'composite', label: 'Composite (UND-Verknüpfung)', unit: '', needsTimeframe: false, isComposite: true }
];

// Bedingungen
const CONDITIONS = [
  { value: 'above', label: 'über' },
  { value: 'below', label: 'unter' },
  { value: 'equals', label: 'gleich' }
];

// Spezielle Bedingungen für MA Cross
const MA_CROSS_CONDITIONS = [
  { value: 'cross_above', label: 'kreuzt nach oben (Golden Cross)' },
  { value: 'cross_below', label: 'kreuzt nach unten (Death Cross)' }
];

// Bedingung für Earnings
const EARNINGS_CONDITIONS = [
  { value: 'before', label: 'vor Earnings-Termin' }
];

// Timeframe-Optionen für prozentuale Änderungen
const TIMEFRAME_OPTIONS = [
  { value: 1, label: '1 Tag' },
  { value: 5, label: '5 Tage' },
  { value: 7, label: '1 Woche' },
  { value: 30, label: '1 Monat' }
];

// Timeframe-Optionen für Earnings (Tage vorher)
const EARNINGS_TIMEFRAME_OPTIONS = [
  { value: 1, label: '1 Tag vorher' },
  { value: 3, label: '3 Tage vorher' },
  { value: 7, label: '1 Woche vorher' },
  { value: 14, label: '2 Wochen vorher' }
];

function AlertModal({ stock, existingAlert = null, onClose, onAlertSaved }) {
  const isEditMode = !!existingAlert;
  const { createAlert, updateAlert } = useAlerts(stock.id);
  
  const [formData, setFormData] = useState({
    alert_type: existingAlert?.alert_type || 'price',
    condition: existingAlert?.condition || 'above',
    threshold_value: existingAlert?.threshold_value || '',
    timeframe_days: existingAlert?.timeframe_days || 1,
    expiry_date: existingAlert?.expiry_date ? formatDateForInput(existingAlert.expiry_date) : '',
    notes: existingAlert?.notes || '',
    is_active: existingAlert?.is_active ?? true
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function formatDateForInput(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  const ALERT_TYPES = getAlertTypes(stock);
  const currentAlertType = ALERT_TYPES.find(at => at.value === formData.alert_type);
  const needsTimeframe = currentAlertType?.needsTimeframe || false;
  const hasSpecialConditions = currentAlertType?.specialConditions || false;
  const isEarningsAlert = currentAlertType?.earningsAlert || false;
  const isComposite = currentAlertType?.isComposite || false;
  
  // Bestimme verfügbare Bedingungen
  let availableConditions = CONDITIONS;
  if (hasSpecialConditions) availableConditions = MA_CROSS_CONDITIONS;
  if (isEarningsAlert) availableConditions = EARNINGS_CONDITIONS;
  
  // Bestimme Timeframe-Optionen
  const timeframeOptions = isEarningsAlert ? EARNINGS_TIMEFRAME_OPTIONS : TIMEFRAME_OPTIONS;

  // Handler für Alarm-Typ-Änderung - setze passende Standardwerte
  const handleAlertTypeChange = (newType) => {
    const newAlertType = ALERT_TYPES.find(at => at.value === newType);
    const needsSpecialConditions = newAlertType?.specialConditions || false;
    const needsEarningsCondition = newAlertType?.earningsAlert || false;
    
    let defaultCondition = 'above';
    if (needsSpecialConditions) defaultCondition = 'cross_above';
    if (needsEarningsCondition) defaultCondition = 'before';
    
    setFormData({
      ...formData,
      alert_type: newType,
      condition: defaultCondition,
      threshold_value: needsSpecialConditions ? 0 : formData.threshold_value,
      timeframe_days: needsEarningsCondition ? 7 : formData.timeframe_days
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    
    // Validierung - Schwellenwert nur für bestimmte Alarm-Typen
    if (!hasSpecialConditions && !isEarningsAlert && !isComposite) {
      if (!formData.threshold_value || isNaN(formData.threshold_value)) {
        setError('Bitte geben Sie einen gültigen Schwellenwert ein.');
        return;
      }
    }

    try {
      setLoading(true);

      const payload = {
        stock_id: stock.id,
        alert_type: formData.alert_type,
        condition: formData.condition,
        threshold_value: (hasSpecialConditions || isEarningsAlert || isComposite) ? 0 : parseFloat(formData.threshold_value),
        timeframe_days: (needsTimeframe || isEarningsAlert) ? parseInt(formData.timeframe_days) : null,
        composite_conditions: isComposite ? formData.composite_conditions : null,
        is_active: formData.is_active,
        notes: formData.notes || null,
        expiry_date: formData.expiry_date ? new Date(formData.expiry_date).toISOString() : null
      };

      let savedAlert;
      if (isEditMode) {
        // Update existing alert
        savedAlert = await updateAlert(existingAlert.id, payload);
      } else {
        // Create new alert
        savedAlert = await createAlert(payload);
      }

      if (!savedAlert) {
        throw new Error('Fehler beim Speichern des Alarms');
      }
      
      if (onAlertSaved) {
        onAlertSaved(savedAlert);
      }
      
      onClose();
    } catch (err) {
      console.error('Error saving alert:', err);
      console.error('Error details:', {
        message: err.message,
        stack: err.stack,
        apiBase: API_BASE,
        payload: {
          stock_id: stock.id,
          alert_type: formData.alert_type,
          condition: formData.condition,
          threshold_value: formData.threshold_value
        }
      });
      setError(err.message || 'Fehler beim Speichern des Alarms');
    } finally {
      setLoading(false);
    }
  };

  const selectedAlertType = ALERT_TYPES.find(t => t.value === formData.alert_type);
  const currentUnit = selectedAlertType?.unit || '';

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal-content alert-modal" onClick={(e) => e.stopPropagation()}>
        <span className="close" onClick={onClose}>&times;</span>
        
        <h2>
          {isEditMode ? '✏️ Alarm bearbeiten' : '🔔 Neuer Alarm'}
        </h2>
        <p className="modal-subtitle">
          {stock.name} ({stock.ticker_symbol})
        </p>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Alarm-Typ Dropdown */}
          <div className="form-group">
            <label>Alarm-Typ *</label>
            <select
              required
              value={formData.alert_type}
              onChange={(e) => handleAlertTypeChange(e.target.value)}
              disabled={loading}
            >
              {ALERT_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Bedingung & Schwellenwert */}
          <div className="form-row">
            <div className="form-group">
              <label>Bedingung *</label>
              <select
                required
                value={formData.condition}
                onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                disabled={loading}
              >
                {availableConditions.map(cond => (
                  <option key={cond.value} value={cond.value}>
                    {cond.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Nur Schwellenwert anzeigen wenn nicht MA Cross, Earnings oder Composite */}
            {!hasSpecialConditions && !isEarningsAlert && !isComposite && (
              <div className="form-group">
                <label>Schwellenwert *</label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.threshold_value}
                    onChange={(e) => setFormData({ ...formData, threshold_value: e.target.value })}
                    disabled={loading}
                    placeholder="z.B. 150.00"
                  />
                  {currentUnit && (
                    <span style={{
                      position: 'absolute',
                      right: '10px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: '#666',
                      pointerEvents: 'none'
                    }}>
                      {currentUnit}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Timeframe für prozentuale Änderungen und Earnings */}
          {(needsTimeframe || isEarningsAlert) && (
            <div className="form-group">
              <label>{isEarningsAlert ? 'Wann warnen? *' : 'Zeitraum *'}</label>
              <select
                required
                value={formData.timeframe_days}
                onChange={(e) => setFormData({ ...formData, timeframe_days: e.target.value })}
                disabled={loading}
              >
                {timeframeOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* MA Cross braucht keinen Schwellenwert, zeige Info */}
          {hasSpecialConditions && (
            <div className="form-group">
              <p style={{ 
                fontSize: '0.9em', 
                color: '#666', 
                padding: '10px', 
                backgroundColor: '#f5f5f5', 
                borderRadius: '4px' 
              }}>
                ℹ️ <strong>Moving Average Cross:</strong> Der Alarm wird ausgelöst, wenn die 50-Tage-Linie die 200-Tage-Linie kreuzt.
              </p>
            </div>
          )}

          {/* Earnings Info */}
          {isEarningsAlert && (
            <div className="form-group">
              <p style={{ 
                fontSize: '0.9em', 
                color: '#666', 
                padding: '10px', 
                backgroundColor: '#fff7ed', 
                borderRadius: '4px',
                border: '1px solid #fed7aa'
              }}>
                📅 <strong>Earnings-Alarm:</strong> Sie werden benachrichtigt, wenn der nächste Earnings-Termin im gewählten Zeitraum liegt.
              </p>
            </div>
          )}

          {/* Composite Info - Vorerst nur Hinweis */}
          {isComposite && (
            <div className="form-group">
              <p style={{ 
                fontSize: '0.9em', 
                color: '#ff9800', 
                padding: '12px', 
                backgroundColor: '#fff3e0', 
                borderRadius: '4px',
                border: '1px solid #ffb74d'
              }}>
                ⚠️ <strong>Composite Alarme:</strong> Diese Funktion ist noch in Entwicklung. Erstellen Sie mehrere einzelne Alarme als Workaround.
              </p>
            </div>
          )}

          {/* Ablaufdatum (optional) */}
          <div className="form-group">
            <label>
              Ablaufdatum (optional)
              <span style={{ fontSize: '0.85em', color: '#999', marginLeft: '5px' }}>
                - Alarm wird automatisch deaktiviert
              </span>
            </label>
            <input
              type="date"
              value={formData.expiry_date}
              onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
              disabled={loading}
              min={new Date().toISOString().split('T')[0]}
            />
          </div>

          {/* Notizen (optional) */}
          <div className="form-group">
            <label>Notizen (optional)</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              disabled={loading}
              placeholder="z.B. Kaufsignal wenn RSI steigt..."
              rows={3}
            />
          </div>

          {/* Status (nur im Edit-Modus) */}
          {isEditMode && (
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  disabled={loading}
                />
                Alarm ist aktiv
              </label>
            </div>
          )}

          {/* Buttons */}
          <div className="form-actions">
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={onClose}
              disabled={loading}
            >
              Abbrechen
            </button>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Speichert...' : (isEditMode ? 'Aktualisieren' : 'Alarm erstellen')}
            </button>
          </div>
        </form>

        {/* Info-Hinweis */}
        <div className="info-hint">
          💡 <strong>Hinweis:</strong> Der Alarm wird ausgelöst, wenn die Bedingung erfüllt ist.
          {!isEditMode && ' Sie können mehrere Alarme für eine Aktie erstellen.'}
        </div>
      </div>
    </div>
  );
}

export default AlertModal;

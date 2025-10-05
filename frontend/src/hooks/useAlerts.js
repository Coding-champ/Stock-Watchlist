import { useState, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || '';

/**
 * Custom Hook for managing alerts
 * @param {number|null} stockId - Optional stock ID to filter alerts
 * @param {function} showToast - Optional toast notification function
 */
export function useAlerts(stockId = null, showToast = null) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load alerts (all or filtered by stock)
  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const url = stockId 
        ? `${API_BASE}/alerts/?stock_id=${stockId}`
        : `${API_BASE}/alerts/`;
      
      const response = await fetch(url);
      const data = await response.json();
      setAlerts(data);
      return data;
    } catch (error) {
      console.error('Error loading alerts:', error);
      if (showToast) showToast('Fehler beim Laden der Alarme', 'error');
      throw error;
    } finally {
      setLoading(false);
    }
  }, [stockId, showToast]);

  // Toggle alert active status
  const toggleAlert = useCallback(async (alert) => {
    try {
      const response = await fetch(`${API_BASE}/alerts/${alert.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          is_active: !alert.is_active
        })
      });

      if (response.ok) {
        await loadAlerts();
        if (showToast) {
          showToast(
            `Alarm ${alert.is_active ? 'deaktiviert' : 'aktiviert'}`, 
            'success'
          );
        }
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error toggling alert:', error);
      if (showToast) showToast('Fehler beim Aktualisieren des Alarms', 'error');
      return false;
    }
  }, [loadAlerts, showToast]);

  // Delete alert
  const deleteAlert = useCallback(async (alertId, skipConfirm = false) => {
    if (!skipConfirm && !window.confirm('Möchten Sie diesen Alarm wirklich löschen?')) {
      return false;
    }

    try {
      const response = await fetch(`${API_BASE}/alerts/${alertId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadAlerts();
        if (showToast) showToast('Alarm gelöscht', 'success');
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error deleting alert:', error);
      if (showToast) showToast('Fehler beim Löschen des Alarms', 'error');
      return false;
    }
  }, [loadAlerts, showToast]);

  // Create alert
  const createAlert = useCallback(async (alertData) => {
    try {
      const response = await fetch(`${API_BASE}/alerts/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(alertData)
      });

      if (response.ok) {
        const newAlert = await response.json();
        await loadAlerts();
        if (showToast) showToast('Alarm erstellt', 'success');
        return newAlert;
      }
      return null;
    } catch (error) {
      console.error('Error creating alert:', error);
      if (showToast) showToast('Fehler beim Erstellen des Alarms', 'error');
      return null;
    }
  }, [loadAlerts, showToast]);

  // Update alert
  const updateAlert = useCallback(async (alertId, alertData) => {
    try {
      const response = await fetch(`${API_BASE}/alerts/${alertId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(alertData)
      });

      if (response.ok) {
        const updatedAlert = await response.json();
        await loadAlerts();
        if (showToast) showToast('Alarm aktualisiert', 'success');
        return updatedAlert;
      }
      return null;
    } catch (error) {
      console.error('Error updating alert:', error);
      if (showToast) showToast('Fehler beim Aktualisieren des Alarms', 'error');
      return null;
    }
  }, [loadAlerts, showToast]);

  // Check all alerts
  const checkAllAlerts = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/alerts/check-all`, {
        method: 'POST'
      });
      const result = await response.json();
      await loadAlerts();
      return result;
    } catch (error) {
      console.error('Error checking alerts:', error);
      if (showToast) showToast('Fehler beim Prüfen der Alarme', 'error');
      throw error;
    }
  }, [loadAlerts, showToast]);

  // Check single alert
  const checkAlert = useCallback(async (alertId) => {
    try {
      const response = await fetch(`${API_BASE}/alerts/check/${alertId}`, {
        method: 'POST'
      });
      const result = await response.json();
      await loadAlerts();
      return result;
    } catch (error) {
      console.error('Error checking alert:', error);
      if (showToast) showToast('Fehler beim Prüfen des Alarms', 'error');
      throw error;
    }
  }, [loadAlerts, showToast]);

  return {
    alerts,
    loading,
    loadAlerts,
    toggleAlert,
    deleteAlert,
    createAlert,
    updateAlert,
    checkAllAlerts,
    checkAlert
  };
}

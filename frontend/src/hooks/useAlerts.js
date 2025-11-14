import { useState, useCallback } from 'react';
import { useApi } from './useApi';

/**
 * Custom Hook for managing alerts
 * @param {number|null} stockId - Optional stock ID to filter alerts
 * @param {function} showToast - Optional toast notification function
 */
export function useAlerts(stockId = null, showToast = null) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const { fetchApi } = useApi();

  // Load alerts (all or filtered by stock)
  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const endpoint = stockId 
        ? `/alerts/?stock_id=${stockId}`
        : `/alerts/`;
      const data = await fetchApi(endpoint, {
        onError: () => showToast && showToast('Fehler beim Laden der Alarme', 'error')
      });
      setAlerts(data);
      return data;
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  }, [stockId, showToast, fetchApi]);

  // Toggle alert active status
  const toggleAlert = useCallback(async (alert) => {
    try {
      await fetchApi(`/alerts/${alert.id}`, {
        method: 'PUT',
        body: { is_active: !alert.is_active },
        onError: () => showToast && showToast('Fehler beim Aktualisieren des Alarms', 'error')
      });
      await loadAlerts();
      if (showToast) {
        showToast(
          `Alarm ${alert.is_active ? 'deaktiviert' : 'aktiviert'}`, 
          'success'
        );
      }
      return true;
    } catch (error) {
      return false;
    }
  }, [loadAlerts, showToast, fetchApi]);

  // Delete alert
  const deleteAlert = useCallback(async (alertId, skipConfirm = false) => {
    if (!skipConfirm && !window.confirm('Möchten Sie diesen Alarm wirklich löschen?')) {
      return false;
    }

    try {
      await fetchApi(`/alerts/${alertId}`, {
        method: 'DELETE',
        onError: () => showToast && showToast('Fehler beim Löschen des Alarms', 'error')
      });
      await loadAlerts();
      if (showToast) showToast('Alarm gelöscht', 'success');
      return true;
    } catch (error) {
      return false;
    }
  }, [loadAlerts, showToast, fetchApi]);

  // Create alert
  const createAlert = useCallback(async (alertData) => {
    try {
      const newAlert = await fetchApi(`/alerts/`, {
        method: 'POST',
        body: alertData,
        onError: () => showToast && showToast('Fehler beim Erstellen des Alarms', 'error')
      });
      await loadAlerts();
      if (showToast) showToast('Alarm erstellt', 'success');
      return newAlert;
    } catch (error) {
      return null;
    }
  }, [loadAlerts, showToast, fetchApi]);

  // Update alert
  const updateAlert = useCallback(async (alertId, alertData) => {
    try {
      const updatedAlert = await fetchApi(`/alerts/${alertId}`, {
        method: 'PUT',
        body: alertData,
        onError: () => showToast && showToast('Fehler beim Aktualisieren des Alarms', 'error')
      });
      await loadAlerts();
      if (showToast) showToast('Alarm aktualisiert', 'success');
      return updatedAlert;
    } catch (error) {
      return null;
    }
  }, [loadAlerts, showToast, fetchApi]);

  // Check all alerts
  const checkAllAlerts = useCallback(async () => {
    try {
      const result = await fetchApi(`/alerts/check-all`, {
        method: 'POST',
        onError: () => showToast && showToast('Fehler beim Prüfen der Alarme', 'error')
      });
      await loadAlerts();
      return result;
    } catch (error) {
      throw error;
    }
  }, [loadAlerts, showToast, fetchApi]);

  // Check single alert
  const checkAlert = useCallback(async (alertId) => {
    try {
      const result = await fetchApi(`/alerts/check/${alertId}`, {
        method: 'POST',
        onError: () => showToast && showToast('Fehler beim Prüfen des Alarms', 'error')
      });
      await loadAlerts();
      return result;
    } catch (error) {
      throw error;
    }
  }, [loadAlerts, showToast, fetchApi]);

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

import React, { useState, useEffect, useCallback } from 'react';
import '../../styles/skeletons.css';
import { getAlertTypeLabel, getConditionLabel, getUnitForAlertType, formatNumber } from '../../utils/currencyUtils';
import { useAlerts } from '../../hooks/useAlerts';
import API_BASE from '../../config';
import { useQueryClient } from '@tanstack/react-query';

function AlertsView({ showToast }) {
  const { alerts, loading, loadAlerts, toggleAlert, deleteAlert, checkAllAlerts } = useAlerts(null, showToast);
  const [stocks, setStocks] = useState({});
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState('all'); // 'all', 'active', 'inactive', 'triggered'
  const [sortBy, setSortBy] = useState('created'); // 'created', 'triggered', 'stock', 'type'

  const loadAllData = useCallback(async () => {
    try {
      // Load alerts
      await loadAlerts();
      
      // Load all stocks to get names
      const url = `${API_BASE}/watchlists/`;
      const watchlistsData = await queryClient.fetchQuery(['api', url], async () => {
        const r = await fetch(url);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }, { staleTime: 60 * 1000 });
      
      // Create stock lookup
      const stockLookup = {};
      watchlistsData.forEach(watchlist => {
        watchlist.stocks?.forEach(stock => {
          stockLookup[stock.id] = stock;
        });
      });
      
      setStocks(stockLookup);
    } catch (error) {
      console.error('Error loading data:', error);
      if (showToast) showToast('Fehler beim Laden der Daten', 'error');
    }
  }, [loadAlerts, showToast, queryClient]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  const handleToggleAlert = async (alert) => {
    await toggleAlert(alert);
  };

  const handleDeleteAlert = async (alertId) => {
    await deleteAlert(alertId);
  };

  const handleCheckAll = async () => {
    try {
      const result = await checkAllAlerts();
      
      // Show toast notifications for triggered alerts
      if (result.triggered_count > 0 && result.triggered_alerts) {
        result.triggered_alerts.forEach((triggered, index) => {
          setTimeout(() => {
            const alertTypeLabel = getAlertTypeLabel(triggered.alert_type);
            const conditionLabel = getConditionLabel(triggered.condition);
            const message = `🔔 ${triggered.stock_name} (${triggered.ticker_symbol}) · ${alertTypeLabel} ${conditionLabel} ${triggered.threshold_value}`;
            if (showToast) showToast(message, 'warning');
          }, index * 1000); // Stagger toasts by 1 second
        });
      }
      
      if (showToast) {
        const summaryMessage = `${result.checked_count || 0} Alarme geprüft · ${result.triggered_count || 0} ausgelöst`;
        setTimeout(() => {
          showToast(summaryMessage, result.triggered_count > 0 ? 'info' : 'success');
        }, (result.triggered_alerts?.length || 0) * 1000);
      }
    } catch (error) {
      console.error('Error checking alerts:', error);
    }
  };

  // Filter alerts
  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'active') return alert.is_active;
    if (filter === 'inactive') return !alert.is_active;
    if (filter === 'triggered') return alert.trigger_count > 0;
    return true;
  });

  // Sort alerts
  const sortedAlerts = [...filteredAlerts].sort((a, b) => {
    if (sortBy === 'created') {
      return new Date(b.created_at) - new Date(a.created_at);
    }
    if (sortBy === 'triggered') {
      if (!a.last_triggered && !b.last_triggered) return 0;
      if (!a.last_triggered) return 1;
      if (!b.last_triggered) return -1;
      return new Date(b.last_triggered) - new Date(a.last_triggered);
    }
    if (sortBy === 'stock') {
      const stockA = stocks[a.stock_id]?.name || '';
      const stockB = stocks[b.stock_id]?.name || '';
      return stockA.localeCompare(stockB);
    }
    if (sortBy === 'type') {
      return a.alert_type.localeCompare(b.alert_type);
    }
    return 0;
  });

  // Statistics
  const stats = {
    total: alerts.length,
    active: alerts.filter(a => a.is_active).length,
    triggered: alerts.filter(a => a.trigger_count > 0).length,
    lastHour: alerts.filter(a => 
      a.last_triggered && 
      (new Date() - new Date(a.last_triggered)) < 3600000
    ).length
  };

  if (loading) {
    return (
      <div className="panel">
        <div style={{ padding: '40px', textAlign: 'center' }}>
          Lade Alarme...
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      {/* Header */}
      <div className="panel__title-group">
        <div className="panel__eyebrow">Überwachung</div>
        <div className="panel__title">📊 Alarm-Dashboard</div>
        <div className="panel__subtitle">Übersicht und Verwaltung aller Alarme</div>
      </div>

      {/* Statistics */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '16px', 
        marginTop: '24px',
        marginBottom: '24px'
      }}>
        <div className="panel" style={{ 
          padding: '16px', 
          background: 'linear-gradient(135deg, #f9fafb 0%, #ffffff 100%)',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '4px' }}>
            Gesamt
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: '#1f2937' }}>
            {stats.total}
          </div>
        </div>
        <div className="panel" style={{ 
          padding: '16px', 
          background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
          border: '1px solid #bbf7d0'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#166534', marginBottom: '4px' }}>
            Aktiv
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: '#15803d' }}>
            {stats.active}
          </div>
        </div>
        <div className="panel" style={{ 
          padding: '16px', 
          background: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
          border: '1px solid #fecaca'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#991b1b', marginBottom: '4px' }}>
            Ausgelöst
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: '#dc2626' }}>
            {stats.triggered}
          </div>
        </div>
        <div className="panel" style={{ 
          padding: '16px', 
          background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
          border: '1px solid #fcd34d'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#92400e', marginBottom: '4px' }}>
            Letzte Stunde
          </div>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: '#d97706' }}>
            {stats.lastHour}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="filter-bar filter-bar--surface" style={{ marginBottom: '20px' }}>
        <div className="filter-group">
          <label htmlFor="alert-filter">Filter</label>
          <select 
            id="alert-filter"
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">Alle Alarme</option>
            <option value="active">Nur Aktive</option>
            <option value="inactive">Nur Inaktive</option>
            <option value="triggered">Bereits ausgelöst</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="alert-sort">Sortierung</label>
          <select 
            id="alert-sort"
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="created">Erstellungsdatum</option>
            <option value="triggered">Zuletzt ausgelöst</option>
            <option value="stock">Nach Aktie</option>
            <option value="type">Nach Typ</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto' }}>
          <button
            onClick={handleCheckAll}
            className="btn"
          >
            <span className="btn__icon">🔍</span>
            Alle Alarme prüfen
          </button>
        </div>
      </div>

      {/* Alerts List */}
      {sortedAlerts.length === 0 ? (
        <div className="empty-state empty-state--hero">
          <h2>Keine Alarme gefunden</h2>
          <p>
            {filter === 'all' 
              ? 'Es wurden noch keine Alarme erstellt.' 
              : `Keine Alarme für den Filter "${filter}" gefunden.`}
          </p>
          <p className="empty-state__hint">
            Erstelle Alarme in den Aktiendetails, um über wichtige Kursveränderungen benachrichtigt zu werden.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {sortedAlerts.map(alert => {
            const stock = stocks[alert.stock_id];
            const unit = stock ? getUnitForAlertType(alert.alert_type, stock) : '';
            
            return (
              <div 
                key={alert.id}
                className="panel"
                style={{
                  padding: '20px',
                  background: alert.is_active ? '#ffffff' : '#f9fafb',
                  border: `1px solid ${alert.is_active ? '#e5e7eb' : '#d1d5db'}`,
                  opacity: alert.is_active ? 1 : 0.7,
                  transition: 'all var(--motion-short)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                  {/* Stock Info */}
                  <div style={{ flex: 1 }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px', 
                      marginBottom: '8px' 
                    }}>
                      <span style={{ 
                        fontWeight: '600', 
                        fontSize: '1.125rem',
                        color: '#1f2937'
                      }}>
                        {stock?.name || 'Unknown Stock'}
                      </span>
                      <span style={{ 
                        fontSize: '0.875rem', 
                        color: '#6b7280',
                        fontFamily: 'var(--font-mono)'
                      }}>
                        ({stock?.ticker_symbol || 'N/A'})
                      </span>
                    </div>
                    
                    {/* Alert Details */}
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      flexWrap: 'wrap',
                      marginBottom: '8px'
                    }}>
                      <span style={{
                        padding: '4px 10px',
                        background: '#f3f4f6',
                        borderRadius: '6px',
                        fontSize: '0.8125rem',
                        fontWeight: '600',
                        color: '#374151'
                      }}>
                        {getAlertTypeLabel(alert.alert_type)}
                      </span>
                      
                      {alert.alert_type !== 'ma_cross' && (
                        <span style={{ fontSize: '0.9375rem', color: '#4b5563', fontWeight: '500' }}>
                          {getConditionLabel(alert.condition)} {formatNumber(alert.threshold_value, 2)}{unit && ` ${unit}`}
                        </span>
                      )}
                      
                      {alert.timeframe_days && (
                        <span style={{ fontSize: '0.8125rem', color: '#6b7280' }}>
                          ({alert.timeframe_days} Tag{alert.timeframe_days > 1 ? 'e' : ''})
                        </span>
                      )}
                    </div>

                    {/* Trigger Info */}
                    {alert.last_triggered && (
                      <div style={{ 
                        fontSize: '0.8125rem', 
                        color: '#ff9800',
                        marginBottom: '4px',
                        fontWeight: '500'
                      }}>
                        🔔 Zuletzt ausgelöst: {new Date(alert.last_triggered).toLocaleString('de-DE')}
                        {alert.trigger_count > 1 && ` (${alert.trigger_count}x)`}
                      </div>
                    )}

                    {/* Notes */}
                    {alert.notes && (
                      <div style={{ 
                        fontSize: '0.9375rem', 
                        color: '#6b7280',
                        fontStyle: 'italic',
                        marginTop: '8px',
                        padding: '8px 12px',
                        background: '#f9fafb',
                        borderRadius: '6px',
                        borderLeft: '3px solid #e5e7eb'
                      }}>
                        💬 {alert.notes}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div style={{ 
                    display: 'flex', 
                    gap: '8px',
                    flexShrink: 0
                  }}>
                    <button
                      onClick={() => handleToggleAlert(alert)}
                      className="button"
                      style={{
                        padding: '8px 14px',
                        background: alert.is_active ? '#fef3c7' : '#d1fae5',
                        color: alert.is_active ? '#92400e' : '#065f46',
                        border: `1px solid ${alert.is_active ? '#fcd34d' : '#6ee7b7'}`,
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.8125rem',
                        fontWeight: '600',
                        transition: 'all var(--motion-short)'
                      }}
                    >
                      {alert.is_active ? '⏸️ Pause' : '▶️ Start'}
                    </button>
                    
                    <button
                      onClick={() => handleDeleteAlert(alert.id)}
                      className="button"
                      style={{
                        padding: '8px 14px',
                        background: '#fee2e2',
                        color: '#991b1b',
                        border: '1px solid #fecaca',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '0.8125rem',
                        fontWeight: '600',
                        transition: 'all var(--motion-short)'
                      }}
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default AlertsView;

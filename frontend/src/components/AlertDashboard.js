import React, { useState, useEffect } from 'react';
import { getAlertTypeLabel, getConditionLabel, getUnitForAlertType, formatNumber } from '../utils/currencyUtils';
import { useAlerts } from '../hooks/useAlerts';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function AlertDashboard({ onClose, showToast }) {
  const { alerts, loading, loadAlerts, toggleAlert, deleteAlert, checkAllAlerts } = useAlerts(null, showToast);
  const [stocks, setStocks] = useState({});
  const [filter, setFilter] = useState('all'); // 'all', 'active', 'inactive', 'triggered'
  const [sortBy, setSortBy] = useState('created'); // 'created', 'triggered', 'stock', 'type'

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      // Load alerts
      await loadAlerts();
      
      // Load all stocks to get names
      const watchlistsResponse = await fetch(`${API_BASE}/watchlists/`);
      const watchlistsData = await watchlistsResponse.json();
      
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
  };

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
      <div className="modal" onClick={onClose}>
        <div className="modal-content" style={{ maxWidth: '1200px' }} onClick={(e) => e.stopPropagation()}>
          <div style={{ padding: '40px', textAlign: 'center' }}>
            Lade Alarme...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '1200px', maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }} onClick={(e) => e.stopPropagation()}>
        <span className="close" onClick={onClose}>&times;</span>
        
        {/* Header */}
        <div style={{ padding: '24px 24px 0' }}>
          <h2 style={{ marginBottom: '8px' }}>📊 Alarm-Dashboard</h2>
          <p style={{ color: '#6b7280', marginBottom: '24px' }}>
            Übersicht aller Alarme
          </p>

          {/* Statistics */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(3, 1fr)', 
            gap: '12px', 
            marginBottom: '20px' 
          }}>
            <div style={{ 
              padding: '12px 16px', 
              background: '#f9fafb', 
              borderRadius: '8px',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '2px' }}>
                Gesamt
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1f2937' }}>
                {stats.total}
              </div>
            </div>
            <div style={{ 
              padding: '12px 16px', 
              background: '#f0fdf4', 
              borderRadius: '8px',
              border: '1px solid #bbf7d0'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#166534', marginBottom: '2px' }}>
                Aktiv
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#15803d' }}>
                {stats.active}
              </div>
            </div>
            <div style={{ 
              padding: '12px 16px', 
              background: '#fef2f2', 
              borderRadius: '8px',
              border: '1px solid #fecaca'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#991b1b', marginBottom: '2px' }}>
                Heute ausgelöst
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#dc2626' }}>
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
          </div>

          {/* Check All Button */}
          <div style={{ 
            marginBottom: '20px',
            paddingBottom: '20px',
            borderBottom: '1px solid #e5e7eb'
          }}>
            <button
              onClick={handleCheckAll}
              style={{ 
                padding: '8px 16px',
                background: '#7c3aed',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
            >
              🔍 Alle Alarme prüfen
            </button>
          </div>
        </div>        {/* Alerts List */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '0 24px 24px' 
        }}>
          {sortedAlerts.length === 0 ? (
            <div style={{ 
              padding: '40px', 
              textAlign: 'center', 
              color: '#6b7280' 
            }}>
              Keine Alarme gefunden
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {sortedAlerts.map(alert => {
                const stock = stocks[alert.stock_id];
                const unit = stock ? getUnitForAlertType(alert.alert_type, stock) : '';
                
                return (
                  <div 
                    key={alert.id}
                    style={{
                      padding: '16px',
                      background: alert.is_active ? '#ffffff' : '#f9fafb',
                      border: `1px solid ${alert.is_active ? '#e5e7eb' : '#d1d5db'}`,
                      borderRadius: '8px',
                      opacity: alert.is_active ? 1 : 0.7
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
                            fontSize: '1rem',
                            color: '#1f2937'
                          }}>
                            {stock?.name || 'Unknown Stock'}
                          </span>
                          <span style={{ 
                            fontSize: '0.875rem', 
                            color: '#6b7280' 
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
                            padding: '4px 8px',
                            background: '#f3f4f6',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: '500'
                          }}>
                            {getAlertTypeLabel(alert.alert_type)}
                          </span>
                          
                          {alert.alert_type !== 'ma_cross' && (
                            <span style={{ fontSize: '0.875rem', color: '#4b5563' }}>
                              {getConditionLabel(alert.condition)} {formatNumber(alert.threshold_value, 2)}{unit && ` ${unit}`}
                            </span>
                          )}
                          
                          {alert.timeframe_days && (
                            <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                              ({alert.timeframe_days} Tag{alert.timeframe_days > 1 ? 'e' : ''})
                            </span>
                          )}
                        </div>

                        {/* Trigger Info */}
                        {alert.last_triggered && (
                          <div style={{ 
                            fontSize: '0.75rem', 
                            color: '#ff9800',
                            marginBottom: '4px'
                          }}>
                            🔔 Zuletzt: {new Date(alert.last_triggered).toLocaleString('de-DE')}
                            {alert.trigger_count > 1 && ` (${alert.trigger_count}x)`}
                          </div>
                        )}

                        {/* Notes */}
                        {alert.notes && (
                          <div style={{ 
                            fontSize: '0.875rem', 
                            color: '#6b7280',
                            fontStyle: 'italic'
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
                          style={{
                            padding: '6px 12px',
                            background: alert.is_active ? '#fef3c7' : '#d1fae5',
                            color: alert.is_active ? '#92400e' : '#065f46',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.75rem',
                            fontWeight: '500'
                          }}
                        >
                          {alert.is_active ? '⏸️ Pause' : '▶️ Start'}
                        </button>
                        
                        <button
                          onClick={() => handleDeleteAlert(alert.id)}
                          style={{
                            padding: '6px 12px',
                            background: '#fee2e2',
                            color: '#991b1b',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.75rem',
                            fontWeight: '500'
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
      </div>
    </div>
  );
}

export default AlertDashboard;

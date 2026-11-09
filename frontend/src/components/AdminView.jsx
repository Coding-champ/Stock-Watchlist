import React, { useCallback, useEffect, useState } from 'react';
import API_BASE from '../config';
import './AdminView.css';

const emptyForm = {
  name: '',
  ticker_symbol: '',
  isin: '',
  wkn: '',
  country: '',
  industry: '',
  sector: '',
};

function AdminView({ showToast }) {
  const [assets, setAssets] = useState([]);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [reloadingAll, setReloadingAll] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [reloadingSelected, setReloadingSelected] = useState(false);
  const [ticker, setTicker] = useState('');
  const [importing, setImporting] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const loadAssets = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/admin/assets?include_archived=${includeArchived}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setAssets((await response.json()).items || []);
      setSelectedIds([]);
    } catch (error) {
      console.error('Admin assets could not be loaded:', error);
      showToast('Assets konnten nicht geladen werden', 'error');
    } finally {
      setLoading(false);
    }
  }, [includeArchived, showToast]);

  useEffect(() => { loadAssets(); }, [loadAssets]);

  const toggleSelected = (assetId) => {
    setSelectedIds((current) => current.includes(assetId)
      ? current.filter((id) => id !== assetId)
      : [...current, assetId]);
  };

  const toggleAllSelected = () => {
    setSelectedIds((current) => current.length === assets.length ? [] : assets.map((asset) => asset.id));
  };

  const reloadSelectedAssets = async () => {
    if (!selectedIds.length) return;
    setReloadingSelected(true);
    try {
      const response = await fetch(`${API_BASE}/admin/assets/reload-selected`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stock_ids: selectedIds }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
      await loadAssets();
      if (result.failed) {
        showToast(`${result.refreshed} ausgewählte Assets geladen, ${result.failed} fehlgeschlagen`, 'warning');
      } else {
        showToast(`${result.refreshed} ausgewählte Assets erfolgreich neu geladen`, 'success');
      }
    } catch (error) {
      showToast(`Reload selected fehlgeschlagen: ${error.message}`, 'error');
    } finally {
      setReloadingSelected(false);
    }
  };

  const reloadAllAssets = async () => {
    setReloadingAll(true);
    try {
      const response = await fetch(`${API_BASE}/admin/assets/reload-all`, { method: 'POST' });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || `HTTP ${response.status}`);
      await loadAssets();
      if (result.failed) {
        showToast(`${result.refreshed} Assets geladen, ${result.failed} fehlgeschlagen`, 'warning');
      } else {
        showToast(`${result.refreshed} Assets erfolgreich neu geladen`, 'success');
      }
    } catch (error) {
      showToast(`Reload all fehlgeschlagen: ${error.message}`, 'error');
    } finally {
      setReloadingAll(false);
    }
  };

  const reloadAsset = async (asset) => {
    setBusyId(asset.id);
    try {
      const response = await fetch(`${API_BASE}/admin/assets/${asset.id}/reload`, { method: 'POST' });
      if (!response.ok) throw new Error((await response.json()).detail || `HTTP ${response.status}`);
      await loadAssets();
      showToast(`Daten für ${asset.ticker_symbol} wurden neu geladen`, 'success');
    } catch (error) {
      showToast(`Reload fehlgeschlagen: ${error.message}`, 'error');
    } finally {
      setBusyId(null);
    }
  };

  const archiveAsset = async (asset) => {
    if (!window.confirm(`${asset.name} archivieren? Die Daten bleiben erhalten.`)) return;
    setBusyId(asset.id);
    try {
      const response = await fetch(`${API_BASE}/admin/assets/${asset.id}`, { method: 'DELETE' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      await loadAssets();
      showToast(`${asset.name} wurde archiviert`, 'success');
    } catch (error) {
      showToast('Asset konnte nicht archiviert werden', 'error');
    } finally {
      setBusyId(null);
    }
  };

  const restoreAsset = async (asset) => {
    setBusyId(asset.id);
    try {
      const response = await fetch(`${API_BASE}/admin/assets/${asset.id}/restore`, { method: 'POST' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      await loadAssets();
      showToast(`${asset.name} wurde wieder aktiviert`, 'success');
    } catch (error) {
      showToast('Asset konnte nicht aktiviert werden', 'error');
    } finally {
      setBusyId(null);
    }
  };

  const importAsset = async (event) => {
    event.preventDefault();
    if (!ticker.trim()) return;
    setImporting(true);
    try {
      const response = await fetch(`${API_BASE}/admin/assets/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker_symbol: ticker.trim(), period: 'max', interval: '1d' }),
      });
      if (!response.ok) throw new Error((await response.json()).detail || `HTTP ${response.status}`);
      setTicker('');
      await loadAssets();
      showToast('Asset und Historie wurden importiert', 'success');
    } catch (error) {
      showToast(`Import fehlgeschlagen: ${error.message}`, 'error');
    } finally {
      setImporting(false);
    }
  };

  const startEditing = (asset) => {
    setEditing(asset);
    setForm({
      name: asset.name || '',
      ticker_symbol: asset.ticker_symbol || '',
      isin: asset.isin || '',
      wkn: '',
      country: '',
      industry: '',
      sector: '',
    });
  };

  const saveAsset = async (event) => {
    event.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/admin/assets/${editing.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setEditing(null);
      await loadAssets();
      showToast('Asset gespeichert', 'success');
    } catch (error) {
      showToast('Asset konnte nicht gespeichert werden', 'error');
    }
  };

  return (
    <main className="layout__content admin-view">
      <section className="panel">
        <div className="panel__header">
          <div className="panel__title-group">
            <div className="panel__eyebrow">Administration</div>
            <div className="panel__title">Assets & Datenqualität</div>
            <div className="panel__subtitle">Stammdaten verwalten und fehlende Kurslieferungen gezielt erneut laden.</div>
          </div>
          <label className="admin-toggle">
            <input type="checkbox" checked={includeArchived} onChange={(event) => setIncludeArchived(event.target.checked)} />
            Archivierte anzeigen
          </label>
          <button className="btn btn--ghost" type="button" onClick={reloadAllAssets} disabled={reloadingAll || loading}>
            {reloadingAll ? 'Alle werden geladen …' : '↻ Reload all'}
          </button>
          <button className="btn btn--ghost" type="button" onClick={reloadSelectedAssets} disabled={!selectedIds.length || reloadingSelected || reloadingAll || loading}>
            {reloadingSelected ? 'Auswahl wird geladen …' : `↻ Reload selected${selectedIds.length ? ` (${selectedIds.length})` : ''}`}
          </button>
        </div>
        <form className="admin-import" onSubmit={importAsset}>
          <input value={ticker} onChange={(event) => setTicker(event.target.value)} placeholder="Ticker, z. B. AAPL" aria-label="Ticker-Symbol" />
          <button className="btn" type="submit" disabled={importing}>{importing ? 'Import läuft …' : 'Asset per Ticker importieren'}</button>
        </form>
      </section>

      <section className="panel admin-table-panel">
        {loading ? <div className="admin-empty">Assets werden geladen …</div> : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th><input type="checkbox" checked={assets.length > 0 && selectedIds.length === assets.length} onChange={toggleAllSelected} aria-label="Alle Assets auswählen" /></th>
                  <th>Typ</th><th>Name</th><th>ISIN</th><th>Datenquelle</th><th>Letzte Lieferung</th><th>Status</th><th>Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => (
                  <tr key={asset.id} className={!asset.is_active ? 'is-archived' : ''}>
                    <td><input type="checkbox" checked={selectedIds.includes(asset.id)} onChange={() => toggleSelected(asset.id)} aria-label={`${asset.name} auswählen`} /></td>
                    <td>{asset.asset_type}</td>
                    <td><strong>{asset.name}</strong><small>{asset.ticker_symbol}</small></td>
                    <td>{asset.isin || '—'}</td>
                    <td>{asset.data_source}</td>
                    <td>{asset.last_successful_delivery || 'Noch keine'}</td>
                    <td><span className={`admin-status admin-status--${asset.quality_status}`}>{asset.quality_status === 'ok' ? 'OK' : 'Fehlt'}</span></td>
                    <td className="admin-actions">
                      {asset.quality_status === 'missing' && <button className="btn btn--ghost" disabled={busyId === asset.id} onClick={() => reloadAsset(asset)}>{busyId === asset.id ? 'Lädt …' : '↻ Reload'}</button>}
                      <button className="btn btn--ghost" onClick={() => startEditing(asset)}>Bearbeiten</button>
                      {asset.is_active ? <button className="btn btn-danger" disabled={busyId === asset.id} onClick={() => archiveAsset(asset)}>Archivieren</button> : <button className="btn btn--ghost" onClick={() => restoreAsset(asset)}>Aktivieren</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!assets.length && <div className="admin-empty">Keine Assets gefunden.</div>}
          </div>
        )}
      </section>

      {editing && (
        <div className="admin-modal-backdrop" role="presentation">
          <form className="panel admin-modal" onSubmit={saveAsset}>
            <div className="panel__header"><div className="panel__title">Asset bearbeiten</div><button type="button" className="drawer__close" onClick={() => setEditing(null)}>×</button></div>
            {Object.keys(form).map((field) => (
              <label className="admin-field" key={field}><span>{field.replace('_', ' ')}</span><input value={form[field]} onChange={(event) => setForm({ ...form, [field]: event.target.value })} /></label>
            ))}
            <div className="admin-modal__actions"><button type="button" className="btn btn--ghost" onClick={() => setEditing(null)}>Abbrechen</button><button type="submit" className="btn">Speichern</button></div>
          </form>
        </div>
      )}
    </main>
  );
}

export default AdminView;

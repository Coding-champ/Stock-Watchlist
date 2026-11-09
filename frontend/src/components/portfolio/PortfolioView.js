import React, { useCallback, useEffect, useState } from 'react';
import API_BASE from '../../config';
import { DISPLAY_DECIMAL_PLACES, DISPLAY_LOCALE, formatDisplayNumber } from '../../utils/numberFormatting';
import './PortfolioView.css';

const EMPTY_FORM = {
  identifier: '',
  quantity: '',
  purchase_price: '',
  purchase_date: new Date().toISOString().slice(0, 10),
};

function formatValue(value, currency) {
  if (value === null || value === undefined) return '-';
  try {
    return new Intl.NumberFormat(DISPLAY_LOCALE, {
      style: 'currency',
      currency: currency || 'USD',
      minimumFractionDigits: DISPLAY_DECIMAL_PLACES,
      maximumFractionDigits: DISPLAY_DECIMAL_PLACES,
    }).format(value);
  } catch {
    return `${formatDisplayNumber(value)} ${currency || ''}`.trim();
  }
}

function formatQuantity(value) {
  return formatDisplayNumber(value);
}

function PortfolioView({ showToast, onOpenStock, onOpenInvestmentCheck }) {
  const [portfolio, setPortfolio] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [buyingHolding, setBuyingHolding] = useState(null);
  const [buyForm, setBuyForm] = useState({ quantity: '', purchase_price: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const loadPortfolio = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/portfolio`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setPortfolio(await response.json());
    } catch (error) {
      console.error('Error loading portfolio:', error);
      showToast?.('Portfolio konnte nicht geladen werden', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadPortfolio();
  }, [loadPortfolio]);

  const submit = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE}/portfolio/holdings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          quantity: Number(form.quantity),
          purchase_price: Number(form.purchase_price),
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
      setForm(EMPTY_FORM);
      showToast?.('Position im Portfolio gespeichert', 'success');
      await loadPortfolio();
    } catch (error) {
      console.error('Error creating portfolio holding:', error);
      showToast?.(error.message || 'Position konnte nicht gespeichert werden', 'error');
    } finally {
      setSaving(false);
    }
  };

  const submitBuy = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE}/portfolio/holdings/${buyingHolding.id}/buy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quantity: Number(buyForm.quantity),
          purchase_price: Number(buyForm.purchase_price),
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
      setBuyingHolding(null);
      setBuyForm({ quantity: '', purchase_price: '' });
      showToast?.('Nachkauf gespeichert und Einstand gewichtet gemittelt', 'success');
      await loadPortfolio();
    } catch (error) {
      console.error('Error buying portfolio holding:', error);
      showToast?.(error.message || 'Nachkauf konnte nicht gespeichert werden', 'error');
    } finally {
      setSaving(false);
    }
  };

  const deleteHolding = async (holding) => {
    if (!window.confirm(`${holding.ticker_symbol} vollständig aus dem Portfolio löschen?`)) return;
    try {
      const response = await fetch(`${API_BASE}/portfolio/holdings/${holding.id}`, { method: 'DELETE' });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      showToast?.('Position gelöscht', 'success');
      await loadPortfolio();
    } catch (error) {
      console.error('Error deleting portfolio holding:', error);
      showToast?.(error.message || 'Position konnte nicht gelöscht werden', 'error');
    }
  };

  const updateForm = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  if (loading && !portfolio) {
    return <div className="panel portfolio-view__loading">Portfolio wird geladen...</div>;
  }

  return (
    <main className="portfolio-view">
      <section className="panel">
        <div className="panel__title-group">
          <div className="panel__eyebrow">Bestand</div>
          <div className="panel__title">{portfolio?.name || 'Mein Portfolio'}</div>
          <div className="panel__subtitle">Positionen verwalten und Nachkäufe zum Einstand hinzufügen.</div>
        </div>

        <form className="portfolio-form" onSubmit={submit}>
          <label>
            Ticker oder ISIN
            <input name="identifier" value={form.identifier} onChange={updateForm} required />
          </label>
          <label>
            Stückzahl
            <input name="quantity" type="number" min="0.0001" step="any" value={form.quantity} onChange={updateForm} required />
          </label>
          <label>
            Kaufkurs
            <input name="purchase_price" type="number" min="0.0001" step="any" value={form.purchase_price} onChange={updateForm} required />
          </label>
          <label>
            Kaufdatum
            <input name="purchase_date" type="date" value={form.purchase_date} onChange={updateForm} required />
          </label>
          <button className="button button--primary" type="submit" disabled={saving}>Position anlegen</button>
        </form>

        {portfolio?.has_mixed_currencies && (
          <div className="portfolio-view__warning" role="note">{portfolio.currency_warning}</div>
        )}

        {portfolio?.holdings?.length ? (
          <div className="portfolio-table-wrap">
            <table className="portfolio-table">
              <thead>
                <tr>
                  <th>Aktie</th>
                  <th>Stück</th>
                  <th>Einstand</th>
                  <th>Aktuell</th>
                  <th>Wert</th>
                  <th>GuV</th>
                  <th aria-label="Aktionen" />
                </tr>
              </thead>
              <tbody>
                {portfolio.holdings.map((holding) => (
                  <tr key={holding.id}>
                    <td>
                      <button
                        type="button"
                        className="portfolio-table__stock"
                        onClick={() => onOpenStock?.({ id: holding.stock_id, ticker_symbol: holding.ticker_symbol, name: holding.name, isin: holding.isin })}
                      >
                        <strong>{holding.ticker_symbol}</strong>
                        <span>{holding.name}</span>
                      </button>
                    </td>
                    <td>{formatQuantity(holding.quantity)}</td>
                    <td>{formatValue(holding.purchase_price, holding.currency)}</td>
                    <td>{formatValue(holding.current_price, holding.currency)}</td>
                    <td>{formatValue(holding.market_value, holding.currency)}</td>
                    <td className={holding.profit_loss >= 0 ? 'is-positive' : 'is-negative'}>
                      {formatValue(holding.profit_loss, holding.currency)}
                      <small>{holding.profit_loss_percent === null ? '-' : `${formatDisplayNumber(holding.profit_loss_percent)} %`}</small>
                    </td>
                    <td className="portfolio-table__actions">
                      {buyingHolding?.id === holding.id ? (
                        <form className="portfolio-buy-form" onSubmit={submitBuy}>
                          <input aria-label="Nachkauf Stückzahl" type="number" min="0.0001" step="any" placeholder="Stück" value={buyForm.quantity} onChange={(event) => setBuyForm({ ...buyForm, quantity: event.target.value })} required />
                          <input aria-label="Nachkauf Kurs" type="number" min="0.0001" step="any" placeholder="Kurs" value={buyForm.purchase_price} onChange={(event) => setBuyForm({ ...buyForm, purchase_price: event.target.value })} required />
                          <button className="button button--small button--primary" type="submit" disabled={saving}>OK</button>
                          <button className="button button--small" type="button" onClick={() => setBuyingHolding(null)}>Abbrechen</button>
                        </form>
                      ) : (
                        <>
                          <button className="button button--small button--primary" type="button" onClick={() => onOpenInvestmentCheck?.(holding.ticker_symbol)}>Check</button>
                          <button className="button button--small" type="button" onClick={() => setBuyingHolding(holding)}>Nachkauf</button>
                          <button className="button button--small button--danger" type="button" onClick={() => deleteHolding(holding)}>Löschen</button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th colSpan="4">Gesamtwert</th>
                  <th>{formatValue(portfolio.total_value)}</th>
                  <th colSpan="2" />
                </tr>
              </tfoot>
            </table>
          </div>
        ) : (
          <div className="empty-state empty-state--card">
            <h3>Noch keine Positionen</h3>
            <p>Lege deine erste Position an, um dein Portfolio aufzubauen.</p>
          </div>
        )}
      </section>
    </main>
  );
}

export default PortfolioView;

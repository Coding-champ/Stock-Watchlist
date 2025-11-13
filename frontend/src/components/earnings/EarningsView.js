import React, { useEffect, useMemo, useState } from 'react';
import '../../styles/skeletons.css';
import API_BASE from '../../config';
import { useQueryClient } from '@tanstack/react-query';

const EarningsView = () => {
  const [earnings, setEarnings] = useState([]);
  const [groupByDate, setGroupByDate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [loadingByDay, setLoadingByDay] = useState({});
  const queryClient = useQueryClient();

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        // Get stocks (limit to 100 to avoid throttling)
        const stocksUrl = `${API_BASE}/stocks?limit=100`;
        const stocks = await queryClient.fetchQuery(['api', stocksUrl], async () => {
          const r = await fetch(stocksUrl);
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        }, { staleTime: 60 * 1000 });

        // For each stock, fetch calendar/earnings
        const requests = stocks.map((s) =>
          queryClient.fetchQuery(['api', `${API_BASE}/stocks/${s.id}/calendar`], async () => {
            const r = await fetch(`${API_BASE}/stocks/${s.id}/calendar`);
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
          }, { staleTime: 60 * 1000 })
          .then((data) => ({ r: { ok: true, status: 200, json: async () => data }, s }))
          .catch((e) => ({ error: e, s }))
        );

        const results = await Promise.all(requests);

        const collected = [];
        const today = new Date();

        for (const item of results) {
          if (item.error) continue;
          const r = item.r;
          const s = item.s;
          if (!r || r.status !== 200) {
            try {
                // try to read json even for non-200 to give more info
                await r.json().catch(() => null);
                continue;
              } catch (e) {
                continue;
              }
          }
          const data = await r.json();

          // Support multiple possible shapes returned by backend yfinance wrappers
          // 1) { earnings_dates: [{date, EPS Estimate, Reported EPS, Surprise(%)}], calendar: {...} }
          // 2) flattened object with next_earnings_date (epoch) and other fields
          // 3) calendar object with 'Earnings Date' array

          let earnings_items = [];

          if (Array.isArray(data.earnings_dates) && data.earnings_dates.length > 0) {
            earnings_items = data.earnings_dates.map((ed) => ({
              raw: ed,
              date: ed.date,
              eps_estimate: ed.eps_estimate ?? ed['EPS Estimate'] ?? ed.EPS ?? null,
              reported_eps: ed.reported_eps ?? ed['Reported EPS'] ?? null,
              surprise: ed.surprise ?? ed['Surprise(%)'] ?? null
            }));
          } else if (data.calendar && data.calendar['Earnings Date']) {
            // calendar may contain a list of dates
            const list = data.calendar['Earnings Date'];
            if (Array.isArray(list)) {
              earnings_items = list.map((d) => ({ raw: d, date: d }));
            } else if (list) {
              earnings_items = [{ raw: list, date: list }];
            }
          } else if (data.next_earnings_date) {
            // next_earnings_date sometimes returned as epoch seconds
            const epoch = Number(data.next_earnings_date);
            if (!isNaN(epoch) && epoch > 0) {
              // yfinance sometimes uses seconds, sometimes milliseconds - normalize
              const maybeMs = epoch > 1e12 ? epoch : epoch * 1000;
              const dt = new Date(maybeMs);
              earnings_items = [{ raw: data, date: dt.toISOString(), eps_estimate: data.forward_eps ?? null }];
            }
          }

          for (const ed of earnings_items) {
            if (!ed || !ed.date) continue;
            // Try to parse date strings / epochs robustly
            let parsed = null;
            if (typeof ed.date === 'number') {
              const maybeMs = ed.date > 1e12 ? ed.date : ed.date * 1000;
              parsed = new Date(maybeMs);
            } else {
              parsed = new Date(ed.date);
            }
            if (isNaN(parsed.getTime())) continue;

            // Only upcoming in next 120 days
            const diffDays = (parsed - today) / (1000 * 60 * 60 * 24);
            if (diffDays < -1) continue; // skip past dates

            collected.push({
              stock_id: s.id,
              ticker: s.ticker_symbol || s.ticker || s.symbol || '',
              name: s.name || '',
              date: ed.date,
              parsed_date: parsed,
              eps_estimate: ed.eps_estimate ?? ed.EPS ?? ed['EPS Estimate'] ?? null,
              reported_eps: ed.reported_eps ?? ed['Reported EPS'] ?? null,
              surprise: ed.surprise ?? ed['Surprise(%)'] ?? null,
              // we'll fill timezone after fetching extended-data
              timezone: null,
              exchange: s.exchange || null,
              raw: ed.raw || ed
            });
          }
        }

        // Sort by date asc
        collected.sort((a, b) => a.parsed_date - b.parsed_date);

        if (!cancelled) setEarnings(collected);

        // Fetch extended-data/timezone for stocks that have earnings to compute accurate timing
        try {
          const idsWithEarnings = Array.from(new Set(collected.map((c) => c.stock_id)));

          if (groupByDate) {
            // When grouped, fetch extended-data per day and mark that day's header as loading
            const dayMap = new Map();
            for (const c of collected) {
              const day = c.parsed_date.toISOString().slice(0, 10);
              if (!dayMap.has(day)) dayMap.set(day, new Set());
              dayMap.get(day).add(c.stock_id);
            }

            for (const [day, idSet] of dayMap.entries()) {
              const ids = Array.from(idSet);
              // mark day as loading
              setLoadingByDay((p) => ({ ...(p || {}), [day]: true }));

              try {
                const extPromises = ids.map((id) =>
                  queryClient.fetchQuery(['api', `${API_BASE}/stocks/${id}/extended-data`], async () => {
                    const r = await fetch(`${API_BASE}/stocks/${id}/extended-data`);
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                  }, { staleTime: 300000 })
                  .then((data) => ({ r: { ok: true, status: 200, json: async () => data }, id }))
                  .catch((e) => ({ error: e, id }))
                );
                const extResults = await Promise.all(extPromises);
                const tzById = {};
                for (const er of extResults) {
                  if (er.error) continue;
                  if (!er.r || er.r.status !== 200) continue;
                  try {
                    const ext = await er.r.json();
                    const tz = (ext && ext.price_data && ext.price_data.market_data && ext.price_data.market_data.timezone) || (ext && ext.price_data && ext.price_data.timezone) || null;
                    if (tz) tzById[er.id] = tz;
                  } catch (e) {
                    // ignore
                  }
                }

                if (Object.keys(tzById).length > 0 && !cancelled) {
                  setEarnings((prev) => prev.map((c) => ({ ...c, timezone: tzById[c.stock_id] || c.timezone })));
                }
              } catch (e) {
                // per-day errors are non-fatal
              } finally {
                // clear loading flag for this day
                setLoadingByDay((p) => ({ ...(p || {}), [day]: false }));
              }
            }
          } else {
            // Non-grouped: fetch all extended-data in bulk (original behavior)
            const extPromises = idsWithEarnings.map((id) =>
              queryClient.fetchQuery(['api', `${API_BASE}/stocks/${id}/extended-data`], async () => {
                const r = await fetch(`${API_BASE}/stocks/${id}/extended-data`);
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
              }, { staleTime: 300000 })
              .then((data) => ({ r: { ok: true, status: 200, json: async () => data }, id }))
              .catch((e) => ({ error: e, id }))
            );

            const extResults = await Promise.all(extPromises);
            const tzById = {};
            for (const er of extResults) {
              if (er.error) continue;
              if (!er.r || er.r.status !== 200) continue;
              try {
                const ext = await er.r.json();
                // try common paths used in backend: ext.price_data.market_data.timezone
                const tz = (ext && ext.price_data && ext.price_data.market_data && ext.price_data.market_data.timezone) || (ext && ext.price_data && ext.price_data.timezone) || null;
                if (tz) tzById[er.id] = tz;
              } catch (e) {
                // ignore
              }
            }

            if (Object.keys(tzById).length > 0 && !cancelled) {
              const enriched = collected.map((c) => ({ ...c, timezone: tzById[c.stock_id] || c.timezone }));
              setEarnings(enriched);
            }
          }
        } catch (e) {
          // non-fatal
        }
      } catch (err) {
        if (!cancelled) setError('Earnings konnten nicht geladen werden.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [groupByDate, queryClient]);

  // Grouped view calculation
  const grouped = useMemo(() => {
    if (!groupByDate) return null;
    const map = new Map();
    for (const e of earnings) {
      const day = e.parsed_date.toISOString().slice(0, 10);
      if (!map.has(day)) map.set(day, []);
      map.get(day).push(e);
    }
    return Array.from(map.entries()).map(([day, items]) => ({ day, items }));
  }, [earnings, groupByDate]);

  const formatDateShort = (d) => new Date(d).toLocaleDateString();

  const getTimingIndicator = (entry) => {
    const raw = entry.raw || {};
    let ts = raw.earningsCallTimestampStart || raw.earningsCallTimestampEnd || raw.earnings_call_timestamp || raw.call || raw.time || null;
    if (!ts && entry.date && typeof entry.date === 'string' && entry.date.includes('T')) ts = entry.date;

    // create a base Date object in UTC
    let dateObj = null;
    if (ts) {
      const n = Number(ts);
      if (!isNaN(n)) {
        const maybeMs = n > 1e12 ? n : n * 1000;
        dateObj = new Date(maybeMs);
      } else {
        dateObj = new Date(ts);
      }
    } else if (entry.parsed_date) {
      dateObj = entry.parsed_date;
    }

    if (!dateObj || isNaN(dateObj.getTime())) return { label: 'Unknown', icon: '❓', title: 'Zeitpunkt unbekannt' };

    // If we have a timezone from extended-data, compute local hour there
    const tz = entry.timezone || entry.timezone || null;
    let localHour = null;
    let localMinute = null;
    if (tz) {
      try {
        // Use Intl to get hour/minute in the target timezone
        const parts = new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: tz }).formatToParts(dateObj);
        const hourPart = parts.find((p) => p.type === 'hour');
        const minutePart = parts.find((p) => p.type === 'minute');
        if (hourPart && minutePart) {
          localHour = Number(hourPart.value);
          localMinute = Number(minutePart.value);
        }
      } catch (e) {
        localHour = dateObj.getHours();
        localMinute = dateObj.getMinutes();
      }
    } else {
      localHour = dateObj.getHours();
      localMinute = dateObj.getMinutes();
    }

    // Determine market open/close (defaults: 09:30 - 16:00 local)
    const openHour = 9;
    const openMinute = 30;
    const closeHour = 16;
    const closeMinute = 0;

    if (localHour === null) return { label: 'Unknown', icon: '❓', title: 'Zeitpunkt unbekannt' };

    const before = localHour < openHour || (localHour === openHour && localMinute < openMinute);
    const after = localHour > closeHour || (localHour === closeHour && localMinute >= closeMinute);

    if (before) return { label: 'Before Market', icon: '🌅', title: `Before Market — ${dateObj.toLocaleString('sv-SE')} (${tz || 'local'})` };
    if (after) return { label: 'After Market', icon: '🌇', title: `After Market — ${dateObj.toLocaleString('sv-SE')} (${tz || 'local'})` };
    return { label: 'During Market', icon: '⚡', title: `During Market — ${dateObj.toLocaleString('sv-SE')} (${tz || 'local'})` };
  };

  return (
    <div className="panel">
      <div className="panel__title-group">
        <div className="panel__eyebrow">Earnings</div>
        <div className="panel__title">Earnings-Kalender</div>
        <div className="panel__subtitle">Ticker-Info und Earnings-Datum</div>
        <div style={{ marginTop: '8px' }}>
          <label style={{ fontSize: '0.9rem', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '8px'}}>
            <input type="checkbox" checked={groupByDate} onChange={(e) => setGroupByDate(e.target.checked)} />
            <span style={{ whiteSpace: 'nowrap' }}>Group by date</span>
          </label>
        </div>
      </div>

      {loading && <div className="loading">Lade Earnings…</div>}
      {error && <div className="error">{error}</div>}

      {!loading && !error && (
        <div className="earnings-table-wrapper">
          {groupByDate && grouped ? (
            <table className="table">
              <thead>
                <tr>
                  <th style={{ width: '180px' }}>Datum</th>
                  <th>Ticker</th>
                  <th>Name</th>
                  <th style={{ width: '120px' }}>EPS Schätzung</th>
                  <th style={{ width: '120px' }}>Berichtete EPS</th>
                  <th style={{ width: '120px' }}>Surprise %</th>
                </tr>
              </thead>
              {grouped.map(({ day, items }) => (
                <tbody key={day}>
                  <tr className="earnings-date-header-row">
                    <td colSpan={6} className="earnings-date-header">
                      {formatDateShort(day)} — {items.length} item(s)
                      {loadingByDay && loadingByDay[day] ? (
                        <span style={{ marginLeft: 8 }} className="day-spinner" aria-hidden="true" />
                      ) : null}
                    </td>
                  </tr>
                  {items.map((e, idx) => {
                    const timing = getTimingIndicator(e);
                    return (
                      <tr key={`${e.ticker}-${e.date}-${idx}`}>
                        <td title={timing.title}>
                          {new Date(e.parsed_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} {timing.icon}
                        </td>
                        <td className="ticker">{e.ticker}</td>
                        <td style={{ maxWidth: 420 }}>{e.name}</td>
                        <td style={{ textAlign: 'right' }}>{e.eps_estimate ?? '-'}</td>
                        <td style={{ textAlign: 'right' }}>{e.reported_eps ?? '-'}</td>
                        <td style={{ textAlign: 'right' }}>{(e.surprise !== null && e.surprise !== undefined) ? String(e.surprise) : '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              ))}
            </table>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Datum</th>
                  <th>Ticker</th>
                  <th>Name</th>
                  <th>EPS Schätzung</th>
                  <th>Berichtete EPS</th>
                  <th>Surprise %</th>
                </tr>
              </thead>
              <tbody>
                {earnings.length === 0 && (
                  <tr>
                    <td colSpan={6} className="earnings-empty">Keine bevorstehenden Earnings gefunden.</td>
                  </tr>
                )}
                {earnings.map((e, idx) => {
                  const timing = getTimingIndicator(e);
                  return (
                    <tr key={`${e.ticker}-${e.date}-${idx}`}>
                      <td title={timing.title}>
                        {new Date(e.parsed_date).toLocaleDateString()} {new Date(e.parsed_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} <span style={{ marginLeft: 6 }}>{timing.icon}</span>
                      </td>
                      <td className="ticker">{e.ticker}</td>
                      <td style={{ maxWidth: 420 }}>{e.name}</td>
                      <td style={{ textAlign: 'right' }}>{e.eps_estimate ?? '-'}</td>
                      <td style={{ textAlign: 'right' }}>{e.reported_eps ?? '-'}</td>
                      <td style={{ textAlign: 'right' }}>{(e.surprise !== null && e.surprise !== undefined) ? String(e.surprise) : '-'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};

export default EarningsView;

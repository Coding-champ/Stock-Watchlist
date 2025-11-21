import React from 'react';
import { useIndexTopFlops } from '../hooks/useIndexTopFlops';
import { useApi } from '../hooks/useApi';

function ArrowPill({ dir }) {
  const up = dir === 'up';
  const bg = up ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)';
  const color = up ? '#16a34a' : '#dc2626';
  return (
    <span style={{
      display:'inline-flex', alignItems:'center', gap:6,
      background:bg, color, padding:'4px 8px', borderRadius:999, fontWeight:600, fontSize:12
    }}>
      <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden>
        {up ? (
          <path d="M12 5l6 6h-4v8h-4v-8H6l6-6z" fill={color}/>
        ) : (
          <path d="M12 19l-6-6h4V5h4v8h4l-6 6z" fill={color}/>
        )}
      </svg>
      {up ? 'Top' : 'Flop'}
    </span>
  );
}

function ItemCard({ item, positive }){
  const color = positive ? '#16a34a' : '#dc2626';
  const sectorBg = positive ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)';
  const sectorColor = positive ? '#059669' : '#b91c1c';
  
  return (
    <div className="tf-card" style={{
      background:'var(--panel-bg, #fff)', 
      border:'1px solid var(--border-color,#eee)',
      borderRadius:12, 
      padding:14, 
      display:'flex', 
      justifyContent:'space-between', 
      alignItems:'center',
      boxShadow:'0 1px 3px 0 rgba(0,0,0,0.08), 0 1px 2px 0 rgba(0,0,0,0.04)',
      transition:'box-shadow 0.15s ease, transform 0.15s ease',
      cursor:'default'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)';
      e.currentTarget.style.transform = 'translateY(-2px)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.boxShadow = '0 1px 3px 0 rgba(0,0,0,0.08), 0 1px 2px 0 rgba(0,0,0,0.04)';
      e.currentTarget.style.transform = 'translateY(0)';
    }}
    >
      <div style={{display:'grid', gap:6, flex:1}}>
        <div style={{fontWeight:600, fontSize:14}}>
          {item.name} <span style={{color:'var(--text-muted)', fontWeight:400, fontSize:13}}>({item.ticker})</span>
        </div>
        {(item.sector || item.industry) && (
          <span style={{
            display:'inline-block',
            background:sectorBg,
            color:sectorColor,
            padding:'2px 8px',
            borderRadius:6,
            fontSize:11,
            fontWeight:500,
            width:'fit-content'
          }}>
            {item.sector || item.industry}
          </span>
        )}
      </div>
      <div style={{textAlign:'right'}}>
        <div style={{color, fontWeight:700, fontSize:16}}>
          {item.change_pct > 0 ? '+' : ''}{item.change_pct.toFixed(2)} %
        </div>
        <div style={{fontSize:12, color:'var(--text-muted)', marginTop:2}}>
          {formatPrice(item.last_price, item.currency)}
        </div>
      </div>
    </div>
  );
}

function formatPrice(price, currency) {
  if (price == null) return '—';
  try {
    const formatted = new Intl.NumberFormat('de-DE', {minimumFractionDigits:2, maximumFractionDigits:2}).format(price);
    return `${formatted} ${currency||''}`.trim();
  } catch {
    return `${price} ${currency||''}`.trim();
  }
}

function SkeletonCard() {
  return (
    <div style={{
      background:'var(--panel-bg, #fff)',
      border:'1px solid var(--border-color,#eee)',
      borderRadius:12,
      padding:14,
      display:'flex',
      justifyContent:'space-between',
      alignItems:'center',
      boxShadow:'0 1px 3px 0 rgba(0,0,0,0.08)'
    }}>
      <div style={{display:'grid', gap:6, flex:1}}>
        <div style={{
          height:16,
          width:'60%',
          background:'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
          backgroundSize:'200% 100%',
          animation:'shimmer 1.5s infinite',
          borderRadius:4
        }} />
        <div style={{
          height:12,
          width:'40%',
          background:'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
          backgroundSize:'200% 100%',
          animation:'shimmer 1.5s infinite',
          borderRadius:4
        }} />
      </div>
      <div style={{textAlign:'right'}}>
        <div style={{
          height:18,
          width:60,
          background:'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
          backgroundSize:'200% 100%',
          animation:'shimmer 1.5s infinite',
          borderRadius:4,
          marginBottom:4
        }} />
        <div style={{
          height:12,
          width:50,
          background:'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
          backgroundSize:'200% 100%',
          animation:'shimmer 1.5s infinite',
          borderRadius:4,
          marginLeft:'auto'
        }} />
      </div>
      <style>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
}

export default function TopFlopsPanel({ symbol, limit=5, onOpenStock }){
  const { data, isLoading, error } = useIndexTopFlops(symbol, limit, !!symbol);
  const { fetchApi } = useApi();
  const top = data?.top || [];
  const flops = data?.flops || [];

  const handleStockClick = async (ticker) => {
    if (!onOpenStock) return;
    try {
      const stocks = await fetchApi(`/stocks/search-db/?q=${encodeURIComponent(ticker)}&limit=1`);
      if (stocks && stocks.length > 0) {
        onOpenStock(stocks[0]);
      }
    } catch (err) {
      console.error('Failed to fetch stock:', err);
    }
  };

  return (
    <div className="panel" style={{ marginTop: 24 }}>
      <div className="panel__title-group">
        <div className="panel__eyebrow">Tagesbewegungen</div>
        <div className="panel__title">Tops / Flops des Tages</div>
        <div className="panel__subtitle">{data?.date ? new Date(data.date).toLocaleDateString('de-DE') : ''}</div>
      </div>
      <div className="panel__body">
        {error && <div style={{color:'var(--danger-color)'}}>Fehler: {String(error.message||error)}</div>}
        {isLoading ? (
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16}}>
            <div>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8}}>
                <ArrowPill dir="up"/>
                <span style={{fontSize:12, color:'var(--text-muted)'}}>Top {limit}</span>
              </div>
              <div style={{display:'grid', gap:10}}>
                {Array.from({length:limit}).map((_, i) => <SkeletonCard key={i} />)}
              </div>
            </div>
            <div>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8}}>
                <ArrowPill dir="down"/>
                <span style={{fontSize:12, color:'var(--text-muted)'}}>Flop {limit}</span>
              </div>
              <div style={{display:'grid', gap:10}}>
                {Array.from({length:limit}).map((_, i) => <SkeletonCard key={i} />)}
              </div>
            </div>
          </div>
        ) : !error && (
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:16}}>
            <div>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8}}>
                <ArrowPill dir="up"/>
                <span style={{fontSize:12, color:'var(--text-muted)'}}>Top {limit}</span>
              </div>
              <div style={{display:'grid', gap:10}}>
                {top.slice(0, limit).map((it) => (
                  <div key={it.ticker} onClick={() => handleStockClick(it.ticker)} style={{cursor: 'pointer'}}>
                    <ItemCard item={it} positive={true} />
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8}}>
                <ArrowPill dir="down"/>
                <span style={{fontSize:12, color:'var(--text-muted)'}}>Flop {limit}</span>
              </div>
              <div style={{display:'grid', gap:10}}>
                {flops.slice(0, limit).map((it) => (
                  <div key={it.ticker} onClick={() => handleStockClick(it.ticker)} style={{cursor: 'pointer'}}>
                    <ItemCard item={it} positive={false} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

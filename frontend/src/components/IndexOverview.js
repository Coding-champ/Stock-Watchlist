import React, { useMemo } from 'react';
import { useIndices } from '../hooks/useIndices';
import IndexCard from './IndexCard';
import './IndexOverview.css';

function IndexOverview({ onIndexClick }) {
  const { data: indices, isLoading, error } = useIndices();

  if (isLoading) {
    return (
      <div className="index-overview">
        <div className="loading-state">Lade Indizes...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="index-overview">
        <div className="error-state">Fehler beim Laden der Indizes: {error.message}</div>
      </div>
    );
  }

  // Group indices by region
  const groupedIndices = {};
  if (indices && indices.length > 0) {
    indices.forEach(index => {
      const region = index.region || 'Sonstige';
      if (!groupedIndices[region]) {
        groupedIndices[region] = [];
      }
      groupedIndices[region].push(index);
    });
  }

  return (
    <div className="index-overview">
      <div className="index-overview-header">
        <h2>Marktindizes</h2>
        <div className="index-stats">
          <span>{indices?.length || 0} Indizes</span>
        </div>
      </div>

      {Object.keys(groupedIndices).length === 0 ? (
        <div className="empty-state">
          <p>Keine Indizes gefunden.</p>
          <p className="hint">Führen Sie das Seeding-Skript aus, um Indizes zu erstellen.</p>
        </div>
      ) : (
        Object.entries(groupedIndices).map(([region, regionIndices]) => (
          <div key={region} className="region-group">
            <h3 className="region-title">{region}</h3>
            <div className="indices-grid">
              {regionIndices.map(index => (
                <IndexCard
                  key={index.id}
                  index={index}
                  onClick={() => onIndexClick && onIndexClick(index)}
                />
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default IndexOverview;

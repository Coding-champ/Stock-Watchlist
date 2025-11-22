import React from 'react';
import { formatPrice } from '../../utils/currencyUtils';

const VolumeProfileLevels = ({
  showVolumeProfile,
  setShowVolumeProfile,
  showVolumeProfileOverlay,
  setShowVolumeProfileOverlay,
  volumeProfileLevels,
  stock,
  isExpanded,
  onToggle
}) => {
  return (
    <div className="collapsible-panel">
      <div 
        className="collapsible-header"
        onClick={onToggle}
      >
        <span className={`collapsible-toggle-icon ${isExpanded ? 'expanded' : ''}`}></span>
        <div style={{ flex: 1 }}>
          <label className="checkbox-label" onClick={(e) => e.stopPropagation()}>
            <input
              type="checkbox"
              checked={showVolumeProfile}
              onChange={(e) => setShowVolumeProfile(e.target.checked)}
            />
            <span style={{ fontWeight: 'bold' }}>📊 Volume Profile (Standalone)</span>
          </label>

          <label className="checkbox-label" style={{ marginTop: '8px' }} onClick={(e) => e.stopPropagation()}>
            <input
              type="checkbox"
              checked={showVolumeProfileOverlay}
              onChange={(e) => setShowVolumeProfileOverlay(e.target.checked)}
            />
            <span style={{ fontWeight: 'bold' }}>📊 Volume Profile (Overlay)</span>
          </label>
        </div>
      </div>
      
      <div className={`collapsible-content ${isExpanded && (showVolumeProfile || showVolumeProfileOverlay) && volumeProfileLevels ? 'expanded' : ''}`}>
        {(showVolumeProfile || showVolumeProfileOverlay) && volumeProfileLevels && (
          <div style={{ 
            fontSize: '11px',
            color: '#666'
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <span>🟢 POC: {volumeProfileLevels.poc != null ? formatPrice(volumeProfileLevels.poc, stock) : 'N/A'}</span>
              <span>🔵 VAH: {volumeProfileLevels.vah != null ? formatPrice(volumeProfileLevels.vah, stock) : 'N/A'}</span>
              <span>🔴 VAL: {volumeProfileLevels.val != null ? formatPrice(volumeProfileLevels.val, stock) : 'N/A'}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VolumeProfileLevels;

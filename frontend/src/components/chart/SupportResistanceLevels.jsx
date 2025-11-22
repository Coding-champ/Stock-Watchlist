import React from 'react';

const SupportResistanceLevels = ({
  showSupportResistance,
  setShowSupportResistance,
  supportResistanceData,
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
        <label className="checkbox-label" onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={showSupportResistance}
            onChange={(e) => setShowSupportResistance(e.target.checked)}
          />
          <span style={{ fontWeight: 'bold' }}>📊 Support & Resistance</span>
        </label>
      </div>
      
      <div className={`collapsible-content ${isExpanded && showSupportResistance && supportResistanceData ? 'expanded' : ''}`}>
        {showSupportResistance && supportResistanceData && (
          <div style={{ 
            fontSize: '11px',
            color: '#666'
          }}>
            <div style={{ display: 'flex', gap: '15px' }}>
              <span>🟢 Support: {supportResistanceData.support.length}</span>
              <span>🔴 Resistance: {supportResistanceData.resistance.length}</span>
            </div>
            <div style={{ marginTop: '5px', fontSize: '10px', fontStyle: 'italic' }}>
              Linienstärke = Anzahl Tests
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SupportResistanceLevels;

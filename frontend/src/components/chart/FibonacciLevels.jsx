import React from 'react';

const FibonacciLevels = ({
  showFibonacci,
  setShowFibonacci,
  fibonacciData,
  fibonacciType,
  setFibonacciType,
  selectedFibLevels,
  setSelectedFibLevels,
  selectedExtensionLevels,
  setSelectedExtensionLevels,
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
            checked={showFibonacci}
            onChange={(e) => setShowFibonacci(e.target.checked)}
          />
          <span style={{ fontWeight: 'bold' }}>📐 Fibonacci Levels</span>
        </label>
      </div>
      
      <div className={`collapsible-content ${isExpanded && showFibonacci && fibonacciData ? 'expanded' : ''}`}>
        {showFibonacci && fibonacciData && (
          <div>
            {/* Type Selection */}
            <div style={{ 
              marginBottom: '10px',
              display: 'flex',
              gap: '5px'
            }}>
              <button
                onClick={() => setFibonacciType('retracement')}
                style={{
                  padding: '5px 12px',
                  fontSize: '12px',
                  border: '1px solid #007bff',
                  borderRadius: '4px',
                  backgroundColor: fibonacciType === 'retracement' ? '#007bff' : 'white',
                  color: fibonacciType === 'retracement' ? 'white' : '#007bff',
                  cursor: 'pointer',
                  fontWeight: fibonacciType === 'retracement' ? 'bold' : 'normal',
                  transition: 'all var(--motion-short)'
                }}
              >
                📉 Retracement
              </button>
              <button
                onClick={() => setFibonacciType('extension')}
                style={{
                  padding: '5px 12px',
                  fontSize: '12px',
                  border: '1px solid #28a745',
                  borderRadius: '4px',
                  backgroundColor: fibonacciType === 'extension' ? '#28a745' : 'white',
                  color: fibonacciType === 'extension' ? 'white' : '#28a745',
                  cursor: 'pointer',
                  fontWeight: fibonacciType === 'extension' ? 'bold' : 'normal',
                  transition: 'all var(--motion-short)'
                }}
              >
                📈 Extension
              </button>
            </div>
            
            {/* Level Selection */}
            <div style={{ 
              fontSize: '11px',
              backgroundColor: 'white',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #dee2e6'
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#495057' }}>
                {fibonacciType === 'retracement' ? 'Retracement Levels:' : 'Extension Levels:'}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {fibonacciType === 'retracement' ? (
                  Object.keys(selectedFibLevels).map(level => (
                    <label key={level} style={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      padding: '3px 8px',
                      backgroundColor: selectedFibLevels[level] ? '#e3f2fd' : '#f8f9fa',
                      border: '1px solid ' + (selectedFibLevels[level] ? '#2196f3' : '#dee2e6'),
                      borderRadius: '3px',
                      cursor: 'pointer',
                      transition: 'all var(--motion-short)'
                    }}>
                      <input
                        type="checkbox"
                        checked={selectedFibLevels[level]}
                        onChange={(e) => setSelectedFibLevels({
                          ...selectedFibLevels,
                          [level]: e.target.checked
                        })}
                        style={{ marginRight: '4px' }}
                      />
                      <span style={{ fontWeight: selectedFibLevels[level] ? 'bold' : 'normal' }}>
                        {level}%
                      </span>
                    </label>
                  ))
                ) : (
                  Object.keys(selectedExtensionLevels).map(level => (
                    <label key={level} style={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      padding: '3px 8px',
                      backgroundColor: selectedExtensionLevels[level] ? '#e8f5e9' : '#f8f9fa',
                      border: '1px solid ' + (selectedExtensionLevels[level] ? '#4caf50' : '#dee2e6'),
                      borderRadius: '3px',
                      cursor: 'pointer',
                      transition: 'all var(--motion-short)'
                    }}>
                      <input
                        type="checkbox"
                        checked={selectedExtensionLevels[level]}
                        onChange={(e) => setSelectedExtensionLevels({
                          ...selectedExtensionLevels,
                          [level]: e.target.checked
                        })}
                        style={{ marginRight: '4px' }}
                      />
                      <span style={{ fontWeight: selectedExtensionLevels[level] ? 'bold' : 'normal' }}>
                        {level}%
                      </span>
                    </label>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FibonacciLevels;

import React, { useState } from 'react';
import './CalculatedMetrics.css';

/**
 * Wiederverwendbare Tooltip-Komponente für Metriken-Erklärungen
 * 
 * @param {Object} props
 * @param {string} props.title - Titel der Metrik
 * @param {string|number} props.value - Aktueller Wert
 * @param {string} props.description - Beschreibung der Metrik
 * @param {Array} props.interpretation - Array von Interpretations-Regeln [{range: string, label: string, isCurrent: boolean}]
 * @param {React.ReactNode} props.children - Child element (z.B. Badge, Text)
 */
const MetricTooltip = ({ title, value, description, interpretation, children }) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="metric-tooltip-container">
      <div
        className="metric-tooltip-trigger"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {children}
      </div>
      
      {isVisible && (
        <div className="metric-tooltip-popup">
          <div className="metric-tooltip-header">
            <span className="metric-tooltip-icon">💡</span>
            <strong>{title}</strong>
          </div>
          
          <div className="metric-tooltip-body">
            {description && (
              <p className="metric-tooltip-description">{description}</p>
            )}
            
            {value !== null && value !== undefined && (
              <div className="metric-tooltip-value">
                <span className="label">Dein Wert:</span>
                <span className="value">{value}</span>
              </div>
            )}
            
            {interpretation && interpretation.length > 0 && (
              <div className="metric-tooltip-interpretation">
                <div className="interpretation-title">Interpretation:</div>
                <ul className="interpretation-list">
                  {interpretation.map((item, index) => (
                    <li
                      key={index}
                      className={item.isCurrent ? 'current' : ''}
                    >
                      <span className="range">{item.range}</span>
                      <span className="label">{item.label}</span>
                      {item.isCurrent && <span className="indicator">← Du bist hier</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MetricTooltip;

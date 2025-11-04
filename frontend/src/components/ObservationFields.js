import React, { useState, useEffect, useRef } from 'react';

export const OBSERVATION_REASON_OPTIONS = [
  { value: 'chart_technical', label: 'Charttechnische Indikatoren' },
  { value: 'earnings', label: 'Earnings Berichte' },
  { value: 'fundamentals', label: 'Fundamentaldaten' },
  { value: 'company', label: 'Unternehmensdaten' },
  { value: 'industry', label: 'Branchendaten' },
  { value: 'economics', label: 'Wirtschaftsdaten' }
];

function ObservationFields({
  reasons = [],
  setReasons = () => {},
  notes = '',
  setNotes = () => {},
  reasonsLabel = 'Beobachtungsgründe',
  notesLabel = 'Bemerkungen',
  notesPlaceholder = ''
}) {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

  const toggleReason = (value) => {
    if (reasons.includes(value)) {
      setReasons(reasons.filter((r) => r !== value));
    } else {
      setReasons([...reasons, value]);
    }
  };

  return (
    <div className="observation-section">
      <div className="form-group observation-section__reasons">
        <label>{reasonsLabel}</label>

        <div className="custom-dropdown-container" ref={dropdownRef}>
          <button
            type="button"
            className={`custom-dropdown-toggle ${showDropdown ? 'open' : ''}`}
            onClick={() => setShowDropdown(!showDropdown)}
          >
            <span className="dropdown-text">
              {reasons.length === 0 ? 'Kategorien auswählen...' : `${reasons.length} ausgewählt`}
            </span>
            <span className="dropdown-arrow">{showDropdown ? '▲' : '▼'}</span>
          </button>

          {showDropdown && (
            <div className="custom-dropdown-menu">
              {OBSERVATION_REASON_OPTIONS.map((option) => (
                <label key={option.value} className="dropdown-item">
                  <input
                    type="checkbox"
                    checked={reasons.includes(option.value)}
                    onChange={() => toggleReason(option.value)}
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {reasons.length > 0 && (
          <div className="selected-tags">
            {reasons.map((reason) => {
              const option = OBSERVATION_REASON_OPTIONS.find((opt) => opt.value === reason);
              return option ? (
                <span key={reason} className="tag">
                  {option.label}
                  <button
                    type="button"
                    className="tag-remove"
                    onClick={() => toggleReason(reason)}
                  >
                    ×
                  </button>
                </span>
              ) : null;
            })}
          </div>
        )}
      </div>

      <div className="form-group observation-section__notes">
        <label>{notesLabel}</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={notesPlaceholder}
          rows={3}
        />
      </div>
    </div>
  );
}

export default ObservationFields;

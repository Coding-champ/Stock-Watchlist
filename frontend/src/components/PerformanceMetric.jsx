import React from 'react';
import { formatPercent, formatSignedCurrency } from '../utils/formatting';

function PerformanceMetric({ label, data, hint, stock }) {
  if (!data) {
    return (
      <div className="performance-metric performance-metric--neutral">
        <span className="performance-metric__label">{label}</span>
        <span className="performance-metric__percent">-</span>
        <span className="performance-metric__amount">-</span>
      </div>
    );
  }

  return (
    <div className={`performance-metric performance-metric--${data.direction}`}>
      <span className="performance-metric__label">{label}</span>
      <span className="performance-metric__percent">{formatPercent(data.percent)}</span>
      <span className="performance-metric__amount">{formatSignedCurrency(data.amount, hint, stock)}</span>
    </div>
  );
}

export default PerformanceMetric;

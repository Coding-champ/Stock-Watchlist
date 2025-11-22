/**
 * Calculate performance metrics between two values
 * @param {number} fromValue - Starting value
 * @param {number} toValue - Ending value
 * @returns {Object|null} Performance object with amount, percent, and direction
 */
export function calculatePerformance(fromValue, toValue) {
  if (typeof fromValue !== 'number' || typeof toValue !== 'number') {
    return null;
  }

  if (fromValue === 0) {
    return null;
  }

  const amount = toValue - fromValue;
  const percent = (amount / fromValue) * 100;
  let direction = 'neutral';
  if (amount > 0) {
    direction = 'positive';
  } else if (amount < 0) {
    direction = 'negative';
  }

  return {
    amount,
    percent,
    direction
  };
}

/**
 * Normalize a sort score for consistent sorting behavior
 * @param {number} score - The score to normalize
 * @param {string} direction - Sort direction ('asc' or 'desc')
 * @returns {number} Normalized score
 */
export function normalizeSortScore(score, direction) {
  if (typeof score !== 'number' || Number.isNaN(score)) {
    return direction === 'asc' ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY;
  }

  return score;
}

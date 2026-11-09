import { useCallback, useEffect, useState } from 'react';
import API_BASE from '../config';

export const INVESTMENT_CHECK_STEPS = [
  { key: 'input', label: 'Eingabe', title: 'Eingabe' },
  { key: 'chart', label: 'Chart / Muster', title: 'Chart / Muster' },
  { key: 'fundamentals', label: 'Finanzkennzahlen', title: 'Finanzkennzahlen' },
  { key: 'stock_metrics', label: 'Aktienkennzahlen', title: 'Aktienkennzahlen' },
  { key: 'peer_market', label: 'Peer / Markt', title: 'Peer / Markt' },
  { key: 'seasonality', label: 'Saisonalität', title: 'Saisonalität' },
  { key: 'dependent_assets', label: 'Kapitalmarkt-Assets', title: 'Abhängige Kapitalmarkt-Assets' },
  { key: 'allocation', label: 'Risiko-Allocation', title: 'Risiko-Allocation' },
  { key: 'result', label: 'Ergebnis', title: 'Ergebnis' },
];

export function useInvestmentCheck({ showToast, initialIdentifier = '' } = {}) {
  const [currentStep, setCurrentStep] = useState(0);
  const [identifier, setIdentifier] = useState(initialIdentifier);
  const [quantity, setQuantity] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [portfolioLoading, setPortfolioLoading] = useState(true);
  const [hasPortfolioHoldings, setHasPortfolioHoldings] = useState(false);

  useEffect(() => {
    let active = true;
    const loadPortfolioGate = async () => {
      try {
        const response = await fetch(`${API_BASE}/portfolio`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (active) setHasPortfolioHoldings(Array.isArray(data.holdings) && data.holdings.length > 0);
      } catch (error) {
        console.error('Error loading portfolio gate:', error);
        showToast?.('Portfolio-Status konnte nicht geprüft werden', 'error');
      } finally {
        if (active) setPortfolioLoading(false);
      }
    };
    loadPortfolioGate();
    return () => { active = false; };
  }, [showToast]);

  const runCheck = useCallback(async () => {
    if (!identifier.trim() || Number(quantity) <= 0) {
      showToast?.('Bitte Symbol/ISIN und eine gültige Stückzahl eingeben', 'error');
      return false;
    }

    let timeout;
    try {
      setLoading(true);
      const controller = new AbortController();
      timeout = setTimeout(() => controller.abort(), 60000);
      const response = await fetch(`${API_BASE}/investment-check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: identifier.trim(), quantity: Number(quantity) }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
      setResult(data);
      setCurrentStep(1);
      return true;
    } catch (error) {
      console.error('Error running investment check:', error);
      showToast?.(
        error.name === 'AbortError'
          ? 'Investitions-Check hat das Zeitlimit von 60 Sekunden überschritten'
          : (error.message || 'Investitions-Check konnte nicht berechnet werden'),
        'error'
      );
      return false;
    } finally {
      if (timeout) clearTimeout(timeout);
      setLoading(false);
    }
  }, [identifier, quantity, showToast]);

  const reset = useCallback(() => {
    setCurrentStep(0);
    setIdentifier('');
    setQuantity('');
    setResult(null);
  }, []);

  const goBack = useCallback(() => {
    setCurrentStep((step) => Math.max(0, step - 1));
  }, []);

  const goNext = useCallback(() => {
    setCurrentStep((step) => Math.min(INVESTMENT_CHECK_STEPS.length - 1, step + 1));
  }, []);

  return {
    currentStep,
    setCurrentStep,
    identifier,
    setIdentifier,
    quantity,
    setQuantity,
    result,
    loading,
    portfolioLoading,
    hasPortfolioHoldings,
    runCheck,
    reset,
    goBack,
    goNext,
  };
}

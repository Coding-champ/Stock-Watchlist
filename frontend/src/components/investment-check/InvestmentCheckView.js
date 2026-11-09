import React from 'react';
import {
  INVESTMENT_CHECK_STEPS,
  useInvestmentCheck,
} from '../../hooks/useInvestmentCheck';
import {
  formatMetricValue,
} from '../../utils/numberFormatting';
import './InvestmentCheckView.css';

function statusLabel(status) {
  return status === 'not_evaluated' ? 'Nicht bewertet' : status;
}

function formatDataLabel(key) {
  return key
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function DataList({ data }) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return <p className="investment-check__muted">Keine Daten verfügbar.</p>;
  }
  const entries = Object.entries(data).filter(([, value]) => value !== null && value !== undefined && typeof value !== 'object');
  if (!entries.length) return <p className="investment-check__muted">Keine Daten verfügbar.</p>;
  return (
    <dl className="investment-check__data-list">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{formatDataLabel(key)}</dt>
          <dd>{formatMetricValue(key, value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function StepContent({ step, result, identifier, setIdentifier, quantity, setQuantity, onSubmit, loading }) {
  if (step.key === 'input') {
    return (
      <form className="investment-check__input-form" onSubmit={onSubmit}>
        <p>Gib ein Wertpapier und die geplante Stückzahl für die hypothetische Prüfung ein.</p>
        <label>
          Symbol oder ISIN
          <input value={identifier} onChange={(event) => setIdentifier(event.target.value)} placeholder="z. B. AAPL oder US0378331005" required />
        </label>
        <label>
          Zu kaufende Stückzahl
          <input type="number" min="0.0001" step="any" value={quantity} onChange={(event) => setQuantity(event.target.value)} required />
        </label>
        <button className="investment-check__button investment-check__button--primary" type="submit" disabled={loading}>
          {loading ? 'Wird berechnet...' : 'Check starten'}
        </button>
      </form>
    );
  }

  if (!result) return <p className="investment-check__muted">Noch keine Prüfung gestartet.</p>;
  const stepData = result.steps?.[step.key];
  if (step.key === 'result') {
    return (
      <div className="investment-check__result-list">
        {INVESTMENT_CHECK_STEPS.slice(1, -1).map((item) => {
          const itemResult = result.steps?.[item.key];
          return (
            <div className="investment-check__result-row" key={item.key}>
              <span>{item.label}</span>
              <strong className="investment-check__status investment-check__status--neutral">
                {statusLabel(itemResult?.status || 'not_evaluated')}
              </strong>
            </div>
          );
        })}
        <p className="investment-check__muted">{result.result?.reason}</p>
      </div>
    );
  }

  return (
    <div className="investment-check__step-content">
      <div className="investment-check__status-line">
        <span>Status</span>
        <strong className="investment-check__status investment-check__status--neutral">
          {statusLabel(stepData?.status || 'not_evaluated')}
        </strong>
      </div>
      <DataList data={stepData?.data || stepData} />
      {stepData?.pending_thresholds?.length > 0 && (
        <p className="investment-check__muted">
          Kriterien werden angezeigt. Schwellenwerte folgen später: {stepData.pending_thresholds.join(', ')}.
        </p>
      )}
    </div>
  );
}

function InvestmentCheckView({ showToast, initialIdentifier = '', onOpenPortfolio }) {
  const check = useInvestmentCheck({ showToast, initialIdentifier });
  const step = INVESTMENT_CHECK_STEPS[check.currentStep];
  const isInput = check.currentStep === 0;
  const isResult = check.currentStep === INVESTMENT_CHECK_STEPS.length - 1;

  if (check.portfolioLoading) {
    return <div className="panel investment-check__gate">Portfolio-Status wird geprüft...</div>;
  }

  if (!check.hasPortfolioHoldings) {
    return (
      <main className="investment-check">
        <section className="investment-check__shell investment-check__gate">
          <div className="investment-check__eyebrow">Investitions-Check</div>
          <h2>Zuerst Bestand anlegen</h2>
          <p>Der Investitions-Check startet, sobald mindestens eine Position in deinem Portfolio vorhanden ist.</p>
          <button className="investment-check__button investment-check__button--primary" type="button" onClick={onOpenPortfolio}>
            Zum Portfolio
          </button>
        </section>
      </main>
    );
  }

  const submitInput = async (event) => {
    event.preventDefault();
    await check.runCheck();
  };

  return (
    <main className="investment-check">
      <section className="investment-check__shell">
        <header className="investment-check__header">
          <div>
            <div className="investment-check__eyebrow">Analyse</div>
            <h2>Investitions-Check</h2>
          </div>
          <button className="investment-check__reset" type="button" onClick={check.reset}>Neu starten</button>
        </header>

        <nav className="investment-check__stepper" aria-label="Investitions-Check Fortschritt">
          {INVESTMENT_CHECK_STEPS.map((item, index) => {
            const visible = index === check.currentStep || index === check.currentStep - 1 || index === check.currentStep + 1;
            const completed = index < check.currentStep;
            return (
              <React.Fragment key={item.key}>
                {index > 0 && <span className={`investment-check__connector ${completed ? 'is-complete' : ''}`} aria-hidden="true">••••</span>}
                <button
                  type="button"
                  className={`investment-check__step ${visible ? 'is-visible' : 'is-compact'} ${index === check.currentStep ? 'is-current' : ''} ${completed ? 'is-complete' : ''}`}
                  onClick={() => visible && check.setCurrentStep(index)}
                  aria-current={index === check.currentStep ? 'step' : undefined}
                  aria-label={`${item.label}, Schritt ${index + 1} von ${INVESTMENT_CHECK_STEPS.length}`}
                >
                  <span className="investment-check__circle">{completed ? '✓' : index + 1}</span>
                  {visible && <span className="investment-check__label">{item.label}</span>}
                </button>
              </React.Fragment>
            );
          })}
        </nav>

        <div className="investment-check__progress">{check.currentStep + 1}/{INVESTMENT_CHECK_STEPS.length}</div>
        {check.result?.data_quality?.price?.is_stale && (
          <div className="investment-check__freshness-warning" role="status">
            Kursdaten sind {check.result.data_quality.price.status === 'missing' ? 'nicht vorhanden' : 'veraltet'}.
            Ergebnisse mit diesen Daten sind nur eingeschränkt aussagekräftig.
          </div>
        )}
        {check.result?.step_errors && Object.keys(check.result.step_errors).length > 0 && (
          <div className="investment-check__error-warning" role="alert">
            Einige Stationen konnten nicht vollständig berechnet werden. Die betroffenen Daten sind nicht bewertet.
          </div>
        )}
        <article className="investment-check__card">
          <div className="investment-check__card-heading">
            <h3>{step.title}</h3>
            {!isInput && check.result?.input?.ticker_symbol && <span>{check.result.input.ticker_symbol}</span>}
          </div>
          <StepContent
            step={step}
            result={check.result}
            identifier={check.identifier}
            setIdentifier={check.setIdentifier}
            quantity={check.quantity}
            setQuantity={check.setQuantity}
            onSubmit={submitInput}
            loading={check.loading}
          />
        </article>

        {!isInput && (
          <div className="investment-check__actions">
            <button type="button" className="investment-check__button" onClick={check.goBack}>Zurück</button>
            {!isResult && <button type="button" className="investment-check__button investment-check__button--primary" onClick={check.goNext}>Weiter</button>}
          </div>
        )}
      </section>
    </main>
  );
}

export default InvestmentCheckView;

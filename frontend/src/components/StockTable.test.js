import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import StockTable from './StockTable';

// Mock global fetch used by StockTable for sparklines and extended data
beforeEach(() => {
  global.fetch = jest.fn((url) => {
    if (String(url).includes('/stock-data/1')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          { current_price: 123.45, timestamp: 1690000000 }
        ])
      });
    }

    if (String(url).includes('/stocks/1/detailed')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ extended_data: null })
      });
    }

    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
});

afterEach(() => {
  global.fetch = undefined;
});

test('renders BMW.DE with euro currency symbol and localized quote type', async () => {
  const stock = {
    id: 1,
    name: 'Bayerische Motoren Werke AG',
    ticker_symbol: 'BMW.DE',
    exchange: 'BMW.DE'
  };

  const { container } = render(
    <StockTable
      stocks={[stock]}
      watchlists={[]}
      currentWatchlistId={null}
      onStockClick={() => {}}
      onDeleteStock={() => {}}
      onMoveStock={() => {}}
      onCopyStock={() => {}}
      onUpdateMarketData={() => {}}
      onShowChart={() => {}}
      onShowToast={() => {}}
    />
  );

  // Wait for the component to finish async fetches and render price (not the '-' placeholder)
  await waitFor(() => {
    const el = container.querySelector('.stock-card__price-value');
    expect(el).toBeTruthy();
    // Expect a non-placeholder value that contains a currency symbol (e.g., € or $)
    expect(el.textContent).not.toBe('-');
  });

  const priceEl = container.querySelector('.stock-card__price-value');
  expect(priceEl.textContent).toMatch(/€/);

  // Subtitle should contain the localized label (default fallback is 'Aktie') and the ticker
  const subtitleRegex = /Aktie\s*·\s*Ticker\s*BMW\.DE/;
  const subtitleEl = screen.getByText(subtitleRegex);
  expect(subtitleEl).toBeTruthy();
});

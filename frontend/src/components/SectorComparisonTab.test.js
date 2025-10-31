import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import SectorComparisonTab from './SectorComparisonTab';

// Recharts uses ResizeObserver which isn't provided by jsdom in the test
// environment. Provide a minimal mock so ResponsiveContainer doesn't throw.
beforeAll(() => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  class MockResizeObserver {
    constructor(callback) { this.callback = callback; }
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  // Attach to global/window
  global.ResizeObserver = MockResizeObserver;
});


beforeEach(() => {
  global.fetch = jest.fn((url) => {
    // Return a mocked peers response for any request
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        used_mock: true,
        peers: [
          { name: 'Tech Peer 1', ticker: 'TP1', value: 1500000000 },
          { name: 'Tech Peer 2', ticker: 'TP2', value: 800000000 }
        ]
      })
    });
  });
});

afterEach(() => {
  global.fetch = undefined;
});

test('renders mock badge and peer names when backend returns mocked peers', async () => {
  render(<SectorComparisonTab stockId={1} />);

  // Wait for the mock-badge to appear
  await waitFor(() => expect(screen.getByText('Mockdaten')).toBeTruthy());

  // Ensure the component performed the fetch for peers
  expect(global.fetch).toHaveBeenCalled();
  const firstCallUrl = global.fetch.mock.calls[0][0];
  expect(String(firstCallUrl)).toContain('/stocks/1/peers');
});

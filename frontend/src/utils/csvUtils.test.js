import { parseCSV, exportCSV, splitCSVLine } from './csvUtils';

describe('csvUtils', () => {
  test('parseCSV parses comma-separated values and headers', () => {
    const text = 'Ticker,Name\nAAPL,Apple Inc.\nMSFT,Microsoft Corp.';
    const { headers, rows } = parseCSV(text);
    expect(headers).toEqual(['ticker', 'name']);
    expect(rows.length).toBe(2);
    expect(rows[0][0]).toBe('AAPL');
    expect(rows[0][1]).toBe('Apple Inc.');
  });

  test('parseCSV parses semicolon-separated values', () => {
    const text = 'ISIN;Ticker\nUS0378331005;AAPL\n';
    const { headers, rows } = parseCSV(text);
    expect(headers).toEqual(['isin', 'ticker']);
    expect(rows[0][0]).toBe('US0378331005');
    expect(rows[0][1]).toBe('AAPL');
  });

  test('splitCSVLine handles quoted commas and escaped quotes', () => {
    const line = '"Last, First",Value,"With ""quotes"" inside"';
    const parts = splitCSVLine(line, ',');
    expect(parts[0]).toBe('Last, First');
    expect(parts[1]).toBe('Value');
    expect(parts[2]).toBe('With "quotes" inside');
  });

  test('exportCSV produces CSV that parseCSV can read (roundtrip)', () => {
    const headers = ['Ticker', 'Name'];
    const rows = [
      ['AAPL', 'Apple "Inc."'],
      ['MSFT', 'Microsoft']
    ];
    const csv = exportCSV(headers, rows);
    const { headers: parsedHeaders, rows: parsedRows } = parseCSV(csv);
    expect(parsedHeaders).toEqual(['ticker', 'name']);
    expect(parsedRows[0][0]).toBe('AAPL');
    expect(parsedRows[0][1]).toBe('Apple "Inc."');
    expect(parsedRows[1][0]).toBe('MSFT');
  });
});

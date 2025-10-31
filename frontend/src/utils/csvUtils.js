/**
 * Kleine CSV-Hilfsfunktionen (keine externe Abhängigkeit)
 * Enthält: exportCSV, parseCSV, splitCSVLine, escapeCell
 */

export const escapeCell = (value) => `"${String(value || '').replace(/"/g, '""')}"`;

export function splitCSVLine(line, delimiter = ',') {
  const res = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        cur += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === delimiter && !inQuotes) {
      res.push(cur);
      cur = '';
    } else {
      cur += ch;
    }
  }
  res.push(cur);
  return res.map(s => s.trim());
}

export function parseCSV(text) {
  const lines = text.split(/\r\n|\n/).filter(l => l.trim().length > 0);
  if (lines.length === 0) return { headers: [], rows: [] };
  const first = lines[0];
  const delimiter = (first.indexOf(';') > -1 && first.indexOf(',') === -1) ? ';' : ',';
  const headers = splitCSVLine(lines[0], delimiter).map(h => h.toLowerCase());
  const rows = lines.slice(1).map(l => splitCSVLine(l, delimiter));
  return { headers, rows };
}

export function exportCSV(headers = [], rows = []) {
  const headerLine = headers.map(escapeCell).join(',');
  const bodyLines = rows.map(r => r.map(escapeCell).join(','));
  return [headerLine].concat(bodyLines).join('\r\n');
}

const csvUtils = {
  escapeCell,
  splitCSVLine,
  parseCSV,
  exportCSV
};

export default csvUtils;

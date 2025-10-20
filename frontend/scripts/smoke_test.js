const http = require('http');
const https = require('https');

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:3000/api';

const endpoints = [
  '/health',           // optional health endpoint
  '/docs',
  '/screener/filters',
  '/screener/run',
  '/watchlists/',
  '/stocks/',
  '/alerts/',
];

function fetchUrl(url) {
  return new Promise((resolve) => {
    const lib = url.startsWith('https') ? https : http;
    const req = lib.get(url, { timeout: 5000 }, (res) => {
      const { statusCode } = res;
      let raw = '';
      res.on('data', (chunk) => raw += chunk);
      res.on('end', () => resolve({ statusCode, body: raw.slice(0, 200) }));
    });
    req.on('error', (err) => resolve({ error: err.message }));
    req.on('timeout', () => { req.destroy(); resolve({ error: 'timeout' }); });
  });
}

(async () => {
  console.log('Using API base:', API_BASE);
  for (const ep of endpoints) {
    const delim = API_BASE.endsWith('/') ? '' : '/';
    const url = `${API_BASE}${delim}${ep.replace(/^\//, '')}`;
    process.stdout.write(`Checking ${url} ... `);
    try {
      const res = await fetchUrl(url);
      if (res.error) {
        console.log(`ERROR: ${res.error}`);
        continue;
      }

      console.log(`HTTP ${res.statusCode}`);
      // Try to parse JSON for known endpoints and provide concise info
      if (res.body) {
        let parsed = null;
        try {
          parsed = JSON.parse(res.body + (res.body.endsWith(']') || res.body.endsWith('}') ? '' : ''));
        } catch (e) {
          // not JSON or truncated
        }

        if (parsed) {
          if (Array.isArray(parsed)) {
            console.log(`  items: ${parsed.length}`);
          } else if (parsed.total !== undefined || parsed.results !== undefined) {
            console.log(`  total: ${parsed.total || 0}, results: ${Array.isArray(parsed.results) ? parsed.results.length : 'unknown'}`);
          } else if (parsed.countries || parsed.sectors) {
            console.log(`  facets: countries=${(parsed.countries||[]).length}, sectors=${(parsed.sectors||[]).length}`);
          } else {
            console.log(`  body: ${String(res.body).slice(0, 200).replace(/\n/g, ' ')}...`);
          }
        } else {
          console.log(`  body: ${String(res.body).slice(0, 200).replace(/\n/g, ' ')}...`);
        }
      }
    } catch (err) {
      console.log('EXCEPTION:', err.message);
    }
  }
})();
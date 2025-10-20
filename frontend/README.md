# Stock Watchlist - React Frontend

This is the React frontend for the Stock Watchlist application.

## Project Structure

```text
frontend/
├── public/              # Static files
│   ├── favicon.ico     # App icon
│   └── index.html      # HTML template
├── src/
│   ├── components/      # React components
│   │   ├── WatchlistSection.js      # Watchlist management
│   │   ├── StocksSection.js         # Stock list with search
│   │   ├── StockTable.js            # Sortable stock table
│   │   ├── StockModal.js            # Add stock form
│   │   └── StockDetailModal.js      # Stock detail view
│   ├── App.js          # Main application component
│   ├── App.css         # Global styles
│   └── index.js        # Application entry point
├── package.json        # Dependencies and scripts
└── README.md          # This file
```

## Development

### Install Dependencies

```bash
npm install
```

### Start Development Server

```bash
npm start
```

The app will run on [http://localhost:3000](http://localhost:3000) and automatically proxy API requests to the backend (see `src/setupProxy.js`).

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory, which is served by the FastAPI backend.

## Features

- **Watchlist Management**: Create and view multiple watchlists
- **Stock Management**: Add, view, move, and delete stocks
- **Search & Filter**: Search stocks by name, ISIN, or ticker symbol
- **Sorting**: Click column headers to sort the stock table
- **Stock Details**: Click on a stock row to view detailed information
- **Responsive Design**: Works on desktop and mobile devices

## API Integration

The frontend communicates with the FastAPI backend using the Fetch API. The base URL is configured to work with both development (via proxy) and production modes.

All API endpoints are documented in the backend's Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

### API base configuration

The frontend uses a centralized `API_BASE` exported from `src/config.js`. By default this is set to `/api` so the development server can proxy requests to the backend (see `src/setupProxy.js`).

- Development (default): `API_BASE = '/api'` — requests like `/api/screener/run` are proxied to the backend. No extra env vars needed when running `npm start`.
- Production: set the environment variable `REACT_APP_API_BASE` to your API URL (for example `https://api.example.com`). The value will be used by the app instead of `/api`.

Examples:

```bash
# Run production build with a real API base
REACT_APP_API_BASE=https://api.stockwatchlist.com npm run build
```

The centralized config helps avoid mismatched URLs across components and keeps dev/prod behavior consistent.

## Technologies

- **React 19**: UI library
- **CSS3**: Styling (no external CSS framework needed)
- **Create React App**: Build tooling

## Browser Support

The application works in all modern browsers that support ES6+ features.

# Comprehensive Codebase Audit (2025-10-10)

## Methodology

- Surveyed backend FastAPI services, routers, and supporting utilities with emphasis on yFinance integration and data ingestion.
- Reviewed representative frontend React components, state management patterns, and API usage.
- Inspected automated test modules under `tests/` to evaluate coverage, determinism, and tooling.
- Assessed security posture (authentication, input validation, secrets handling) and performance considerations (I/O patterns, caching, concurrency).
- Cross-referenced architecture documentation already present in the repo to spot divergences between intent and implementation.

## Architectural Observations

- **Layer leakage (`backend/app/routes/stocks.py`, `backend/app/routes/stock_data.py`)**: Routers orchestrate persistence, caching, external API calls, and domain rules inline. This blurs the separation between transport layer (FastAPI) and domain/application services, making reuse (e.g., CLI jobs) hard and increasing testing complexity.
- **Monolithic gateway (`backend/app/services/yfinance_service.py`)**: The file aggregates identifier resolution, market data fetchers, technical indicator proxies, and analytics helpers (~1.1k LOC). Multiple downstream services re-implement similar logic rather than depending on a unified boundary.
- **Mixed caching concerns (`backend/app/services/cache_service.py`)**: Persistent cache (SQL-backed) and transient in-memory cache share a single module, with route-level helpers directly referencing implementation details. TTL configuration is duplicated (constants + inline values).
- **Frontend shell (`frontend/src/App.js`)**: App component controls navigation, data fetching, alert polling, and toast UX. Responsibilities could be decomposed into dedicated providers or state containers to prevent prop drilling and side-effect scattering.
- **Documentation drift**: `ARCHITECTURE.md` describes intended layering, but the implementation diverges (e.g., computed metrics still depend on live yFinance calls). Aligning documentation with actual behavior would avoid onboarding confusion. Please notise that the architecture.md is not at the current state of the project.

## Backend Findings

- **Duplicate yFinance calls**: `HistoricalPriceService` and `FundamentalDataService` each fetch `Stock`, instantiate `yf.Ticker`, and manage transaction safety separately. Shared ingestion scaffolding would reduce duplication and ease introducing retries or throttling.
- **Synchronous external calls inside DB transactions** (`backend/app/services/stock_service.py`): `create_stock_with_watchlist` loads historical and fundamental data before commit, risking partial failures and long-lived transactions. Offloading to background tasks or orchestrating post-commit hooks would improve resilience.
- **Routes performing heavy lifting**: `stock_data.get_stock_chart_data` handles cache checks, direct yFinance calls, JSON cleaning, and error translation. A dedicated service (e.g., `ChartQueryService`) would isolate this logic and enable reuse by CLI/testing environments.
- **Inconsistent error handling**: Some services swallow exceptions (`FundamentalDataService`, `CacheService`) while others propagate them. Standardizing error taxonomy and logging levels (info/warning/error) would improve observability.
- **Scheduler lifecycle** (`backend/app/main.py`): Background scheduler starts unconditionally at API boot. In environments without DB connectivity this logs errors repeatedly. Consider feature flagging via env var.
- **Validation gaps**: Pydantic schemas enforce structure, but upstream inputs (e.g., ticker symbols) feed straight into yFinance. Sanitization or allowlists could mitigate invalid calls and reduce API throttling risk.
- **Deprecated fields kept alive**: Routes still populate `stock_data` arrays (set to empty) to satisfy legacy clients. Planning a deprecation path would simplify payloads.

## Frontend Findings

- **Centralized state in `App.js`**: Single component manages watchlists, toasts, navigation, and alert polling. This violates single-responsibility and complicates testing. Extracting context providers (WatchlistProvider, ToastProvider) would clarify boundaries.
- **Fetch scatter & no cancellation**: Components like `WatchlistSection.js` use `fetch` directly without abort controllers or error boundary integration. A reusable API client hook would centralize headers, error translation, and cancellation.
- **Styling inline side effects**: Buttons mutate `style` in `onMouseOver/onMouseOut`. CSS classes or utility tokens would be more maintainable and accessible.
- **Mixed language semantics**: UI copy combines German and English; ensure localization strategy is documented.
- **Missing suspense/loading states**: `App.js` toggles a global loading overlay, but specific sections (e.g., `StocksSection`) may need localized skeletons to avoid layout jank.

## Testing & Quality

- **Tests behave as scripts**: Many files under `tests/` (e.g., `test_api.py`, `test_calculated_metrics.py`) print to stdout and rely on live services instead of using pytest assertions/mocks. CI cannot rely on deterministic outcomes, and coverage is effectively zero.
- **No automated front-end tests**: No Jest/React Testing Library specs detected. UI regressions risk going unnoticed.
- **Test data management**: Scripts call production APIs and yFinance. Introducing fixtures and mocking external services is necessary for repeatable tests.
- **Coverage & tooling**: No coverage reports or config present. Establish baseline using `pytest --cov` and `npm test -- --coverage` once real tests exist.

## Security Assessment

- **Open CORS policy** (`backend/app/main.py`): `allow_origins=["*"]` with credentials permitted enables CSRF scenarios. Restrict origins or disable credentials when wildcarding.
- **Lack of authentication/authorization**: All CRUD operations for watchlists/stocks are public. If multi-user support is expected, add auth middleware and ownership checks.
- **No rate limiting**: yFinance endpoints are exposed indirectly; malicious clients could trigger rapid external calls, risking IP bans. Introduce server-side throttling or caching.
- **Scheduler exposure**: `/scheduler/status` returns job metadata without auth. Consider securing or disabling in production.
- **Secrets management**: `.env` loading exists, but no validation ensures required keys. Document required env vars and consider using pydantic settings models.
- **Input sanitization**: User-provided notes and reasons propagate to DB without escaping. Ensure frontend/DB layers prevent XSS when values are reflected.

## Performance & Reliability

- **Blocking network calls**: yFinance requests are synchronous; long latencies can cascade across requests. Consider async wrappers or caching to reduce load.
- **Cache TTL inconsistencies**: Chart cache uses ad-hoc TTL parameters; persistent cache uses minimum TTL across datasets, potentially expiring slow-changing data too aggressively. Standardize TTL strategy and monitor hit rates.
- **Bulk inserts with per-row queries**: `_save_price_data` queries for each date before deciding to update or create. Batch lookups or rely on unique constraints to reduce DB round trips.
- **Frontend polling**: Alerts poll every 15 minutes even if user not on alerts view. Gate polling behind user focus or manual refresh to save bandwidth.
- **Large module bundles**: `App.js` imports entire `AlertDashboard` even when closed. Use dynamic import with React.lazy to defer heavy UI until needed.
- **Thread-safety**: `SimpleCache` is not protected by locks. In multi-threaded workers this can cause race conditions.

## API Integration & yFinance Usage

- **Direct DTO flattening**: Routes flatten nested structures manually, leading to duplication. Adapters or dataclasses could formalize transformation.
- **Identifier resolution**: `get_stock_info_by_identifier` guesses ISIN format but lacks structured validation. False positives could query invalid tickers.
- **Error propagation**: Many yFinance wrappers catch `Exception` broadly and return `None`, hiding root causes. Surfacing error categories (network vs. rate limit vs. missing ticker) would inform retries.
- **Dependency on `.info`**: yFinance `.info` is slow and sometimes deprecated. Moving to `.fast_info` or explicit endpoints would improve performance and future-proof integration.

## Recommendations

1. **Define service boundaries**: Extract application services (e.g., `StockQueryService`, `ChartService`) so routes become thin controllers. Update documentation accordingly.
2. **Introduce a `YFinanceGateway`**: Centralize all external calls with rate limiting, caching strategy, and structured errors. Refactor ingestion services to depend on this gateway.
3. **Refactor caching architecture**: Split persistent vs. in-memory cache modules, define TTL registry, and wrap cache access in interfaces for testability.
4. **Enhance security posture**: Restrict CORS origins, add auth/authorization where applicable, and secure scheduler endpoints. Document env var requirements.
5. **Improve testing discipline**: Replace script-like tests with pytest suites using mocks/fixtures. Add React component tests and configure coverage reporting in CI.
6. **Manage background processing**: Move expensive data loads (historical/fundamental) to background jobs triggered post-commit. Implement retry/backoff policies.
7. **Frontend modularization**: Introduce context providers and API hooks, replace inline styles with CSS classes, and consider code-splitting heavy modals.
8. **Performance monitoring**: Add logging/metrics around external call durations, cache hit rates, and scheduler outcomes. Use this data to tune TTLs and polling intervals.
9. **Plan deprecations**: Document and schedule removal of legacy payload fields (`stock_data`) and align frontend consumption.
10. **Establish CI pipeline**: Automate linting, tests, and security scans (e.g., Bandit for Python, npm audit for frontend) to maintain quality over time.

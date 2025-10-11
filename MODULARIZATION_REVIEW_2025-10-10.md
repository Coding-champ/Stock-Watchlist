# Modularization Review (2025-10-10)

## Scope & Approach

- Focused on backend service layer, FastAPI routes, and supporting utilities where data collectors and scrapers are implemented.
- Read representative files with the highest complexity and duplication risk (`backend/app/services`, `backend/app/routes`).
- Analyzed responsibility boundaries, cross-module dependencies, and repetition of logic.

## Executive Takeaways

- Several modules have grown into "god objects" that combine unrelated responsibilities, making reuse and testing difficult.
- YFinance access patterns are duplicated across services rather than being centralized behind a consistent gateway.
- FastAPI route modules contain substantial business logic that should live in services/use-cases, creating duplication and tightly coupling HTTP concerns with domain logic.
- Caching concerns are scattered, mixing persistent and in-memory strategies in a single module.

## High-Priority Findings

1. **Monolithic `yfinance_service`** (`backend/app/services/yfinance_service.py`, ~1.1k LOC)
   - *Issue*: Aggregates identifier resolution, raw data fetching, indicator wrappers, calendar data, analyst info, and dividend/split utilities in one module. This duplicates logic already present in specialized services (e.g., `HistoricalPriceService`, `FundamentalDataService`) and forces wide imports.
   - *Impact*: Hard to test (no clear seams), elevated coupling (almost every route/service imports it), and frequent merge pain. ADP-level duplication evident in functions like `get_stock_info`, `get_current_stock_data`, and `get_extended_stock_data` which all repeat ticker creation and error handling.
   - *Recommendation*: Split into cohesive components, e.g. `data_fetchers/identifier_resolution.py`, `data_fetchers/market_snapshot.py`, `data_fetchers/fundamentals.py`, and `indicators/external_wrappers.py`. Provide a thin gateway interface (`YFinanceGateway`) consumed by downstream services so ingestion code (`HistoricalPriceService`, `FundamentalDataService`) can defer to a single entry point.

2. **Oversized Route Modules Embedding Business Logic** (`backend/app/routes/stocks.py` ~1.4k LOC, `backend/app/routes/stock_data.py` ~750 LOC)
   - *Issue*: Routes orchestrate watchlist movements, cache lifecycle, metric calculations, and data normalization directly. Repeated patterns include stock lookups, cache fetch/refresh decisions, and error handling for yfinance outages.
   - *Impact*: Duplicated logic (stock lookup + 404 occurs in 20+ endpoints), tight HTTP coupling (business rules depend on FastAPI request context), and hindered reuse (CLI jobs or background workers must re-implement logic).
   - *Recommendation*: Introduce use-case services (e.g., `StockReadService`, `ChartQueryService`) encapsulating the repeated flows. Provide dependency-injected helpers for "get stock or 404" logic. Consider splitting routes by bounded context (`stocks_watchlists.py`, `stocks_metrics.py`, `stocks_admin.py`) once service layer absorbs business logic.

3. **Parallel YFinance Ingestion Pipelines** (`HistoricalPriceService`, `FundamentalDataService`)
   - *Issue*: Both services independently fetch the `Stock` record, instantiate `yf.Ticker`, and perform similar error handling/commit logic. `_save_price_data` and `_save_fundamental_data` manage transaction flow identically (loop, check existing, update/create, commit).
   - *Impact*: Divergent behavior (one updates dividends within price save, the other handles period strings), duplicated error handling, and inconsistent logging. Hard to introduce retries or rate limiting centrally.
   - *Recommendation*: Extract a shared ingestion template (e.g., `BaseYFinanceIngestion`) handling session management, stock resolution, logging, and ticker hydration. Concrete subclasses implement `_fetch_raw` and `_persist` to reduce duplication and enable cross-cutting concerns (throttling, retries, API key rotation).

## Medium-Priority Findings

- **Caching Concerns Mixed in `cache_service.py`** (`backend/app/services/cache_service.py`, ~430 LOC)
  - Persistent cache (DB-backed `ExtendedStockDataCache`) and transient in-memory cache (`SimpleCache`) cohabit the file. Chart caching helpers hardcode TTL logic alongside analyst data caching. This redundancy complicates swapping cache backends or adding metrics.
  - *Recommendation*: Separate into `persistent_cache_service.py` (DB) and `in_memory_cache.py` (SimpleCache) modules. Expose a shared interface so route handlers depend on abstractions instead of concrete helpers. Centralize TTL configuration to avoid drift (currently defined both in constants and inline).

- **Indicator Calculation Split Across Services With Overlap** (`technical_indicators_service.py`, `calculated_metrics_service.py`)
  - Both modules implement RSI/MACD interpretations, divergence detection, and price pattern analysis. Some functions re-export or rewrap each other (`calculate_rsi` defined twice). Results and data structures differ slightly across modules, leading to conversion code in routes.
  - *Recommendation*: Consolidate indicator math into a single analytics core (pure functions returning typed results). Higher-level metrics services should compose these primitives instead of re-deriving them.

- **Watchlist/Stock Service Coupling External Calls** (`backend/app/services/stock_service.py`)
  - `create_stock_with_watchlist` performs synchronous external fetches (historical + fundamental) during a transaction. This ties DB commits to network IO and increases the chance of partially persisted states.
  - *Recommendation*: Decouple creation from data backfill (enqueue background task or emit domain event). Encapsulate external fetch orchestration in a dedicated `StockOnboardingService` to clarify responsibilities.

## Lower-Priority Observations

- Route-level helper functions such as `_normalize_observation_reasons` are duplicated across modules; promoting them to shared validators would reduce repetition.
- Several services (`HistoricalPriceService`, `FundamentalDataService`, `StockService`) construct their collaborators directly. Leveraging FastAPI dependency injection or a lightweight service container would improve testability.
- Logging strategy varies widely (some modules swallow exceptions, others raise) resulting in inconsistent telemetry.

## Opportunities for Reorganization

1. **Define Clear Bounded Contexts**
   - *Market Data Ingestion*: Responsible for pulling and persisting raw prices/fundamentals. Shared ingestion base class + repository interfaces.
   - *Analytics & Scoring*: Pure calculation modules consuming stored data; should not reach out to yfinance.
   - *Presentation APIs*: Thin FastAPI handlers delegating exclusively to use-case services.

2. **Centralize External Gateway**
   - Provide a `yfinance_gateway` package exposing high-level methods (`fetch_price_history`, `fetch_fundamentals`, `resolve_identifier`). Downstream modules should consume this instead of importing `yfinance` directly.

3. **Cache Strategy Review**
   - Introduce a cache abstraction (interface + adapters) to standardize TTLs, serialization, and invalidation. Enables future replacement with Redis or Dynamo while keeping API unchanged.

4. **Module Granularity**
   - Split massive files into topic-based modules (e.g., `stocks_watchlists.py`, `stocks_admin.py`, `stock_metrics.py`). Pair with service-layer movers to gradually reduce file size.

## Open Questions / Follow-Ups

- Do we plan to support multiple market data providers? If yes, abstraction around the gateway becomes critical now.
- Are there SLAs around response time for stock creation or chart endpoints? That informs whether synchronous ingestion is acceptable.
- Should computed analytics be persisted for dashboard use, or remain on-demand? This decision affects service boundaries between calculation and storage.

## Suggested Next Steps

1. Reach agreement on target architecture layers (gateway → ingestion → domain services → API) and document in `ARCHITECTURE.md`.
2. Pilot refactor by extracting a `YFinanceGateway` consumed by `HistoricalPriceService` and `FundamentalDataService` to validate approach.
3. Introduce a `StockQueryService` encapsulating the repeated stock lookup + 404 logic; apply to a subset of routes and measure LOC reduction.
4. Plan cache module split to separate persistent cache handling from transient chart caching and define a consistent TTL registry.

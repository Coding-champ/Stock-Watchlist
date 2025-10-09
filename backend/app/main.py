from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from backend.app.routes import watchlists, stocks, alerts, stock_data
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Try to create database tables if database is available
try:
    from backend.app.database import engine, Base
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not connect to database: {e}")
    print("The API will start but database operations will fail until database is configured.")

app = FastAPI(
    title="Stock Watchlist API",
    description="API for managing stock watchlists with alerts and detailed stock data",
    version="1.0.0"
)


# Custom middleware to add cache control headers for API endpoints
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add no-cache headers for API endpoints (not static files)
        if request.url.path.startswith(("/stocks", "/watchlists", "/alerts", "/stock-data")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


# Add middlewares
app.add_middleware(NoCacheMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(watchlists.router)
app.include_router(stocks.router)
app.include_router(stock_data.router)
app.include_router(alerts.router)


# Startup event - start background scheduler
@app.on_event("startup")
async def startup_event():
    """Start background services on application startup"""
    try:
        from backend.app.services.scheduler import start_scheduler
        # Check alerts every 15 minutes
        start_scheduler(interval_minutes=15)
        logger.info("Background alert scheduler started")
    except Exception as e:
        logger.error(f"Failed to start alert scheduler: {e}")


# Shutdown event - stop background scheduler
@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services on application shutdown"""
    try:
        from backend.app.services.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Background alert scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop alert scheduler: {e}")


# Mount React build directory
frontend_build_path = "frontend/build"
if os.path.exists(frontend_build_path) and os.path.exists(frontend_build_path + "/static"):
    app.mount("/static", StaticFiles(directory=frontend_build_path + "/static"), name="static")


@app.get("/")
def read_root():
    # Serve React app if build exists, otherwise return API info
    if os.path.exists(frontend_build_path + "/index.html"):
        return FileResponse(frontend_build_path + "/index.html")
    return {
        "message": "Stock Watchlist API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/scheduler/status")
def get_scheduler_status():
    """Get the current status of the alert scheduler"""
    try:
        from backend.app.services.scheduler import get_scheduler_status
        return get_scheduler_status()
    except Exception as e:
        return {"error": str(e)}

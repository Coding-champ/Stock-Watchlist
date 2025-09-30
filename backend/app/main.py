from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.routes import watchlists, stocks, stock_data, alerts

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return {
        "message": "Stock Watchlist API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

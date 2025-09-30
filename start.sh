#!/bin/bash

# Quick start script for Stock Watchlist

echo "🚀 Starting Stock Watchlist application..."

# Check if uvicorn is available
if command -v uvicorn &> /dev/null; then
    echo "Using local Python environment..."
    uvicorn backend.app.main:app --reload &
    SERVER_PID=$!
    echo "✓ Server started (PID: $SERVER_PID)"
    echo ""
    sleep 3
    echo "📊 Stock Watchlist is ready!"
    echo "   Frontend: http://localhost:8000/"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop the server"
    wait $SERVER_PID
else
    echo "❌ Error: uvicorn not found"
    echo "Please install Python dependencies:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

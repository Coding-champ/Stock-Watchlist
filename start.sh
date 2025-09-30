#!/bin/bash

# Quick start script for Stock Watchlist

echo "🚀 Starting Stock Watchlist application..."

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo "Using Docker Compose..."
    docker-compose up -d
    echo "✓ Services started"
    echo ""
    echo "Waiting for database to be ready..."
    sleep 5
    echo ""
    echo "📊 Stock Watchlist is ready!"
    echo "   Frontend: http://localhost:8000/static/index.html"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    read -p "Load sample data? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose exec app python sample_data.py
    fi
elif command -v uvicorn &> /dev/null; then
    echo "Using local Python environment..."
    uvicorn backend.app.main:app --reload &
    SERVER_PID=$!
    echo "✓ Server started (PID: $SERVER_PID)"
    echo ""
    sleep 3
    echo "📊 Stock Watchlist is ready!"
    echo "   Frontend: http://localhost:8000/static/index.html"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop the server"
    wait $SERVER_PID
else
    echo "❌ Error: Neither docker-compose nor uvicorn found"
    echo "Please install either Docker or Python dependencies"
    exit 1
fi

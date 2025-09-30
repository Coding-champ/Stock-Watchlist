#!/bin/bash

# Build script for React frontend

echo "🔨 Building React frontend..."

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

# Build the React app
echo "🚀 Building production bundle..."
npm run build

if [ $? -eq 0 ]; then
    echo "✓ Frontend build successful!"
    echo ""
    echo "The built files are in frontend/build/"
    echo "You can now start the backend server to serve the React app:"
    echo "  uvicorn backend.app.main:app --reload"
else
    echo "✗ Build failed. Please check the error messages above."
    exit 1
fi

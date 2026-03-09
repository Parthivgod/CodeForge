#!/bin/bash

# Railway start script for CodeForge
echo "Starting CodeForge on Railway..."

# Set default port if not provided
export PORT=${PORT:-8000}

# Start the FastAPI backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port $PORT
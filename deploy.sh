#!/bin/bash

# CodeForge Deployment Script
# Usage: ./deploy.sh [dev|prod]

set -e

MODE=${1:-dev}

echo "🚀 CodeForge Deployment Script"
echo "================================"
echo "Mode: $MODE"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with required environment variables."
    echo "See DEPLOYMENT.md for details."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed!"
    echo "Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed!"
    echo "Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

if [ "$MODE" = "prod" ]; then
    echo "📦 Building and starting production services..."
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d --build
    
    echo ""
    echo "⏳ Waiting for services to be healthy..."
    sleep 10
    
    echo ""
    echo "✅ Production deployment complete!"
    echo ""
    echo "🌐 Access your application:"
    echo "   Frontend: http://$(curl -s ifconfig.me)"
    echo "   Backend API: http://$(curl -s ifconfig.me):8000"
    echo "   API Docs: http://$(curl -s ifconfig.me):8000/docs"
    
else
    echo "📦 Building and starting development services..."
    docker-compose down
    docker-compose up -d --build
    
    echo ""
    echo "⏳ Waiting for services to be healthy..."
    sleep 10
    
    echo ""
    echo "✅ Development deployment complete!"
    echo ""
    echo "🌐 Access your application:"
    echo "   Frontend: http://localhost:5173"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
fi

echo ""
echo "📊 Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "📝 View logs with:"
if [ "$MODE" = "prod" ]; then
    echo "   docker-compose -f docker-compose.prod.yml logs -f"
else
    echo "   docker-compose logs -f"
fi

echo ""
echo "🛑 Stop services with:"
if [ "$MODE" = "prod" ]; then
    echo "   docker-compose -f docker-compose.prod.yml down"
else
    echo "   docker-compose down"
fi

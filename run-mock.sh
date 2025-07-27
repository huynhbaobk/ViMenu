#!/bin/bash

# Script to run the Vietnamese Menu Analyzer in mock mode

echo "🍜 Starting Vietnamese Menu Analyzer in MOCK MODE"
echo "=================================================="
echo ""
echo "💡 Features in mock mode:"
echo "   • No external API calls"
echo "   • Instant mock results"
echo "   • 10 sample Vietnamese dishes"
echo "   • Mock ingredients and images"
echo ""
echo "🌐 Access URLs:"
echo "   • Web: http://localhost:8000"
echo "   • API: http://localhost:8000/docs"
echo "   • Health: http://localhost:8000/health"
echo ""

# Check if .env.mock exists, create if not
if [ ! -f .env.mock ]; then
    echo "⚠️  .env.mock not found, creating..."
    cp .env.example .env.mock
fi

# Use mock environment
cp .env.mock .env

# Start the application
echo "🚀 Starting server..."
python -m app.main
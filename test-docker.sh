#!/bin/bash

# ViMenu Docker Test Script

echo "🐳 Testing Docker builds..."

# Test development build
echo "📦 Building development image..."
docker build -t vimenu:dev .

if [ $? -eq 0 ]; then
    echo "✅ Development build successful!"
else
    echo "❌ Development build failed!"
    exit 1
fi

# Test production build
echo "📦 Building production image..."
docker build -f Dockerfile.prod -t vimenu:prod .

if [ $? -eq 0 ]; then
    echo "✅ Production build successful!"
else
    echo "❌ Production build failed!"
    exit 1
fi

echo "🚀 All Docker builds completed successfully!"
echo ""
echo "To run the containers:"
echo "  Development: docker-compose up"
echo "  Production:  docker-compose -f docker-compose.prod.yml up"

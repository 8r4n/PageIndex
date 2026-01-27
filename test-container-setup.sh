#!/bin/bash
# Test script for PageIndex container setup

set -e

echo "======================================"
echo "PageIndex Container Setup Test"
echo "======================================"
echo ""

# Check if Docker is installed
echo "[1/5] Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✓ Docker is installed: $(docker --version)"
echo ""

# Check if .env file exists
echo "[2/5] Checking environment configuration..."
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env file. Please edit it to add your OpenAI API key."
    else
        echo "❌ .env.example not found."
        exit 1
    fi
else
    echo "✓ .env file exists"
fi
echo ""

# Create data and results directories
echo "[3/5] Creating data and results directories..."
mkdir -p data results
echo "✓ Directories created"
echo ""

# Validate Dockerfile
echo "[4/5] Validating Dockerfile..."
if [ ! -f Dockerfile ]; then
    echo "❌ Dockerfile not found."
    exit 1
fi
echo "✓ Dockerfile found"
echo ""

# Check docker-compose
echo "[5/5] Checking docker-compose..."
if command -v docker-compose &> /dev/null; then
    echo "✓ docker-compose is installed: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    echo "✓ docker compose plugin is installed: $(docker compose version)"
else
    echo "⚠️  docker-compose not found (optional)"
fi
echo ""

echo "======================================"
echo "Setup check complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Build the container: docker build -t pageindex:latest ."
echo "3. Place PDF files in the data/ directory"
echo "4. Run PageIndex:"
echo "   docker run --rm \\"
echo "     -v \$(pwd)/data:/app/data \\"
echo "     -v \$(pwd)/results:/app/results \\"
echo "     --env-file .env \\"
echo "     pageindex:latest \\"
echo "     python3 run_pageindex.py --pdf_path /app/data/your-file.pdf"
echo ""
echo "For more details, see CONTAINER.md"

#!/bin/bash

# UPPETIT Promo Bot - Quick Start Script

set -e

echo "🚀 UPPETIT Promo Bot - Quick Start"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from example..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env file and add your BOT_TOKEN!"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after you've configured .env file..."
fi

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Import test codes
echo "📝 Importing test codes..."
python -m tools.import_codes --test

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the bot:"
echo "  source .venv/bin/activate"
echo "  python -m app.main"
echo ""
echo "Or use make:"
echo "  make run"
echo ""

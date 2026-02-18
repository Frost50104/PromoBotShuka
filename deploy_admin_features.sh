#!/bin/bash
# Deployment script for admin features

set -e  # Exit on error

echo "🚀 Deploying admin features..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on production server
if [ ! -f "/opt/bots/uppetit-bot/.env" ] && [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please ensure you're in the project directory or /opt/bots/uppetit-bot/"
    exit 1
fi

# Detect if we're in production or local
if [ -d "/opt/bots/uppetit-bot" ]; then
    PROJECT_DIR="/opt/bots/uppetit-bot"
    IS_PRODUCTION=true
    echo -e "${GREEN}📍 Detected production environment${NC}"
else
    PROJECT_DIR="$(pwd)"
    IS_PRODUCTION=false
    echo -e "${YELLOW}📍 Detected local environment${NC}"
fi

cd "$PROJECT_DIR"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
else
    echo -e "${RED}❌ Error: Virtual environment not found${NC}"
    exit 1
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q greenlet

# Check current migration status
echo "🔍 Checking current migration status..."
alembic current

# Apply migrations
echo "🗄️  Applying database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migrations applied successfully${NC}"
else
    echo -e "${RED}❌ Error applying migrations${NC}"
    exit 1
fi

# Verify admin table
echo "🔍 Verifying admin table..."
if command -v psql &> /dev/null; then
    # PostgreSQL
    DB_NAME=$(grep "DATABASE_URL" .env | cut -d'/' -f4)
    DB_USER=$(grep "DATABASE_URL" .env | cut -d'/' -f3 | cut -d':' -f1 | cut -d'@' -f1)
    sudo -u postgres psql -d "$DB_NAME" -c "SELECT COUNT(*) as admin_count FROM admins;" 2>/dev/null || echo "Skipping DB check"
else
    # SQLite
    if [ -f "promo_bot.db" ]; then
        sqlite3 promo_bot.db "SELECT COUNT(*) as admin_count FROM admins;"
    fi
fi

# Restart bot if in production
if [ "$IS_PRODUCTION" = true ]; then
    echo "🔄 Restarting bot service..."
    sudo systemctl restart uppetit-bot

    echo "⏳ Waiting for bot to start..."
    sleep 3

    echo "📊 Checking bot status..."
    sudo systemctl status uppetit-bot --no-pager | head -10

    echo ""
    echo -e "${GREEN}✅ Deployment completed!${NC}"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Test /show_info command in Telegram"
    echo "   2. Try /add_admin to add new admin"
    echo "   3. Try /delete_admin to manage admins"
    echo ""
    echo "📋 Logs:"
    echo "   journalctl -u uppetit-bot -f"
else
    echo ""
    echo -e "${GREEN}✅ Local setup completed!${NC}"
    echo ""
    echo "📝 To start the bot locally:"
    echo "   python -m app.main"
    echo ""
    echo "📝 New admin commands:"
    echo "   /show_info    - Detailed statistics"
    echo "   /add_admin    - Add new admin"
    echo "   /delete_admin - Remove admin"
fi

echo ""
echo "🎉 Admin features are now active!"

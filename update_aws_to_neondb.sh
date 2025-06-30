#!/bin/bash

# Script to update AWS EC2 deployment from MySQL RDS to NeonDB
# Run this on your EC2 instance: ssh -i your-key.pem ubuntu@3.109.103.171

echo "🔄 Updating AWS deployment to use NeonDB..."

# Navigate to application directory
cd /opt/cv-review-app

# Stop the current service
echo "⏹️ Stopping current application..."
sudo systemctl stop cv-review-app

# Pull latest code from repository
echo "📥 Pulling latest code..."
git fetch origin
git reset --hard origin/main

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies (in case requirements.txt changed)
echo "📦 Updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Update .env file to use NeonDB instead of MySQL RDS
echo "🔧 Updating database configuration to NeonDB..."
cat > .env << 'EOF'
# Database Configuration (NeonDB PostgreSQL)
DATABASE_URL=postgresql://neondb_owner:npg_Y0eCWsbQT4tJ@ep-quiet-base-a1ts0jr8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
EOF

echo "✅ Updated .env with NeonDB connection"

# Test database connection
echo "🔍 Testing NeonDB connection..."
python3 -c "
from database_pool import get_db_cursor
import os

try:
    with get_db_cursor() as (_, cursor):
        cursor.execute('SELECT COUNT(*) as count FROM reviewer_data')
        reviewer_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM user_data')
        user_count = cursor.fetchone()['count']
        
        print(f'✅ NeonDB connection successful!')
        print(f'📊 Reviewers: {reviewer_count}')
        print(f'🎓 Students: {user_count}')
        
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Restart the application with new configuration
echo "🚀 Starting application with NeonDB..."
sudo systemctl start cv-review-app

# Wait a moment for startup
sleep 5

# Check service status
echo "📊 Checking service status..."
sudo systemctl status cv-review-app --no-pager -l

# Show recent logs
echo "📋 Recent application logs:"
sudo journalctl -u cv-review-app -n 20 --no-pager

echo ""
echo "🎉 AWS deployment updated to use NeonDB!"
echo "🌐 Your app should now show the latest data at: http://3.109.103.171/"
echo ""
echo "🔧 Useful commands:"
echo "  - Check status: sudo systemctl status cv-review-app"
echo "  - View logs: sudo journalctl -u cv-review-app -f"
echo "  - Restart app: sudo systemctl restart cv-review-app" 
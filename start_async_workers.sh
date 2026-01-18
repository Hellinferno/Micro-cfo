#!/bin/bash
# Bash script to start all async task queue components
# Run this script to start Redis, Celery workers, Beat, and Flower

echo "🚀 Starting MicroCFO Async Task Queue System"
echo ""

# Check if Redis is running
echo "📡 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is already running"
else
    echo "❌ Redis is not running. Starting Redis..."
    echo "Please start Redis manually or use Docker:"
    echo "  docker run -d -p 6379:6379 redis:7-alpine"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🔧 Starting Celery components..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Start Celery Worker for Visual Auditor (background)
echo "Starting Celery Worker - Visual Auditor Queue..."
celery -A celery_app worker -Q visual_auditor --loglevel=info --concurrency=2 \
    --logfile=logs/celery_visual_auditor.log &

sleep 2

# Start Celery Worker for Legal Sentinel (background)
echo "Starting Celery Worker - Legal Sentinel Queue..."
celery -A celery_app worker -Q legal_sentinel --loglevel=info --concurrency=2 \
    --logfile=logs/celery_legal_sentinel.log &

sleep 2

# Start Celery Worker for Subsidy Hunter (background)
echo "Starting Celery Worker - Subsidy Hunter Queue..."
celery -A celery_app worker -Q subsidy_hunter --loglevel=info --concurrency=1 \
    --logfile=logs/celery_subsidy_hunter.log &

sleep 2

# Start Celery Worker for Negotiator (background)
echo "Starting Celery Worker - Negotiator Queue..."
celery -A celery_app worker -Q negotiator --loglevel=info --concurrency=1 \
    --logfile=logs/celery_negotiator.log &

sleep 2

# Start Celery Beat (background)
echo "Starting Celery Beat - Periodic Tasks Scheduler..."
celery -A celery_app beat --loglevel=info \
    --logfile=logs/celery_beat.log &

sleep 2

# Start Flower (background)
echo "Starting Flower - Celery Monitoring Dashboard..."
celery -A celery_app flower --port=5555 \
    --logfile=logs/flower.log &

echo ""
echo "✅ All components started!"
echo ""
echo "📊 Access Points:"
echo "  • Flower Dashboard: http://localhost:5555"
echo "  • API Server: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo ""
echo "🔍 Monitor your tasks:"
echo "  • Open Flower at http://localhost:5555"
echo "  • View active tasks, workers, and queues"
echo "  • Check logs in logs/ directory"
echo ""
echo "⚠️  To stop all workers:"
echo "  • Run: ./stop_async_workers.sh"
echo "  • Or: pkill -f celery"
echo ""
echo "📝 Logs are saved in logs/ directory"
echo ""

# Save PIDs for later cleanup
pgrep -f "celery.*worker" > /tmp/microcfo_celery_workers.pid
pgrep -f "celery.*beat" > /tmp/microcfo_celery_beat.pid
pgrep -f "celery.*flower" > /tmp/microcfo_flower.pid

echo "Process IDs saved for cleanup"
echo "Press Ctrl+C to stop monitoring (workers will continue in background)"
echo ""

# Keep script running to show logs
tail -f logs/celery_*.log logs/flower.log

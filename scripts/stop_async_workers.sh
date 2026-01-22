#!/bin/bash
# Stop all Celery workers, Beat, and Flower

echo "🛑 Stopping MicroCFO Async Task Queue System"
echo ""

# Function to stop processes
stop_processes() {
    local name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        echo "Stopping $name..."
        while read pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                echo "  Stopped process $pid"
            fi
        done < "$pid_file"
        rm "$pid_file"
    else
        echo "No $name processes found"
    fi
}

# Stop Celery workers
stop_processes "Celery Workers" "/tmp/microcfo_celery_workers.pid"

# Stop Celery Beat
stop_processes "Celery Beat" "/tmp/microcfo_celery_beat.pid"

# Stop Flower
stop_processes "Flower" "/tmp/microcfo_flower.pid"

# Fallback: kill any remaining celery processes
echo ""
echo "Checking for remaining Celery processes..."
if pgrep -f "celery" > /dev/null; then
    echo "Found remaining processes, stopping..."
    pkill -f "celery"
    sleep 2
    
    # Force kill if still running
    if pgrep -f "celery" > /dev/null; then
        echo "Force stopping remaining processes..."
        pkill -9 -f "celery"
    fi
fi

echo ""
echo "✅ All async task queue components stopped"
echo ""

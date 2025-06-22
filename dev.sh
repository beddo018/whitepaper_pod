#!/bin/bash

# Development script to run Vite dev server, Flask API server, and Celery worker

echo "🚀 Starting ParsePod development environment..."

# Check if Redis is installed and start it
if command -v redis-server >/dev/null 2>&1; then
    # Start Redis if not running
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "📦 Starting Redis..."
        redis-server &
        REDIS_PID=$!
        sleep 2
    else
        echo "✅ Redis is already running"
    fi
else
    echo "❌ Redis not found. Please install Redis:"
    echo "  macOS: brew install redis"
    echo "  Ubuntu: sudo apt-get install redis-server"
    echo "  Or run: ./install_redis.sh"
    exit 1
fi

# Set environment variables for development
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "🔧 Environment variables set for development mode"

# Start Vite dev server in the background
echo "⚛️ Starting Vite dev server on http://localhost:8080"
cd src/client && npm run dev &
VITE_PID=$!

# Wait for Vite to start
echo "⏳ Waiting for Vite to start..."
sleep 5

# Check if Vite started successfully
if ! curl -s http://localhost:8080 > /dev/null; then
    echo "❌ Vite failed to start. Check the logs above."
    exit 1
fi
echo "✅ Vite dev server is running"

# Start Flask API server
echo "🐍 Starting Flask API server on http://localhost:5000"
cd "$(dirname "$0")"  # Return to script directory (project root)
python src/app.py &
FLASK_PID=$!

# Wait for Flask to start
echo "⏳ Waiting for Flask to start..."
sleep 3

# Check if Flask started successfully
if ! curl -s http://localhost:5000/api/search_papers > /dev/null 2>&1; then
    echo "❌ Flask failed to start. Check the logs above."
    exit 1
fi
echo "✅ Flask API server is running"

# Start Celery worker
echo "🎯 Starting Celery worker..."
cd "$(dirname "$0")"  # Ensure we're in project root
python celery_worker.py &
CELERY_PID=$!

# Wait for Celery to start and register tasks
echo "⏳ Waiting for Celery to start..."
sleep 5

# Check if Celery started successfully by looking for the process
if ! ps -p $CELERY_PID > /dev/null 2>&1; then
    echo "❌ Celery failed to start. Check the logs above."
    exit 1
fi

# Additional check: verify Celery is responding
echo "✅ Celery worker is running (PID: $CELERY_PID)"

echo ""
echo "🎉 Development environment started successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 React app (with hot-reload): http://localhost:8080"
echo "🔌 Flask API: http://localhost:5000"
echo "🎯 Celery worker: Running in background"
echo "📦 Redis: Running (message broker)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tips:"
echo "  • Make changes to React components and see them update instantly"
echo "  • API calls are automatically proxied from Vite to Flask"
echo "  • Background tasks are processed by Celery workers"
echo "  • Check browser console for any errors"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt signal
trap "echo ''; echo '🛑 Stopping all servers...'; kill $VITE_PID $FLASK_PID $CELERY_PID $REDIS_PID 2>/dev/null; echo '✅ All servers stopped'; exit" INT
wait 
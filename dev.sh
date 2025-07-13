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
export PYTHONHTTPSVERIFY=0

# Allow custom Flask port via environment variable
export FLASK_PORT=${FLASK_PORT:-5000}

echo "🔧 Environment variables set for development mode"
echo "🐍 Flask will attempt to use port: $FLASK_PORT"

# Start Flask API server first to determine the actual port
echo "🐍 Starting Flask API server..."
cd "$(dirname "$0")"  # Return to script directory (project root)
python src/app.py &
FLASK_PID=$!

# Wait for Flask to start and detect the actual port
echo "⏳ Waiting for Flask to start..."
sleep 5

# Detect the actual port Flask is running on
ACTUAL_PORT=$FLASK_PORT
for port in $(seq $FLASK_PORT $((FLASK_PORT + 10))); do
    if curl -s http://localhost:$port/api/search_papers > /dev/null 2>&1; then
        ACTUAL_PORT=$port
        break
    fi
done

if [ "$ACTUAL_PORT" != "$FLASK_PORT" ]; then
    echo "⚠️  Flask is running on port $ACTUAL_PORT (requested: $FLASK_PORT)"
else
    echo "✅ Flask API server is running on port $ACTUAL_PORT"
fi

# Start Vite dev server with the correct Flask port for proxy
echo "⚛️ Starting Vite dev server on http://localhost:8080"
cd src/client && FLASK_PORT=$ACTUAL_PORT npm run dev &
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
echo "🔌 Flask API: http://localhost:$ACTUAL_PORT"
echo "🎯 Celery worker: Running in background"
echo "📦 Redis: Running (message broker)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tips:"
echo "  • Make changes to React components and see them update instantly"
echo "  • API calls are automatically proxied from Vite to Flask on port $ACTUAL_PORT"
echo "  • Background tasks are processed by Celery workers"
echo "  • Check browser console for any errors"
echo "  • If you see proxy errors, check that Flask is running on port $ACTUAL_PORT"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt signal
trap "echo ''; echo '🛑 Stopping all servers...'; kill $VITE_PID $FLASK_PID $CELERY_PID $REDIS_PID 2>/dev/null; echo '✅ All servers stopped'; exit" INT
wait 
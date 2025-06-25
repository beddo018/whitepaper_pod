# ParsePod

An application for converting scientific papers into podcasts so you can catch up with the latest breakthroughs on the go.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis (for Celery background tasks)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd whitepaper_pod
   ```

2. **Set up Python environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install Python dependencies
   pip install -r requirements.txt
   ```

3. **Set up React frontend**
   ```bash
   cd src/client
   npm install
   cd ../..
   ```

4. **Install and start Redis** (required for background tasks)
   ```bash
   # Option 1: Use the helper script
   ./install_redis.sh
   
   # Option 2: Manual installation
   # On macOS with Homebrew
   brew install redis
   brew services start redis
   
   # On Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   
   # Verify Redis is running
   redis-cli ping  # Should return PONG
   ```

## 🛠️ Development Mode (Recommended)

For development with hot-reload and live updates:

```bash
# Start Vite dev server, Flask API server, and Celery worker
./dev.sh
```

This will start:
- **React app** on http://localhost:8080 (with hot-reload)
- **Flask API** on http://localhost:5000
- **Celery worker** (background task processing)
- **Redis** (message broker, if not already running)

Visit http://localhost:8080 to see your app with live updates!

**Note**: The dev script automatically starts all required services including Redis and Celery workers for background task processing.

### Alternative Startup Methods

If the dev script has issues, you can start services manually:

**Terminal 1 - Vite Dev Server:**
```bash
cd src/client
npm run dev
```

**Terminal 2 - Flask API Server:**
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python src/app.py
```

**Terminal 3 - Celery Worker:**
```bash
python celery_worker.py
```

**Terminal 4 - Redis (if not running):**
```bash
redis-server
```

## 🏭 Production Mode

For production deployment:

```bash
# Build the React app
cd src/client
npm run build
cd ../..

# Start Flask server (serves built React app)
python src/app.py
```

Visit http://localhost:5000 to see your app.

## 📁 Project Structure

```
whitepaper_pod/
├── src/
│   ├── app.py                 # Main Flask application
│   ├── client/                # React frontend
│   │   ├── src/               # React source code
│   │   ├── dist/              # Built React app (production)
│   │   └── package.json       # Node dependencies
│   └── server/                # Backend services
│       ├── generate_audio/    # Text-to-speech
│       └── generate_transcript/ # PDF processing
├── dev.sh                     # Development startup script
├── requirements.txt           # Python dependencies
└── README.md
```

## 🔧 Configuration

### Environment Variables

Set these for development:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### API Endpoints

- `POST /api/search_papers` - Search for scientific papers
- `POST /api/generate_podcast` - Generate podcast from paper
- `GET /api/task_status/<task_id>` - Check background task status
- `GET /static/audio/<filename>` - Serve generated audio files

## 🐛 Troubleshooting

### Common Issues

**1. 404 Error on Flask Production Mode**
- Make sure you've built the React app: `cd src/client && npm run build`
- Check that `src/client/dist/index.html` exists
- Verify Flask is serving from the correct static folder

**2. Hot-reload not working**
- Use the development mode: `./dev.sh`
- Don't use `flask run` or `python src/app.py` for development
- Make sure both servers are running (Vite on 8080, Flask on 5000)

**3. API calls failing**
- In development: API calls are proxied from Vite (8080) to Flask (5000)
- In production: API calls go directly to Flask (5000)
- Check that Redis is running for background tasks

**4. Redis connection errors**
- Start Redis: `brew services start redis` (macOS) or `sudo systemctl start redis` (Linux)
- Verify Redis is running: `redis-cli ping` should return `PONG`

**5. Celery worker not starting**
- Check if Redis is running: `redis-cli ping`
- Try starting Celery manually: `python celery_worker.py`
- Verify Python path: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`
- Check Celery logs for import errors

**6. Module import errors**
- Ensure you're in the project root directory
- Set Python path: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Manual Server Startup

If the dev script doesn't work, start servers manually:

**Terminal 1 - Vite Dev Server:**
```bash
cd src/client
npm run dev
```

**Terminal 2 - Flask API Server:**
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python src/app.py
```

## 🧪 Testing

```bash
# Run Python tests
python -m pytest src/tests/

# Run React tests (if configured)
cd src/client
npm test
```

## 📦 Deployment

1. Build the React app: `cd src/client && npm run build`
2. Set up production environment variables
3. Start Flask server: `python src/app.py`
4. Configure reverse proxy (nginx) if needed

## 🤝 Contributing

1. Use development mode for local development
2. Make sure tests pass before submitting PRs
3. Follow the existing code structure
4. Update this README if you add new setup requirements

## 📝 Notes for Developers

- **Always use `./dev.sh` for development** - this ensures hot-reload works
- The Flask app serves different content in dev vs production modes
- API calls are automatically proxied in development mode
- Redis is required for background task processing
- Build the React app before testing production mode

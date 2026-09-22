#!/bin/bash
# start_ui.sh - Start the Job Tracker Web UI
PROJECT_DIR="/Users/carrienon/Desktop/code-project/job_scraper"
PYTHON="/opt/miniconda3/bin/python3"
PORT="${1:-5000}"

cd "$PROJECT_DIR" || exit 1

echo "🌐 Starting Job Tracker UI at http://127.0.0.1:${PORT}"
echo "   Press Ctrl+C to stop."
echo ""

# Open browser after a short delay
(sleep 1.5 && open "http://127.0.0.1:${PORT}") &

exec "$PYTHON" src/web_app.py --port "$PORT"

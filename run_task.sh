#!/bin/bash
# run_task.sh - Automated job scraping and matching pipeline

# Configuration
PROJECT_DIR="/Users/carrienon/Desktop/code-project/job_scraper"
LOG_FILE="$PROJECT_DIR/task.log"
PYTHON="/opt/homebrew/bin/python3"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
set -e
trap 'log "ERROR: Script failed at line $LINENO"' ERR

log "=== Job Scraping Pipeline Started ==="

# 1. Start Chrome in debug mode (background)
log "Starting Chrome with remote debugging..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome_selenium" \
  > /dev/null 2>&1 &

CHROME_PID=$!
log "Chrome started (PID: $CHROME_PID)"

# Wait for Chrome to be ready
sleep 5

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# 2. Run Indeed scraper
log "Running Indeed scraper..."
$PYTHON indeed_scraper.py --max-pages 2 || log "WARNING: Indeed scraper failed"

# 3. Run LinkedIn scraper
log "Running LinkedIn scraper..."
$PYTHON linkedin_scraper.py --max-pages 2 || log "WARNING: LinkedIn scraper failed"

# 4. Run AI job matching
log "Running AI job matching..."
$PYTHON ai_matcher.py --threshold 7.0 || log "WARNING: AI matcher failed"

# 5. Optional: Sync to Notion (if you have this script)
# log "Syncing to Notion..."
# $PYTHON sync_to_notion.py || log "WARNING: Notion sync failed"

# Cleanup: Close Chrome
log "Closing Chrome..."
kill $CHROME_PID 2>/dev/null || true

# Summary
log "=== Job Scraping Pipeline Completed ==="

# Optional: Send notification email
# echo "Job scraping pipeline completed at $(date)" | mail -s "Job Scraper Report" your_email@example.com

exit 0

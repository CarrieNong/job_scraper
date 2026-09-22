#!/bin/bash
# run_task.sh - Daily job scraping and AI matching pipeline
# Execution order: Indeed -> LinkedIn -> AI Matching

# Configuration
PROJECT_DIR="/Users/carrienon/Desktop/code-project/job_scraper"
LOG_DIR="$PROJECT_DIR/logs"
PYTHON="/opt/miniconda3/bin/python3"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging helper
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/main.log"
}

# Log errors but don't stop the pipeline on failure
trap 'log "ERROR: Script failed at line $LINENO"' ERR

log "=== Job Scraping Pipeline Started ==="

# Step 1: Launch Chrome in remote debug mode (background)
log "Starting Chrome with remote debugging..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome_selenium" \
  > /dev/null 2>&1 &

CHROME_PID=$!
log "Chrome started (PID: $CHROME_PID)"

# Wait for Chrome to be ready
sleep 5

cd "$PROJECT_DIR" || exit 1

# Step 2: Indeed scraper
log "Step 1/3: Running Indeed scraper..."
$PYTHON src/indeed_scraper.py --max-pages 3 > "$LOG_DIR/indeed_$(date +%Y%m%d).log" 2>&1
INDEED_EXIT=$?
if [ $INDEED_EXIT -eq 0 ]; then
    log "✅ Indeed scraper completed successfully"
else
    log "⚠️  WARNING: Indeed scraper failed (exit code: $INDEED_EXIT)"
fi

# Step 3: LinkedIn scraper
log "Step 2/3: Running LinkedIn scraper..."
$PYTHON src/linkedin_scraper.py --max-pages 3 > "$LOG_DIR/linkedin_$(date +%Y%m%d).log" 2>&1
LINKEDIN_EXIT=$?
if [ $LINKEDIN_EXIT -eq 0 ]; then
    log "✅ LinkedIn scraper completed successfully"
else
    log "⚠️  WARNING: LinkedIn scraper failed (exit code: $LINKEDIN_EXIT)"
fi

# Step 4: AI matching
log "Step 3/3: Running AI job matching..."
$PYTHON src/ai_matcher.py --threshold 7.0 > "$LOG_DIR/matcher_$(date +%Y%m%d).log" 2>&1
MATCHER_EXIT=$?
if [ $MATCHER_EXIT -eq 0 ]; then
    log "✅ AI matcher completed successfully"
else
    log "⚠️  WARNING: AI matcher failed (exit code: $MATCHER_EXIT)"
fi

# Close Chrome
log "Closing Chrome..."
kill $CHROME_PID 2>/dev/null || true

# Pipeline summary
log "=== Pipeline Completed ==="
log "Indeed:     $([ $INDEED_EXIT -eq 0 ] && echo '✅' || echo '❌')"
log "LinkedIn:   $([ $LINKEDIN_EXIT -eq 0 ] && echo '✅' || echo '❌')"
log "AI Matcher: $([ $MATCHER_EXIT -eq 0 ] && echo '✅' || echo '❌')"

# Get today's stats from the database
log "Fetching today's stats..."
STATS=$($PYTHON << 'EOF'
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from db_mongo import get_collection
from datetime import datetime
try:
    jobs         = get_collection("jobs")
    matched_jobs = get_collection("matched_jobs")
    today_start  = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    scraped = jobs.count_documents({"created_at": {"$gte": today_start}})
    matched = matched_jobs.count_documents({"matched_at": {"$gte": today_start}})
    print(f"{scraped} {matched}")
except Exception as e:
    print("0 0")
EOF
)

SCRAPED=$(echo "$STATS" | awk '{print $1}')
MATCHED=$(echo "$STATS" | awk '{print $2}')
log "Today: ${SCRAPED} jobs scraped, ${MATCHED} high-quality matches"

# macOS desktop notification
osascript -e "display notification \"${SCRAPED} new jobs scraped, ${MATCHED} matched\" with title \"Job Scraper Done\" sound name \"Glass\"" 2>/dev/null || true

exit 0

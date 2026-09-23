#!/bin/bash
# run_quick.sh — Morning quick-scrape pipeline (run at ~11 AM)
#
# Fetches LinkedIn jobs posted in the last 12 hours, then runs AI matching
# so you have fresh, scored results ready before your daily application session.
#
# Complements the full 24-hour scrape (run_task.sh) that runs at ~6 PM.
#
# Usage:
#   caffeinate -i ./run_quick.sh          # recommended (keeps Mac awake)
#   ./run_quick.sh                        # without caffeinate

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_DIR="/Users/carrienon/Desktop/code-project/job_scraper"
LOG_DIR="$PROJECT_DIR/logs"
PYTHON="/opt/miniconda3/bin/python3"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/main.log"
}

trap 'log "ERROR: Script failed at line $LINENO"' ERR

log "=== Quick Scrape Pipeline Started (12-hour window) ==="

# ---------------------------------------------------------------------------
# Step 1: Launch Chrome in remote-debug mode
# ---------------------------------------------------------------------------
log "Starting Chrome with remote debugging..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome_selenium" \
  > /dev/null 2>&1 &

CHROME_PID=$!
log "Chrome started (PID: $CHROME_PID)"
sleep 5

cd "$PROJECT_DIR" || exit 1

# ---------------------------------------------------------------------------
# Step 2: LinkedIn quick scraper (3 pages × 30 jobs, last 12 hours)
# ---------------------------------------------------------------------------
log "Step 1/2: Running LinkedIn quick scraper (12-hour window)..."
$PYTHON src/linkedin_quick_scraper.py \
  --max-pages 3 \
  > "$LOG_DIR/linkedin_quick_$(date +%Y%m%d).log" 2>&1
QUICK_EXIT=$?

if [ $QUICK_EXIT -eq 0 ]; then
    log "✅ LinkedIn quick scraper completed successfully"
else
    log "⚠️  WARNING: LinkedIn quick scraper failed (exit code: $QUICK_EXIT)"
fi

# ---------------------------------------------------------------------------
# Step 3: AI matching (only jobs not yet analyzed)
# ---------------------------------------------------------------------------
log "Step 2/2: Running AI job matching..."
$PYTHON src/ai_matcher.py --threshold 7.0 \
  > "$LOG_DIR/matcher_quick_$(date +%Y%m%d).log" 2>&1
MATCHER_EXIT=$?

if [ $MATCHER_EXIT -eq 0 ]; then
    log "✅ AI matcher completed successfully"
else
    log "⚠️  WARNING: AI matcher failed (exit code: $MATCHER_EXIT)"
fi

# ---------------------------------------------------------------------------
# Close Chrome
# ---------------------------------------------------------------------------
log "Closing Chrome..."
kill $CHROME_PID 2>/dev/null || true

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log "=== Quick Scrape Pipeline Completed ==="
log "LinkedIn Quick: $([ $QUICK_EXIT  -eq 0 ] && echo '✅' || echo '❌')"
log "AI Matcher:     $([ $MATCHER_EXIT -eq 0 ] && echo '✅' || echo '❌')"

# Fetch stats from MongoDB
STATS=$($PYTHON << 'EOF'
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from db_mongo import get_collection
from datetime import datetime, timedelta
try:
    jobs         = get_collection("jobs")
    matched_jobs = get_collection("matched_jobs")
    since = datetime.now() - timedelta(hours=12)
    scraped = jobs.count_documents({"created_at": {"$gte": since}})
    matched = matched_jobs.count_documents({"matched_at": {"$gte": since}})
    print(f"{scraped} {matched}")
except Exception:
    print("0 0")
EOF
)

SCRAPED=$(echo "$STATS" | awk '{print $1}')
MATCHED=$(echo "$STATS" | awk '{print $2}')
log "Last 12 h: ${SCRAPED} jobs scraped, ${MATCHED} high-quality matches"

# macOS desktop notification
osascript -e "display notification \"${SCRAPED} new jobs scraped (12 h), ${MATCHED} matched\" with title \"Quick Scrape Done\" sound name \"Glass\"" 2>/dev/null || true

exit 0

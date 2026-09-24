#!/usr/bin/env python3
"""
Job Tracker Web UI
Flask web app to view and manage matched jobs
"""
import sys
import os
from datetime import datetime
from bson import ObjectId
import json

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import threading
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from db_mongo import (
    get_collection,
    get_scraper_stats,
    get_unmatched_jobs,
    count_unmatched_jobs,
    _parse_filter_date,
)

load_dotenv()

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static"),
)

# ─── Status mapping ───────────────────────────────────────────────────────────
# DB value → English label
STATUS_MAP = {
    "pending":    "Not Applied",
    "applied":    "Applied",
    "rejected":   "Rejected",
    "interview":  "Interview",
    "unsuitable": "Unsuitable",
    "closed":     "Closed",
}

# Unmatched jobs user_status mapping (for 6-7 score borderline jobs)
UNMATCHED_USER_STATUS_MAP = {
    "":           "Unmarked",
    "watchlist":  "Can Apply",
}

# English label → DB value (reverse mapping used nowhere yet, kept for clarity)
STATUS_REVERSE = {v: k for k, v in STATUS_MAP.items()}

MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "7.0"))
UNMATCHED_PAGE_SIZE = 20


def _normalize_link(job: dict) -> str:
    """
    Return a valid absolute URL for the job posting.

    LinkedIn cards store relative hrefs like /jobs/view/1234567890/
    or full URLs with tracking params. We normalise to the clean canonical form.
    """
    link = job.get("link", "")
    source = job.get("source", "")

    if source == "linkedin":
        job_id = job.get("job_id", "")
        if job_id:
            # Always use the canonical LinkedIn job URL
            return f"https://www.linkedin.com/jobs/view/{job_id}/"
        # Fallback: prepend domain if link is relative
        if link and not link.startswith("http"):
            return "https://www.linkedin.com" + link

    return link


def _serialize(job: dict) -> dict:
    """Convert MongoDB document to JSON-serialisable dict."""
    job["_id"] = str(job["_id"])
    for key in ("matched_at", "applied_at", "created_at", "updated_at"):
        if key in job and isinstance(job[key], datetime):
            job[key] = job[key].strftime("%Y-%m-%d %H:%M")
    # Normalise job link (fixes relative LinkedIn URLs)
    job["link"] = _normalize_link(job)
    # Ensure notes field always exists
    job.setdefault("notes", "")
    # Ensure status always exists
    job.setdefault("status", "pending")
    return job


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/unmatched")
def unmatched():
    return render_template("unmatched.html")


@app.route("/api/jobs")
def api_jobs():
    """Return all matched jobs, newest first."""
    collection = get_collection("matched_jobs")

    # Optional filters from query-string
    status_filter = request.args.get("status")      # e.g. ?status=pending
    source_filter = request.args.get("source")      # e.g. ?source=linkedin
    search_query  = request.args.get("q", "").strip()
    date_from     = request.args.get("date_from", "").strip() or None
    date_to       = request.args.get("date_to", "").strip() or None

    query: dict = {}
    if status_filter and status_filter != "all":
        query["status"] = status_filter
    if source_filter and source_filter != "all":
        query["source"] = source_filter
    if search_query:
        query["$or"] = [
            {"title":   {"$regex": search_query, "$options": "i"}},
            {"company": {"$regex": search_query, "$options": "i"}},
        ]
    if date_from or date_to:
        time_filter: dict = {}
        start = _parse_filter_date(date_from)
        end   = _parse_filter_date(date_to, end_of_day=True)
        if start:
            time_filter["$gte"] = start
        if end:
            time_filter["$lte"] = end
        query["matched_at"] = time_filter

    jobs = list(collection.find(query).sort("matched_at", -1).limit(500))
    jobs = [_serialize(j) for j in jobs]

    return jsonify({"jobs": jobs, "total": len(jobs)})


@app.route("/api/unmatched-jobs")
def api_unmatched_jobs():
    """Return AI-rejected jobs from the original jobs collection, paginated."""
    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.args.get("page_size", UNMATCHED_PAGE_SIZE))
    except (TypeError, ValueError):
        page_size = UNMATCHED_PAGE_SIZE
    page_size = max(1, min(page_size, 50))

    source_filter = request.args.get("source")
    if source_filter == "all":
        source_filter = None
    search_query = request.args.get("q", "").strip()
    date_from = request.args.get("date_from", "").strip() or None
    date_to = request.args.get("date_to", "").strip() or None

    score_min = None
    score_max = None
    try:
        if request.args.get("score_min") not in (None, ""):
            score_min = float(request.args.get("score_min"))
    except (TypeError, ValueError):
        score_min = None
    try:
        if request.args.get("score_max") not in (None, ""):
            score_max = float(request.args.get("score_max"))
    except (TypeError, ValueError):
        score_max = None

    user_status_filter = request.args.get("user_status")  # "watchlist" or None

    jobs, total = get_unmatched_jobs(
        page=page,
        page_size=page_size,
        source=source_filter,
        search=search_query or None,
        threshold=MATCH_THRESHOLD,
        date_from=date_from,
        date_to=date_to,
        score_min=score_min,
        score_max=score_max,
        user_status=user_status_filter,
    )
    jobs = [_serialize(j) for j in jobs]
    pages = max(1, (total + page_size - 1) // page_size) if total else 1
    page = min(max(1, page), pages)

    return jsonify({
        "jobs": jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "threshold": MATCH_THRESHOLD,
    })


@app.route("/api/jobs/<job_id>/status", methods=["PATCH"])
def api_update_status(job_id: str):
    """Update job status."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in STATUS_MAP:
        return jsonify({"error": f"Invalid status. Allowed: {list(STATUS_MAP.keys())}"}), 400

    collection = get_collection("matched_jobs")
    result = collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"status": new_status, "updated_at": datetime.now()}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"ok": True, "status": new_status})


@app.route("/api/jobs/<job_id>/notes", methods=["PATCH"])
def api_update_notes(job_id: str):
    """Update job notes."""
    data = request.get_json(silent=True) or {}
    notes = data.get("notes", "")

    collection = get_collection("matched_jobs")
    result = collection.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"notes": notes, "updated_at": datetime.now()}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"ok": True})


@app.route("/api/jobs/<job_id>/info", methods=["PATCH"])
def api_update_job_info(job_id: str):
    """Update job title / company / location in matched_jobs."""
    data = request.get_json(silent=True) or {}
    update_fields = {}
    for field in ("title", "company", "location"):
        if field in data and isinstance(data[field], str):
            update_fields[field] = data[field].strip()

    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    try:
        oid = ObjectId(job_id)
    except Exception:
        return jsonify({"error": "Invalid job ID"}), 400

    update_fields["updated_at"] = datetime.now()
    collection = get_collection("matched_jobs")
    result = collection.update_one({"_id": oid}, {"$set": update_fields})

    if result.matched_count == 0:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"ok": True})


@app.route("/api/unmatched-jobs/<job_id>/status", methods=["PATCH"])
def api_update_unmatched_status(job_id: str):
    """Update user_status of an unmatched (borderline) job.
    When marked as 'watchlist' (Can Apply), also copy the job to matched_jobs.
    """
    data = request.get_json(silent=True) or {}
    new_status = data.get("user_status", "")
    if new_status not in UNMATCHED_USER_STATUS_MAP:
        return jsonify({"error": f"Invalid user_status. Allowed: {list(UNMATCHED_USER_STATUS_MAP.keys())}"}), 400

    jobs_col = get_collection("jobs")
    result = jobs_col.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"user_status": new_status, "updated_at": datetime.now()}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Job not found"}), 404

    # When marked Can Apply → copy to matched_jobs so it shows in the tracker
    copied_to_matched = False
    copy_error = None
    if new_status == "watchlist":
        try:
            job = jobs_col.find_one({"_id": ObjectId(job_id)})
            if not job:
                copy_error = "Source job not found after update"
            else:
                matched_col = get_collection("matched_jobs")
                jid    = job.get("job_id") or ""
                source = job.get("source") or ""
                now    = datetime.now()

                doc = {
                    "title":       job.get("title", ""),
                    "company":     job.get("company", ""),
                    "location":    job.get("location", ""),
                    "link":        job.get("link", ""),
                    "job_id":      jid,
                    "source":      source,
                    "description": job.get("description", ""),
                    "applicants":  job.get("applicants", ""),
                    "match_score": job.get("match_score", 0),
                    "recommendation":          job.get("recommendation", ""),
                    "disqualification_reason": job.get("disqualification_reason", ""),
                    "match_reasons":           job.get("match_reasons", []),
                    "missing_requirements":    job.get("missing_requirements", []),
                    "red_flags":               job.get("red_flags", []),
                    "nice_to_have_matches":    job.get("nice_to_have_matches", []),
                    "summary":                 job.get("summary", ""),
                    "what_youll_do":           job.get("what_youll_do", {"matched": [], "unmatched": []}),
                    "what_theyre_looking_for": job.get("what_theyre_looking_for", {"matched": [], "unmatched": []}),
                    "status":         "pending",
                    "matched_at":     now,   # use NOW so it appears at top of list
                    "applied_at":     None,
                    "notes":          "",
                    "created_at":     now,
                    "from_unmatched": True,
                }

                # replace_one with upsert: inserts if not there, updates if already there
                matched_col.replace_one(
                    {"job_id": jid, "source": source},
                    doc,
                    upsert=True,
                )
                copied_to_matched = True
                print(f"[Can Apply] Copied job_id={jid} source={source} to matched_jobs")

        except Exception as e:
            copy_error = str(e)
            print(f"[Can Apply] ERROR copying to matched_jobs: {e}")

    return jsonify({"ok": True, "user_status": new_status,
                    "copied_to_matched": copied_to_matched,
                    "copy_error": copy_error})


@app.route("/api/stats")
def api_stats():
    """Return status counts for the summary bar and pipeline funnel."""
    collection = get_collection("matched_jobs")
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    raw = list(collection.aggregate(pipeline))
    by_status = {item["_id"]: item["count"] for item in raw}
    ai_matched = sum(by_status.values())

    scraper = get_scraper_stats()
    unmatched = count_unmatched_jobs(threshold=MATCH_THRESHOLD)

    return jsonify({
        # existing: matched-jobs filter chips
        "total":     ai_matched,
        "by_status": by_status,
        "unmatched": unmatched,
        # new: full-pipeline funnel
        "funnel": {
            "title_clicked": scraper.get("title_passed_clicked", 0),
            "german_filtered": scraper.get("german_filtered", 0),
            "ai_matched": ai_matched,
            "ai_unmatched": unmatched,
            "applied": by_status.get("applied", 0),
        },
    })


# ─── Manual-apply endpoint ────────────────────────────────────────────────────

# Background task state (one run at a time)
_manual_apply_lock = threading.Lock()
_manual_apply_state: dict = {"running": False, "log": [], "done_count": 0, "fail_count": 0}


@app.route("/manual-apply")
def manual_apply_page():
    return render_template("manual_apply.html")


@app.route("/api/manual-apply", methods=["POST"])
def api_manual_apply():
    """
    Accepts a JSON body: {"urls": [...], "applied_date": "YYYY-MM-DD"}
    Runs the manual-apply scraper in a background thread.
    Returns immediately with {"status": "started"} or an error.
    """
    data = request.get_json(silent=True) or {}
    urls = data.get("urls", [])
    if not isinstance(urls, list):
        return jsonify({"error": "urls must be a list"}), 400
    urls = [u.strip() for u in urls if isinstance(u, str) and u.strip()]
    if not urls:
        return jsonify({"error": "No valid URLs provided"}), 400

    # Parse optional applied_date
    applied_date = None
    raw_date = data.get("applied_date", "").strip()
    if raw_date:
        try:
            applied_date = datetime.strptime(raw_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": f"Invalid applied_date format, expected YYYY-MM-DD"}), 400

    if not _manual_apply_lock.acquire(blocking=False):
        return jsonify({"error": "A manual-apply run is already in progress. Please wait."}), 429

    def run():
        try:
            _manual_apply_state["running"] = True
            _manual_apply_state["log"] = []
            _manual_apply_state["done_count"] = 0
            _manual_apply_state["fail_count"] = 0

            # Import here to avoid circular deps at module load
            from manual_apply_scraper import process_urls as _process_urls

            # Monkey-patch print so progress goes to the state log
            import builtins
            _original_print = builtins.print

            def _capture_print(*args, **kwargs):
                line = " ".join(str(a) for a in args)
                _manual_apply_state["log"].append(line)
                _original_print(*args, **kwargs)

            builtins.print = _capture_print
            try:
                _process_urls(urls, applied_date=applied_date)
                # Count results from log
                for line in _manual_apply_state["log"]:
                    if "✅ Saved to matched_jobs" in line:
                        _manual_apply_state["done_count"] += 1
                    elif "❌ Scraping failed" in line or "Failed  :" in line:
                        _manual_apply_state["fail_count"] += 1
            finally:
                builtins.print = _original_print
        except Exception as e:
            _manual_apply_state["log"].append(f"❌ Fatal error: {e}")
        finally:
            _manual_apply_state["running"] = False
            _manual_apply_lock.release()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return jsonify({"status": "started", "total": len(urls)})


@app.route("/api/manual-apply/status")
def api_manual_apply_status():
    """Poll this to get progress of the current / last manual-apply run."""
    state = _manual_apply_state
    return jsonify({
        "running":    state["running"],
        "log":        state["log"][-100:],   # last 100 lines
        "done_count": state["done_count"],
        "fail_count": state["fail_count"],
    })


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Job Tracker Web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", "-p", type=int, default=5050, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print(f"\n🌐 Job Tracker starting at http://{args.host}:{args.port}")
    print("   Press Ctrl+C to stop.\n")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()

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

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from db_mongo import get_collection, get_scraper_stats

load_dotenv()

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static"),
)

# ─── Status mapping ───────────────────────────────────────────────────────────
# DB value → Chinese label
STATUS_MAP = {
    "pending":    "未投递",
    "applied":    "已投递",
    "rejected":   "已拒绝",
    "interview":  "面试中",
    "unsuitable": "不符合",
}

# Chinese label → DB value (reverse mapping used nowhere yet, kept for clarity)
STATUS_REVERSE = {v: k for k, v in STATUS_MAP.items()}


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


@app.route("/api/jobs")
def api_jobs():
    """Return all matched jobs, newest first."""
    collection = get_collection("matched_jobs")

    # Optional filters from query-string
    status_filter = request.args.get("status")      # e.g. ?status=pending
    source_filter = request.args.get("source")      # e.g. ?source=linkedin
    search_query  = request.args.get("q", "").strip()

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

    jobs = list(collection.find(query).sort("matched_at", -1).limit(500))
    jobs = [_serialize(j) for j in jobs]

    return jsonify({"jobs": jobs, "total": len(jobs)})


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


@app.route("/api/stats")
def api_stats():
    """Return status counts for the summary bar and pipeline funnel."""
    collection = get_collection("matched_jobs")
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    raw = list(collection.aggregate(pipeline))
    by_status = {item["_id"]: item["count"] for item in raw}
    ai_matched = sum(by_status.values())

    scraper = get_scraper_stats()

    return jsonify({
        # existing: matched-jobs filter chips
        "total":     ai_matched,
        "by_status": by_status,
        # new: full-pipeline funnel
        "funnel": {
            "title_clicked": scraper.get("title_passed_clicked", 0),
            "german_filtered": scraper.get("german_filtered", 0),
            "ai_matched": ai_matched,
            "applied": by_status.get("applied", 0),
        },
    })


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Job Tracker Web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", "-p", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print(f"\n🌐 Job Tracker starting at http://{args.host}:{args.port}")
    print("   Press Ctrl+C to stop.\n")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()

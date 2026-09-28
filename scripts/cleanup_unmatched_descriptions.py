#!/usr/bin/env python3
"""
Clear the description field on unmatched jobs older than N days.

Keeps link / title / company / AI analysis fields. Skips:
- watchlist (Can Apply) jobs
- jobs already applied / rejected / interviewed in matched_jobs

Safe to run daily — only non-empty descriptions on jobs with
matched_at older than the window are cleared.

Usage:
  python3 scripts/cleanup_unmatched_descriptions.py            # dry-run
  python3 scripts/cleanup_unmatched_descriptions.py --execute
  python3 scripts/cleanup_unmatched_descriptions.py --execute --days 14
"""
import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, _SRC)

from dotenv import load_dotenv

from core.db_mongo import (
    clear_unmatched_descriptions,
    get_applied_job_keys,
    get_collection,
)

load_dotenv()

_SAMPLE_LIMIT = 10


def _preview(days, threshold):
    """Print a few sample jobs that would be cleared."""
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)
    protected = get_applied_job_keys()
    jobs = get_collection("jobs")
    cursor = jobs.find(
        {
            "matched_at": {"$exists": True, "$lt": cutoff},
            "match_score": {"$lt": float(threshold)},
            "user_status": {"$ne": "watchlist"},
            "description": {"$exists": True, "$nin": [None, ""]},
        },
        {
            "title": 1,
            "company": 1,
            "match_score": 1,
            "matched_at": 1,
            "job_id": 1,
            "source": 1,
            "link": 1,
            "description": 1,
        },
    ).sort("matched_at", 1)

    samples = []
    for job in cursor:
        if (job.get("job_id"), job.get("source")) in protected:
            continue
        samples.append(job)
        if len(samples) >= _SAMPLE_LIMIT:
            break

    if not samples:
        print("No matching jobs.")
        return

    print(f"\nSample (up to {_SAMPLE_LIMIT}):")
    for job in samples:
        desc_len = len(job.get("description") or "")
        matched_at = job.get("matched_at")
        matched_str = matched_at.strftime("%Y-%m-%d") if matched_at else "?"
        print(
            f"  · [{job.get('match_score', '?')}/10] {job.get('title', '?')} "
            f"@ {job.get('company', '?')}  matched={matched_str}  "
            f"desc={desc_len} chars"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Clear description on unmatched jobs older than N days."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually clear descriptions (default is dry-run)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Clear descriptions when matched_at is older than this many days (default: 14)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=float(os.getenv("MATCH_THRESHOLD", "7.0")),
        help="Match score below which a job counts as unmatched (default: MATCH_THRESHOLD or 7.0)",
    )
    args = parser.parse_args()

    print(
        f"{'EXECUTE' if args.execute else 'DRY-RUN'}: "
        f"unmatched (score < {args.threshold}) with matched_at older than "
        f"{args.days} days"
    )

    count = clear_unmatched_descriptions(
        days=args.days,
        threshold=args.threshold,
        dry_run=not args.execute,
    )

    if not args.execute:
        print(f"Would clear description on {count} jobs.")
        _preview(args.days, args.threshold)
        print("\nRe-run with --execute to apply.")
    else:
        print(f"Done. Cleared description on {count} jobs.")


if __name__ == "__main__":
    main()

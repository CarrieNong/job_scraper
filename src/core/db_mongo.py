# db_mongo.py - MongoDB database operations
from pymongo import MongoClient, errors
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection configuration
# Local test: mongodb://localhost:27017/
# MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "job_scraper"
COLLECTION_NAME = "jobs"


def get_db():
    """Get database connection"""
    client = MongoClient(MONGO_URI)
    return client[DATABASE_NAME]


def get_collection(collection_name=None):
    """
    Get a specific collection
    
    Args:
        collection_name (str): Name of the collection, defaults to main jobs collection
        
    Returns:
        Collection: MongoDB collection object
    """
    db = get_db()
    if collection_name is None:
        collection_name = COLLECTION_NAME
    return db[collection_name]


def init_db():
    """Initialize database and create indexes"""
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    # Create unique index to prevent duplicates
    collection.create_index("link", unique=True)
    collection.create_index("job_id")
    collection.create_index("source")
    collection.create_index("created_at")
    collection.create_index("matched_at")
    collection.create_index("match_score")
    
    print(f"MongoDB initialized: {DATABASE_NAME}.{COLLECTION_NAME}")
    print(f"Indexes created: link (unique), job_id, source, created_at, matched_at, match_score")


def save_job(job_data):
    """
    Save job data to MongoDB
    
    Args:
        job_data (dict): Job information dictionary
        
    Returns:
        bool: True if saved successfully, False if already exists or failed
    """
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    # Add creation timestamp
    job_data["created_at"] = datetime.now()
    
    # Ensure required fields have default values
    job_data.setdefault("source", "linkedin")
    job_data.setdefault("status", "new")
    
    try:
        result = collection.insert_one(job_data)
        print(f"✅ Saved job: {job_data.get('title', 'Untitled')} (ID: {result.inserted_id})")
        return True
    except errors.DuplicateKeyError:
        print(f"⚠️  Job already exists: {job_data.get('title', 'Untitled')}")
        return False
    except Exception as e:
        print(f"❌ Error saving job: {e}")
        return False


def is_job_id_exists(job_id, source="linkedin"):
    """
    Check if job_id already exists
    
    Args:
        job_id (str): Job ID
        source (str): Job source website
        
    Returns:
        bool: True if exists, False otherwise
    """
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    count = collection.count_documents({"job_id": job_id, "source": source})
    return count > 0


def get_jobs(filter_dict=None, limit=100):
    """
    Query job data
    
    Args:
        filter_dict (dict): Query filter, e.g. {"source": "linkedin"}
        limit (int): Maximum number of results to return
        
    Returns:
        list: List of job documents
    """
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    if filter_dict is None:
        filter_dict = {}
    
    jobs = list(collection.find(filter_dict).sort("created_at", -1).limit(limit))
    return jobs


def get_new_jobs(limit=None, source=None):
    """
    Get jobs with status "new" that haven't been analyzed yet
    
    Args:
        limit (int): Maximum number of jobs to return (None for all)
        source (str): Filter by source (indeed, linkedin, or None for all)
        
    Returns:
        list: List of new job documents
    """
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    # Only query jobs with status="new" and without matched_at field (not yet AI matched)
    filter_dict = {
        "status": "new",
        "matched_at": {"$exists": False}  # New: exclude already matched jobs
    }
    if source:
        filter_dict["source"] = source
    
    query = collection.find(filter_dict).sort("created_at", -1)
    
    if limit:
        query = query.limit(limit)
    
    return list(query)


def get_jobs_by_source(source, limit=100):
    """
    Get jobs by source
    
    Args:
        source (str): Job source (indeed, linkedin)
        limit (int): Maximum number of results
        
    Returns:
        list: List of job documents
    """
    return get_jobs(filter_dict={"source": source}, limit=limit)


def count_jobs(source=None):
    """
    Count jobs, optionally filtered by source
    
    Args:
        source (str): Job source (indeed, linkedin, or None for all)
        
    Returns:
        int: Number of jobs
    """
    filter_dict = {"source": source} if source else {}
    return get_job_count(filter_dict)


def get_job_count(filter_dict=None):
    """
    Count jobs matching the filter
    
    Args:
        filter_dict (dict): Query filter
        
    Returns:
        int: Number of jobs
    """
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    if filter_dict is None:
        filter_dict = {}
    
    return collection.count_documents(filter_dict)


def update_job_status(job_id, source, new_status):
    """
    Update job status
    
    Args:
        job_id (str): Job ID
        source (str): Job source website
        new_status (str): New status, e.g. "applied", "interviewed", "rejected"
        
    Returns:
        bool: True if updated successfully
    """
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    result = collection.update_one(
        {"job_id": job_id, "source": source},
        {"$set": {"status": new_status, "updated_at": datetime.now()}}
    )
    
    return result.modified_count > 0


def increment_scraper_stat(key: str, amount: int = 1) -> None:
    """
    Atomically increment a global scraper counter by `amount`.

    Counters are stored in the `scraper_stats` collection as a single
    document with _id="global".  The document is created on first use.

    Recognised keys
    ---------------
    title_passed_clicked  – jobs that passed the title filter and were new
                            (i.e. we actually clicked into the detail page)
    german_filtered       – detail pages detected as German and skipped
    """
    db = get_db()
    db["scraper_stats"].update_one(
        {"_id": "global"},
        {"$inc": {key: amount}, "$set": {"updated_at": datetime.now()}},
        upsert=True,
    )


def get_scraper_stats() -> dict:
    """
    Return all scraper counters as a plain dict (keys without leading '_').

    Returns an empty dict if no scraping run has taken place yet.
    """
    db = get_db()
    doc = db["scraper_stats"].find_one({"_id": "global"}) or {}
    doc.pop("_id", None)
    doc.pop("updated_at", None)
    return doc


def mark_job_as_matched(job_id, source, match_score=None, analysis=None):
    """
    Mark a job as AI-analyzed and persist the full analysis on the jobs document.

    Matched jobs are also copied to matched_jobs separately. Unmatched jobs stay
    here so the unmatched page can show score, reason, and breakdowns.

    Args:
        job_id (str): Job ID
        source (str): Job source website
        match_score (float): Match score (0-10)
        analysis (dict): Full AI analysis payload to store on the job

    Returns:
        bool: True if updated successfully
    """
    db = get_db()
    collection = db[COLLECTION_NAME]

    update_data = {
        "matched_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    if match_score is not None:
        update_data["match_score"] = match_score

    if analysis:
        update_data.update({
            "recommendation": analysis.get("recommendation", ""),
            "disqualification_reason": analysis.get("disqualification_reason", ""),
            "match_reasons": analysis.get("match_reasons", []),
            "missing_requirements": analysis.get("missing_requirements", []),
            "red_flags": analysis.get("red_flags", []),
            "nice_to_have_matches": analysis.get("nice_to_have_matches", []),
            "summary": analysis.get("summary", ""),
            "what_youll_do": analysis.get("what_youll_do") or {"matched": [], "unmatched": []},
            "what_theyre_looking_for": analysis.get("what_theyre_looking_for") or {"matched": [], "unmatched": []},
        })

    result = collection.update_one(
        {"job_id": job_id, "source": source},
        {"$set": update_data}
    )

    return result.modified_count > 0


def _parse_filter_date(value, end_of_day=False):
    """Parse YYYY-MM-DD or YYYY-MM-DDTHH:MM into a datetime, or None."""
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            parsed = datetime.strptime(text, fmt)
            if end_of_day and fmt == "%Y-%m-%d":
                parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
            return parsed
        except ValueError:
            continue
    return None


def get_unmatched_jobs(
    page=1,
    page_size=20,
    source=None,
    search=None,
    threshold=7.0,
    date_from=None,
    date_to=None,
    score_min=None,
    score_max=None,
    user_status=None,
):
    """
    Return AI-analyzed jobs that scored below the match threshold.

    Newest matched_at first. Optional time range and score range filters
    are applied on top of the unmatched threshold.
    """
    db = get_db()
    collection = db[COLLECTION_NAME]

    page = max(1, int(page or 1))
    page_size = max(1, min(int(page_size or 20), 50))

    score_filter = {"$lt": float(threshold)}
    if score_min is not None:
        score_filter["$gte"] = float(score_min)
    if score_max is not None:
        score_filter["$lte"] = min(float(score_max), float(threshold) - 0.0001)

    filter_dict = {
        "matched_at": {"$exists": True},
        "match_score": score_filter,
    }

    start = _parse_filter_date(date_from)
    end = _parse_filter_date(date_to, end_of_day=True)
    if start or end:
        time_filter = {}
        if start:
            time_filter["$gte"] = start
        if end:
            time_filter["$lte"] = end
        filter_dict["matched_at"] = time_filter

    if source:
        filter_dict["source"] = source
    if user_status == "watchlist":
        filter_dict["user_status"] = "watchlist"
    if search:
        filter_dict["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"disqualification_reason": {"$regex": search, "$options": "i"}},
            {"summary": {"$regex": search, "$options": "i"}},
        ]

    total = collection.count_documents(filter_dict)
    pages = max(1, (total + page_size - 1) // page_size) if total else 1
    page = min(page, pages)
    skip = (page - 1) * page_size
    projection = {"description": 0}
    jobs = list(
        collection.find(filter_dict, projection)
        .sort("matched_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    return jobs, total


def count_unmatched_jobs(threshold=7.0):
    """Count AI-analyzed jobs that scored below the match threshold."""
    db = get_db()
    return db[COLLECTION_NAME].count_documents({
        "matched_at": {"$exists": True},
        "match_score": {"$lt": float(threshold)},
    })


def delete_old_jobs(days=30):
    """
    Delete jobs older than specified days (optional cleanup)
    
    Args:
        days (int): Number of days threshold
        
    Returns:
        int: Number of deleted jobs
    """
    from datetime import timedelta
    
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    threshold = datetime.now() - timedelta(days=days)
    result = collection.delete_many({"created_at": {"$lt": threshold}})
    
    print(f"🗑️  Deleted {result.deleted_count} jobs older than {days} days")
    return result.deleted_count


# Testing and statistics
def print_stats():
    """Print database statistics"""
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    total = collection.count_documents({})
    linkedin_count = collection.count_documents({"source": "linkedin"})
    indeed_count = collection.count_documents({"source": "indeed"})
    
    print("\n📊 Database Statistics:")
    print(f"Total jobs: {total}")
    print(f"LinkedIn jobs: {linkedin_count}")
    print(f"Indeed jobs: {indeed_count}")
    
    # Group by status
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    status_stats = list(collection.aggregate(pipeline))
    
    print("\nBy status:")
    for stat in status_stats:
        print(f"  {stat['_id']}: {stat['count']}")


if __name__ == "__main__":
    # Test connection and initialization
    print("Initializing MongoDB...")
    init_db()
    
    # Test saving data
    test_job = {
        "title": "Senior Frontend Engineer",
        "company": "Test Company",
        "location": "Berlin, Germany",
        "link": "https://example.com/job/12345",
        "job_id": "test_12345",
        "applicants": "50 applicants",
        "description": "We are looking for...",
        "source": "linkedin",
        "status": "new"
    }
    
    save_job(test_job)
    
    # Print statistics
    print_stats()

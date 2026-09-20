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


def init_db():
    """Initialize database and create indexes"""
    db = get_db()
    collection = db[COLLECTION_NAME]
    
    # Create unique index to prevent duplicates
    collection.create_index("link", unique=True)
    collection.create_index("job_id")
    collection.create_index("source")
    collection.create_index("created_at")
    
    print(f"MongoDB initialized: {DATABASE_NAME}.{COLLECTION_NAME}")
    print(f"Indexes created: link (unique), job_id, source, created_at")


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

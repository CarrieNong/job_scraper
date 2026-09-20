#!/usr/bin/env python3
"""
AI-Powered Job Matching System
Uses AI to analyze job listings and match them with user profile and preferences
"""
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional

# Add src directory to path to allow imports when running from project root
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI
from dotenv import load_dotenv

from db_mongo import (
    init_db,
    get_collection,
    get_new_jobs,
    is_job_id_exists,
)

load_dotenv()

# AI Configuration
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")  # or "claude-3-5-sonnet-20241022"
AI_API_KEY = os.getenv("OPENAI_API_KEY")  # or ANTHROPIC_API_KEY
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "7.0"))  # Minimum match score (0-10)


def load_user_profile(profile_path: str = "docs/user_profile.md") -> str:
    """
    Load user's resume and profile information.
    
    Args:
        profile_path: Path to the user profile/resume file (supports .txt, .md)
        
    Returns:
        User profile content as string
    """
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Profile file not found at {profile_path}")
        return ""


def load_matching_criteria(criteria_path: str = "docs/matching_criteria.md") -> str:
    """
    Load user's custom matching criteria and preferences.
    
    Args:
        criteria_path: Path to the matching criteria file
        
    Returns:
        Matching criteria as string
    """
    try:
        with open(criteria_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Criteria file not found at {criteria_path}")
        return ""


def build_matching_prompt(job: Dict, user_profile: str, criteria: str) -> str:
    """
    Build the AI prompt for job matching analysis.
    
    Args:
        job: Job data dictionary
        user_profile: User's resume/profile
        criteria: Custom matching criteria
        
    Returns:
        Formatted prompt string
    """
    job_description = job.get("description", "")[:4000]  # Limit description length
    
    prompt = f"""You are a professional career advisor. Analyze if this job posting matches the candidate's profile and preferences.

## Job Information
**Title**: {job.get('title', 'N/A')}
**Company**: {job.get('company', 'N/A')}
**Location**: {job.get('location', 'N/A')}
**Source**: {job.get('source', 'N/A')}
**Link**: {job.get('link', 'N/A')}

**Job Description**:
{job_description}

## Candidate Profile
{user_profile}

## Matching Criteria
{criteria}

## Your Task
Analyze the job posting and provide:

1. **Match Score** (0-10): How well does this job match the candidate's profile and criteria?
   - 0-3: Poor match (not recommended)
   - 4-6: Moderate match (consider carefully)
   - 7-8: Good match (recommended)
   - 9-10: Excellent match (highly recommended)

2. **Match Reasons**: List 3-5 key reasons why this job matches or doesn't match

3. **Missing Requirements**: Any important requirements the candidate might not meet

4. **Red Flags**: Any concerning aspects of the job posting

5. **Recommendation**: Should the candidate apply? (Yes/No/Maybe)

Please respond in the following JSON format:
{{
    "match_score": 8.5,
    "recommendation": "Yes",
    "match_reasons": [
        "Strong alignment with frontend skills",
        "Company values match preferences",
        "Remote work option available"
    ],
    "missing_requirements": [
        "Prefers 5+ years experience but candidate has 3"
    ],
    "red_flags": [],
    "summary": "Brief 1-2 sentence summary of why this is a good/bad match"
}}
"""
    return prompt


def analyze_job_with_ai(job: Dict, user_profile: str, criteria: str) -> Optional[Dict]:
    """
    Use AI to analyze a job posting and determine match quality.
    
    Args:
        job: Job data dictionary
        user_profile: User's resume/profile
        criteria: Custom matching criteria
        
    Returns:
        AI analysis results as dictionary, or None if analysis fails
    """
    if not AI_API_KEY:
        print("Error: AI API key not configured in .env")
        return None
    
    prompt = build_matching_prompt(job, user_profile, criteria)
    
    try:
        # Using OpenAI API (compatible with OpenAI, Azure OpenAI, or OpenRouter)
        client = OpenAI(api_key=AI_API_KEY)
        
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional career advisor specializing in job matching. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}  # Ensures JSON response
        )
        
        result = response.choices[0].message.content
        
        # Parse JSON response
        import json
        analysis = json.loads(result)
        
        return analysis
        
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        return None


def save_matched_job(job: Dict, analysis: Dict) -> bool:
    """
    Save a matched job to the matched_jobs collection.
    
    Args:
        job: Original job data
        analysis: AI analysis results
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        matched_jobs = get_collection("matched_jobs")
        
        # Check if already exists
        if matched_jobs.find_one({"job_id": job["job_id"], "source": job["source"]}):
            print(f"Matched job {job['job_id']} already exists, skip")
            return False
        
        matched_job_data = {
            # Original job fields
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "link": job.get("link", ""),
            "job_id": job.get("job_id", ""),
            "source": job.get("source", ""),
            "description": job.get("description", ""),
            "applicants": job.get("applicants", ""),
            
            # AI matching analysis
            "match_score": analysis.get("match_score", 0),
            "recommendation": analysis.get("recommendation", ""),
            "match_reasons": analysis.get("match_reasons", []),
            "missing_requirements": analysis.get("missing_requirements", []),
            "red_flags": analysis.get("red_flags", []),
            "summary": analysis.get("summary", ""),
            
            # Metadata
            "status": "pending",  # pending, applied, rejected, interview
            "matched_at": datetime.utcnow(),
            "applied_at": None,
            "notes": "",
        }
        
        matched_jobs.insert_one(matched_job_data)
        print(f"✓ Saved matched job: {job.get('title')} (score: {analysis.get('match_score')})")
        return True
        
    except Exception as e:
        print(f"Error saving matched job: {e}")
        return False


def process_new_jobs(limit: Optional[int] = None, source: Optional[str] = None):
    """
    Process new job listings and find matches using AI.
    
    Args:
        limit: Maximum number of jobs to process (None for all)
        source: Filter by source (indeed, linkedin, or None for all)
    """
    print("=== Starting AI Job Matching ===")
    
    # Load user data
    user_profile = load_user_profile()
    if not user_profile:
        print("Error: No user profile found. Create docs/user_profile.md first.")
        return
    
    criteria = load_matching_criteria()
    if not criteria:
        print("Warning: No matching criteria found. Using profile only.")
    
    # Get new jobs from database
    new_jobs = get_new_jobs(limit=limit, source=source)
    total_jobs = len(new_jobs)
    print(f"Found {total_jobs} new jobs to analyze")
    
    if total_jobs == 0:
        print("No new jobs to process.")
        return
    
    matched_count = 0
    processed_count = 0
    
    for i, job in enumerate(new_jobs, 1):
        print(f"\n--- Processing job {i}/{total_jobs} ---")
        print(f"Title: {job.get('title')}")
        print(f"Company: {job.get('company')}")
        print(f"Source: {job.get('source')}")
        
        # Analyze with AI
        analysis = analyze_job_with_ai(job, user_profile, criteria)
        
        if not analysis:
            print("⚠ AI analysis failed, skip")
            continue
        
        processed_count += 1
        match_score = analysis.get("match_score", 0)
        print(f"Match score: {match_score}/10")
        print(f"Recommendation: {analysis.get('recommendation')}")
        
        # Save if meets threshold
        if match_score >= MATCH_THRESHOLD:
            if save_matched_job(job, analysis):
                matched_count += 1
        else:
            print(f"✗ Score below threshold ({MATCH_THRESHOLD}), not saved")
    
    print(f"\n=== Matching Complete ===")
    print(f"Processed: {processed_count}/{total_jobs}")
    print(f"Matched: {matched_count}")
    print(f"Threshold: {MATCH_THRESHOLD}/10")


def main():
    """Main entry point for AI job matching."""
    global MATCH_THRESHOLD
    
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-powered job matching system")
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        help="Limit number of jobs to process"
    )
    parser.add_argument(
        "--source",
        "-s",
        choices=["indeed", "linkedin"],
        default=None,
        help="Filter by job source"
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=MATCH_THRESHOLD,
        help="Minimum match score threshold (0-10)"
    )
    
    args = parser.parse_args()
    
    # Override threshold if specified
    MATCH_THRESHOLD = args.threshold
    
    init_db()
    process_new_jobs(limit=args.limit, source=args.source)


if __name__ == "__main__":
    main()

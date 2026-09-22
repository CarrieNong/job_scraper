#!/usr/bin/env python3
"""
AI-Powered Job Matching System
Uses AI to analyze job listings and match them with user profile and preferences
"""
import sys
import os
import re
import html as html_module
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
    mark_job_as_matched,
)

load_dotenv()

# AI Configuration
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")  # or "claude-3-5-sonnet-20241022"
AI_API_KEY = os.getenv("OPENAI_API_KEY")  # or ANTHROPIC_API_KEY
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "7.0"))  # Minimum match score (0-10)


def strip_html(html_text: str) -> str:
    """
    Convert raw HTML to plain text.
    - Removes all tags
    - Decodes HTML entities (&amp; → &, &lt; → <, etc.)
    - Collapses excessive whitespace / blank lines
    
    Args:
        html_text: Raw HTML string
        
    Returns:
        Clean plain-text string
    """
    if not html_text:
        return ""
    # Remove <style> and <script> blocks entirely
    text = re.sub(r'<(style|script)[^>]*>.*?</\1>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    # Replace block-level tags with newlines so paragraphs/list items stay readable
    text = re.sub(r'<(br|p|li|h[1-6]|div|tr)[^>]*>', '\n', text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = html_module.unescape(text)
    # Collapse multiple blank lines into one
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    text = '\n'.join(line for line in lines if line)
    return text.strip()


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
    # Strip HTML tags first so the character budget covers actual text, not markup
    raw_description = job.get("description", "")
    job_description = strip_html(raw_description)[:6000]
    
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

## Matching Criteria (FOLLOW STRICTLY)
{criteria}

## CRITICAL EVALUATION PROCESS - FOLLOW THIS ORDER:

### STEP 1: Hard Requirements Check (IMMEDIATE DISQUALIFICATION)
**Check these FIRST. If ANY fails, assign score ≤ 3 immediately:**

1. **German Language Check**:
   **CRITICAL DISTINCTION**: 
   - ❌ DO NOT disqualify just because the JD is written in German language
   - ✅ ONLY disqualify if German is explicitly listed as a JOB REQUIREMENT
   
   **DISQUALIFY (score ≤ 3) if ANY of the following appear anywhere in the job text**:
   
   *Explicit requirement keywords:*
   - "German required" / "Deutsch erforderlich" / "Deutsch ist erforderlich"
   - "Deutschkenntnisse erforderlich" / "German skills required"
   - "German mandatory" / "Deutsch zwingend erforderlich"
   - "Deutsch ist Voraussetzung" / "German is a must"
   - "Sehr gute Deutschkenntnisse erforderlich"
   
   *Language level declarations (these always mean German IS required):*
   - "Deutsch - Fließend" / "Deutsch - Verhandlungssicher" / "Deutsch - Konversationssicher"
   - "Deutsch - Grundkenntnisse" / "Deutsch - Muttersprache"
   - "Sprachanforderungen" / "Sprachanforderung" (language requirements section)
   - "Fluent German" / "Fließend Deutsch" / "Fließende Deutschkenntnisse"
   - "German C1" / "German C2" / "German B2" / "Deutsch (C1)" / "Deutsch (C2)" / "Deutsch (B2)"
   - "Native German" / "Muttersprache Deutsch" / "Deutsch auf Muttersprachniveau"
   
   *General proficiency requirements:*
   - "Gute Deutschkenntnisse" / "Gutes Deutsch" / "Sehr gute Deutschkenntnisse"
   - "Deutschkenntnisse" (when listed under requirements/Anforderungen/Qualifikationen)
   - "Deutsch in Wort und Schrift"
   
   **Decision**:
   - ❌ If ANY of the above is found → DISQUALIFY (score ≤ 3)
   - ✅ If JD is written in German but none of the above appear → PASS
   - ✅ If German is explicitly "nice to have" / "von Vorteil" → PASS

2. **Backend Language Check** (ONLY if backend is explicitly required):
   - Does JD explicitly require a specific backend language as mandatory?
   - Candidate has: Node.js only (1 year experience)
   - ❌ If requires Python/Java/Go/PHP/Ruby/C#/.NET as mandatory → DISQUALIFY (score ≤ 3)
   - ✅ If requires Node.js or no specific backend requirement → PASS

3. **DevOps/SRE Check**:
   - Is this primarily a DevOps/SRE role OR does it require DevOps as core responsibility?
   - ❌ If YES → DISQUALIFY (score ≤ 3)
   - ✅ If DevOps is "nice to have" or basic CI/CD → PASS

**If ANY hard requirement fails, stop here and provide clear disqualification reason.**

---

### STEP 2: Required Skills Match (Base Score: 4-8)
Evaluate ONLY skills marked as "required" or "mandatory" in JD:
- Frontend frameworks: React/Vue/Angular (candidate has 7 years)
- Experience level match
- Required technical stack alignment
- Role focus (frontend vs backend split)

**Scoring Guide**:
- 8: 90%+ required skills match
- 7: 70-89% required skills match
- 6: 50-69% required skills match
- 5: 40-49% required skills match
- 4: 30-39% required skills match

---

### STEP 3: Nice to Have Bonus (+0 to +2)
**CRITICAL**: "Nice to have", "Plus", "Bonus", "Preferred" skills:
- ✅ Add +0.5 to +2 points ONLY if candidate HAS these skills
- ➖ Add ZERO penalty if candidate does NOT have these skills
- NEVER reduce base score for missing nice-to-have skills

---

### STEP 4: Domain Fit Bonus (+0 to +1)
- +1: E-commerce, SaaS, food compliance (perfect match)
- +0.5: Related domains
- +0: Neutral

---

## Your Task - Provide JSON Response:

**Match Score Range**:
- 0-3: Disqualified (hard requirements not met)
- 4-6: Weak match (many required skills missing)
- 7-8: Good match (most required skills present)
- 9-10: Excellent match (all required + many nice-to-have)

Please respond in the following JSON format:
{{
    "match_score": <number 0-10>,
    "recommendation": "<Yes/No>",
    "disqualification_reason": "<Only include this field if score ≤ 3, provide specific reason>",
    "match_reasons": [
        "<List specific matching points>"
    ],
    "missing_requirements": [
        "<List missing REQUIRED skills only>"
    ],
    "red_flags": [
        "<List concerning points>"
    ],
    "nice_to_have_matches": [
        "<List nice-to-have skills candidate HAS>"
    ],
    "summary": "<Brief 1-2 sentence summary explaining the match score>"
}}

EXAMPLE for a disqualified job (score ≤ 3):
{{
    "match_score": 2.0,
    "recommendation": "No",
    "disqualification_reason": "Position explicitly requires Python as mandatory backend language, but candidate only has Node.js experience",
    "match_reasons": ["Frontend React experience matches requirement"],
    "missing_requirements": ["Python (mandatory)", "5+ years backend experience"],
    "red_flags": ["Backend-heavy role (70% backend work)", "Python explicitly required"],
    "nice_to_have_matches": [],
    "summary": "Strong frontend skills but fails hard requirement of mandatory Python backend experience."
}}

EXAMPLE for a good match (score 7-8):
{{
    "match_score": 8.0,
    "recommendation": "Yes",
    "match_reasons": [
        "Frontend skills align perfectly with React requirement",
        "Experience level matches (5-7 years required)",
        "E-commerce domain experience highly relevant"
    ],
    "missing_requirements": [],
    "red_flags": [],
    "nice_to_have_matches": [
        "TypeScript (listed as nice to have)",
        "Docker experience (listed as plus)"
    ],
    "summary": "Excellent match with strong frontend skills and relevant e-commerce experience."
}}

**Important Notes**:
- Include "disqualification_reason" ONLY if score ≤ 3
- List "nice_to_have_matches" to show which bonus skills candidate has
- Be STRICT on hard requirements (German, backend language, DevOps)
- Be FAIR on required vs nice-to-have distinction
- Focus scoring on REQUIRED skills only, add bonus for nice-to-have
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
                    "content": "You are a strict professional career advisor specializing in job matching. You must follow the matching criteria exactly. Be STRICT on hard requirements (German language, backend language, DevOps). CRITICAL GERMAN LANGUAGE RULE: A job written in German does NOT mean German is required. HOWEVER, you MUST disqualify if ANY of these German requirement signals appear anywhere in the job text: 'Sprachanforderungen', 'Deutsch - Fließend', 'Deutsch - Verhandlungssicher', 'Deutsch - Konversationssicher', 'Deutsch (C1)', 'Deutsch (C2)', 'Deutsch (B2)', 'Gutes Deutsch', 'Gute Deutschkenntnisse', 'Deutschkenntnisse', 'Deutsch erforderlich', 'Deutsch in Wort und Schrift', 'Fluent German', 'Fließend Deutsch'. Be FAIR on required vs nice-to-have skills. NEVER penalize missing nice-to-have skills. Provide SPECIFIC disqualification reasons based on the actual job requirements. Respond only with valid JSON."
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
            "disqualification_reason": analysis.get("disqualification_reason", ""),  # New field
            "match_reasons": analysis.get("match_reasons", []),
            "missing_requirements": analysis.get("missing_requirements", []),
            "red_flags": analysis.get("red_flags", []),
            "nice_to_have_matches": analysis.get("nice_to_have_matches", []),  # New field
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
            # 即使失败也标记，避免重复处理
            mark_job_as_matched(job.get("job_id"), job.get("source"), match_score=0)
            continue
        
        processed_count += 1
        match_score = analysis.get("match_score", 0)
        recommendation = analysis.get("recommendation", "")
        disqualification_reason = analysis.get("disqualification_reason", "")
        
        print(f"Match score: {match_score}/10")
        print(f"Recommendation: {recommendation}")
        
        # Show disqualification reason if present
        if disqualification_reason:
            print(f"⚠️  Disqualification: {disqualification_reason}")
        
        # Show nice-to-have matches if present
        nice_to_have = analysis.get("nice_to_have_matches", [])
        if nice_to_have and len(nice_to_have) > 0:
            print(f"✨ Nice-to-have matches: {', '.join(nice_to_have[:3])}")
        
        # Save if meets threshold
        if match_score >= MATCH_THRESHOLD:
            if save_matched_job(job, analysis):
                matched_count += 1
        else:
            print(f"✗ Score below threshold ({MATCH_THRESHOLD}), not saved")
        
        # 标记此job已经过AI匹配（重要：避免重复处理）
        mark_job_as_matched(job.get("job_id"), job.get("source"), match_score=match_score)
        print(f"✓ Marked as matched in jobs collection")
    
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

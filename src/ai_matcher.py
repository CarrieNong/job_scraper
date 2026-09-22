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
    mark_job_as_matched,
)
from scraper_utils import strip_html

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

### STEP 0: Parse the JD (Job Wizard style) — ALWAYS DO THIS FIRST
Read the full job description and split it into two lists of atomic items (one responsibility or requirement per bullet). Paraphrase clearly; do not invent items that are not in the JD.

1. **What you'll do** — day-to-day responsibilities, duties, tasks, ownership
2. **What they're looking for** — qualifications, skills, years of experience, languages, education, must-haves and nice-to-haves

Then compare EACH item against the candidate profile:
- **matched**: the candidate can reasonably do / already has this, based on the resume
- **unmatched**: the candidate cannot do this, or it is a gap

These two breakdowns MUST appear in the JSON. They are independent of scoring: still fill them even if the job is disqualified.

---

### STEP 1: Hard Requirements Check (IMMEDIATE DISQUALIFICATION)
**Check these FIRST. If ANY fails, assign score ≤ 3 immediately.** Still complete Step 0 breakdowns.

1. **German language** (explicit written requirement only — NEVER infer from location):
   - German-language JDs are already filtered out. Do not re-filter because the text looks German.
   - ❌ DISQUALIFY only if the JD **explicitly states** German as a mandatory job-language requirement (must-have / required / fluent / native / C1). English JDs can still say this in writing; only then fail.
   - ✅ PASS if German is nice-to-have / plus / advantage, not mentioned as a language skill, or you would only be guessing from location.
   - **NEVER infer German from**: "Berlin, Germany (On-site/Hybrid)", DACH, "Berlin office", "in-person culture in Berlin", a German/European company, German customers/brands, or office perks. Location ≠ language requirement.
   - Do **not** invent "Fluency in German" (or similar) in what_theyre_looking_for / unmatched if the JD never asked for German.

2. **Years of experience**:
   - Candidate: **7 years** frontend / software engineering; **1 year** full-stack / backend (Node.js).
   - ❌ DISQUALIFY if a **must-have** year requirement exceeds the candidate in that dimension (overall/frontend/software > 7, or backend-specific > 1). A range that includes the candidate's years (e.g. "1-2 years" backend) PASSES.
   - ✅ PASS if years are within range, unstated, or only a nice-to-have. "Senior" in the title alone is not a disqualification.

3. **Backend language** (ONLY if a backend language is a hard/mandatory requirement):
   - Candidate: Node.js ecosystem (Express, Nest, Fastify, Koa, etc.) + a little Python (NOT enough for a Python-primary backend role).
   - ❌ DISQUALIFY if the required backend is Python/Django/Flask/FastAPI, Java, Go, PHP, Ruby, C#, .NET, or any language the candidate does not know.
   - ✅ PASS if required backend is Node.js, or no backend language is mandatory, or backend is nice-to-have.

4. **DevOps/SRE**:
   - ❌ DISQUALIFY if this is primarily a DevOps/SRE role OR DevOps is a core responsibility.
   - ✅ PASS if DevOps is nice-to-have or only basic CI/CD / Docker / Git.

**If ANY hard requirement fails, score ≤ 3 and give a specific disqualification_reason.**

---

### STEP 2: Required Skills Match (Base Score: 4-8)
Evaluate ONLY skills marked as "required" or "mandatory" in JD:
- Frontend frameworks: React/Vue/Angular (candidate has 7 years); candidate also has strong vanilla JS / ES6+ throughout
- Experience level match
- Required technical stack alignment
- Role focus (frontend vs backend split)

**IMPORTANT — JavaScript / vanilla JS roles**:
- If the JD is primarily a frontend JavaScript role (vanilla JS, DOM, browser APIs) rather than requiring a specific proprietary framework, count the candidate's 7 years of JS development as a FULL match for the JS requirement.
- If the JD uses a niche/legacy framework (CanJS, Backbone, Ember, Knockout, etc.) but also lists React, Angular, or Vue as reference keywords or the core requirement is "strong JavaScript", do NOT heavily penalize. The framework gap is at most −0.5 to −1 point on the base score. The candidate's deep React/Vue/Angular + vanilla JS background demonstrates the same fundamental frontend engineering skills.
- Build tool equivalence: Candidate's Webpack/Vite = Grunt/Gulp for scoring purposes (both are frontend build tooling). Do NOT deduct for this difference.
- Test framework equivalence: Candidate's Jest/Cypress ≈ Mocha/Chai. Do NOT deduct.

**Scoring Guide**:
- 8: 90%+ required skills match
- 7: 70-89% required skills match (includes: strong JS match + minor framework difference)
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
    "what_youll_do": {{
        "matched": ["<responsibility the candidate can do>"],
        "unmatched": ["<responsibility the candidate cannot do>"]
    }},
    "what_theyre_looking_for": {{
        "matched": ["<requirement the candidate meets>"],
        "unmatched": ["<requirement the candidate does not meet>"]
    }},
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
    "disqualification_reason": "Must-have backend is Python/Django; candidate only has Node.js plus light Python, which is not enough",
    "what_youll_do": {{
        "matched": ["Build React user interfaces", "Collaborate with product and design"],
        "unmatched": ["Own Django REST APIs"]
    }},
    "what_theyre_looking_for": {{
        "matched": ["5+ years frontend experience", "React and TypeScript"],
        "unmatched": ["3+ years Python/Django as mandatory backend"]
    }},
    "match_reasons": ["Frontend React experience matches requirement"],
    "missing_requirements": ["Python (mandatory)", "3+ years backend experience"],
    "red_flags": ["Backend-heavy role", "Python explicitly required"],
    "nice_to_have_matches": [],
    "summary": "Strong frontend skills but fails hard requirement of mandatory Python backend experience."
}}

EXAMPLE for a good match (score 7-8):
{{
    "match_score": 8.0,
    "recommendation": "Yes",
    "what_youll_do": {{
        "matched": ["Develop React/TypeScript features", "Improve web performance", "Work with designers on UI"],
        "unmatched": []
    }},
    "what_theyre_looking_for": {{
        "matched": ["5+ years frontend", "React and TypeScript", "E-commerce experience"],
        "unmatched": ["GraphQL in production"]
    }},
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
- Always fill what_youll_do and what_theyre_looking_for with concrete JD items
- Include "disqualification_reason" ONLY if score ≤ 3
- List "nice_to_have_matches" to show which bonus skills candidate has
- Be STRICT on hard requirements (explicit mandatory German only — never infer from Berlin/Germany location, years of experience, backend language, DevOps)
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
                    "content": "You are a strict professional career advisor specializing in job matching. Always parse each JD into 'what you'll do' and 'what they're looking for', then compare every item to the resume. Follow the matching criteria exactly. Be STRICT on hard requirements: mandatory German ONLY if the JD explicitly writes German as a required job language (never infer from Berlin/Germany/on-site/office location; do not invent a German requirement; do not re-filter German-written JDs), years of experience (candidate has 7 years frontend and 1 year backend), backend language (Node.js ecosystem plus light Python only; Python-primary backend is a fail), and DevOps/SRE. Be FAIR on required vs nice-to-have skills. NEVER penalize missing nice-to-have skills. IMPORTANT for JavaScript/frontend roles: (1) If a JD primarily requires vanilla JS / strong JavaScript skills, treat the candidate's 7 years of JS development as a FULL match. (2) If a JD uses a niche/legacy framework (CanJS, Backbone, Ember, etc.) but lists React/Angular/Vue as reference keywords OR the core requirement is strong JavaScript, do NOT heavily penalize — the framework gap is at most −0.5 to −1 point; these are learnable given deep JS fundamentals. (3) Webpack/Vite = Grunt/Gulp for scoring (same build tooling responsibility). (4) Jest/Cypress ≈ Mocha/Chai for scoring. Respond only with valid JSON."
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


def _normalize_breakdown(section) -> Dict:
    """Coerce AI breakdown into {matched: [...], unmatched: [...]} lists."""
    if not isinstance(section, dict):
        return {"matched": [], "unmatched": []}
    matched = section.get("matched") or []
    unmatched = section.get("unmatched") or []
    return {
        "matched": [str(item).strip() for item in matched if str(item).strip()],
        "unmatched": [str(item).strip() for item in unmatched if str(item).strip()],
    }


def _analysis_fields(analysis: Dict) -> Dict:
    """Normalize AI analysis into the fields stored on job documents."""
    return {
        "recommendation": analysis.get("recommendation", ""),
        "disqualification_reason": analysis.get("disqualification_reason", ""),
        "match_reasons": analysis.get("match_reasons", []),
        "missing_requirements": analysis.get("missing_requirements", []),
        "red_flags": analysis.get("red_flags", []),
        "nice_to_have_matches": analysis.get("nice_to_have_matches", []),
        "summary": analysis.get("summary", ""),
        "what_youll_do": _normalize_breakdown(analysis.get("what_youll_do")),
        "what_theyre_looking_for": _normalize_breakdown(analysis.get("what_theyre_looking_for")),
    }


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
            **_analysis_fields(analysis),
            
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
            # Still mark so the same job is not retried forever
            mark_job_as_matched(
                job.get("job_id"),
                job.get("source"),
                match_score=0,
                analysis={
                    "recommendation": "No",
                    "disqualification_reason": "AI analysis failed",
                    "summary": "AI analysis failed; skipped to avoid reprocessing.",
                },
            )
            continue
        
        processed_count += 1
        match_score = analysis.get("match_score", 0)
        recommendation = analysis.get("recommendation", "")
        disqualification_reason = analysis.get("disqualification_reason", "")
        analysis_fields = _analysis_fields(analysis)
        
        print(f"Match score: {match_score}/10")
        print(f"Recommendation: {recommendation}")
        
        # Show disqualification reason if present
        if disqualification_reason:
            print(f"⚠️  Disqualification: {disqualification_reason}")
        
        # Show nice-to-have matches if present
        nice_to_have = analysis.get("nice_to_have_matches", [])
        if nice_to_have and len(nice_to_have) > 0:
            print(f"✨ Nice-to-have matches: {', '.join(nice_to_have[:3])}")

        looking = analysis_fields["what_theyre_looking_for"]
        doing = analysis_fields["what_youll_do"]
        print(
            f"What you'll do: {len(doing['matched'])} matched / {len(doing['unmatched'])} unmatched"
        )
        print(
            f"What they're looking for: {len(looking['matched'])} matched / {len(looking['unmatched'])} unmatched"
        )
        if looking["unmatched"]:
            preview = "; ".join(looking["unmatched"][:3])
            print(f"  gaps: {preview}")
        
        # High-score jobs also go to matched_jobs for the tracker
        if match_score >= MATCH_THRESHOLD:
            if save_matched_job(job, analysis):
                matched_count += 1
        else:
            print(f"✗ Score below threshold ({MATCH_THRESHOLD}), kept on jobs with AI reason")
        
        # Always write the full AI result onto the original jobs document
        mark_job_as_matched(
            job.get("job_id"),
            job.get("source"),
            match_score=match_score,
            analysis=analysis_fields,
        )
        print(f"✓ Saved AI analysis on jobs collection")
    
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

# AI Job Matching - Quick Start Guide

This guide will help you set up and use the AI-powered job matching feature.

## 🎯 Overview

The AI matcher analyzes job postings from your database and automatically identifies positions that match your profile and preferences. It scores each job from 0-10 and saves high-quality matches to a separate collection for easy review.

## 📋 Prerequisites

1. Python dependencies installed (including `openai`)
2. MongoDB set up with job listings
3. OpenAI API key (or other AI provider)

## 🛠 Setup (One-Time)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure AI API Key

Edit your `.env` file and add your OpenAI API key:

```bash
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx

# Choose your model
AI_MODEL=gpt-4o-mini

# Set minimum match score (jobs below this won't be saved)
MATCH_THRESHOLD=7.0
```

**Model Options:**
- `gpt-4o-mini` - Fast and cost-effective (recommended for testing)
- `gpt-4o` - More capable, higher cost
- `gpt-4-turbo` - Balance of speed and quality

### Step 3: Create Your Profile

Edit `user_profile.txt` with your information:

```text
# User Profile & Resume

## Personal Information
- Name: Your Name
- Current Role: Software Engineer
- Years of Experience: 3+ years
- Location: Berlin, Germany
- Languages: English (Fluent), German (B1)

## Technical Skills
- Frontend: React, Vue.js, TypeScript
- Backend: Node.js, Python
- Database: MongoDB, PostgreSQL
- Tools: Git, Docker, AWS

## Work Experience
[Add your work history here]

## Preferences
- Interested in: Frontend, Full-Stack
- Work Style: Remote or hybrid
- Company Size: Startups or scale-ups
```

### Step 4: Define Matching Criteria

Edit `matching_criteria.txt` with your requirements:

```text
# Job Matching Criteria

## Must-Have Requirements
1. Position involves React or modern frontend frameworks
2. Remote-friendly or Berlin-based
3. English-speaking environment
4. Visa sponsorship (if needed)

## Strong Preferences
1. Hybrid work (2+ days remote)
2. Small to medium team size
3. Modern tech stack
4. Learning opportunities

## Red Flags (Avoid)
- No remote work options
- Unpaid trial periods
- Unclear compensation
```

## 🚀 Usage

### Basic Usage

Run the AI matcher on all new jobs:

```bash
python3 ai_matcher.py
```

This will:
1. Load all jobs with status "new" from MongoDB
2. Analyze each job using AI
3. Save jobs scoring ≥7.0 to the `matched_jobs` collection

### Command-Line Options

```bash
# Limit number of jobs to process (good for testing)
python3 ai_matcher.py --limit 10

# Filter by source
python3 ai_matcher.py --source indeed
python3 ai_matcher.py --source linkedin

# Set custom threshold
python3 ai_matcher.py --threshold 8.0

# Combine options
python3 ai_matcher.py --source linkedin --limit 5 --threshold 7.5
```

### Examples

```bash
# Quick test: analyze only 3 jobs
python3 ai_matcher.py -l 3

# Only analyze Indeed jobs
python3 ai_matcher.py -s indeed

# Only save excellent matches (8+)
python3 ai_matcher.py -t 8.0

# Process LinkedIn jobs, save top matches
python3 ai_matcher.py -s linkedin -t 8.5 -l 20
```

## 📊 Understanding Results

### Match Scores

- **9-10**: Excellent match - Apply immediately
- **7-8**: Good match - Strongly consider
- **4-6**: Moderate match - Review carefully
- **0-3**: Poor match - Not saved

### Output Example

```
=== Starting AI Job Matching ===
Found 15 new jobs to analyze

--- Processing job 1/15 ---
Title: Senior Frontend Engineer
Company: Tech Startup GmbH
Source: linkedin
Match score: 8.5/10
Recommendation: Yes
✓ Saved matched job: Senior Frontend Engineer (score: 8.5)

--- Processing job 2/15 ---
Title: Backend Java Developer
Company: Enterprise Corp
Source: indeed
Match score: 4.0/10
Recommendation: No
✗ Score below threshold (7.0), not saved

...

=== Matching Complete ===
Processed: 15/15
Matched: 4
Threshold: 7.0/10
```

## 🗄 Database Collections

### Original Jobs Collection: `jobs`

All scraped jobs with status "new", "applied", etc.

### Matched Jobs Collection: `matched_jobs`

High-quality matches with additional AI analysis fields:

```javascript
{
  // Original job fields
  "title": "Senior Frontend Engineer",
  "company": "Tech Company",
  "location": "Berlin",
  "link": "https://...",
  "job_id": "123456",
  "source": "linkedin",
  "description": "...",
  
  // AI analysis fields
  "match_score": 8.5,
  "recommendation": "Yes",
  "match_reasons": [
    "Strong React expertise match",
    "Remote work option available",
    "Salary range meets expectations"
  ],
  "missing_requirements": [
    "Prefers 5+ years but candidate has 3"
  ],
  "red_flags": [],
  "summary": "Excellent match for frontend role with modern stack",
  
  // Metadata
  "status": "pending",  // pending, applied, rejected, interview
  "matched_at": ISODate("2026-09-20T19:30:00Z"),
  "applied_at": null,
  "notes": ""
}
```

## 📈 Workflow Integration

### Daily Automated Pipeline

The `run_task.sh` script now includes AI matching:

```bash
./run_task.sh
```

This will:
1. Scrape Indeed jobs
2. Scrape LinkedIn jobs
3. **Run AI matcher on new jobs**
4. Log results

### Manual Review

After matching, review results in MongoDB:

```python
from db_mongo import get_collection

# Get all matched jobs sorted by score
matched = get_collection("matched_jobs")
jobs = matched.find().sort("match_score", -1)

for job in jobs:
    print(f"{job['match_score']}/10 - {job['title']} at {job['company']}")
    print(f"  Reasons: {', '.join(job['match_reasons'])}")
    print(f"  Link: {job['link']}\n")
```

### Update Job Status

After applying to a job:

```python
from db_mongo import get_collection
from datetime import datetime

matched = get_collection("matched_jobs")
matched.update_one(
    {"job_id": "123456", "source": "linkedin"},
    {
        "$set": {
            "status": "applied",
            "applied_at": datetime.utcnow(),
            "notes": "Applied via LinkedIn, mentioned referral"
        }
    }
)
```

## 💰 Cost Estimation

### OpenAI Pricing (as of 2024)

**GPT-4o-mini** (recommended):
- ~$0.15 per 1M input tokens
- ~$0.60 per 1M output tokens
- Typical job analysis: $0.001-0.003 per job
- **100 jobs ≈ $0.10-0.30**

**GPT-4o**:
- ~$2.50 per 1M input tokens
- ~$10.00 per 1M output tokens
- Typical job analysis: $0.02-0.05 per job
- **100 jobs ≈ $2-5**

💡 **Tip**: Start with `gpt-4o-mini` for testing, then upgrade if needed.

## ⚙️ Customization

### Adjust Match Threshold

In `.env`:
```bash
# Only save excellent matches
MATCH_THRESHOLD=8.5

# Save more matches for review
MATCH_THRESHOLD=6.0
```

### Modify AI Prompt

Edit `ai_matcher.py` → `build_matching_prompt()` to customize:
- Scoring criteria
- Analysis format
- Specific requirements to check

### Use Different AI Provider

For Claude (Anthropic):

1. Install SDK:
   ```bash
   pip install anthropic
   ```

2. Update `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   AI_MODEL=claude-3-5-sonnet-20241022
   ```

3. Modify `ai_matcher.py` to use Anthropic client instead of OpenAI

## 🐛 Troubleshooting

### "Error: AI API key not configured"

- Check `.env` file exists
- Verify `OPENAI_API_KEY` is set
- Make sure there are no extra spaces or quotes

### "No new jobs to process"

- All jobs may have been processed already
- Run scrapers first: `python3 indeed_scraper.py`
- Check database: all jobs with status="new" will be processed

### "AI analysis failed"

- Check API key is valid
- Verify internet connection
- Check OpenAI API status
- Try with a smaller limit first: `python3 ai_matcher.py -l 1`

### High API costs

- Use `gpt-4o-mini` instead of `gpt-4o`
- Set higher threshold to analyze fewer jobs
- Use `--limit` to control batch size
- Reduce job description length in prompt

## 📝 Best Practices

1. **Test with small batches first**
   ```bash
   python3 ai_matcher.py --limit 3
   ```

2. **Review AI recommendations**
   - Don't blindly trust scores
   - Read the match_reasons and red_flags
   - Adjust criteria if results are off

3. **Refine your profile**
   - Update `user_profile.txt` with specific skills
   - Be clear about must-haves in `matching_criteria.txt`
   - Add examples of ideal job descriptions

4. **Monitor costs**
   - Check OpenAI usage dashboard
   - Start with `gpt-4o-mini`
   - Set budgets in OpenAI account settings

5. **Iterate on criteria**
   - If too many false positives, increase threshold
   - If missing good jobs, lower threshold or refine criteria
   - Adjust prompt for better results

## 🎓 Next Steps

1. ✅ Set up your profile and criteria
2. ✅ Test with a small batch
3. ✅ Review and refine
4. ✅ Integrate into daily automation
5. ✅ Build a job application tracking system

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [MongoDB Query Guide](https://docs.mongodb.com/manual/tutorial/query-documents/)
- [Scheduling Guide](SCHEDULING.md) - Set up daily automation

---

**Questions?** Check the main [README.md](README.md) or open an issue.

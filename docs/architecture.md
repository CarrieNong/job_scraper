# Job Scraper — Architecture & Flows

This document describes the current architecture, entry commands, and the full chain: scrape → filter → AI match.

All project docs and code comments are written in English.

---

## 1. System overview

```mermaid
flowchart TB
    subgraph Triggers["Entry points"]
        T1["Telegram<br/>/jobs · /quick_jobs · /matches"]
        T2["Shell<br/>run_task.sh · run_quick.sh"]
        T3["LaunchD schedule<br/>~18:00 / ~11:00"]
        T4["Web UI<br/>start_ui.sh"]
        T5["Manual CLI<br/>scrapers / matcher"]
    end

    subgraph Scrape["Scrape layer"]
        Chrome["Chrome CDP :9222"]
        Indeed["indeed_scraper.py<br/>last 24h"]
        LI["linkedin_scraper.py<br/>last 24h × keywords"]
        LIQ["linkedin_quick_scraper.py<br/>last 12h · fixed OR URL"]
        Manual["manual_apply_scraper.py<br/>already-applied URLs"]
    end

    subgraph Filters["Per-card filters (before/after click)"]
        F1["1. Title blacklist<br/>TITLE_EXCLUDE_KEYWORDS"]
        F2["2. Title keywords<br/>DEFAULT_KEYWORDS"]
        F3["3. AI title relevance<br/>only if no keyword hit"]
        F4["4. Dedup<br/>job_id already in DB?"]
        F5["5. JD language · Lingua<br/>non-English → do not save"]
    end

    subgraph Store["MongoDB"]
        Jobs[("jobs")]
        Matched[("matched_jobs")]
        Stats[("scraper_stats")]
    end

    subgraph Match["Match layer · ai_matcher.py"]
        M0["Empty description → skip AI"]
        M1["German gate (rules)<br/>mandatory German in English JD"]
        M2["Full AI match<br/>matching_criteria.md"]
        M3["Score ≥ threshold<br/>→ matched_jobs"]
    end

    T1 --> T2
    T3 --> T2
    T2 --> Chrome
    T5 --> Chrome
    Chrome --> Indeed & LI & LIQ & Manual

    Indeed & LI & LIQ --> F1 --> F2 --> F3 --> F4 --> F5
    F5 -->|English JD saved| Jobs
    F5 -->|non-English| Stats

    Jobs --> M0 --> M1 --> M2
    M2 -->|≥ 7.0| Matched
    M2 -->|write analysis back| Jobs

    T4 --> Matched & Jobs
    T1 -->|/matches| Matched
```

---

## 2. Commands / entry points

### 2.1 Daily pipelines

| Command | When | What it does | Typical time |
|---------|------|--------------|--------------|
| `./run_task.sh` | ~18:00 (or Telegram `/jobs`) | Indeed + LinkedIn in parallel (24h) → AI match → cleanup old unmatched descriptions | 40–60 min |
| `./run_quick.sh` | ~11:00 (or Telegram `/quick_jobs`) | LinkedIn Quick only (12h) → AI match | 10–20 min |
| `./start_ui.sh` | Anytime | Start Job Tracker Web UI (default `:5050`) | — |

Prefer `caffeinate -i` for manual runs so sleep does not interrupt Playwright:

```bash
caffeinate -i ./run_task.sh
caffeinate -i ./run_quick.sh
```

### 2.2 Telegram bot commands

| Command | Purpose |
|---------|---------|
| `/start` | Confirm bot is online |
| `/test` | Confirm the Mac is connected and ready |
| `/jobs` | Run `run_task.sh` in the background; push today’s match cards when done |
| `/quick_jobs` | Run `run_quick.sh` in the background |
| `/matches` | Push today’s `matched_jobs` without scraping |

Start the bot: `python3 src/bot/telegram_bot.py`

### 2.3 Standalone CLI (debug / partial runs)

| Command | Purpose |
|---------|---------|
| `python3 src/scrapers/indeed_scraper.py [-k …] [-p N]` | Indeed only |
| `python3 src/scrapers/linkedin_scraper.py [-k …] [-p N]` | Full LinkedIn (keyword loop) |
| `python3 src/scrapers/linkedin_quick_scraper.py [-p N] [-j N]` | LinkedIn 12h Quick |
| `python3 src/matching/ai_matcher.py [-l N] [-s source] [-t 7.0]` | AI match only (jobs without `matched_at`) |
| `python3 src/scrapers/manual_apply_scraper.py <urls…>` | Already-applied jobs → scrape + score → `matched_jobs` with `status=applied` |
| `python3 scripts/cleanup_unmatched_descriptions.py …` | Clear old unmatched JD text (also run at end of full pipeline) |
| `python3 scripts/cleanup_excluded_titles.py …` | Cleanup DB rows by title blacklist |
| `python3 scripts/eval_matcher.py …` | Matcher evaluation |

---

## 3. Full vs Quick pipelines

### 3.1 Full — `run_task.sh` / `/jobs`

```mermaid
sequenceDiagram
    participant S as run_task.sh
    participant C as Chrome :9222
    participant I as Indeed scraper
    participant L as LinkedIn scraper
    participant DB as MongoDB
    participant AI as ai_matcher
    participant CL as cleanup script

    S->>C: Start or reuse debug Chrome
    par Parallel scrape
        S->>I: indeed_scraper.py -p 3
        I->>DB: save_job after filters
    and
        S->>L: linkedin_scraper.py -p 3
        L->>DB: save_job after filters
    end
    S->>AI: ai_matcher.py --threshold 7.0
    AI->>DB: mark_job_as_matched / save matched_jobs
    S->>CL: cleanup_unmatched_descriptions --days 14
    S->>S: Desktop notification + close Chrome (only if this run started it)
```

Order:

1. Chrome remote debugging (reuse if `:9222` already open)
2. **Indeed + LinkedIn in parallel** (up to 3 pages × keywords)
3. After both finish → **AI matcher**
4. Clear descriptions on unmatched jobs older than 14 days
5. Notify + optionally close Chrome

### 3.2 Quick — `run_quick.sh` / `/quick_jobs`

```mermaid
sequenceDiagram
    participant S as run_quick.sh
    participant C as Chrome :9222
    participant Q as LinkedIn Quick
    participant DB as MongoDB
    participant AI as ai_matcher

    S->>C: Start debug Chrome
    S->>Q: linkedin_quick_scraper.py -p 3
    Note over Q: Fixed 12h OR search URL<br/>reuses scrape_jobs() filters
    Q->>DB: save_job after filters
    S->>AI: ai_matcher.py --threshold 7.0
    AI->>DB: mark / matched_jobs
    S->>S: Notify + close Chrome
```

Differences from Full:

- **LinkedIn only** (no Indeed)
- No keyword loop — one pre-built OR search URL (Full Stack / Frontend / Product / GenAI, `f_TPR=r43200` = 12h)
- **No** description cleanup step
- Card processing reuses `linkedin_scraper.scrape_jobs()` (same title + language filters)

---

## 4. Per-job funnel: list card → database

For every list card during scrape:

```mermaid
flowchart TD
    Card["List card: read title"]

    Card --> Excl{"1. Title hits<br/>TITLE_EXCLUDE_KEYWORDS?<br/>e.g. Java / DevOps / Lead / QA…"}
    Excl -->|yes| Skip1["Skip — do not open detail"]
    Excl -->|no| KW{"2. Title contains<br/>DEFAULT_KEYWORDS?<br/>frontend / fullstack / …"}

    KW -->|yes| Dedup
    KW -->|no| AITitle{"3. AI title check<br/>related to target roles?"}
    AITitle -->|unrelated| Skip2["Skip<br/>count ai_title_filtered"]
    AITitle -->|related / API fail-open| Dedup

    Dedup{"4. job_id already in DB?"}
    Dedup -->|yes| Skip3["Skip click"]
    Dedup -->|no| Click["Open detail<br/>count title_passed_clicked"]

    Click --> Fetch["Fetch description (up to 3 retries)"]
    Fetch --> Empty{"Usable description?<br/>≥ MIN_JOB_DESCRIPTION_CHARS"}
    Empty -->|no| SaveEmpty["Still save<br/>description_empty=true<br/>matcher will skip AI"]
    Empty -->|yes| Lang{"5. Lingua language check<br/>is_non_english_job_detail"}

    Lang -->|non-English de/fr/…| SkipDE["Do not save<br/>count german_filtered"]
    Lang -->|English or undetectable| Save["save_job → jobs"]
```

### What each stage does

| Step | Implementation | Purpose |
|------|----------------|---------|
| 1. Title blacklist | `is_title_excluded()` · `TITLE_EXCLUDE_KEYWORDS` | Skip clearly wrong roles before clicking |
| 2. Keyword hit | `title_matches_default_keywords()` · `DEFAULT_KEYWORDS` | Title already on-target → click without AI |
| 3. AI title screen | `is_title_relevant_by_ai()` | After blacklist + no keyword: cheap AI “is this a target role?” |
| 4. Dedup | `is_job_id_exists()` | Do not re-open known jobs |
| 5. JD language | `is_non_english_job_detail()` · Lingua | **JD body not English** (usually German posts) → **do not save**. UI: German Filtered |

> Step 5 answers “what language is the JD written in?”, not “does an English JD require German skills?”. The latter is the match-stage German gate.

Unified title-gate entry point:

`should_skip_title_before_click()` → `src/core/scraper_utils.py`

---

## 5. After save: pre-AI and AI matching

`ai_matcher.py` only processes `jobs` documents that still lack `matched_at`:

```mermaid
flowchart TD
    New["get_new_jobs()<br/>no matched_at yet"]

    New --> Empty{"Usable description?"}
    Empty -->|no| FailEmpty["mark_job_as_matched<br/>score=0 · Missing description<br/>no AI call"]

    Empty -->|yes| Gate{"German gate (rules)<br/>find_mandatory_german_requirement()<br/>English JD requires mandatory German?"}

    Gate -->|mandatory German| FailDE["Local reject<br/>score≈1 · no full AI match<br/>write analysis"]
    Gate -->|pass| AI["analyze_job_with_ai()<br/>user_profile.md<br/>+ matching_criteria.md"]

    AI --> Score{"match_score ≥ MATCH_THRESHOLD<br/>default 7.0?"}
    Score -->|yes| MJ["Write matched_jobs<br/>status=pending"]
    Score -->|no| OnlyJobs["Write AI analysis on jobs only"]
    MJ --> Mark["mark_job_as_matched"]
    OnlyJobs --> Mark
```

### Do not confuse the two German-related gates

| | Scrape · language detection | Match · German gate |
|--|-----------------------------|---------------------|
| **Module** | `scraper_utils.is_non_english_job_detail` | `matching/german_gate.py` |
| **Question** | What language is the JD **written in**? (Lingua) | Does an **English** JD require German as a must-have skill? |
| **Typical hit** | Entire German posting | “German fluent required”, “C1 Deutsch”, “must speak German” |
| **Does not hit** | — | “Berlin, Germany” alone, German company, German as nice-to-have |
| **Outcome** | **Not saved**; count `german_filtered` | **Saved then rejected**; low score; **no full AI scoring** |
| **Order** | Earlier (on detail fetch) | Later (matcher entry) |

The AI prompt / `matching_criteria.md` also describes a German gate as a fallback. In code, the rule-based `german_gate` runs first and skips the model when it hits.

### AI scoring order (criteria)

1. Hard gates: mandatory German → sole unknown backend → years too high → DevOps/SRE-core
2. Ordinary score 4–8 (required skills + nice-to-have / domain bonuses)
3. Special Match A/B/C → 9–10 (Leipzig can add +0.5–1)
4. `match_score ≥ threshold` → `matched_jobs`

Details: [`matching_criteria.md`](./matching_criteria.md).

---

## 6. Data stores

| Collection | Written by | Contents |
|------------|------------|----------|
| `jobs` | scrapers; matcher writes analysis back | Jobs that passed the language gate (including empty-description placeholders) |
| `matched_jobs` | matcher (≥ threshold); manual_apply | High-score matches / already applied. UI can store manual `highlights` tags (separate from AI `special_match`). |
| `scraper_stats` | scrapers | Counters: `title_passed_clicked`, `german_filtered`, `ai_title_filtered`, … |

Web UI (`web_app.py`) reads these for today’s funnel, match list, and unmatched reasons.

AI `special_match` / `special_match_reasons` are still written by the matcher for scoring (9–10 band) but are **not** shown as badges on the Tracker. Highlight badges on the matched-jobs page come only from the user-editable `highlights` list (`PATCH /api/jobs/<id>/highlights`).

---

## 7. Directory map

```
job_scraper/
├── run_task.sh / run_quick.sh / start_ui.sh   # main entry scripts
├── docs/
│   ├── architecture.md          # this file
│   ├── matching_criteria.md     # AI scoring source of truth
│   └── user_profile.md          # resume / profile
├── src/
│   ├── core/
│   │   ├── config.py            # keywords, title blacklist, platform URLs
│   │   ├── db_mongo.py          # Mongo helpers
│   │   └── scraper_utils.py     # title gates, Lingua, CDP helpers
│   ├── scrapers/                # Indeed / LinkedIn / Quick / Manual
│   ├── matching/
│   │   ├── ai_matcher.py        # match orchestration
│   │   └── german_gate.py       # mandatory-German rule gate on English JDs
│   ├── web/web_app.py           # Tracker UI
│   └── bot/telegram_bot.py      # Telegram commands
└── scripts/                     # cleanup / eval helpers
```

---

## 8. One-line funnel

> **Title gates (blacklist → keywords → AI title) → open detail → discard non-English JD → save English JD → matcher skips empty desc → mandatory-German rule gate → AI scores by criteria → ≥ 7 enters Tracker.**

The two daily commands only change *where/how long* to scrape: evening Full 24h (Indeed + LinkedIn), morning Quick 12h (LinkedIn only). **Filter and match rules are the same.**

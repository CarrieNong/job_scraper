import asyncio
import html
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import os

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Repo root: src/bot/telegram_bot.py -> ../../
PROJECT_DIR = Path(__file__).resolve().parents[2]
SRC_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_DIR / ".env")

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.db_mongo import get_collection  # noqa: E402

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_ALLOWED_USER_ID"))

# Prevent overlapping pipeline runs (full and quick share Chrome / scrapers)
_pipeline_running = False

# Telegram message hard limit; leave headroom for HTML entities
_TELEGRAM_MSG_LIMIT = 4000

STATUS_LABELS = {
    "pending": "Not Applied",
    "applied": "Applied",
    "rejected": "Rejected",
    "interview": "Interview",
    "unsuitable": "Unsuitable",
    "closed": "Closed",
}


def is_allowed(update: Update) -> bool:
    return (
        update.effective_user is not None
        and update.effective_user.id == ALLOWED_USER_ID
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    await update.message.reply_text(
        "👋 Job Assistant is online."
    )


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    await update.message.reply_text(
        "✅ Mac is connected and ready."
    )


def _normalize_job_link(job: dict) -> str:
    """
    Return an absolute job URL.

    Some LinkedIn scrapes store relative hrefs like /jobs/view/123/ —
    Telegram (and browsers) need a full https:// URL.
    """
    link = (job.get("link") or "").strip()
    source = (job.get("source") or "").lower()
    job_id = str(job.get("job_id") or "").strip()

    if source == "linkedin":
        if job_id:
            return f"https://www.linkedin.com/jobs/view/{job_id}/"
        if link and not link.startswith("http"):
            return "https://www.linkedin.com" + link

    if link and not link.startswith("http") and source == "indeed":
        return "https://www.indeed.com" + link

    return link


def _fetch_todays_matched_jobs() -> list[dict]:
    """Return today's matched_jobs, highest score first (sync Mongo call)."""
    matched_jobs = get_collection("matched_jobs")
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return list(
        matched_jobs.find(
            {"matched_at": {"$gte": today_start}},
            {
                "title": 1,
                "location": 1,
                "match_score": 1,
                "source": 1,
                "link": 1,
                "job_id": 1,
                "company": 1,
                "status": 1,
            },
        ).sort("match_score", -1)
    )


def _format_job_block(index: int, job: dict) -> str:
    """One job block inside the combined daily card."""
    title = html.escape(str(job.get("title") or "Untitled"))
    location = html.escape(str(job.get("location") or "N/A"))
    source = html.escape(str(job.get("source") or "unknown").title())
    status_key = str(job.get("status") or "pending")
    status = html.escape(STATUS_LABELS.get(status_key, status_key))

    score = job.get("match_score", 0)
    try:
        score_text = f"{float(score):.1f}"
    except (TypeError, ValueError):
        score_text = str(score)

    lines = [
        f"<b>{index}. {title}</b>",
        f"📍 {location}",
        f"⭐ {score_text}/10 · {source}",
        f"🏷 {status}",
    ]

    link = _normalize_job_link(job)
    if link.startswith("http"):
        lines.append(f'🔗 <a href="{html.escape(link, quote=True)}">Open job</a>')

    return "\n".join(lines)


def _build_match_messages(jobs: list[dict]) -> list[str]:
    """Pack all jobs into as few Telegram messages as possible (usually one)."""
    header = f"📋 Today's matches: <b>{len(jobs)}</b>\n"
    blocks = [_format_job_block(i, job) for i, job in enumerate(jobs, start=1)]

    messages: list[str] = []
    current = header

    for block in blocks:
        candidate = current + "\n\n" + block if current != header else header + "\n" + block
        if len(candidate) <= _TELEGRAM_MSG_LIMIT:
            current = candidate
            continue

        if current != header:
            messages.append(current)
        # Rare: a single block alone exceeds the limit — still send it truncated
        if len(header + "\n" + block) > _TELEGRAM_MSG_LIMIT:
            messages.append((header + "\n" + block)[:_TELEGRAM_MSG_LIMIT])
            current = header
        else:
            current = header + "\n" + block

    if current != header:
        messages.append(current)

    return messages


async def _push_todays_matched_jobs(bot, chat_id: int) -> None:
    """Send today's matched jobs as one combined card (split only if too long)."""
    try:
        jobs = await asyncio.to_thread(_fetch_todays_matched_jobs)
    except Exception as exc:
        await bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Failed to load matches: {exc}",
        )
        return

    if not jobs:
        await bot.send_message(
            chat_id=chat_id,
            text="📭 No matched jobs for today.",
        )
        return

    for message in _build_match_messages(jobs):
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        await asyncio.sleep(0.2)


async def _run_pipeline(
    bot,
    chat_id: int,
    script: str,
    done_text: str,
    *,
    push_matches: bool = False,
) -> None:
    """Run a scrape pipeline in the background; notify when done."""
    global _pipeline_running
    try:
        process = await asyncio.create_subprocess_exec(
            "caffeinate",
            "-i",
            script,
            cwd=str(PROJECT_DIR),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        returncode = await process.wait()

        if returncode == 0:
            await bot.send_message(chat_id=chat_id, text=done_text)
            if push_matches:
                await _push_todays_matched_jobs(bot, chat_id)
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Pipeline exited with code {returncode}. Check logs/.",
            )
    except Exception as exc:
        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ Pipeline failed to start: {exc}",
        )
    finally:
        _pipeline_running = False


async def _start_pipeline(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    script: str,
    started_text: str,
    done_text: str,
    push_matches: bool = False,
) -> None:
    global _pipeline_running

    if not is_allowed(update):
        return

    if _pipeline_running:
        await update.message.reply_text(
            "⏳ Pipeline is already running. I'll notify you when it finishes."
        )
        return

    _pipeline_running = True
    chat_id = update.effective_chat.id

    await update.message.reply_text(started_text)

    # Schedule on the PTB event loop so the handler returns immediately
    # and polling stays responsive while Playwright / scrapers run.
    context.application.create_task(
        _run_pipeline(
            context.bot,
            chat_id,
            script,
            done_text,
            push_matches=push_matches,
        )
    )


async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /jobs — full scrape + AI match (Indeed + LinkedIn, ~24h window).

    Flow:
      /jobs → "Started" → caffeinate -i ./run_task.sh → "Done" → today's match cards
    """
    await _start_pipeline(
        update,
        context,
        script="./run_task.sh",
        started_text=(
            "🚀 Started — Indeed / LinkedIn / AI match running in the background "
            "(~40–60 min)."
        ),
        done_text="✅ Done — full pipeline finished.",
        push_matches=True,
    )


async def quick_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /quick_jobs — morning quick scrape + AI match (LinkedIn, ~12h window).

    Flow:
      /quick_jobs → "Started" → background: caffeinate -i ./run_quick.sh → "Done"
    """
    await _start_pipeline(
        update,
        context,
        script="./run_quick.sh",
        started_text=(
            "⚡ Started — LinkedIn quick scrape / AI match running in the background "
            "(~10–20 min)."
        ),
        done_text="✅ Done — quick pipeline finished.",
    )


async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/matches — push today's matched job cards without running a scrape."""
    if not is_allowed(update):
        return

    await update.message.reply_text("📥 Fetching today's matches...")
    await _push_todays_matched_jobs(context.bot, update.effective_chat.id)


async def _post_init(app: Application) -> None:
    """Register slash commands so they appear in Telegram's menu."""
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Check bot is online"),
            BotCommand("test", "Check Mac is ready"),
            BotCommand("jobs", "Full scrape + AI match (~40–60 min)"),
            BotCommand("quick_jobs", "Quick LinkedIn scrape + AI match (~10–20 min)"),
            BotCommand("matches", "Push today's matched job cards"),
        ]
    )


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("jobs", jobs))
    app.add_handler(CommandHandler("quick_jobs", quick_jobs))
    app.add_handler(CommandHandler("matches", matches))

    print(f"Telegram bot is running... (cwd={PROJECT_DIR})")
    print("Commands: /start /test /jobs /quick_jobs /matches")

    app.run_polling()


if __name__ == "__main__":
    main()

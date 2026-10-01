import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
import os

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# Repo root: src/bot/telegram_bot.py -> ../../
PROJECT_DIR = Path(__file__).resolve().parents[2]
SRC_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_DIR / ".env")

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.challenge_wait import signal_indeed_resume  # noqa: E402
from core.match_digest import (  # noqa: E402
    build_match_messages,
    fetch_todays_matched_jobs,
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_ALLOWED_USER_ID"))

# Prevent overlapping pipeline runs (full and quick share Chrome / scrapers)
_pipeline_running = False


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


async def _push_todays_matched_jobs(bot, chat_id: int) -> None:
    """Send today's matched jobs as one combined card (split only if too long)."""
    try:
        jobs = await asyncio.to_thread(fetch_todays_matched_jobs)
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

    for message in build_match_messages(jobs):
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
) -> None:
    """
    Run a scrape pipeline in the background; notify when done.

    Match cards are pushed by the shell script itself (run_task.sh /
    run_quick.sh) so cron / launchd / Telegram all get the same digest.
    The bot only sends Started / Done status here.
    """
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
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Pipeline exited with code {returncode}. Check logs/.",
            )
    except Exception as exc:
        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ Pipeline error: {exc}",
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
        )
    )


async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /jobs — full scrape + AI match (Indeed + LinkedIn, ~24h window).

    Flow:
      /jobs → "Started" → caffeinate -i ./run_task.sh
            → (script pushes today's match cards) → "Done"
    """
    await _start_pipeline(
        update,
        context,
        script="./run_task.sh",
        started_text=(
            "🚀 Started — Indeed / LinkedIn / AI match running in the background "
            "(~40–60 min). Match cards will arrive when matching finishes."
        ),
        done_text="✅ Done — full pipeline finished.",
    )


async def quick_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /quick_jobs — morning light scrape + AI match.

    Indeed reuses the 24h search with fewer pages per keyword.
    LinkedIn uses the 12h quick URL (no keyword loop).

    Flow:
      /quick_jobs → "Started" → caffeinate -i ./run_quick.sh
                  → (script pushes today's match cards) → "Done"
    """
    await _start_pipeline(
        update,
        context,
        script="./run_quick.sh",
        started_text=(
            "⚡ Started — light scrape (Indeed + LinkedIn quick) / AI match "
            "running in the background (~20–40 min). Match cards will arrive "
            "when matching finishes."
        ),
        done_text="✅ Done — light pipeline finished.",
    )


async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/matches — push today's matched job cards without running a scrape."""
    if not is_allowed(update):
        return

    await update.message.reply_text("📥 Fetching today's matches...")
    await _push_todays_matched_jobs(context.bot, update.effective_chat.id)


async def indeed_ok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /indeed_ok — tell a paused Indeed scraper that human verification is done.

    The scraper polls logs/indeed_human_resume.flag; this command writes it.
    """
    if not is_allowed(update):
        return

    path = signal_indeed_resume()
    await update.message.reply_text(
        "✅ Resume signal sent. The Indeed scraper will continue shortly.\n"
        f"({path.name})"
    )


async def indeed_resume_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Inline button: Continue after Indeed human verification."""
    query = update.callback_query
    if query is None:
        return

    if not is_allowed(update):
        await query.answer("Not authorized.", show_alert=True)
        return

    if query.data != "indeed_resume":
        await query.answer()
        return

    path = signal_indeed_resume()
    await query.answer("Resume signal sent")
    try:
        await query.edit_message_text(
            "✅ Resume signal sent. The Indeed scraper will continue shortly.\n"
            f"({path.name})"
        )
    except Exception:
        # Message may already be edited or too old — still confirm in chat
        if update.effective_chat is not None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="✅ Resume signal sent. The Indeed scraper will continue shortly.",
            )


async def _post_init(app: Application) -> None:
    """Register slash commands so they appear in Telegram's menu."""
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Check bot is online"),
            BotCommand("test", "Check Mac is ready"),
            BotCommand("jobs", "Full scrape + AI match (~40–60 min)"),
            BotCommand("quick_jobs", "Light scrape + AI match (~20–40 min)"),
            BotCommand("matches", "Push today's matched job cards"),
            BotCommand("indeed_ok", "Resume Indeed after human verification"),
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
    app.add_handler(CommandHandler("indeed_ok", indeed_ok))
    app.add_handler(CallbackQueryHandler(indeed_resume_callback, pattern=r"^indeed_resume$"))

    print(f"Telegram bot is running... (cwd={PROJECT_DIR})")
    print("Commands: /start /test /jobs /quick_jobs /matches /indeed_ok")

    app.run_polling()


if __name__ == "__main__":
    main()

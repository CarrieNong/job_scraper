import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Repo root: src/bot/telegram_bot.py -> ../../
PROJECT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_DIR / ".env")

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


async def _run_pipeline(
    bot,
    chat_id: int,
    script: str,
    done_text: str,
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
        _run_pipeline(context.bot, chat_id, script, done_text)
    )


async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /jobs — full scrape + AI match (Indeed + LinkedIn, ~24h window).

    Flow:
      /jobs → "Started" → background: caffeinate -i ./run_task.sh → "Done"
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


async def _post_init(app: Application) -> None:
    """Register slash commands so they appear in Telegram's menu."""
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Check bot is online"),
            BotCommand("test", "Check Mac is ready"),
            BotCommand("jobs", "Full scrape + AI match (~40–60 min)"),
            BotCommand("quick_jobs", "Quick LinkedIn scrape + AI match (~10–20 min)"),
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

    print(f"Telegram bot is running... (cwd={PROJECT_DIR})")
    print("Commands: /start /test /jobs /quick_jobs")

    app.run_polling()


if __name__ == "__main__":
    main()

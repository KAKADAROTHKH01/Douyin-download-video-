import os
import logging
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from downloader import download_douyin


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 សួស្តី!\n\n"
        "📥 ផ្ញើ Douyin URL មកខ្ញុំ\n"
        "ខ្ញុំនឹងព្យាយាមទាញវីដេអូឱ្យអ្នក។\n\n"
        "ឧទាហរណ៍:\n"
        "https://www.douyin.com/video/XXXXXXXX"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 របៀបប្រើ\n\n"
        "1️⃣ Copy Douyin video URL\n"
        "2️⃣ ផ្ញើ URL មក Bot\n"
        "3️⃣ រង់ចាំ Bot ទាញវីដេអូ\n"
        "4️⃣ Bot ផ្ញើវីដេអូមកវិញ"
    )


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    if "douyin.com" not in url:
        await update.message.reply_text(
            "❌ សូមផ្ញើ Douyin URL ប៉ុណ្ណោះ។"
        )
        return

    status = await update.message.reply_text(
        "⏳ កំពុងទាញវីដេអូ...\n"
        "សូមរង់ចាំបន្តិច។"
    )

    try:
        result = await asyncio.to_thread(download_douyin, url)

        if not result:
            await status.edit_text(
                "❌ មិនអាចទាញវីដេអូបានទេ។\n\n"
                "Douyin អាចត្រូវការ verification ឬ "
                "link នេះមិនអាចចូលប្រើបាន។"
            )
            return

        file_path, title = result

        await status.edit_text("📤 កំពុងផ្ញើវីដេអូ...")

        with open(file_path, "rb") as video:
            await update.message.reply_video(
                video=video,
                caption=f"🎬 {title[:900]}",
                supports_streaming=True,
            )

        try:
            os.remove(file_path)
        except OSError:
            pass

        try:
            await status.delete()
        except Exception:
            pass

    except Exception as e:
        logger.exception("Download error")

        await status.edit_text(
            "❌ Download failed.\n\n"
            f"Error: {str(e)[:500]}"
        )


def main():
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_url,
        )
    )

    logger.info("Bot started")

    application.run_polling()


if __name__ == "__main__":
    main()

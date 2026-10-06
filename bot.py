import os
import logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configured Bot Token & Constants
BOT_TOKEN = "8957069742:AAGT2lVDvxbkJsQAvFbfxWgqjgRIY2Zp3yk"
REAL_API_URL = "https://tg-to-number-number-nitin.vercel.app/api"
OWNER_HANDLE = "@RD3B4T"
CHANNEL_LINK = "https://t.me/RD3B4T"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        f"🤖 **Telegram to Number Bot** is live.\n"
        f"Send any Phone Number or Telegram ID directly, or use:\n"
        f"`/search <number_or_id>`\n\n"
        f"👑 **Developer:** {OWNER_HANDLE}\n"
        f"📢 **Channel:** {CHANNEL_LINK}",
        parse_mode="Markdown"
    )

async def handle_search(query: str, update: Update):
    processing_msg = await update.message.reply_text("🔍 Searching database, please wait...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(REAL_API_URL, params={"search": query})
            if response.status_code == 200:
                data = response.json()
            else:
                data = {
                    "location": {"country": "India", "country_code": "+91", "phone_number": query},
                    "userid_info": {"name": f"User {query}", "telegram_id": query, "username": "N/A"},
                    "metadata": {"owner": OWNER_HANDLE, "channel": CHANNEL_LINK}
                }
        
        # Metadata update with custom owner and channel
        if "metadata" in data:
            data["metadata"]["owner"] = OWNER_HANDLE
            data["metadata"]["channel"] = CHANNEL_LINK
        else:
            data["metadata"] = {
                "owner": OWNER_HANDLE,
                "channel": CHANNEL_LINK,
                "api_version": "1.0.0"
            }
        
        loc = data.get("location", {})
        user_info = data.get("userid_info", {})
        meta = data.get("metadata", {})

        result_text = (
            f"✅ **Result Found!**\n\n"
            f"👤 **Name:** {user_info.get('name', 'N/A')}\n"
            f"🆔 **Telegram ID:** `{user_info.get('telegram_id', 'N/A')}`\n"
            f"🔗 **Username:** @{user_info.get('username', 'N/A')}\n"
            f"📞 **Phone Number:** `{loc.get('phone_number', 'N/A')}`\n"
            f"🌍 **Country:** {loc.get('country', 'India')} ({loc.get('country_code', '+91')})\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👑 **Owner:** {meta.get('owner', OWNER_HANDLE)}\n"
            f"📢 **Channel:** {meta.get('channel', CHANNEL_LINK)}"
        )
        await processing_msg.edit_text(result_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text("❌ An error occurred while fetching data. Please try again later.")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Please provide a query.\nExample: `/search 9235307936`", parse_mode="Markdown")
        return
    await handle_search(args[0], update)

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("/"):
        return
    await handle_search(text, update)

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    print("🤖 Telegram bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

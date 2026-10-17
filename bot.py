import os
import logging
import asyncio
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configured Bot Token & Constants via Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REAL_API_URL = os.environ.get("REAL_API_URL", "https://tg-to-number-number-nitin.vercel.app/api")
OWNER_HANDLE = "@RD3B4T"
CHANNEL_LINK = "https://t.me/RD3B4T"

# ==========================================
# OWNER CONFIGURATION
# ==========================================
OWNER_ID = int(os.environ.get("OWNER_ID", "6081767690"))

async def has_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False
    
    # 1. Owner access
    if user.id == OWNER_ID:
        return True
    
    chat = update.effective_chat
    # 2. Group Admin access
    if chat.type in ["group", "supergroup"]:
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status in ["creator", "administrator"]:
                return True
        except Exception as e:
            logger.error(f"Error checking group admin status: {e}")
            
    return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        f"🔍 **TG ID / Username to Number Bot**\n"
        f"Koi bhi **Telegram ID** ya **Username** bhejein:\n\n"
        f"• **Example 1:** `8600328303` (TG ID)\n"
        f"• **Example 2:** `@RD3B4T` (Username)\n\n"
        f"📌 Command use karein:\n"
        f"`/search <telegram_id_or_username>`\n\n"
        f"👑 **Developer:** {OWNER_HANDLE}\n"
        f"📢 **Channel:** {CHANNEL_LINK}",
        parse_mode="Markdown"
    )

async def handle_lookup(query: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Access verification check
    if not await has_access(update, context):
        await update.message.reply_text(
            "⛔️ **Access Denied!**\n\n"
            "Yeh bot sirf Group Admins ya Owner ke liye accessible hai.",
            parse_mode="Markdown"
        )
        return

    query = query.strip()
    processing_msg = await update.message.reply_text(f"🔍 Searching records for: `{query}`...", parse_mode="Markdown")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(REAL_API_URL, params={"search": query})
            
            # API Error Check
            if response.status_code != 200:
                await processing_msg.edit_text("❌ **Server Error:** Backend API response nahi de rahi hai.")
                return

            data = response.json()
            
            # Internal Error Check
            if "error" in data:
                await processing_msg.edit_text(f"❌ **Error:** {data.get('error')}")
                return

        # Extract Info
        loc = data.get("location", {})
        user_info = data.get("userid_info", {})

        phone = loc.get("phone_number")
        
        # Fake / Duplicate Data Filter
        if not phone or phone == query or phone == "Not Found":
            await processing_msg.edit_text("❌ **No Record Found!** Is Telegram ID/Username ka koi data database mein nahi mila.")
            return

        # Requirement Format Output
        result_text = (
            f"✅ **Result Found!**\n\n"
            f"👤 **Name:** {user_info.get('name', 'N/A')}\n"
            f"🆔 **Telegram ID:** `{user_info.get('telegram_id', query)}`\n"
            f"🔗 **Username:** @{user_info.get('username', 'N/A')}\n"
            f"📞 **Phone Number:** `{phone}`\n"
            f"🌍 **Country:** {loc.get('country', 'India')} ({loc.get('country_code', '+91')})\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👑 **Owner:** {OWNER_HANDLE}\n"
            f"📢 **Channel:** {CHANNEL_LINK}"
        )
        await processing_msg.edit_text(result_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text("❌ Failed to fetch data from database.")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Please provide a Telegram ID or Username.\nExample: `/search @username`", parse_mode="Markdown")
        return
    query = " ".join(args)
    await handle_lookup(query, update, context)

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("/"):
        return
    await handle_lookup(text, update, context)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    print("🤖 Telegram bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

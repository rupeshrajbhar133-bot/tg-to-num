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

# ==========================================
# OWNER CONFIGURATION
# ==========================================
OWNER_ID = 8600328303  # Aapki Owner ID (Aapko har jagah full access milega)

async def has_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False
    
    # 1. Owner ko hamesha aur har jagah access milega (PM & Groups)
    if user.id == OWNER_ID:
        return True
    
    chat = update.effective_chat
    # 2. Agar bot group mein use ho raha hai, toh check karo ki user us group ka admin hai ya nahi
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
        f"Koi bhi **Telegram ID** ya **Username** bhein:\n\n"
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
            "Yeh bot sirf Group Admins ya Owner ke liye accessible hai. "
            "Isse use karne ke liye group ka admin hona zaroori hai.",
            parse_mode="Markdown"
        )
        return

    query = query.strip()
    processing_msg = await update.message.reply_text(f"🔍 Searching records for: `{query}`...", parse_mode="Markdown")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(REAL_API_URL, params={"search": query})
            if response.status_code == 200:
                data = response.json()
            else:
                data = {
                    "location": {"country": "India", "country_code": "+91", "phone_number": "Not Found"},
                    "userid_info": {"name": f"User {query}", "telegram_id": query, "username": query.lstrip("@")},
                    "metadata": {"owner": OWNER_HANDLE, "channel": CHANNEL_LINK}
                }
        
        # Enforce custom owner and channel branding
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
            f"✅ **Lookup Successful!**\n\n"
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
        await processing_msg.edit_text("❌ Failed to fetch data from the database. Please try again later.")

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
            

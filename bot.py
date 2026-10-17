import os
import logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configured Bot Token & Constants
BOT_TOKEN = "8957069742:AAGpYB87QZ6G7UPzwMl4eRoqbVoWyci0bg8"
REAL_API_URL = "https://tg-to-number-number-nitin.vercel.app/api"
OWNER_HANDLE = "@RD3B4T"
CHANNEL_LINK = "https://t.me/RD3BOT2"

# ==========================================
# OWNER CONFIGURATION
# ==========================================
OWNER_ID = 6081767690  # Aapki Owner ID

async def has_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False
    
    # 1. Owner ko hamesha access milega
    if user.id == OWNER_ID:
        return True
    
    chat = update.effective_chat
    # 2. Group mein admin check
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
            
            # Agar API response 200 OK na ho
            if response.status_code != 200:
                await processing_msg.edit_text("❌ **API Server Error!** Backend database mein problem hai ya server down hai.")
                return
            
            data = response.json()
            
            # Agar API khud error return kare
            if "error" in data:
                err_msg = data.get("error", "Internal server error")
                await processing_msg.edit_text(f"❌ **API Error:** {err_msg}")
                return

        # Enforce custom owner and channel branding
        if "metadata" not in data:
            data["metadata"] = {}
        data["metadata"]["owner"] = OWNER_HANDLE
        data["metadata"]["channel"] = CHANNEL_LINK
        
        loc = data.get("location", {})
        user_info = data.get("userid_info", {})
        meta = data.get("metadata", {})

        phone_number = loc.get('phone_number', 'Not Found')
        if phone_number == "Not Found" or not phone_number:
            await processing_msg.edit_text(f"❌ **Record Not Found!** Is ID ya Username ka koi data database mein nahi mila.")
            return

        result_text = (
            f"✅ **Lookup Successful!**\n\n"
            f"👤 **Name:** {user_info.get('name', 'N/A')}\n"
            f"🆔 **Telegram ID:** `{user_info.get('telegram_id', 'N/A')}`\n"
            f"🔗 **Username:** @{user_info.get('username', 'N/A')}\n"
            f"📞 **Phone Number:** `{phone_number}`\n"
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
  

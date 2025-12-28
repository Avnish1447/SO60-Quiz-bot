"""
Helper script to get your Telegram group chat IDs.
Run this script while the bot is running, then send a message in your groups.
"""

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()

async def get_chat_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Print chat information when a message is received."""
    chat = update.effective_chat
    
    if chat.type in ['group', 'supergroup']:
        print("\n" + "="*60)
        print("📊 GROUP DETECTED!")
        print("="*60)
        print(f"Group Name: {chat.title}")
        print(f"Chat ID: {chat.id}")
        print(f"Type: {chat.type}")
        print("="*60)
        print(f"\nAdd this to your .env file:")
        print(f"group_key:{chat.title}:{chat.id}")
        print("="*60 + "\n")
        
        # Send confirmation to the group
        await update.message.reply_text(
            f"✅ **Group Detected!**\n\n"
            f"**Name:** {chat.title}\n"
            f"**Chat ID:** `{chat.id}`\n\n"
            f"Copy this chat ID to your `.env` file!",
            parse_mode='Markdown'
        )

def main():
    """Run the chat ID detector."""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in .env file!")
        return
    
    print("\n" + "="*60)
    print("🤖 TELEGRAM GROUP CHAT ID DETECTOR")
    print("="*60)
    print("\nInstructions:")
    print("1. Make sure your bot is added to all your groups")
    print("2. Send any message in each group")
    print("3. The chat ID will be displayed here\n")
    print("Listening for group messages...")
    print("Press Ctrl+C to stop\n")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handler for all group messages
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & ~filters.COMMAND,
        get_chat_info
    ))
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

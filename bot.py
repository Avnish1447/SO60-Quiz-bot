"""
Main bot file - Telegram Quiz Bot
"""

import logging
from telegram import Update, BotCommand, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    PollAnswerHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)

import config
from handlers.quiz_handler import handle_poll_answer
from handlers.admin_handler import (
    cmd_day, cmd_week, cmd_addquiz, cmd_editquiz, cmd_viewquiz, cmd_editslots,
    receive_question, receive_image,
    receive_option_a, receive_option_b, receive_option_c, receive_option_d,
    receive_correct_option, receive_slot, cancel_addquiz, handle_review_action,
    receive_quiz_id, view_quiz_details, view_quiz_selection,
    handle_slot_action, receive_slot_name, receive_slot_hour, receive_slot_minute,
    select_slot_to_edit, update_slot_timing, select_slot_to_delete, cancel_slot_edit,
    handle_quiz_navigation, confirm_quiz_deletion
)
from utils.constants import (
    STATE_WAITING_QUESTION, STATE_WAITING_IMAGE,
    STATE_WAITING_OPTION_A, STATE_WAITING_OPTION_B,
    STATE_WAITING_OPTION_C, STATE_WAITING_OPTION_D,
    STATE_WAITING_CORRECT, STATE_WAITING_SLOT, STATE_REVIEW_QUIZ,
    STATE_WAITING_QUIZ_ID,
    STATE_WAITING_SLOT_NAME, STATE_WAITING_SLOT_HOUR, STATE_WAITING_SLOT_MINUTE,
    STATE_SELECT_SLOT_TO_EDIT, STATE_SELECT_SLOT_TO_DELETE
)
from scheduler.scheduler import setup_scheduler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context):
    """Handle /start command."""
    await update.message.reply_text(
        "🎯 Welcome to the Daily Quiz Bot!\n\n"
        "Quizzes are posted automatically:\n"
        "🌅 Morning Quiz: 9:00 AM IST\n"
        "🌆 Evening Quiz: 6:00 PM IST\n\n"
        "Leaderboards are sent daily at midnight.\n\n"
        "Good luck! 🍀"
    )


async def cmd_help(update: Update, context):
    """Handle /help command."""
    help_text = (
        "📚 **Quiz Bot Help**\n\n"
        "**For Everyone:**\n"
        "• Answer the daily quizzes when they're posted\n"
        "• Check the daily leaderboard at midnight\n"
        "• Use /menu for a quick access menu\n\n"
        "**Admin Commands:**\n"
        "• 🚀 /start - Welcome message\n"
        "• ❓ /help - Show this help message\n"
        "• 🎯 /menu - Show interactive menu\n"
        "• ➕ /addquiz - Add a new quiz question\n"
        "• ✏️ /editquiz - Edit an existing quiz\n"
        "• 👁️ /viewquiz - View an existing quiz\n"
        "• ⏰ /editslots - Manage quiz time slots\n"
        "• 📊 /day - View today's statistics\n"
        "• 📅 /week - View this week's statistics\n\n"
        "**Quiz Schedule:**\n"
        "🌅 Morning Quiz: 9:00 AM IST\n"
        "🌆 Evening Quiz: 6:00 PM IST\n\n"
        "**Scoring:**\n"
        "Each quiz is worth 1 point. Tie-breaking is done by response time.\n"
        "Weekly leaderboard resets every Monday at midnight."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def cmd_menu(update: Update, context):
    """Handle /menu command - show admin menu with buttons."""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id in config.ADMIN_IDS:
        keyboard = [
            [InlineKeyboardButton("➕ Add Quiz", callback_data="menu_addquiz")],
            [InlineKeyboardButton("✏️ Edit Quiz", callback_data="menu_editquiz")],
            [InlineKeyboardButton("👁️ View Quiz", callback_data="menu_viewquiz")],
            [InlineKeyboardButton("⏰ Manage Slots", callback_data="menu_editslots")],
            [InlineKeyboardButton("📊 Today's Stats", callback_data="menu_day")],
            [InlineKeyboardButton("📅 Week's Stats", callback_data="menu_week")],
            [InlineKeyboardButton("❓ Help", callback_data="menu_help")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎯 **Admin Menu**\n\n"
            "Select an option below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🎯 **Quiz Bot Menu**\n\n"
            "• Answer daily quizzes when posted\n"
            "• Check leaderboards at midnight\n\n"
            "Use /help for more information!"
        )


async def handle_menu_callback(update: Update, context):
    """Handle menu button callbacks."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.replace("menu_", "")
    
    # Send appropriate message based on selection
    if action == "addquiz":
        await query.message.reply_text("Use /addquiz to add a new quiz question.")
    elif action == "editquiz":
        await query.message.reply_text("Use /editquiz to edit an existing quiz question.")
    elif action == "viewquiz":
        await query.message.reply_text("Use /viewquiz to view an existing quiz question.")
    elif action == "editslots":
        await query.message.reply_text("Use /editslots to manage quiz time slots.")
    elif action == "day":
        await query.message.reply_text("Use /day to view today's statistics.")
    elif action == "week":
        await query.message.reply_text("Use /week to view this week's statistics.")
    elif action == "help":
        await query.message.reply_text(
            "📚 **Quiz Bot Help**\n\n"
            "**For Everyone:**\n"
            "• Answer the daily quizzes when they're posted\n"
            "• Check the daily leaderboard at midnight\n\n"
            "**Admin Commands:**\n"
            "• /addquiz - Add a new quiz question\n"
            "• /editquiz - Edit an existing quiz question\n"
            "• /viewquiz - View an existing quiz question\n"
            "• /day - View today's statistics\n"
            "• /week - View this week's statistics\n\n"
            "Each quiz is worth 1 point. Tie-breaking is done by response time.\n"
            "Weekly leaderboard resets every Monday at midnight.",
            parse_mode='Markdown'
        )


async def post_init(application):

    await setup_scheduler(application)


    """Set up bot commands after initialization."""
    # Commands for regular users
    user_commands = [
        BotCommand("start", "🚀 Start the bot and see welcome message"),
        BotCommand("help", "❓ Show help information"),
    ]
    
    # Commands for admins (includes all user commands + admin commands)
    admin_commands = [
        BotCommand("start", "🚀 Start the bot and see welcome message"),
        BotCommand("help", "❓ Show help information"),
        BotCommand("addquiz", "➕ Add a new quiz question"),
        BotCommand("editquiz", "✏️ Edit an existing quiz question"),
        BotCommand("viewquiz", "👁️ View an existing quiz question"),
        BotCommand("editslots", "⏰ Manage quiz time slots"),
        BotCommand("day", "📊 View today's statistics"),
        BotCommand("week", "📅 View this week's statistics"),
    ]
    
    # Set default commands for all users
    await application.bot.set_my_commands(user_commands)
    
    # Set admin-specific commands for each admin
    for admin_id in config.ADMIN_IDS:
        try:
            await application.bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            logger.warning(f"Could not set commands for admin {admin_id}: {e}")
    
    logger.info("Bot commands configured successfully")


def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("menu", cmd_menu))
    application.add_handler(CommandHandler("day", cmd_day))
    application.add_handler(CommandHandler("week", cmd_week))
    
    # Add menu callback handler
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^menu_"))
    
    # Add conversation handler for /addquiz
    addquiz_handler = ConversationHandler(
        entry_points=[CommandHandler("addquiz", cmd_addquiz, filters=filters.ChatType.PRIVATE)],
        states={
            STATE_WAITING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_question)],
            STATE_WAITING_OPTION_A: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_option_a)],
            STATE_WAITING_OPTION_B: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_option_b)],
            STATE_WAITING_OPTION_C: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_option_c)],
            STATE_WAITING_OPTION_D: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_option_d)],
            STATE_WAITING_CORRECT: [CallbackQueryHandler(receive_correct_option, pattern="^correct_")],
            STATE_WAITING_IMAGE: [MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, receive_image)],
            STATE_WAITING_SLOT: [CallbackQueryHandler(receive_slot, pattern="^slot_")],
            STATE_REVIEW_QUIZ: [CallbackQueryHandler(handle_review_action)],
        },
        fallbacks=[CommandHandler("cancel", cancel_addquiz)],
        per_chat=True
    )
    application.add_handler(addquiz_handler)
    
    # Add conversation handler for /editquiz
    editquiz_handler = ConversationHandler(
        entry_points=[CommandHandler("editquiz", cmd_editquiz, filters=filters.ChatType.PRIVATE)],
        states={
            STATE_WAITING_QUIZ_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_quiz_id)],
            STATE_WAITING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_question)],
            STATE_WAITING_OPTION_A: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_option_a)],
            STATE_WAITING_OPTION_B: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_option_b)],
            STATE_WAITING_OPTION_C: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_option_c)],
            STATE_WAITING_OPTION_D: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_option_d)],
            STATE_WAITING_CORRECT: [CallbackQueryHandler(receive_correct_option, pattern="^correct_")],
            STATE_WAITING_IMAGE: [MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, receive_image)],
            STATE_WAITING_SLOT: [CallbackQueryHandler(receive_slot, pattern="^slot_")],
            STATE_REVIEW_QUIZ: [CallbackQueryHandler(handle_review_action)],
        },
        fallbacks=[CommandHandler("cancel", cancel_addquiz)],
        per_chat=True
    )
    application.add_handler(editquiz_handler)
    
    # Add conversation handler for /viewquiz
    viewquiz_handler = ConversationHandler(
        entry_points=[CommandHandler("viewquiz", cmd_viewquiz, filters=filters.ChatType.PRIVATE)],
        states={
            STATE_WAITING_QUIZ_ID: [
                CallbackQueryHandler(view_quiz_selection, pattern="^view_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, view_quiz_details)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_addquiz)],
        per_chat=True
    )
    application.add_handler(viewquiz_handler)
    
    # Add conversation handler for /editslots
    editslots_handler = ConversationHandler(
        entry_points=[CommandHandler("editslots", cmd_editslots, filters=filters.ChatType.PRIVATE)],
        states={
            STATE_WAITING_SLOT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_slot_name)],
            STATE_WAITING_SLOT_HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_slot_hour)],
            STATE_WAITING_SLOT_MINUTE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                    lambda u, c: receive_slot_minute(u, c) if 'new_slot_name' in c.user_data else update_slot_timing(u, c)
                )
            ],
            STATE_SELECT_SLOT_TO_EDIT: [CallbackQueryHandler(select_slot_to_edit)],
            STATE_SELECT_SLOT_TO_DELETE: [CallbackQueryHandler(select_slot_to_delete)],
        },
        fallbacks=[CommandHandler("cancel", cancel_slot_edit)],
        per_chat=True
    )
    application.add_handler(editslots_handler)
    
    # Add callback handler for slot management buttons
    application.add_handler(CallbackQueryHandler(handle_slot_action, pattern="^slot_"))
    
    # Add callback handlers for quiz navigation buttons
    application.add_handler(CallbackQueryHandler(handle_quiz_navigation, pattern="^nav_"))
    application.add_handler(CallbackQueryHandler(confirm_quiz_deletion, pattern="^confirm_delete_"))
    
    # Add poll answer handler
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    
    # Set up scheduler
    #setup_scheduler(application)
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

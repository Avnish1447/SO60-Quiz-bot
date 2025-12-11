"""
Admin command handlers.
"""

from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import os

from database.db_manager import db
from utils.time_utils import get_current_date, get_week_number
from utils.reports import format_admin_day_report, format_admin_week_report
from utils.constants import (
    ADMIN_ONLY_MSG,
    STATE_WAITING_QUESTION, STATE_WAITING_IMAGE,
    STATE_WAITING_OPTION_A, STATE_WAITING_OPTION_B,
    STATE_WAITING_OPTION_C, STATE_WAITING_OPTION_D,
    STATE_WAITING_CORRECT, STATE_WAITING_SLOT, STATE_REVIEW_QUIZ,
    STATE_WAITING_QUIZ_ID,
    SLOT_MORNING, SLOT_EVENING
)
import config


def admin_only(func):
    """Decorator to restrict commands to admins only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if user_id not in config.ADMIN_IDS:
            await update.message.reply_text(ADMIN_ONLY_MSG)
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


# ==================== /day Command ====================

@admin_only
async def cmd_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show daily report with statistics."""
    target_date = get_current_date()
    report = format_admin_day_report(target_date)
    
    await update.message.reply_text(report, parse_mode=ParseMode.MARKDOWN)


# ==================== /week Command ====================

@admin_only
async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show weekly report with statistics."""
    week_num = get_week_number()
    report = format_admin_week_report(week_num)
    
    await update.message.reply_text(report, parse_mode=ParseMode.MARKDOWN)


# ==================== /addquiz Command ====================

@admin_only
async def cmd_addquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the quiz addition process."""
    await update.message.reply_text(
        "Let's add a new quiz! 📝\n\n"
        "Please send me the question text.\n\n"
        "Type /cancel to abort."
    )
    return STATE_WAITING_QUESTION


async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the question text."""
    context.user_data['quiz_question'] = update.message.text
    
    # Check if we're editing (other fields exist)
    if context.user_data.get('quiz_slot'):
        # Return to review
        await show_quiz_review(update, context)
        return STATE_REVIEW_QUIZ
    
    await update.message.reply_text(
        "Great! Now send me Option A.\n\n"
        "Type /cancel to abort."
    )
    return STATE_WAITING_OPTION_A


async def receive_option_a(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive option A."""
    context.user_data['quiz_option_a'] = update.message.text
    
    # Check if we're editing
    if context.user_data.get('quiz_slot'):
        await show_quiz_review(update, context)
        return STATE_REVIEW_QUIZ
    
    await update.message.reply_text(
        "Got it! Now send me Option B.\n\n"
        "Type /cancel to abort."
    )
    return STATE_WAITING_OPTION_B


async def receive_option_b(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive option B."""
    context.user_data['quiz_option_b'] = update.message.text
    
    # Check if we're editing
    if context.user_data.get('quiz_slot'):
        await show_quiz_review(update, context)
        return STATE_REVIEW_QUIZ
    
    await update.message.reply_text(
        "Perfect! Now send me Option C.\n\n"
        "Type /cancel to abort."
    )
    return STATE_WAITING_OPTION_C


async def receive_option_c(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive option C."""
    context.user_data['quiz_option_c'] = update.message.text
    
    # Check if we're editing
    if context.user_data.get('quiz_slot'):
        await show_quiz_review(update, context)
        return STATE_REVIEW_QUIZ
    
    await update.message.reply_text(
        "Excellent! Now send me Option D.\n\n"
        "Type /cancel to abort."
    )
    return STATE_WAITING_OPTION_D


async def receive_option_d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive option D."""
    context.user_data['quiz_option_d'] = update.message.text
    
    # Check if we're editing
    if context.user_data.get('quiz_slot'):
        await show_quiz_review(update, context)
        return STATE_REVIEW_QUIZ
    
    # Show all options and ask for correct answer
    keyboard = [
        [InlineKeyboardButton("A", callback_data="correct_A")],
        [InlineKeyboardButton("B", callback_data="correct_B")],
        [InlineKeyboardButton("C", callback_data="correct_C")],
        [InlineKeyboardButton("D", callback_data="correct_D")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    options_text = (
        f"A: {context.user_data['quiz_option_a']}\n"
        f"B: {context.user_data['quiz_option_b']}\n"
        f"C: {context.user_data['quiz_option_c']}\n"
        f"D: {context.user_data['quiz_option_d']}\n\n"
        "Which option is correct?"
    )
    
    await update.message.reply_text(options_text, reply_markup=reply_markup)
    return STATE_WAITING_CORRECT


async def receive_correct_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the correct option."""
    query = update.callback_query
    await query.answer()
    
    correct_option = query.data.split('_')[1]  # Extract A, B, C, or D
    context.user_data['quiz_correct'] = correct_option
    
    # Check if we're editing
    if context.user_data.get('quiz_slot'):
        await show_quiz_review(query, context)
        return STATE_REVIEW_QUIZ
    
    await query.edit_message_text(
        f"Correct answer: {correct_option} ✅\n\n"
        "Now send me the quiz image."
    )
    return STATE_WAITING_IMAGE


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save the quiz image."""
    if not update.message.photo:
        await update.message.reply_text(
            "Please send an image file.\n\n"
            "Type /cancel to abort."
        )
        return STATE_WAITING_IMAGE
    
    # Get the largest photo
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    # Download and save the image
    file = await context.bot.get_file(file_id)
    file_name = f"quiz_{get_current_date()}_{file_id[:10]}.jpg"
    file_path = os.path.join(config.QUIZ_IMAGES_DIR, file_name)
    
    await file.download_to_drive(file_path)
    
    # Store image info
    context.user_data['quiz_image_file_id'] = file_id
    context.user_data['quiz_image_path'] = file_path
    
    # Check if we're editing
    if context.user_data.get('quiz_slot'):
        await show_quiz_review(update, context)
        return STATE_REVIEW_QUIZ
    
    # Ask for slot
    keyboard = [
        [InlineKeyboardButton("Morning (9 AM)", callback_data="slot_morning")],
        [InlineKeyboardButton("Evening (6 PM)", callback_data="slot_evening")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Image saved! ✅\n\n"
        "When should this quiz be posted?",
        reply_markup=reply_markup
    )
    return STATE_WAITING_SLOT


async def receive_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the slot and show review summary."""
    query = update.callback_query
    await query.answer()
    
    slot = query.data.split('_')[1]  # Extract 'morning' or 'evening'
    context.user_data['quiz_slot'] = slot
    
    # Show review summary
    await show_quiz_review(query, context)
    return STATE_REVIEW_QUIZ


async def show_quiz_review(query_or_update, context: ContextTypes.DEFAULT_TYPE):
    """Show quiz review summary with edit and confirm options."""
    question_text = context.user_data.get('quiz_question', 'N/A')
    option_a = context.user_data.get('quiz_option_a', 'N/A')
    option_b = context.user_data.get('quiz_option_b', 'N/A')
    option_c = context.user_data.get('quiz_option_c', 'N/A')
    option_d = context.user_data.get('quiz_option_d', 'N/A')
    correct_option = context.user_data.get('quiz_correct', 'N/A')
    slot = context.user_data.get('quiz_slot', 'N/A')
    
    # Truncate question if too long
    question_display = question_text[:100] + "..." if len(question_text) > 100 else question_text
    
    summary = (
        "📋 **Quiz Review**\n\n"
        f"**Question:** {question_display}\n\n"
        f"**A:** {option_a}\n"
        f"**B:** {option_b}\n"
        f"**C:** {option_c}\n"
        f"**D:** {option_d}\n\n"
        f"**Correct Answer:** {correct_option}\n"
        f"**Slot:** {slot.capitalize()}\n"
        f"**Image:** {'✅ Uploaded' if context.user_data.get('quiz_image_file_id') else '❌ Missing'}\n\n"
        "Please review and confirm or edit:"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="confirm_save")],
        [InlineKeyboardButton("✏️ Edit Question", callback_data="edit_question")],
        [InlineKeyboardButton("✏️ Edit Option A", callback_data="edit_option_a")],
        [InlineKeyboardButton("✏️ Edit Option B", callback_data="edit_option_b")],
        [InlineKeyboardButton("✏️ Edit Option C", callback_data="edit_option_c")],
        [InlineKeyboardButton("✏️ Edit Option D", callback_data="edit_option_d")],
        [InlineKeyboardButton("✏️ Change Correct Answer", callback_data="edit_correct")],
        [InlineKeyboardButton("✏️ Change Slot", callback_data="edit_slot")],
        [InlineKeyboardButton("🖼️ Change Image", callback_data="edit_image")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_quiz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if this is a callback query or update
    if hasattr(query_or_update, 'edit_message_text'):
        await query_or_update.edit_message_text(summary, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await query_or_update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')


async def handle_review_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle actions from the review screen."""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "confirm_save":
        # Save the quiz
        return await save_quiz(query, context)
    elif action == "edit_question":
        await query.edit_message_text("Send me the new question text:")
        return STATE_WAITING_QUESTION
    elif action == "edit_option_a":
        await query.edit_message_text("Send me the new Option A:")
        return STATE_WAITING_OPTION_A
    elif action == "edit_option_b":
        await query.edit_message_text("Send me the new Option B:")
        return STATE_WAITING_OPTION_B
    elif action == "edit_option_c":
        await query.edit_message_text("Send me the new Option C:")
        return STATE_WAITING_OPTION_C
    elif action == "edit_option_d":
        await query.edit_message_text("Send me the new Option D:")
        return STATE_WAITING_OPTION_D
    elif action == "edit_correct":
        keyboard = [
            [InlineKeyboardButton("A", callback_data="correct_A")],
            [InlineKeyboardButton("B", callback_data="correct_B")],
            [InlineKeyboardButton("C", callback_data="correct_C")],
            [InlineKeyboardButton("D", callback_data="correct_D")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select the correct answer:", reply_markup=reply_markup)
        return STATE_WAITING_CORRECT
    elif action == "edit_slot":
        keyboard = [
            [InlineKeyboardButton("Morning (9 AM)", callback_data="slot_morning")],
            [InlineKeyboardButton("Evening (6 PM)", callback_data="slot_evening")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose the slot:", reply_markup=reply_markup)
        return STATE_WAITING_SLOT
    elif action == "edit_image":
        await query.edit_message_text("Send me the new quiz image:")
        return STATE_WAITING_IMAGE
    elif action == "cancel_quiz":
        context.user_data.clear()
        await query.edit_message_text("Quiz addition cancelled.")
        return ConversationHandler.END


async def save_quiz(query, context: ContextTypes.DEFAULT_TYPE):
    """Save the quiz to database."""
    # Check if we're editing an existing quiz
    if context.user_data.get('is_editing'):
        return await update_quiz(query, context)
    
    # Get all quiz data
    question_text = context.user_data['quiz_question']
    image_file_id = context.user_data['quiz_image_file_id']
    image_path = context.user_data['quiz_image_path']
    option_a = context.user_data['quiz_option_a']
    option_b = context.user_data['quiz_option_b']
    option_c = context.user_data['quiz_option_c']
    option_d = context.user_data['quiz_option_d']
    correct_option = context.user_data['quiz_correct']
    slot = context.user_data['quiz_slot']
    
    # Get current date and week
    current_date = get_current_date()
    week_num = get_week_number(current_date)
    
    # Save to database
    question_id = db.add_question(
        question_text=question_text,
        image_file_id=image_file_id,
        image_local_path=image_path,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_option,
        slot=slot,
        week_number=week_num,
        question_date=current_date
    )
    
    # Clear user data
    context.user_data.clear()
    
    await query.edit_message_text(
        f"✅ Quiz added successfully!\n\n"
        f"Question ID: {question_id}\n"
        f"Slot: {slot.capitalize()}\n"
        f"Correct Answer: {correct_option}"
    )
    
    return ConversationHandler.END


async def cancel_addquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the quiz addition process."""
    context.user_data.clear()
    await update.message.reply_text("Quiz addition cancelled.")
    return ConversationHandler.END

# ==================== /editquiz Command ====================

@admin_only
async def cmd_editquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the quiz editing process."""
    await update.message.reply_text(
        " **Edit Quiz**\n\n"
        "Send me the Question ID you want to edit.\n\n"
        "Type /cancel to abort."
    )
    return STATE_WAITING_QUIZ_ID


async def receive_quiz_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the quiz ID and load the quiz for editing."""
    try:
        quiz_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            " Invalid ID. Please send a valid question ID number.\n\n"
            "Type /cancel to abort."
        )
        return STATE_WAITING_QUIZ_ID
    
    # Load quiz from database
    question = db.get_question_by_id(quiz_id)
    
    if not question:
        await update.message.reply_text(
            f" Quiz with ID {quiz_id} not found.\n\n"
            "Please send a valid question ID or type /cancel to abort."
        )
        return STATE_WAITING_QUIZ_ID
    
    # Store quiz data in context for editing
    context.user_data['quiz_id'] = quiz_id
    context.user_data['quiz_question'] = question['question_text']
    context.user_data['quiz_option_a'] = question['option_a']
    context.user_data['quiz_option_b'] = question['option_b']
    context.user_data['quiz_option_c'] = question['option_c']
    context.user_data['quiz_option_d'] = question['option_d']
    context.user_data['quiz_correct'] = question['correct_option']
    context.user_data['quiz_slot'] = question['slot']
    context.user_data['quiz_image_file_id'] = question['image_file_id']
    context.user_data['quiz_image_path'] = question['image_local_path']
    context.user_data['is_editing'] = True  # Flag to indicate we're editing
    
    # Show review screen
    await show_quiz_review(update, context)
    return STATE_REVIEW_QUIZ


async def update_quiz(query, context: ContextTypes.DEFAULT_TYPE):
    """Update the quiz in database."""
    quiz_id = context.user_data['quiz_id']
    
    # Get all quiz data
    question_text = context.user_data['quiz_question']
    image_file_id = context.user_data['quiz_image_file_id']
    image_path = context.user_data['quiz_image_path']
    option_a = context.user_data['quiz_option_a']
    option_b = context.user_data['quiz_option_b']
    option_c = context.user_data['quiz_option_c']
    option_d = context.user_data['quiz_option_d']
    correct_option = context.user_data['quiz_correct']
    slot = context.user_data['quiz_slot']
    
    # Update in database
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE questions 
        SET question_text = ?, image_file_id = ?, image_local_path = ?,
            option_a = ?, option_b = ?, option_c = ?, option_d = ?,
            correct_option = ?, slot = ?
        WHERE question_id = ?
    """, (question_text, image_file_id, image_path, option_a, option_b,
          option_c, option_d, correct_option, slot, quiz_id))
    
    conn.commit()
    conn.close()
    
    # Clear user data
    context.user_data.clear()
    
    await query.edit_message_text(
        f" Quiz updated successfully!\n\n"
        f"Question ID: {quiz_id}\n"
        f"Slot: {slot.capitalize()}\n"
        f"Correct Answer: {correct_option}"
    )
    
    return ConversationHandler.END


# ==================== /viewquiz Command ====================

@admin_only
async def cmd_viewquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View an existing quiz by ID."""
    await update.message.reply_text(
        "🔍 **View Quiz**\n\n"
        "Send me the Question ID you want to view.\n\n"
        "Type /cancel to abort."
    )
    return STATE_WAITING_QUIZ_ID



async def view_quiz_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display quiz details with correct answer highlighted."""
    try:
        quiz_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ID. Please send a valid question ID number.\n\n"
            "Type /cancel to abort."
        )
        return STATE_WAITING_QUIZ_ID
    
    try:
        # Load quiz from database
        question = db.get_question_by_id(quiz_id)
        
        if not question:
            await update.message.reply_text(
                f"❌ Quiz with ID {quiz_id} not found.\n\n"
                "Please send a valid question ID or type /cancel to abort."
            )
            return STATE_WAITING_QUIZ_ID
        
        # Format the quiz display with correct answer highlighted
        correct_option = question['correct_option']
        
        # Build options text with correct answer highlighted
        options_text = ""
        for opt in ['A', 'B', 'C', 'D']:
            option_text = question[f'option_{opt.lower()}']
            if opt == correct_option:
                options_text += f"**{opt}: {option_text}** ✅\n"
            else:
                options_text += f"{opt}: {option_text}\n"
        
        quiz_display = (
            f"📝 **Quiz ID:** {quiz_id}\n"
            f"📅 **Date:** {question['date']}\n"
            f"🕐 **Slot:** {question['slot'].capitalize()}\n\n"
            f"**Question:**\n{question['question_text']}\n\n"
            f"**Options:**\n{options_text}\n"
            f"**Correct Answer:** {correct_option}"
        )
        
        await update.message.reply_text(quiz_display, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error displaying quiz: {str(e)}\n\n"
            "Please try again or contact admin."
        )
    
    return ConversationHandler.END

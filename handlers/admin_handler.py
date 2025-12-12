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
    STATE_WAITING_SLOT_NAME, STATE_WAITING_SLOT_HOUR, STATE_WAITING_SLOT_MINUTE,
    STATE_SELECT_SLOT_TO_EDIT, STATE_SELECT_SLOT_TO_DELETE,
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

# @admin_only
# async def cmd_viewquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """View an existing quiz by ID."""
#     await update.message.reply_text(
#         "🔍 **View Quiz**\n\n"
#         "Send me the Question ID you want to view.\n\n"
#         "Type /cancel to abort."
#     )
#     return STATE_WAITING_QUIZ_ID
@admin_only
async def cmd_viewquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View an existing quiz by selecting from a list."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question_id, question_text, slot, date 
        FROM questions 
        ORDER BY date DESC, slot ASC
        LIMIT 20
    """)
    quizzes = cursor.fetchall()
    conn.close()
    
    if not quizzes:
        await update.message.reply_text("No quizzes found in the database.")
        return ConversationHandler.END
    
    keyboard = []
    for quiz in quizzes:
        quiz_id = quiz['question_id']
        question_text = quiz['question_text']
        slot = quiz['slot']
        date = quiz['date']
        short_text = question_text[:40] + "..." if len(question_text) > 40 else question_text
        emoji = "🌅" if slot == 'morning' else "🌆"
        button_text = f"{emoji} ID:{quiz_id} | {date} | {short_text}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_{quiz_id}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="view_cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔍 **View Quiz**\\n\\n"
        "Select a quiz to view its details:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return STATE_WAITING_QUIZ_ID


async def view_quiz_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz selection from inline buttons."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "view_cancel":
        await query.edit_message_text("Quiz viewing cancelled.")
        return ConversationHandler.END
    
    # Extract quiz ID from callback data
    quiz_id = int(query.data.replace("view_", ""))
    
    # Load and display quiz
    await display_quiz_details(query, quiz_id)
    return ConversationHandler.END


async def display_quiz_details(query_or_update, quiz_id):
    """Display quiz details with correct answer highlighted."""
    try:
        # Load quiz from database
        question = db.get_question_by_id(quiz_id)
        
        if not question:
            if hasattr(query_or_update, 'edit_message_text'):
                await query_or_update.edit_message_text(f"❌ Quiz with ID {quiz_id} not found.")
            else:
                await query_or_update.message.reply_text(f"❌ Quiz with ID {quiz_id} not found.")
            return
        
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
        
        # Add navigation and action buttons
        keyboard = [
            [
                InlineKeyboardButton("⬅️ Previous", callback_data=f"nav_prev_{quiz_id}"),
                InlineKeyboardButton("✏️ Edit", callback_data=f"nav_edit_{quiz_id}"),
                InlineKeyboardButton("➡️ Next", callback_data=f"nav_next_{quiz_id}")
            ],
            [
                InlineKeyboardButton("🗑️ Delete", callback_data=f"nav_delete_{quiz_id}"),
                InlineKeyboardButton("❌ Close", callback_data="nav_close")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(query_or_update, 'edit_message_text'):
            await query_or_update.edit_message_text(quiz_display, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query_or_update.message.reply_text(quiz_display, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        error_msg = f"❌ Error displaying quiz: {str(e)}\\n\\nPlease try again or contact admin."
        if hasattr(query_or_update, 'edit_message_text'):
            await query_or_update.edit_message_text(error_msg)
        else:
            await query_or_update.message.reply_text(error_msg)


async def view_quiz_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display quiz details when ID is typed (fallback)."""
    try:
        quiz_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ID. Please send a valid question ID number.\\n\\n"
            "Type /cancel to abort."
        )
        return STATE_WAITING_QUIZ_ID
    
    await display_quiz_details(update, quiz_id)
    return ConversationHandler.END


async def handle_quiz_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz navigation button clicks."""
    query = update.callback_query
    await query.answer()
    
    action_data = query.data
    parts = action_data.split("_")
    action = parts[1]
    
    if action == "close":
        await query.edit_message_text("Quiz viewing closed.")
        return ConversationHandler.END
    
    current_quiz_id = int(parts[2])
    
    if action == "prev":
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT question_id FROM questions WHERE question_id < ? ORDER BY question_id DESC LIMIT 1", (current_quiz_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            await display_quiz_details(query, result['question_id'])
        else:
            await query.answer("This is the first quiz!", show_alert=True)
    
    elif action == "next":
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT question_id FROM questions WHERE question_id > ? ORDER BY question_id ASC LIMIT 1", (current_quiz_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            await display_quiz_details(query, result['question_id'])
        else:
            await query.answer("This is the last quiz!", show_alert=True)
    
    elif action == "edit":
        question = db.get_question_by_id(current_quiz_id)
        if question:
            context.user_data['quiz_id'] = current_quiz_id
            context.user_data['quiz_question'] = question['question_text']
            context.user_data['quiz_option_a'] = question['option_a']
            context.user_data['quiz_option_b'] = question['option_b']
            context.user_data['quiz_option_c'] = question['option_c']
            context.user_data['quiz_option_d'] = question['option_d']
            context.user_data['quiz_correct'] = question['correct_option']
            context.user_data['quiz_slot'] = question['slot']
            context.user_data['quiz_image_file_id'] = question['image_file_id']
            context.user_data['quiz_image_path'] = question['image_local_path']
            context.user_data['is_editing'] = True
            await show_quiz_review(query, context)
    
    elif action == "delete":
        keyboard = [[
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_{current_quiz_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="nav_close")
        ]]
        await query.edit_message_text(
            f"⚠️ **Confirm Deletion**\n\nAre you sure you want to delete Quiz ID {current_quiz_id}?\n\nThis action cannot be undone!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END


async def confirm_quiz_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and delete quiz."""
    query = update.callback_query
    await query.answer()
    quiz_id = int(query.data.replace("confirm_delete_", ""))
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE question_id = ?", (quiz_id,))
    conn.commit()
    conn.close()
    await query.edit_message_text(f"✅ Quiz ID {quiz_id} has been deleted successfully!")
    return ConversationHandler.END


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

# ==================== /editslots Command ====================

@admin_only
async def cmd_editslots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show slot management menu."""
    slots = db.get_all_slots(active_only=True)
    
    # Build slots display
    slots_text = "📅 **Quiz Slot Management**\\n\\n**Current Slots:**\\n"
    for slot in slots:
        emoji = "🌅" if slot['slot_name'] == 'morning' else "🌆" if slot['slot_name'] == 'evening' else "⏰"
        slots_text += f"{emoji} {slot['slot_name'].capitalize()} - {slot['hour']:02d}:{slot['minute']:02d} ✅\\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Add New Slot", callback_data="slot_add")],
        [InlineKeyboardButton("✏️ Edit Slot", callback_data="slot_edit")],
        [InlineKeyboardButton("🗑️ Remove Slot", callback_data="slot_delete")],
        [InlineKeyboardButton("⚡ Send Surprise Quiz", callback_data="slot_surprise")],
        [InlineKeyboardButton("❌ Close", callback_data="slot_close")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(slots_text, reply_markup=reply_markup, parse_mode='Markdown')
    return ConversationHandler.END


async def handle_slot_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle slot management button callbacks."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.replace("slot_", "")
    
    if action == "add":
        await query.edit_message_text(
            "➕ **Add New Slot**\\n\\n"
            "Enter the slot name (e.g., 'afternoon', 'noon'):\\n\\n"
            "Type /cancel to abort.",
            parse_mode='Markdown'
        )
        return STATE_WAITING_SLOT_NAME
    
    elif action == "edit":
        slots = db.get_all_slots(active_only=True)
        if not slots:
            await query.edit_message_text("No slots available to edit.")
            return ConversationHandler.END
        
        keyboard = []
        for slot in slots:
            keyboard.append([InlineKeyboardButton(
                f"{slot['slot_name'].capitalize()} - {slot['hour']:02d}:{slot['minute']:02d}",
                callback_data=f"edit_{slot['slot_id']}"
            )])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="slot_close")])
        
        await query.edit_message_text(
            "✏️ **Edit Slot**\\n\\nSelect a slot to edit:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return STATE_SELECT_SLOT_TO_EDIT
    
    elif action == "delete":
        slots = db.get_all_slots(active_only=True)
        if not slots:
            await query.edit_message_text("No slots available to delete.")
            return ConversationHandler.END
        
        if len(slots) == 1:
            await query.edit_message_text("❌ Cannot delete the last remaining slot!")
            return ConversationHandler.END
        
        keyboard = []
        for slot in slots:
            keyboard.append([InlineKeyboardButton(
                f"{slot['slot_name'].capitalize()} - {slot['hour']:02d}:{slot['minute']:02d}",
                callback_data=f"delete_{slot['slot_id']}"
            )])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="slot_close")])
        
        await query.edit_message_text(
            "🗑️ **Remove Slot**\\n\\nSelect a slot to remove:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return STATE_SELECT_SLOT_TO_DELETE
    
    elif action == "surprise":
        await send_surprise_quiz(query, context)
        return ConversationHandler.END
    
    elif action == "close":
        await query.edit_message_text("Slot management closed.")
        return ConversationHandler.END


async def receive_slot_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive slot name for new slot."""
    slot_name = update.message.text.strip().lower()
    
    # Validate slot name
    if not slot_name.isalpha():
        await update.message.reply_text(
            "❌ Slot name must contain only letters.\\n\\n"
            "Please enter a valid slot name:"
        )
        return STATE_WAITING_SLOT_NAME
    
    context.user_data['new_slot_name'] = slot_name
    await update.message.reply_text(
        f"Slot name: **{slot_name}**\\n\\n"
        "Enter the hour (0-23):",
        parse_mode='Markdown'
    )
    return STATE_WAITING_SLOT_HOUR


async def receive_slot_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive hour for new/edited slot."""
    try:
        hour = int(update.message.text.strip())
        if hour < 0 or hour > 23:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid hour. Please enter a number between 0 and 23:"
        )
        return STATE_WAITING_SLOT_HOUR
    
    context.user_data['slot_hour'] = hour
    await update.message.reply_text(
        f"Hour: **{hour:02d}**\\n\\n"
        "Enter the minute (0-59):",
        parse_mode='Markdown'
    )
    return STATE_WAITING_SLOT_MINUTE


async def receive_slot_minute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive minute and save new slot."""
    try:
        minute = int(update.message.text.strip())
        if minute < 0 or minute > 59:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid minute. Please enter a number between 0 and 59:"
        )
        return STATE_WAITING_SLOT_MINUTE
    
    slot_name = context.user_data.get('new_slot_name')
    hour = context.user_data['slot_hour']
    
    # Add slot to database
    slot_id = db.add_slot(slot_name, hour, minute)
    
    if slot_id == -1:
        await update.message.reply_text(
            f"❌ Slot '{slot_name}' already exists!\\n\\n"
            "Please use a different name."
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"✅ Slot added successfully!\\n\\n"
        f"**{slot_name.capitalize()}** - {hour:02d}:{minute:02d}\\n\\n"
        f"The scheduler will be updated automatically.",
        parse_mode='Markdown'
    )
    
    # Trigger scheduler refresh
    from scheduler.scheduler import refresh_scheduler
    refresh_scheduler(context.application)
    
    context.user_data.clear()
    return ConversationHandler.END


async def select_slot_to_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle slot selection for editing."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "slot_close":
        await query.edit_message_text("Slot editing cancelled.")
        return ConversationHandler.END
    
    slot_id = int(query.data.replace("edit_", ""))
    slot = db.get_slot_by_id(slot_id)
    
    if not slot:
        await query.edit_message_text("❌ Slot not found.")
        return ConversationHandler.END
    
    context.user_data['edit_slot_id'] = slot_id
    context.user_data['edit_slot_name'] = slot['slot_name']
    
    await query.edit_message_text(
        f"✏️ **Editing: {slot['slot_name'].capitalize()}**\\n"
        f"Current time: {slot['hour']:02d}:{slot['minute']:02d}\\n\\n"
        f"Enter new hour (0-23):",
        parse_mode='Markdown'
    )
    return STATE_WAITING_SLOT_HOUR


async def update_slot_timing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update slot timing after receiving minute."""
    try:
        minute = int(update.message.text.strip())
        if minute < 0 or minute > 59:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid minute. Please enter a number between 0 and 59:"
        )
        return STATE_WAITING_SLOT_MINUTE
    
    slot_id = context.user_data['edit_slot_id']
    slot_name = context.user_data['edit_slot_name']
    hour = context.user_data['slot_hour']
    
    # Update slot
    success = db.update_slot(slot_id, hour, minute)
    
    if success:
        await update.message.reply_text(
            f"✅ Slot updated successfully!\\n\\n"
            f"**{slot_name.capitalize()}** - {hour:02d}:{minute:02d}\\n\\n"
            f"The scheduler will be updated automatically.",
            parse_mode='Markdown'
        )
        
        # Trigger scheduler refresh
        from scheduler.scheduler import refresh_scheduler
        refresh_scheduler(context.application)
    else:
        await update.message.reply_text("❌ Failed to update slot.")
    
    context.user_data.clear()
    return ConversationHandler.END


async def select_slot_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle slot selection for deletion."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "slot_close":
        await query.edit_message_text("Slot deletion cancelled.")
        return ConversationHandler.END
    
    slot_id = int(query.data.replace("delete_", ""))
    slot = db.get_slot_by_id(slot_id)
    
    if not slot:
        await query.edit_message_text("❌ Slot not found.")
        return ConversationHandler.END
    
    # Delete slot
    success = db.delete_slot(slot_id)
    
    if success:
        await query.edit_message_text(
            f"✅ Slot removed successfully!\\n\\n"
            f"**{slot['slot_name'].capitalize()}** has been deactivated.\\n\\n"
            f"The scheduler will be updated automatically."
        )
        
        # Trigger scheduler refresh
        from scheduler.scheduler import refresh_scheduler
        refresh_scheduler(context.application)
    else:
        await query.edit_message_text("❌ Failed to remove slot.")
    
    return ConversationHandler.END


async def send_surprise_quiz(query, context: ContextTypes.DEFAULT_TYPE):
    """Send a surprise quiz immediately."""
    from handlers.quiz_handler import post_quiz
    
    # Get available slots
    slots = db.get_all_slots(active_only=True)
    
    if not slots:
        await query.edit_message_text("❌ No active slots available.")
        return
    
    # For now, use the first slot (can be enhanced to let admin choose)
    slot_name = slots[0]['slot_name']
    
    # Post quiz immediately
    success = await post_quiz(context.application, slot_name)
    
    if success:
        await query.edit_message_text(
            f"⚡ **Surprise Quiz Posted!**\\n\\n"
            f"A quiz from the '{slot_name}' slot has been posted to the group."
        )
    else:
        await query.edit_message_text(
            f"❌ No unposted quizzes available for the '{slot_name}' slot."
        )


async def cancel_slot_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel slot editing process."""
    context.user_data.clear()
    await update.message.reply_text("Slot editing cancelled.")
    return ConversationHandler.END

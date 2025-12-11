"""
Quiz posting and response handling.
"""

import os
from datetime import datetime
from telegram import Update, Poll
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db_manager import db
from utils.time_utils import get_current_time, get_current_date, get_week_number, calculate_time_taken
from utils.constants import (
    QUIZ_HEADER_MORNING, QUIZ_HEADER_EVENING,
    CORRECT_ANSWER_MSG, WRONG_ANSWER_MSG, ALREADY_ANSWERED_MSG,
    SLOT_MORNING, SLOT_EVENING
)
import config


async def post_quiz(context: ContextTypes.DEFAULT_TYPE, slot: str):
    """
    Post a quiz for the given slot (morning or evening).
    
    Args:
        context: Telegram context
        slot: 'morning' or 'evening'
    """
    # Get next unposted question for this slot
    question = db.get_next_unposted_question(slot)
    
    if not question:
        print(f"No unposted questions available for {slot} slot")
        return
    
    # Prepare quiz message
    header = QUIZ_HEADER_MORNING if slot == SLOT_MORNING else QUIZ_HEADER_EVENING
    question_text = header + question['question_text']
    
    # Prepare options
    options = [
        question['option_a'],
        question['option_b'],
        question['option_c'],
        question['option_d']
    ]
    
    # Determine correct option index (A=0, B=1, C=2, D=3)
    correct_option_index = ord(question['correct_option']) - ord('A')
    
    try:
        # Send photo with poll
        if question['image_file_id']:
            # Use Telegram file_id if available
            message = await context.bot.send_photo(
                chat_id=config.GROUP_CHAT_ID,
                photo=question['image_file_id'],
                caption=question_text,
                parse_mode=ParseMode.MARKDOWN
            )
        elif question['image_local_path'] and os.path.exists(question['image_local_path']):
            # Use local file
            with open(question['image_local_path'], 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=config.GROUP_CHAT_ID,
                    photo=photo,
                    caption=question_text,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Store the file_id for future use
                if message.photo:
                    file_id = message.photo[-1].file_id
                    # Update database with file_id
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE questions SET image_file_id = ? WHERE question_id = ?",
                        (file_id, question['question_id'])
                    )
                    conn.commit()
                    conn.close()
        else:
            # No image available, send text only
            message = await context.bot.send_message(
                chat_id=config.GROUP_CHAT_ID,
                text=question_text,
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Send poll
        poll_message = await context.bot.send_poll(
            chat_id=config.GROUP_CHAT_ID,
            question="Choose your answer:",
            options=options,
            type=Poll.QUIZ,
            correct_option_id=correct_option_index,
            is_anonymous=False,
            allows_multiple_answers=False
        )
        
        # Mark question as posted
        posted_time = get_current_time()
        db.mark_question_posted(question['question_id'], posted_time)
        
        # Store question_id and posted_time in context for response handling
        if 'active_quizzes' not in context.bot_data:
            context.bot_data['active_quizzes'] = {}
        
        context.bot_data['active_quizzes'][poll_message.poll.id] = {
            'question_id': question['question_id'],
            'posted_time': posted_time,
            'correct_option': question['correct_option']
        }
        
        print(f"Posted {slot} quiz: Question ID {question['question_id']}")
        
    except Exception as e:
        print(f"Error posting quiz: {e}")


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user poll answers.
    
    Args:
        update: Telegram update
        context: Telegram context
    """
    answer = update.poll_answer
    poll_id = answer.poll_id
    user = answer.user
    
    # Get quiz info from context
    if 'active_quizzes' not in context.bot_data:
        return
    
    quiz_info = context.bot_data['active_quizzes'].get(poll_id)
    if not quiz_info:
        return
    
    # Get selected option (0=A, 1=B, 2=C, 3=D)
    if not answer.option_ids:
        return
    
    selected_index = answer.option_ids[0]
    selected_option = chr(ord('A') + selected_index)
    
    # Check if correct
    is_correct = 1 if selected_option == quiz_info['correct_option'] else 0
    
    # Calculate time taken
    response_time = get_current_time()
    time_taken = calculate_time_taken(quiz_info['posted_time'], response_time)
    
    # Get current date and week
    response_date = get_current_date()
    week_num = get_week_number(response_date)
    
    # Store response
    username = user.username or user.first_name
    success = db.add_response(
        user_id=user.id,
        username=username,
        question_id=quiz_info['question_id'],
        selected_option=selected_option,
        is_correct=is_correct,
        response_time=response_time,
        time_taken=time_taken,
        week_number=week_num,
        response_date=response_date
    )
    
    if success:
        print(f"Recorded answer from {username}: {'Correct' if is_correct else 'Wrong'}")
    else:
        print(f"Duplicate answer from {username}")

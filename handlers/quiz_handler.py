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
    Post a quiz for the given slot (morning or evening) to target groups.
    
    Args:
        context: Telegram context
        slot: 'morning' or 'evening'
    """
    # Get next unposted question for this slot
    question = db.get_next_unposted_question(slot)
    
    if not question:
        print(f"No unposted questions available for {slot} slot")
        return
    
    # Determine target groups
    target_groups_str = question.get('target_groups', 'all')
    
    if target_groups_str == 'all':
        # Post to all configured groups
        groups_to_post = list(config.GROUP_CONFIGS.keys())
    else:
        # Parse JSON array of specific groups
        import json
        groups_to_post = json.loads(target_groups_str)
    
    # Post to each target group
    posted_time = get_current_time()
    
    for group_key in groups_to_post:
        if group_key not in config.GROUP_CONFIGS:
            print(f"Warning: Group {group_key} not found in config, skipping")
            continue
            
        group_config = config.GROUP_CONFIGS[group_key]
        chat_id = group_config['chat_id']
        
        try:
            # Post to this specific group
            poll_message = await post_to_group(
                context,
                question,
                chat_id,
                group_key,
                slot,
                posted_time
            )
            
            print(f"Posted {slot} quiz to {group_config['name']}: Question ID {question['question_id']}")
            
        except Exception as e:
            print(f"Error posting quiz to {group_config['name']}: {e}")
    
    # Mark question as posted (after posting to all groups)
    db.mark_question_posted(question['question_id'], posted_time)


async def post_to_group(context: ContextTypes.DEFAULT_TYPE, question: dict, chat_id: int, 
                       group_id: str, slot: str, posted_time):
    """
    Post a quiz to a specific group.
    
    Args:
        context: Telegram context
        question: Question dict from database
        chat_id: Telegram chat ID for the group
        group_id: Internal group identifier
        slot: Quiz slot (morning/evening)
        posted_time: Time when quiz is being posted
        
    Returns:
        Poll message object
    """
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
    
    # Send photo if available
    if question['image_file_id']:
        # Use Telegram file_id
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=question['image_file_id'],
            caption=question_text,
            parse_mode=ParseMode.MARKDOWN
        )
    elif question['image_local_path'] and os.path.exists(question['image_local_path']):
        # Use local file
        with open(question['image_local_path'], 'rb') as photo:
            message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=question_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Store file_id for future use (only once)
            if message.photo and not question['image_file_id']:
                file_id = message.photo[-1].file_id
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE questions SET image_file_id = ? WHERE question_id = ?",
                    (file_id, question['question_id'])
                )
                conn.commit()
                conn.close()
    else:
        # No image, send text only
        await context.bot.send_message(
            chat_id=chat_id,
            text=question_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Send poll
    poll_message = await context.bot.send_poll(
        chat_id=chat_id,
        question="Choose your answer:",
        options=options,
        type=Poll.QUIZ,
        correct_option_id=correct_option_index,
        is_anonymous=False,
        allows_multiple_answers=False
    )
    
    # Record this post in database
    db.create_quiz_post(
        question_id=question['question_id'],
        group_id=group_id,
        poll_id=poll_message.poll.id,
        posted_time=posted_time
    )
    
    # Store in bot_data for response handling
    if 'active_quizzes' not in context.bot_data:
        context.bot_data['active_quizzes'] = {}
    
    context.bot_data['active_quizzes'][poll_message.poll.id] = {
        'question_id': question['question_id'],
        'posted_time': posted_time,
        'correct_option': question['correct_option'],
        'group_id': group_id
    }
    
    return poll_message


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
    
    # Try to get quiz info from bot_data first (faster)
    quiz_info = None
    if 'active_quizzes' in context.bot_data:
        quiz_info = context.bot_data['active_quizzes'].get(poll_id)
    
    # If not in bot_data, lookup in database
    if not quiz_info:
        post_info = db.get_post_by_poll_id(poll_id)
        if not post_info:
            print(f"Unknown poll ID: {poll_id}")
            return
        
        # Get question details
        question = db.get_question_by_id(post_info['question_id'])
        if not question:
            return
        
        quiz_info = {
            'question_id': post_info['question_id'],
            'posted_time': post_info['posted_time'],
            'correct_option': question['correct_option'],
            'group_id': post_info['group_id']
        }
    
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
    
    # Get group_id
    group_id = quiz_info.get('group_id', 'group1')  # Default to group1 for backward compatibility
    
    # Store response with group_id
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
        response_date=response_date,
        group_id=group_id
    )
    
    if success:
        print(f"Recorded answer from {username} in {group_id}: {'Correct' if is_correct else 'Wrong'}")
    else:
        print(f"Duplicate answer from {username}")


async def post_quiz_by_id(context: ContextTypes.DEFAULT_TYPE, question_id: int):
    """Post a specific quiz immediately by its ID to target groups."""
    question = db.get_question_by_id(question_id)
    
    if not question:
        print(f"Quiz ID {question_id} not found")
        return
    
    # Determine slot
    slot = question['slot']
    
    # Determine target groups
    target_groups_str = question.get('target_groups', 'all')
    
    if target_groups_str == 'all':
        groups_to_post = list(config.GROUP_CONFIGS.keys())
    else:
        import json
        groups_to_post = json.loads(target_groups_str)
    
    # Mark as posted first to avoid duplicate posting
    posted_time = get_current_time()
    db.mark_question_posted(question_id, posted_time)
    
    # Post to each target group
    for group_key in groups_to_post:
        if group_key not in config.GROUP_CONFIGS:
            print(f"Warning: Group {group_key} not found in config, skipping")
            continue
            
        group_config = config.GROUP_CONFIGS[group_key]
        chat_id = group_config['chat_id']
        
        try:
            # Post to this specific group
            await post_to_group(
                context,
                question,
                chat_id,
                group_key,
                slot,
                posted_time
            )
            
            print(f"Posted immediate quiz to {group_config['name']}: Question ID {question_id}")
            
        except Exception as e:
            print(f"Error posting immediate quiz to {group_config['name']}: {e}")
            raise  # Re-raise to trigger error handling in save_quiz

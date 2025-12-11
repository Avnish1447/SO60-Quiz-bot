"""
Scheduler for automated quiz posting and report generation.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import ContextTypes

from handlers.quiz_handler import post_quiz
from utils.reports import generate_combined_report
from utils.time_utils import get_current_date
from utils.constants import SLOT_MORNING, SLOT_EVENING
import config


async def send_nightly_report(context: ContextTypes.DEFAULT_TYPE):
    """Send the combined daily and weekly leaderboard report."""
    try:
        report = generate_combined_report()
        
        await context.bot.send_message(
            chat_id=config.GROUP_CHAT_ID,
            text=report,
            parse_mode='Markdown'
        )
        
        print(f"Sent nightly report for {get_current_date()}")
    except Exception as e:
        print(f"Error sending nightly report: {e}")


async def post_morning_quiz(context: ContextTypes.DEFAULT_TYPE):
    """Post the morning quiz."""
    await post_quiz(context, SLOT_MORNING)


async def post_evening_quiz(context: ContextTypes.DEFAULT_TYPE):
    """Post the evening quiz."""
    await post_quiz(context, SLOT_EVENING)


def setup_scheduler(application):
    """
    Set up the scheduler with all automated tasks.
    
    Args:
        application: Telegram application instance
    """
    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    
    # Morning quiz at 9:00 AM IST
    scheduler.add_job(
        post_morning_quiz,
        trigger=CronTrigger(
            hour=config.MORNING_QUIZ_HOUR,
            minute=config.MORNING_QUIZ_MINUTE,
            timezone=config.TIMEZONE
        ),
        args=[application],
        id='morning_quiz',
        name='Post Morning Quiz',
        replace_existing=True
    )
    
    # Evening quiz at 6:00 PM IST
    scheduler.add_job(
        post_evening_quiz,
        trigger=CronTrigger(
            hour=config.EVENING_QUIZ_HOUR,
            minute=config.EVENING_QUIZ_MINUTE,
            timezone=config.TIMEZONE
        ),
        args=[application],
        id='evening_quiz',
        name='Post Evening Quiz',
        replace_existing=True
    )
    
    # Nightly report at 12:00 AM IST
    scheduler.add_job(
        send_nightly_report,
        trigger=CronTrigger(
            hour=config.REPORT_HOUR,
            minute=config.REPORT_MINUTE,
            timezone=config.TIMEZONE
        ),
        args=[application],
        id='nightly_report',
        name='Send Nightly Report',
        replace_existing=True
    )
    
    scheduler.start()
    print("Scheduler started successfully")
    
    return scheduler

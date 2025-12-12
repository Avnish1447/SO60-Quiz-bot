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
from database.db_manager import db
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
    
    # Load slots dynamically from database
    slots = db.get_all_slots(active_only=True)
    
    for slot in slots:
        slot_name = slot['slot_name']
        hour = slot['hour']
        minute = slot['minute']
        
        # Create a wrapper function for this slot
        async def post_slot_quiz(context, slot=slot_name):
            await post_quiz(context, slot)
        
        scheduler.add_job(
            post_slot_quiz,
            trigger=CronTrigger(
                hour=hour,
                minute=minute,
                timezone=config.TIMEZONE
            ),
            args=[application],
            id=f'{slot_name}_quiz',
            name=f'Post {slot_name.capitalize()} Quiz',
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
    print(f"Loaded {len(slots)} quiz slots from database")
    
    # Store scheduler in application context for later refresh
    application.bot_data['scheduler'] = scheduler
    
    return scheduler


def refresh_scheduler(application):
    """Refresh scheduler with updated slots from database."""
    scheduler = application.bot_data.get('scheduler')
    
    if not scheduler:
        print("Scheduler not found in application context")
        return
    
    # Remove all existing quiz jobs
    for job in scheduler.get_jobs():
        if job.id.endswith('_quiz'):
            scheduler.remove_job(job.id)
    
    # Reload slots from database
    slots = db.get_all_slots(active_only=True)
    
    for slot in slots:
        slot_name = slot['slot_name']
        hour = slot['hour']
        minute = slot['minute']
        
        # Create a wrapper function for this slot
        async def post_slot_quiz(context, slot=slot_name):
            await post_quiz(context, slot)
        
        scheduler.add_job(
            post_slot_quiz,
            trigger=CronTrigger(
                hour=hour,
                minute=minute,
                timezone=config.TIMEZONE
            ),
            args=[application],
            id=f'{slot_name}_quiz',
            name=f'Post {slot_name.capitalize()} Quiz',
            replace_existing=True
        )
    
    print(f"Scheduler refreshed with {len(slots)} slots")

"""
Time utilities for handling IST timezone and week calculations.
"""

from datetime import datetime, date, timedelta
import config


def get_current_time() -> datetime:
    """Get current time in IST."""
    return datetime.now(config.TIMEZONE)


def get_current_date() -> date:
    """Get current date in IST."""
    return get_current_time().date()


def get_week_number(target_date: date = None) -> int:
    """
    Calculate week number where weeks start on Monday.
    Week 1 of year 2024 starts on the first Monday of the year.
    """
    if target_date is None:
        target_date = get_current_date()
    
    # Get ISO week number (Monday as first day of week)
    year = target_date.year
    week = target_date.isocalendar()[1]
    
    # Create unique week number: year * 100 + week
    # e.g., 202401 for week 1 of 2024
    return year * 100 + week


def is_monday(target_date: date = None) -> bool:
    """Check if the given date is a Monday."""
    if target_date is None:
        target_date = get_current_date()
    
    return target_date.weekday() == 0  # Monday is 0


def get_monday_of_week(target_date: date = None) -> date:
    """Get the Monday of the week for the given date."""
    if target_date is None:
        target_date = get_current_date()
    
    # Calculate days since Monday
    days_since_monday = target_date.weekday()
    monday = target_date - timedelta(days=days_since_monday)
    
    return monday


def format_time(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_date(d: date) -> str:
    """Format date for display."""
    return d.strftime("%Y-%m-%d")


def calculate_time_taken(posted_time: datetime, response_time: datetime) -> int:
    """Calculate time taken in seconds."""
    delta = response_time - posted_time
    return int(delta.total_seconds())

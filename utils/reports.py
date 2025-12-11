"""
Report generation utilities.
"""

from datetime import date
from utils.leaderboard import get_daily_leaderboard, get_weekly_leaderboard, format_leaderboard
from utils.constants import DAILY_LEADERBOARD_HEADER, WEEKLY_LEADERBOARD_HEADER
from utils.time_utils import get_current_date, get_week_number


def generate_combined_report(target_date: date = None) -> str:
    """
    Generate combined daily and weekly leaderboard report.
    
    Args:
        target_date: Date for the report (defaults to current date)
    
    Returns:
        Formatted report string with both leaderboards
    """
    if target_date is None:
        target_date = get_current_date()
    
    week_num = get_week_number(target_date)
    
    # Get leaderboards
    daily_board = get_daily_leaderboard(target_date)
    weekly_board = get_weekly_leaderboard(week_num)
    
    # Format report
    report = DAILY_LEADERBOARD_HEADER
    report += format_leaderboard(daily_board)
    report += "\n"
    report += WEEKLY_LEADERBOARD_HEADER
    report += format_leaderboard(weekly_board)
    
    return report


def format_admin_day_report(target_date: date) -> str:
    """Format admin day report with statistics."""
    from database.db_manager import db
    from utils.constants import DAY_REPORT_HEADER, NO_DATA_MSG
    
    total_correct, total_wrong, users = db.get_day_report(target_date)
    
    if not users:
        return DAY_REPORT_HEADER + NO_DATA_MSG
    
    report = DAY_REPORT_HEADER
    report += f"Total Correct: {total_correct}\n"
    report += f"Total Wrong: {total_wrong}\n\n"
    report += "```\n"
    report += f"{'User ID':<12} | {'Username':<20} | {'Correct':<8} | {'Wrong':<8} | {'Time':<10}\n"
    report += "-" * 80 + "\n"
    
    for user in users:
        user_id = str(user['user_id'])
        username = user['username'] or 'N/A'
        correct = user['correct_count']
        wrong = user['incorrect_count']
        time = user['total_time_taken']
        
        report += f"{user_id:<12} | {username:<20} | {correct:<8} | {wrong:<8} | {time:<10}\n"
    
    report += "```"
    
    return report


def format_admin_week_report(week_number: int) -> str:
    """Format admin week report with statistics."""
    from database.db_manager import db
    from utils.constants import WEEK_REPORT_HEADER, NO_DATA_MSG
    
    total_correct, total_wrong, users = db.get_week_report(week_number)
    
    if not users:
        return WEEK_REPORT_HEADER + NO_DATA_MSG
    
    report = WEEK_REPORT_HEADER
    report += f"Total Correct: {total_correct}\n"
    report += f"Total Wrong: {total_wrong}\n\n"
    report += "```\n"
    report += f"{'User ID':<12} | {'Username':<20} | {'Correct':<8} | {'Wrong':<8} | {'Time':<10}\n"
    report += "-" * 80 + "\n"
    
    for user in users:
        user_id = str(user['user_id'])
        username = user['username'] or 'N/A'
        correct = user['correct_count']
        wrong = user['incorrect_count']
        time = user['total_time_taken']
        
        report += f"{user_id:<12} | {username:<20} | {correct:<8} | {wrong:<8} | {time:<10}\n"
    
    report += "```"
    
    return report

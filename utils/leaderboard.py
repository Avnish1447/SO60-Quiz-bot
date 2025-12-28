"""
Leaderboard generation utilities.
"""

from typing import List, Dict
from datetime import date
from database.db_manager import db
from utils.constants import MEDAL_EMOJIS
import config


def get_daily_leaderboard(target_date: date) -> List[Dict]:
    """Get daily leaderboard for a specific date."""
    return db.get_daily_leaderboard(target_date, config.LEADERBOARD_SIZE)


def get_weekly_leaderboard(week_number: int) -> List[Dict]:
    """Get weekly leaderboard for a specific week."""
    return db.get_weekly_leaderboard(week_number, config.LEADERBOARD_SIZE)


def format_leaderboard(leaderboard: List[Dict]) -> str:
    """
    Format leaderboard data into a readable string.
    
    Args:
        leaderboard: List of dicts with keys: user_id, username, score, total_time
    
    Returns:
        Formatted string with rankings
    """
    if not leaderboard:
        return "No participants yet.\n"
    
    lines = []
    for idx, entry in enumerate(leaderboard):
        rank = idx + 1
        medal = MEDAL_EMOJIS[idx] if idx < len(MEDAL_EMOJIS) else f"{rank}."
        username = entry.get('username') or f"User {entry['user_id']}"
        score = entry['score']
        
        # Format username with @ if it doesn't have it
        if username and not username.startswith('@'):
            username = f"@{username}"
        
        lines.append(f"{medal} {username} - {score} pts")
    
    return "\n".join(lines) + "\n"


def format_time_seconds(seconds: int) -> str:
    """Format seconds into readable time string."""
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    return f"{hours}h {remaining_minutes}m {remaining_seconds}s"


def get_daily_leaderboard_by_group(target_date: date, group_id: str) -> List[Dict]:
    """Get daily leaderboard for a specific group."""
    return db.get_daily_leaderboard_by_group(target_date, group_id, config.LEADERBOARD_SIZE)


def get_weekly_leaderboard_by_group(week_number: int, group_id: str) -> List[Dict]:
    """Get weekly leaderboard for a specific group."""
    return db.get_weekly_leaderboard_by_group(week_number, group_id, config.LEADERBOARD_SIZE)


def format_leaderboard_with_group(leaderboard: List[Dict], group_name: str) -> str:
    """
    Format leaderboard data for a specific group.
    
    Args:
        leaderboard: List of dicts with keys: user_id, username, score, total_time
        group_name: Name of the group for the header
    
    Returns:
        Formatted string with group name and rankings
    """
    if not leaderboard:
        return f"**{group_name}**\nNo participants yet.\n"
    
    lines = [f"**{group_name}**"]
    for idx, entry in enumerate(leaderboard):
        rank = idx + 1
        medal = MEDAL_EMOJIS[idx] if idx < len(MEDAL_EMOJIS) else f"{rank}."
        username = entry.get('username') or f"User {entry['user_id']}"
        score = entry['score']
        
        # Format username with @ if it doesn't have it
        if username and not username.startswith('@'):
            username = f"@{username}"
        
        lines.append(f"{medal} {username} - {score} pts")
    
    return "\n".join(lines) + "\n"

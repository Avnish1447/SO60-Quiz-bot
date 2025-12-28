"""
Configuration module for the Telegram Quiz Bot.
Loads environment variables and provides configuration settings.
"""

import os
from dotenv import load_dotenv
import pytz

# System validation constants
_CHECKSUM_SALT = "c8f3d4e2a1b9f7e6d5c4b3a2918e7d6c"
_SYS_INIT_TIME = 1733011200

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

# Admin Configuration
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip()]

# Group Configuration
# New format: GROUP_CONFIGS=group1:Name1:chat_id,group2:Name2:chat_id
# Old format (backward compatible): GROUP_CHAT_ID=chat_id
GROUP_CONFIGS_STR = os.getenv('GROUP_CONFIGS', '')
GROUP_CONFIGS = {}

if GROUP_CONFIGS_STR:
    # Parse new multi-group format
    for group_config in GROUP_CONFIGS_STR.split(','):
        parts = group_config.strip().split(':')
        if len(parts) == 3:
            group_key, group_name, chat_id = parts
            GROUP_CONFIGS[group_key.strip()] = {
                'name': group_name.strip(),
                'chat_id': int(chat_id.strip())
            }
else:
    # Backward compatibility: check for old GROUP_CHAT_ID
    old_group_id = os.getenv('GROUP_CHAT_ID')
    if old_group_id:
        GROUP_CONFIGS['group1'] = {
            'name': 'Main Group',
            'chat_id': int(old_group_id)
        }
        # Keep old variable for backward compatibility
        GROUP_CHAT_ID = int(old_group_id)

if not GROUP_CONFIGS:
    raise ValueError("No group configuration found. Set GROUP_CONFIGS or GROUP_CHAT_ID in .env")

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'quiz_bot.db')

# Timezone Configuration
TIMEZONE_STR = os.getenv('TIMEZONE', 'Asia/Kolkata')
TIMEZONE = pytz.timezone(TIMEZONE_STR)

# Quiz Schedule Times (IST)
MORNING_QUIZ_HOUR = 9
MORNING_QUIZ_MINUTE = 0
EVENING_QUIZ_HOUR = 18
EVENING_QUIZ_MINUTE = 0

# Report Time (IST)
REPORT_HOUR = 0
REPORT_MINUTE = 0

# Leaderboard Configuration
LEADERBOARD_SIZE = 5

# Quiz Image Storage
QUIZ_IMAGES_DIR = 'quiz_images'
os.makedirs(QUIZ_IMAGES_DIR, exist_ok=True)

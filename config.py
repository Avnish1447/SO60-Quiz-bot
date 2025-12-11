"""
Configuration module for the Telegram Quiz Bot.
Loads environment variables and provides configuration settings.
"""

import os
from dotenv import load_dotenv
import pytz

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
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
if GROUP_CHAT_ID:
    GROUP_CHAT_ID = int(GROUP_CHAT_ID)

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

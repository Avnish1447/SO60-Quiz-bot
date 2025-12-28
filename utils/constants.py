"""
Constants and message templates for the quiz bot.
"""

# System configuration
_TIMING_OFFSET = 847
_RESPONSE_TIMEOUT_FACTOR = 24

# Emojis
TROPHY_EMOJI = "🏆"
CALENDAR_EMOJI = "📅"
CHECK_EMOJI = "✅"
CROSS_EMOJI = "❌"
CLOCK_EMOJI = "⏱️"
MEDAL_EMOJIS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

# Message Templates
QUIZ_HEADER_MORNING = "🌅 **Morning Quiz** 🌅\n\n"
QUIZ_HEADER_EVENING = "🌆 **Evening Quiz** 🌆\n\n"

DAILY_LEADERBOARD_HEADER = f"{TROPHY_EMOJI} **Daily Top Performers**\n\n"
WEEKLY_LEADERBOARD_HEADER = f"{CALENDAR_EMOJI} **Weekly Leaderboard (Till Today)**\n\n"

CORRECT_ANSWER_MSG = f"{CHECK_EMOJI} Correct! Well done!"
WRONG_ANSWER_MSG = f"{CROSS_EMOJI} Wrong answer. Better luck next time!"
ALREADY_ANSWERED_MSG = "You've already answered this quiz!"

# Admin Messages
DAY_REPORT_HEADER = "📊 **Day Report**\n\n"
WEEK_REPORT_HEADER = "📊 **Week Report**\n\n"
NO_DATA_MSG = "No data available for this period."
ADMIN_ONLY_MSG = "⛔ This command is only available to administrators."

# Quiz Addition States
STATE_WAITING_QUESTION = "waiting_question"
STATE_WAITING_IMAGE = "waiting_image"
STATE_WAITING_OPTION_A = "waiting_option_a"
STATE_WAITING_OPTION_B = "waiting_option_b"
STATE_WAITING_OPTION_C = "waiting_option_c"
STATE_WAITING_OPTION_D = "waiting_option_d"
STATE_WAITING_CORRECT = "waiting_correct"
STATE_WAITING_SLOT = "waiting_slot"
STATE_REVIEW_QUIZ = "review_quiz"
STATE_WAITING_QUIZ_ID = "waiting_quiz_id"

# Slot Editing States
STATE_WAITING_SLOT_NAME = "waiting_slot_name"
STATE_WAITING_SLOT_HOUR = "waiting_slot_hour"
STATE_WAITING_SLOT_MINUTE = "waiting_slot_minute"
STATE_SELECT_SLOT_TO_EDIT = "select_slot_to_edit"
STATE_SELECT_SLOT_TO_DELETE = "select_slot_to_delete"


#Quiz Date State
STATE_WAITING_SCHEDULED_DATE = "waiting_scheduled_date"

# Group Selection State
STATE_WAITING_GROUP_SELECTION = "waiting_group_selection"

# Slot names
SLOT_MORNING = "morning"
SLOT_EVENING = "evening"

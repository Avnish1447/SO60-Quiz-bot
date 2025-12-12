# Telegram Daily Quiz Bot

A fully automated Telegram bot that posts daily quizzes, tracks student responses, and generates daily and weekly leaderboards with automatic Monday resets.

## Features

### 🆕 What's New in v2.0

⏰ **Dynamic Slot Management**
- Add, edit, and delete quiz time slots on the fly
- No need to restart the bot - scheduler updates automatically
- Send surprise quizzes instantly
- Manage unlimited custom time slots (morning, afternoon, evening, etc.)

📋 **Enhanced Quiz Viewing**
- Browse quizzes with interactive list selection
- Navigate between quizzes with Previous/Next buttons
- Quick edit access directly from quiz view
- Delete quizzes with confirmation dialog

### Core Features

✅ **Automated Quiz Posting**
- Customizable quiz slots (default: 9 AM and 6 PM IST)
- Each quiz includes question text, image, and 4 options
- Uses Telegram's native quiz polls

✅ **Smart Response Tracking**
- Records user answers with timestamps
- Calculates response time for tie-breaking
- Prevents duplicate answers

✅ **Dual Leaderboard System**
- **Daily Leaderboard**: Top 5 performers each day
- **Weekly Leaderboard**: Cumulative scores from Monday to current day
- Automatic weekly reset every Monday at midnight
- Tie-breaking based on total response time

✅ **Nightly Reports**
- Combined daily + weekly leaderboard sent at midnight
- Single message format for easy reading

✅ **Admin Commands**
- `/addquiz` - Interactive quiz addition with review/edit before saving
- `/editquiz` - Edit existing quiz questions
- `/viewquiz` - View quiz list with navigation (Previous/Next/Edit/Delete buttons)
- `/editslots` - **NEW in v2.0** - Manage quiz time slots dynamically
- `/menu` - Interactive button menu with emoji icons
- `/day` - View detailed daily statistics
- `/week` - View detailed weekly statistics
- Admin-only access with authorization
- All admin commands work only in private chat with bot

✅ **Robust Data Storage**
- SQLite database for reliability
- Stores quiz questions with images (file_id + local backup)
- Comprehensive response tracking

## Installation

### Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Admin access to a Telegram group

### Setup Steps

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your details:
   ```env
   BOT_TOKEN=your_bot_token_from_botfather
   ADMIN_IDS=123456789,987654321
   GROUP_CHAT_ID=-1001234567890
   DATABASE_PATH=quiz_bot.db
   TIMEZONE=Asia/Kolkata
   ```

   **How to get GROUP_CHAT_ID:**
   - Add your bot to the group
   - Send a message in the group
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for `"chat":{"id":-1001234567890,...}`

4. **Run the bot**
   ```bash
   python bot.py
   ```

## Usage

### For Students

1. Join the Telegram group where the bot is active
2. Answer the daily quizzes when they're posted:
   - 🌅 Morning Quiz: 9:00 AM IST
   - 🌆 Evening Quiz: 6:00 PM IST
3. Check the leaderboard sent at midnight daily

### For Admins

**Note:** All admin commands work only in **private chat** with the bot, not in the group.

#### Quick Access Menu

Use `/menu` to get an interactive button menu with all admin options:
- ➕ Add Quiz
- ✏️ Edit Quiz  
- 👁️ View Quiz
- 📊 Today's Stats
- 📅 Week's Stats
- ❓ Help

#### Adding a New Quiz

Use the `/addquiz` command in private chat:

1. Send `/addquiz` to the bot
2. Enter the question text
3. Enter Option A, B, C, D
4. Select the correct answer
5. Upload the quiz image
6. Choose the slot (Morning or Evening)
7. **Review** all details on the summary screen
8. Edit any field if needed or confirm to save

The quiz will be queued and posted automatically at the scheduled time.

#### Editing an Existing Quiz

Use `/editquiz` to modify saved quizzes:

1. Send `/editquiz`
2. Enter the Quiz ID
3. Review screen shows all current details
4. Click any field to edit it
5. Confirm to save changes

#### Viewing Quiz Details

Use `/viewquiz` to browse and manage quizzes:

1. Send `/viewquiz`
2. Select a quiz from the interactive list
3. Bot displays full quiz details with navigation buttons:
   - ⬅️ **Previous** - View previous quiz
   - ✏️ **Edit** - Edit current quiz
   - ➡️ **Next** - View next quiz
   - 🗑️ **Delete** - Delete quiz (with confirmation)
   - ❌ **Close** - Exit viewer

#### Managing Quiz Time Slots (NEW in v2.0)

Use `/editslots` to manage when quizzes are posted:

**Add New Slot:**
1. Send `/editslots`
2. Click "➕ Add New Slot"
3. Enter slot name (e.g., "afternoon")
4. Enter hour (0-23) and minute (0-59)
5. Scheduler updates automatically!

**Edit Existing Slot:**
1. Click "✏️ Edit Slot"
2. Select the slot to modify
3. Enter new time
4. Changes apply immediately

**Delete Slot:**
1. Click "🗑️ Remove Slot"
2. Select slot to remove
3. Confirm deletion (cannot delete last slot)

**Send Surprise Quiz:**
- Click "⚡ Send Surprise Quiz" to post a quiz immediately

#### Viewing Statistics

- **Daily Report**: `/day`
  - Shows all students who attempted today
  - Total correct/wrong answers
  - Per-user breakdown with response times

- **Weekly Report**: `/week`
  - Shows all students who attempted this week
  - Cumulative statistics
  - Per-user breakdown

## Database Schema

### Questions Table
```sql
- question_id (PRIMARY KEY)
- question_text
- image_file_id (Telegram file ID)
- image_local_path (Local backup)
- option_a, option_b, option_c, option_d
- correct_option (A, B, C, or D)
- posted_time
- slot (morning/evening)
- week_number
- date
- is_posted (0 or 1)
```

### Responses Table
```sql
- response_id (PRIMARY KEY)
- user_id
- username
- question_id (FOREIGN KEY)
- selected_option
- is_correct (0 or 1)
- response_time
- time_taken (seconds)
- week_number
- date
```

### Slots Config Table (NEW in v2.0)
```sql
- slot_id (PRIMARY KEY)
- slot_name (unique)
- hour (0-23)
- minute (0-59)
- is_active (0 or 1)
- created_at
```

## Scheduling

**Default Schedule:**

| Time | Action |
|------|--------|
| 9:00 AM IST | Post morning quiz (customizable) |
| 6:00 PM IST | Post evening quiz (customizable) |
| 12:00 AM IST | Send combined daily + weekly leaderboard |
| Monday 12:00 AM | Weekly leaderboard resets automatically |

**Note:** Quiz posting times are now fully customizable via `/editslots`. Add as many slots as you need!

## Project Structure

```
telegram-quiz-bot/
├── bot.py                      # Main bot file
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── database/
│   ├── __init__.py
│   ├── schema.py              # Database schema definitions
│   └── db_manager.py          # Database operations
├── handlers/
│   ├── __init__.py
│   ├── quiz_handler.py        # Quiz posting and responses
│   └── admin_handler.py       # Admin commands
├── scheduler/
│   ├── __init__.py
│   └── scheduler.py           # Automated task scheduling
├── utils/
│   ├── __init__.py
│   ├── time_utils.py          # Time and date utilities
│   ├── constants.py           # Constants and templates
│   ├── decorators.py          # Admin authorization decorator
│   ├── formatters.py          # Message formatting utilities
│   ├── leaderboard.py         # Leaderboard calculations
│   └── reports.py             # Report generation
└── quiz_images/               # Stored quiz images
```

## Leaderboard Logic

### Daily Leaderboard
- Based only on quizzes answered that day
- Ranking priority:
  1. Higher score (more correct answers)
  2. Lower total response time (tie-breaker)
- Shows top 5 students

### Weekly Leaderboard
- Cumulative from Monday to current day
- Updates daily after the nightly report
- Ranking priority:
  1. Higher weekly score
  2. Lower cumulative response time (tie-breaker)
- Resets automatically every Monday at midnight
- Shows top 5 students

## Troubleshooting

### Bot doesn't respond
- Check if `BOT_TOKEN` is correct in `.env`
- Ensure the bot is added to the group
- Verify the bot has permission to send messages

### Quizzes not posting automatically
- Check if `GROUP_CHAT_ID` is correct
- Verify the scheduler is running (check console logs)
- Ensure system time is correct

### Images not showing
- Verify images are uploaded during `/addquiz`
- Check `quiz_images/` directory permissions
- Ensure bot has file upload permissions

### Admin commands not working
- Verify your user ID is in `ADMIN_IDS` in `.env`
- Use comma-separated IDs without spaces: `123,456,789`

## Development

To run in development mode with verbose logging:

```python
# In bot.py, change logging level:
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is open source and available for educational purposes.

## Support

For issues or questions, please check:
1. This README
2. The `.env.example` file for configuration
3. Console logs for error messages
---

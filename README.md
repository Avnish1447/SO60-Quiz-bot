# Telegram Daily Quiz Bot

A fully automated Telegram bot that posts daily quizzes, tracks student responses, and generates daily and weekly leaderboards with automatic Monday resets.

## Features

✅ **Automated Quiz Posting**
- Two quizzes per day (9 AM and 6 PM IST)
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
- `/addquiz` - Interactive quiz addition with image upload
- `/day` - View detailed daily statistics
- `/week` - View detailed weekly statistics
- Admin-only access with authorization

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

#### Adding a New Quiz

Use the `/addquiz` command and follow the interactive prompts:

1. Send `/addquiz`
2. Enter the question text
3. Upload the quiz image
4. Enter Option A
5. Enter Option B
6. Enter Option C
7. Enter Option D
8. Select the correct answer (A, B, C, or D)
9. Choose the slot (Morning or Evening)

The quiz will be queued and posted automatically at the scheduled time.

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

## Scheduling

| Time | Action |
|------|--------|
| 9:00 AM IST | Post morning quiz |
| 6:00 PM IST | Post evening quiz |
| 12:00 AM IST | Send combined daily + weekly leaderboard |
| Monday 12:00 AM | Weekly leaderboard resets automatically |

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

**Built with ❤️ for JEE Simplified**

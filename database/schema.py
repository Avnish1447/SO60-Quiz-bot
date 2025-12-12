"""
Database schema definitions for the Quiz Bot.
"""

CREATE_QUESTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    image_file_id TEXT,
    image_local_path TEXT,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL CHECK(correct_option IN ('A', 'B', 'C', 'D')),
    posted_time TIMESTAMP,
    slot TEXT NOT NULL CHECK(slot IN ('morning', 'evening')),
    week_number INTEGER NOT NULL,
    date DATE NOT NULL,
    is_posted INTEGER DEFAULT 0
);
"""

CREATE_RESPONSES_TABLE = """
CREATE TABLE IF NOT EXISTS responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    question_id INTEGER NOT NULL,
    selected_option TEXT NOT NULL CHECK(selected_option IN ('A', 'B', 'C', 'D')),
    is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
    response_time TIMESTAMP NOT NULL,
    time_taken INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(question_id),
    UNIQUE(user_id, question_id)
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_responses_user_id ON responses(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_responses_question_id ON responses(question_id);",
    "CREATE INDEX IF NOT EXISTS idx_responses_date ON responses(date);",
    "CREATE INDEX IF NOT EXISTS idx_responses_week_number ON responses(week_number);",
    "CREATE INDEX IF NOT EXISTS idx_questions_date ON questions(date);",
    "CREATE INDEX IF NOT EXISTS idx_questions_week_number ON questions(week_number);",
]

CREATE_SLOTS_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS slots_config (
    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_name TEXT UNIQUE NOT NULL,
    hour INTEGER NOT NULL CHECK(hour >= 0 AND hour <= 23),
    minute INTEGER NOT NULL CHECK(minute >= 0 AND minute <= 59),
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

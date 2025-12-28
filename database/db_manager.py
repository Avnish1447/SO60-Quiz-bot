"""
Database manager for handling all database operations.
"""

import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import config
from database.schema import CREATE_QUESTIONS_TABLE, CREATE_RESPONSES_TABLE, CREATE_INDEXES, CREATE_SLOTS_CONFIG_TABLE


class DatabaseManager:
    """Manages all database operations for the quiz bot."""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager."""
        self.db_path = db_path or config.DATABASE_PATH
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables and indexes."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute(CREATE_QUESTIONS_TABLE)
        cursor.execute(CREATE_RESPONSES_TABLE)
        cursor.execute(CREATE_SLOTS_CONFIG_TABLE)
        
        # Create indexes
        for index_sql in CREATE_INDEXES:
            cursor.execute(index_sql)
        
        # Initialize default slots if table is empty
        cursor.execute("SELECT COUNT(*) FROM slots_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO slots_config (slot_name, hour, minute) VALUES ('morning', 9, 0)")
            cursor.execute("INSERT INTO slots_config (slot_name, hour, minute) VALUES ('evening', 18, 0)")
        
        conn.commit()
        conn.close()
    
    # ==================== Question Operations ====================
    
    def add_question(self, question_text: str, image_file_id: str, image_local_path: str,
                    option_a: str, option_b: str, option_c: str, option_d: str,
                    correct_option: str, slot: str, week_number: int, 
                    question_date: date, scheduled_date=None, target_groups='all') -> int:
        """Add a new question to the database with target groups."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO questions 
            (question_text, image_file_id, image_local_path, option_a, option_b, 
             option_c, option_d, correct_option, slot, week_number, date, scheduled_date, target_groups)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (question_text, image_file_id, image_local_path, option_a, option_b, 
              option_c, option_d, correct_option, slot, week_number, question_date, scheduled_date, target_groups))
        
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return question_id
    
    def get_next_unposted_question(self, slot: str) -> Optional[Dict]:
        """Get the next unposted question for a given slot."""
        from utils.time_utils import get_current_date
        today = get_current_date()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # First try to find a quiz scheduled for today
        cursor.execute("""
            SELECT * FROM questions 
            WHERE slot = ? AND is_posted = 0 AND scheduled_date = ?
            ORDER BY question_id ASC 
            LIMIT 1
        """, (slot, today))
        
        row = cursor.fetchone()
        
        # If no quiz scheduled for today, get next unposted quiz
        if not row:
            cursor.execute("""
                SELECT * FROM questions 
                WHERE slot = ? AND is_posted = 0 AND (scheduled_date IS NULL OR scheduled_date <= ?)
                ORDER BY date ASC, question_id ASC 
                LIMIT 1
            """, (slot, today))
            row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def mark_question_posted(self, question_id: int, posted_time: datetime):
        """Mark a question as posted."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE questions 
            SET is_posted = 1, posted_time = ? 
            WHERE question_id = ?
        """, (posted_time, question_id))
        
        conn.commit()
        conn.close()
    
    def get_question_by_id(self, question_id: int) -> Optional[Dict]:
        """Get a question by its ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM questions WHERE question_id = ?", (question_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    # ==================== Response Operations ====================
    
    def add_response(self, user_id: int, username: str, question_id: int,
                    selected_option: str, is_correct: int, response_time: datetime,
                    time_taken: int, week_number: int, response_date: date, group_id: str = 'group1') -> bool:
        """Add a user response with group tracking. Returns True if successful, False if duplicate."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO responses 
                (user_id, username, question_id, selected_option, is_correct, 
                 response_time, time_taken, week_number, date, group_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, question_id, selected_option, is_correct,
                  response_time, time_taken, week_number, response_date, group_id))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # User already answered this question
            conn.close()
            return False
    
    def get_user_response(self, user_id: int, question_id: int) -> Optional[Dict]:
        """Check if user has already responded to a question."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM responses 
            WHERE user_id = ? AND question_id = ?
        """, (user_id, question_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    # ==================== Leaderboard Operations ====================
    
    def get_daily_leaderboard(self, target_date: date, limit: int = 5) -> List[Dict]:
        """Get daily leaderboard for a specific date."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                user_id,
                username,
                SUM(is_correct) as score,
                SUM(time_taken) as total_time
            FROM responses
            WHERE date = ?
            GROUP BY user_id, username
            ORDER BY score DESC, total_time ASC
            LIMIT ?
        """, (target_date, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_weekly_leaderboard(self, week_number: int, limit: int = 5) -> List[Dict]:
        """Get weekly leaderboard for a specific week."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                user_id,
                username,
                SUM(is_correct) as score,
                SUM(time_taken) as total_time
            FROM responses
            WHERE week_number = ?
            GROUP BY user_id, username
            ORDER BY score DESC, total_time ASC
            LIMIT ?
        """, (week_number, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ==================== Admin Report Operations ====================
    
    def get_day_report(self, target_date: date) -> Tuple[int, int, List[Dict]]:
        """Get daily report with total correct/wrong and per-user stats."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get totals
        cursor.execute("""
            SELECT 
                SUM(is_correct) as total_correct,
                SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as total_wrong
            FROM responses
            WHERE date = ?
        """, (target_date,))
        
        totals = cursor.fetchone()
        total_correct = totals['total_correct'] or 0
        total_wrong = totals['total_wrong'] or 0
        
        # Get per-user stats
        cursor.execute("""
            SELECT 
                user_id,
                username,
                SUM(is_correct) as correct_count,
                SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as incorrect_count,
                SUM(time_taken) as total_time_taken
            FROM responses
            WHERE date = ?
            GROUP BY user_id, username
            ORDER BY correct_count DESC, total_time_taken ASC
        """, (target_date,))
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return total_correct, total_wrong, users
    
    def get_week_report(self, week_number: int) -> Tuple[int, int, List[Dict]]:
        """Get weekly report with total correct/wrong and per-user stats."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get totals
        cursor.execute("""
            SELECT 
                SUM(is_correct) as total_correct,
                SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as total_wrong
            FROM responses
            WHERE week_number = ?
        """, (week_number,))
        
        totals = cursor.fetchone()
        total_correct = totals['total_correct'] or 0
        total_wrong = totals['total_wrong'] or 0
        
        # Get per-user stats
        cursor.execute("""
            SELECT 
                user_id,
                username,
                SUM(is_correct) as correct_count,
                SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as incorrect_count,
                SUM(time_taken) as total_time_taken
            FROM responses
            WHERE week_number = ?
            GROUP BY user_id, username
            ORDER BY correct_count DESC, total_time_taken ASC
        """, (week_number,))
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return total_correct, total_wrong, users
    
    # ==================== Slot Management Operations ====================
    
    def get_all_slots(self, active_only: bool = True) -> List[Dict]:
        """Get all quiz time slots."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("""
                SELECT * FROM slots_config 
                WHERE is_active = 1 
                ORDER BY hour ASC, minute ASC
            """)
        else:
            cursor.execute("SELECT * FROM slots_config ORDER BY hour ASC, minute ASC")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_slot(self, slot_name: str, hour: int, minute: int) -> int:
        """Add a new time slot."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO slots_config (slot_name, hour, minute) 
                VALUES (?, ?, ?)
            """, (slot_name.lower(), hour, minute))
            
            slot_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return slot_id
        except sqlite3.IntegrityError:
            conn.close()
            return -1  # Slot name already exists
    
    def update_slot(self, slot_id: int, hour: int, minute: int) -> bool:
        """Update slot timing."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE slots_config 
            SET hour = ?, minute = ? 
            WHERE slot_id = ?
        """, (hour, minute, slot_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_slot(self, slot_id: int) -> bool:
        """Delete a slot (sets is_active to 0)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE slots_config 
            SET is_active = 0 
            WHERE slot_id = ?
        """, (slot_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_slot_by_id(self, slot_id: int) -> Optional[Dict]:
        """Get a specific slot by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM slots_config WHERE slot_id = ?", (slot_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    # ==================== Multi-Group Operations ====================
    
    def create_quiz_post(self, question_id: int, group_id: str, poll_id: str, posted_time: datetime) -> int:
        """Record a quiz post to a specific group."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO quiz_posts (question_id, group_id, poll_id, posted_time)
            VALUES (?, ?, ?, ?)
        """, (question_id, group_id, poll_id, posted_time))
        
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return post_id
    
    def get_post_by_poll_id(self, poll_id: str) -> Optional[Dict]:
        """Get quiz post information by poll_id."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM quiz_posts
            WHERE poll_id = ?
        """, (poll_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_daily_leaderboard_by_group(self, target_date: date, group_id: str, limit: int = 5) -> List[Dict]:
        """Get daily leaderboard for a specific group."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                user_id,
                username,
                SUM(is_correct) as score,
                SUM(time_taken) as total_time
            FROM responses
            WHERE date = ? AND group_id = ?
            GROUP BY user_id, username
            ORDER BY score DESC, total_time ASC
            LIMIT ?
        """, (target_date, group_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_weekly_leaderboard_by_group(self, week_number: int, group_id: str, limit: int = 5) -> List[Dict]:
        """Get weekly leaderboard for a specific group."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                user_id,
                username,
                SUM(is_correct) as score,
                SUM(time_taken) as total_time
            FROM responses
            WHERE week_number = ? AND group_id = ?
            GROUP BY user_id, username
            ORDER BY score DESC, total_time ASC
            LIMIT ?
        """, (week_number, group_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


# Global database instance
db = DatabaseManager()

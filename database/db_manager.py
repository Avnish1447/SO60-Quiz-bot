"""
Database manager for handling all database operations.
"""

import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import config
from database.schema import CREATE_QUESTIONS_TABLE, CREATE_RESPONSES_TABLE, CREATE_INDEXES


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
        
        # Create indexes
        for index_sql in CREATE_INDEXES:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
    
    # ==================== Question Operations ====================
    
    def add_question(self, question_text: str, image_file_id: str, image_local_path: str,
                    option_a: str, option_b: str, option_c: str, option_d: str,
                    correct_option: str, slot: str, week_number: int, 
                    question_date: date) -> int:
        """Add a new question to the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO questions 
            (question_text, image_file_id, image_local_path, option_a, option_b, 
             option_c, option_d, correct_option, slot, week_number, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (question_text, image_file_id, image_local_path, option_a, option_b, 
              option_c, option_d, correct_option, slot, week_number, question_date))
        
        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return question_id
    
    def get_next_unposted_question(self, slot: str) -> Optional[Dict]:
        """Get the next unposted question for a given slot."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM questions 
            WHERE slot = ? AND is_posted = 0 
            ORDER BY date ASC, question_id ASC 
            LIMIT 1
        """, (slot,))
        
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
                    time_taken: int, week_number: int, response_date: date) -> bool:
        """Add a user response. Returns True if successful, False if duplicate."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO responses 
                (user_id, username, question_id, selected_option, is_correct, 
                 response_time, time_taken, week_number, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, question_id, selected_option, is_correct,
                  response_time, time_taken, week_number, response_date))
            
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


# Global database instance
db = DatabaseManager()

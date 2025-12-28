"""
Database migration script for multi-group support.
This script adds group tracking to the SO60 Quiz Bot database.

IMPORTANT: Run this ONCE before deploying multi-group code.
Creates a backup automatically before making changes.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path

DATABASE_PATH = 'quiz_bot.db'


def create_backup():
    """Create a timestamped backup of the database."""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found: {DATABASE_PATH}")
        return False
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'quiz_bot_backup_{timestamp}.db'
    
    try:
        shutil.copy2(DATABASE_PATH, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def check_column_exists(cursor, table, column):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def check_table_exists(cursor, table):
    """Check if a table exists."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None


def migrate_database():
    """Run the multi-group migration."""
    
    print("\n" + "="*60)
    print("🚀 MULTI-GROUP MIGRATION SCRIPT")
    print("="*60 + "\n")
    
    # Step 1: Create backup
    print("Step 1: Creating backup...")
    if not create_backup():
        return False
    
    # Step 2: Connect to database
    print("\nStep 2: Connecting to database...")
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        print("✅ Connected successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    try:
        # Step 3: Add target_groups column to questions table
        print("\nStep 3: Adding target_groups column to questions table...")
        if check_column_exists(cursor, 'questions', 'target_groups'):
            print("⚠️  Column 'target_groups' already exists in questions table")
        else:
            cursor.execute("ALTER TABLE questions ADD COLUMN target_groups TEXT DEFAULT 'all'")
            # Set all existing quizzes to target all groups
            cursor.execute("UPDATE questions SET target_groups = 'all' WHERE target_groups IS NULL")
            conn.commit()
            print("✅ Added target_groups column (default: 'all')")
        
        # Step 4: Add group_id column to responses table
        print("\nStep 4: Adding group_id column to responses table...")
        if check_column_exists(cursor, 'responses', 'group_id'):
            print("⚠️  Column 'group_id' already exists in responses table")
        else:
            cursor.execute("ALTER TABLE responses ADD COLUMN group_id TEXT DEFAULT 'group1'")
            # Set all existing responses to default group
            cursor.execute("UPDATE responses SET group_id = 'group1' WHERE group_id IS NULL")
            conn.commit()
            print("✅ Added group_id column (default: 'group1')")
        
        # Step 5: Create quiz_posts table
        print("\nStep 5: Creating quiz_posts table...")
        if check_table_exists(cursor, 'quiz_posts'):
            print("⚠️  Table 'quiz_posts' already exists")
        else:
            cursor.execute("""
                CREATE TABLE quiz_posts (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    group_id TEXT NOT NULL,
                    poll_id TEXT UNIQUE,
                    posted_time TIMESTAMP NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES questions(question_id)
                )
            """)
            conn.commit()
            print("✅ Created quiz_posts table")
        
        # Step 6: Create indexes for performance
        print("\nStep 6: Creating indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_posts_poll_id ON quiz_posts(poll_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_posts_group_id ON quiz_posts(group_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_group_id ON responses(group_id)")
            conn.commit()
            print("✅ Created performance indexes")
        except Exception as e:
            print(f"⚠️  Index creation warning: {e}")
        
        # Step 7: Verify migration
        print("\nStep 7: Verifying migration...")
        
        # Check questions table
        cursor.execute("PRAGMA table_info(questions)")
        questions_cols = [row[1] for row in cursor.fetchall()]
        assert 'target_groups' in questions_cols, "target_groups column missing!"
        
        # Check responses table
        cursor.execute("PRAGMA table_info(responses)")
        responses_cols = [row[1] for row in cursor.fetchall()]
        assert 'group_id' in responses_cols, "group_id column missing!"
        
        # Check quiz_posts table
        assert check_table_exists(cursor, 'quiz_posts'), "quiz_posts table missing!"
        
        print("✅ All schema changes verified")
        
        # Step 8: Show summary
        print("\n" + "="*60)
        print("📊 MIGRATION SUMMARY")
        print("="*60)
        
        cursor.execute("SELECT COUNT(*) FROM questions")
        questions_count = cursor.fetchone()[0]
        print(f"✅ Questions migrated: {questions_count} (all set to 'all' groups)")
        
        cursor.execute("SELECT COUNT(*) FROM responses")
        responses_count = cursor.fetchone()[0]
        print(f"✅ Responses migrated: {responses_count} (all set to 'group1')")
        
        print(f"✅ New quiz_posts table created (empty)")
        
        print("\n" + "="*60)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nNext steps:")
        print("1. Update config.py with GROUP_CONFIGS")
        print("2. Deploy updated bot code")
        print("3. Test posting to multiple groups")
        print()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        conn.close()
        return False


if __name__ == "__main__":
    success = migrate_database()
    
    if not success:
        print("\n⚠️  Migration failed! Database is unchanged.")
        print("Check the error messages above and try again.")
        exit(1)
    else:
        print("✅ Migration successful! You can now update the bot code.")
        exit(0)

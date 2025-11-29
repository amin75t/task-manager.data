"""
Migration script to add data_version column to users table
Run this once to update the existing database schema
"""
import sqlite3
import os

DB_PATH = "./tasks.db"

def migrate():
    """Add data_version column to users table"""
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. No migration needed.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'data_version' in columns:
            print("✓ Column 'data_version' already exists. No migration needed.")
            return

        # Add the data_version column
        print("Adding 'data_version' column to users table...")
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN data_version INTEGER NOT NULL DEFAULT 0
        """)

        conn.commit()
        print("✓ Migration completed successfully!")
        print("  - Added 'data_version' column to users table")
        print("  - Default value: 0")

    except sqlite3.Error as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

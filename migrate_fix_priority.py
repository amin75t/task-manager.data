"""
Migration script to convert numeric proprietary values to enum strings
Run this to fix existing tasks with numeric priority values
"""
import sqlite3
import os

DB_PATH = "./tasks.db"

def migrate():
    """Convert numeric proprietary values to Priority enum strings"""
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. No migration needed.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get all tasks
        cursor.execute("SELECT id, proprietary FROM tasks")
        tasks = cursor.fetchall()

        if not tasks:
            print("No tasks found. No migration needed.")
            return

        updated_count = 0

        for task_id, proprietary in tasks:
            new_priority = None

            # Convert numeric values to enum strings
            try:
                numeric_value = float(proprietary)
                if numeric_value >= 8:
                    new_priority = "Urgent"
                elif numeric_value >= 6:
                    new_priority = "High"
                elif numeric_value >= 4:
                    new_priority = "Medium"
                else:
                    new_priority = "Low"

                cursor.execute(
                    "UPDATE tasks SET proprietary = ? WHERE id = ?",
                    (new_priority, task_id)
                )
                updated_count += 1
                print(f"  Task {task_id}: {proprietary} → {new_priority}")

            except (ValueError, TypeError):
                # Already a string (enum value), skip
                if proprietary not in ["Urgent", "High", "Medium", "Low"]:
                    # Invalid value, set to default
                    cursor.execute(
                        "UPDATE tasks SET proprietary = ? WHERE id = ?",
                        ("Low", task_id)
                    )
                    updated_count += 1
                    print(f"  Task {task_id}: {proprietary} → Low (invalid value)")

        conn.commit()

        if updated_count > 0:
            print(f"\n✓ Migration completed successfully!")
            print(f"  - Updated {updated_count} task(s)")
        else:
            print("✓ All tasks already have valid priority values. No changes needed.")

    except sqlite3.Error as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

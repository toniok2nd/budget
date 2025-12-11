import sqlite3
import os

DB_PATH = 'instance/app.db'

def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Adding last_login column...")
        cursor.execute("ALTER TABLE user ADD COLUMN last_login TIMESTAMP")
    except sqlite3.OperationalError as e:
        print(f"Skipping last_login: {e}")

    conn.commit()
    conn.close()
    print("Migration v2 complete.")

if __name__ == "__main__":
    run_migration()

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
        print("Adding is_admin column...")
        cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError as e:
        print(f"Skipping is_admin: {e}")

    try:
        print("Adding is_approved column...")
        cursor.execute("ALTER TABLE user ADD COLUMN is_approved BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError as e:
        print(f"Skipping is_approved: {e}")

    # Set existing users to approved=True and admin=False?
    # Or should we make the first user admin?
    # Let's just default to approved=False for safety, or Approved=True for existing users?
    # Requirement: "the cration o a new user must be validated". Implies EXISTING users might should be approved.
    # Let's Approve ALL existing users to avoid locking them out.
    print("Approving all existing users...")
    cursor.execute("UPDATE user SET is_approved = 1")
    
    # Check if any user exists, if so, make the first one admin? 
    # Or just leave manual admin assignment for now?
    # Plan said: "First registered user...".
    # Let's make user with ID 1 admin if they exist.
    print("Making user ID 1 admin...")
    cursor.execute("UPDATE user SET is_admin = 1 WHERE id = 1")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    run_migration()

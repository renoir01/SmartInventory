import sqlite3
import os

# Path to the database
DB_PATH = 'inventory.db'

def list_users():
    """List all users in the database"""
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            print("User table doesn't exist in the database")
            return
        
        # Get all users
        cursor.execute("SELECT id, username, role FROM user")
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the database")
            return
        
        print(f"Found {len(users)} users:")
        print("ID | Username | Role")
        print("-" * 30)
        for user in users:
            print(f"{user[0]} | {user[1]} | {user[2]}")
        
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Listing users from database...")
    list_users()

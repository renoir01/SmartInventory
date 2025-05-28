import sqlite3
import os
import hashlib
from werkzeug.security import generate_password_hash

# Path to the database
DB_PATH = 'inventory.db'

def update_user_password(username, password):
    """Update a user's password in the database"""
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the user exists
        cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"User {username} not found in the database")
            return False
        
        # Generate password hash using Werkzeug (same as Flask-Login)
        password_hash = generate_password_hash(password)
        
        # Update the user's password
        cursor.execute(
            "UPDATE user SET password_hash = ? WHERE username = ?",
            (password_hash, username)
        )
        
        conn.commit()
        print(f"Password updated for user: {username}")
        return True
        
    except Exception as e:
        print(f"Error updating password: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Updating user passwords...")
    
    # Update renoir01's password
    update_user_password('renoir01', 'Renoir@654')
    
    # Update epi's password
    update_user_password('epi', 'Epi@654')
    
    print("Password updates completed")

#!/usr/bin/env python3
"""
Fix schema mismatch between local and PythonAnywhere databases.
This script will update the local database schema to match the PythonAnywhere schema.
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

# Backup the current database
def backup_database(db_path):
    """Create a backup of the database before making changes"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        return False

# Main function to fix the schema
def fix_schema():
    """Update the local database schema to match PythonAnywhere"""
    # Database path
    db_path = "inventory.db"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    # Create backup
    if not backup_database(db_path):
        response = input("Failed to create backup. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Checking database schema...")
        
        # Check if sale table has the required columns
        cursor.execute("PRAGMA table_info(sale)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Add missing columns to sale table
        if 'is_cashed_out' not in columns:
            print("Adding is_cashed_out column to sale table")
            cursor.execute("ALTER TABLE sale ADD COLUMN is_cashed_out BOOLEAN DEFAULT 0")
        
        if 'cashout_id' not in columns:
            print("Adding cashout_id column to sale table")
            cursor.execute("ALTER TABLE sale ADD COLUMN cashout_id INTEGER")
        
        # Check if cashout table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cashout'")
        has_cashout_table = cursor.fetchone() is not None
        
        # Check if cashout_record table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cashout_record'")
        has_cashout_record_table = cursor.fetchone() is not None
        
        # Create cashout table if it doesn't exist
        if not has_cashout_table:
            print("Creating cashout table")
            cursor.execute("""
            CREATE TABLE cashout (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cashier_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                amount FLOAT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                note TEXT
            )
            """)
        
        # If cashout_record exists but cashout doesn't, migrate the data
        if has_cashout_record_table and has_cashout_table:
            print("Migrating data from cashout_record to cashout")
            try:
                # Get data from cashout_record
                cursor.execute("""
                SELECT cashed_out_by, cashed_out_by, total_amount, cashed_out_at, notes
                FROM cashout_record
                """)
                records = cursor.fetchall()
                
                # Insert into cashout table
                for record in records:
                    cursor.execute("""
                    INSERT INTO cashout (cashier_id, admin_id, amount, date, note)
                    VALUES (?, ?, ?, ?, ?)
                    """, record)
                
                print(f"Migrated {len(records)} records from cashout_record to cashout")
            except Exception as e:
                print(f"Error migrating data: {str(e)}")
        
        # Commit changes
        conn.commit()
        print("Schema update completed successfully")
        
        # Verify the changes
        print("\nVerifying updated schema:")
        cursor.execute("PRAGMA table_info(sale)")
        print("Sale table columns:")
        for col in cursor.fetchall():
            print(f"  - {col[1]} ({col[2]})")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        print("\nTables in database:")
        for table in cursor.fetchall():
            print(f"  - {table[0]}")
        
        return True
    
    except Exception as e:
        print(f"Error updating schema: {str(e)}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Schema Mismatch Fix Tool")
    print("========================")
    
    if fix_schema():
        print("\nSchema update completed. Your local database should now be compatible with PythonAnywhere.")
    else:
        print("\nFailed to update schema. Please check the errors above.")

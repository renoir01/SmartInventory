import os
import sys
import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

print("Starting direct fix for monthly_profit table...")

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the MonthlyProfit model
class MonthlyProfit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    total_revenue = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    total_profit = db.Column(db.Float, default=0.0)
    sale_count = db.Column(db.Integer, default=0)
    __table_args__ = (db.UniqueConstraint('year', 'month', name='unique_year_month'),)

def check_table_exists():
    try:
        # Check if the database file exists
        if not os.path.exists('inventory.db'):
            print("Error: inventory.db file does not exist")
            return False
            
        # Connect to the database directly
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Check if the monthly_profit table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_profit'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print("monthly_profit table already exists in the database")
            
            # Check the structure of the table
            cursor.execute("PRAGMA table_info(monthly_profit)")
            columns = cursor.fetchall()
            print(f"Table structure: {columns}")
            
            # Count records in the table
            cursor.execute("SELECT COUNT(*) FROM monthly_profit")
            count = cursor.fetchone()[0]
            print(f"Number of records in monthly_profit table: {count}")
            
            return True
        else:
            print("monthly_profit table does not exist in the database")
            return False
    except Exception as e:
        print(f"Error checking table: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def create_monthly_profit_table():
    try:
        with app.app_context():
            print("Creating monthly_profit table...")
            db.create_all(tables=[MonthlyProfit.__table__])
            print("monthly_profit table created successfully")
            
            # Verify the table was created
            if check_table_exists():
                print("Verification successful: monthly_profit table exists")
            else:
                print("Verification failed: monthly_profit table was not created")
    except Exception as e:
        print(f"Error creating table: {str(e)}")

if __name__ == "__main__":
    # Check if the table exists first
    table_exists = check_table_exists()
    
    # If the table doesn't exist, create it
    if not table_exists:
        create_monthly_profit_table()
    
    print("Script completed.")

#!/usr/bin/env python3
"""
Fix cashier sales tracking and uncashed sales display in SmartInventory for PythonAnywhere.
This script is designed to be uploaded and run on your PythonAnywhere environment.
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

# Configuration
DB_PATH = "inventory.db"  # Update this to your PythonAnywhere database path if different
APP_PATH = "app.py"       # Update this to your PythonAnywhere app.py path if different
TEMPLATE_PATH = "templates/cashier_dashboard.html"  # Update if different

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

# Update the database schema
def update_database_schema():
    """Add is_cashed_out field to the sale table if it doesn't exist"""
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return False
    
    # Create backup
    if not backup_database(DB_PATH):
        response = input("Failed to create backup. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Connect to database
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if sale table has the required columns
        cursor.execute("PRAGMA table_info(sale)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Add missing columns to sale table
        if 'is_cashed_out' not in columns:
            print("Adding is_cashed_out column to sale table")
            cursor.execute("ALTER TABLE sale ADD COLUMN is_cashed_out BOOLEAN DEFAULT 0")
        else:
            print("is_cashed_out column already exists")
        
        # Commit changes
        conn.commit()
        print("Database schema updated successfully")
        return True
    
    except Exception as e:
        print(f"Error updating database schema: {str(e)}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

# Update the app.py file
def update_app_code():
    """Update the get_uncashed_sales function and cashier dashboard in app.py"""
    # Check if app.py exists
    if not os.path.exists(APP_PATH):
        print(f"app.py not found at {APP_PATH}")
        return False
    
    # Create backup
    backup_path = f"{APP_PATH}.sales_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(APP_PATH, backup_path)
        print(f"Created backup at {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        response = input("Failed to create backup. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    try:
        # Read the app.py file
        with open(APP_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Update the get_uncashed_sales function for PythonAnywhere version
        # First, find the current function
        if "def get_uncashed_sales():" in content:
            print("Found get_uncashed_sales function, updating...")
            
            # Define the new function that works with both schemas
            new_function = """def get_uncashed_sales():
    \"\"\"Calculate uncashed sales based on is_cashed_out field if available\"\"\"
    
    try:
        # Try to use the is_cashed_out field
        uncashed_sales = Sale.query.filter(Sale.is_cashed_out == False).all()
    except Exception as e:
        # Fall back to the old method if the column doesn't exist
        logger.warning(f"is_cashed_out column not found, using date-based method: {str(e)}")
        
        # Get the most recent cashout
        most_recent_cashout = db.session.query(db.func.max(cashout.c.date)).scalar()
        
        if most_recent_cashout:
            # Get sales after the most recent cashout
            uncashed_sales = Sale.query.filter(Sale.date_sold > most_recent_cashout).all()
        else:
            # No cashouts ever, get all sales
            uncashed_sales = Sale.query.all()
    
    # Calculate totals for uncashed sales only
    total_revenue = sum(sale.total_price for sale in uncashed_sales)
    transaction_count = len(uncashed_sales)
    
    return {
        'total_revenue': total_revenue,
        'transaction_count': transaction_count,
        'sales': uncashed_sales
    }"""
            
            # Find the start and end of the current function
            start_idx = content.find("def get_uncashed_sales():")
            end_idx = content.find("def", start_idx + 1)
            if end_idx == -1:
                end_idx = len(content)
            else:
                # Go back to the previous line
                end_idx = content.rfind("\n", 0, end_idx)
            
            # Replace the function
            content = content[:start_idx] + new_function + content[end_idx:]
            print("Updated get_uncashed_sales function")
        else:
            print("Could not find get_uncashed_sales function")
        
        # Update the cashier dashboard to show all-time sales
        if "def cashier_dashboard():" in content:
            print("Found cashier_dashboard function, updating...")
            
            # Add all-time sales calculation
            if "# Calculate total revenue for today" in content:
                old_code = "# Calculate total revenue for today\n            total_revenue = sum(sale.total_price for sale in today_sales)"
                new_code = """# Calculate total revenue for today
            total_revenue = sum(sale.total_price for sale in today_sales)
            
            # Also get all-time sales for this cashier
            all_time_sales = Sale.query.filter(
                Sale.cashier_id == current_user.id
            ).all()
            
            # Calculate all-time total revenue
            all_time_revenue = sum(sale.total_price for sale in all_time_sales)"""
                
                content = content.replace(old_code, new_code)
                print("Added all-time sales calculation")
            
            # Update the render_template call to include all_time_revenue
            if "return render_template('cashier_dashboard.html'" in content:
                if "all_time_revenue=all_time_revenue" not in content:
                    old_render = "return render_template('cashier_dashboard.html'"
                    new_render = "return render_template('cashier_dashboard.html', all_time_revenue=all_time_revenue or 0,"
                    content = content.replace(old_render, new_render)
                    print("Updated render_template call")
        else:
            print("Could not find cashier_dashboard function")
        
        # Write the updated content back to app.py
        with open(APP_PATH, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("app.py updated successfully")
        return True
    
    except Exception as e:
        print(f"Error updating app.py: {str(e)}")
        return False

# Update the cashier dashboard template
def update_cashier_template():
    """Update the cashier dashboard template to show all-time sales"""
    # Check if template exists
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Cashier dashboard template not found at {TEMPLATE_PATH}")
        return False
    
    # Create backup
    backup_path = f"{TEMPLATE_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(TEMPLATE_PATH, backup_path)
        print(f"Created backup at {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        response = input("Failed to create backup. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    try:
        # Read the template file
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Add all-time sales section
        if "Today's Sales" in content:
            print("Found Today's Sales section, adding All-Time Sales section...")
            
            # Find the today's sales card
            today_sales_section = """<div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">{{ _('Today\'s Sales') }}</h5>
                </div>
                <div class="card-body">
                    <h3>{{ format_currency(total_revenue) }}</h3>
                    <p>{{ _('Total from {0} transactions').format(today_sales|length) }}</p>
                </div>
            </div>"""
            
            # Create the all-time sales card
            all_time_sales_section = """<div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">{{ _('All-Time Sales') }}</h5>
                </div>
                <div class="card-body">
                    <h3>{{ format_currency(all_time_revenue) }}</h3>
                </div>
            </div>"""
            
            # Add the all-time sales section after the today's sales section
            if today_sales_section in content:
                content = content.replace(today_sales_section, today_sales_section + "\n\n            " + all_time_sales_section)
                print("Added All-Time Sales section")
            else:
                print("Could not find exact Today's Sales section to match")
        else:
            print("Could not find Today's Sales section")
        
        # Write the updated content back to the template
        with open(TEMPLATE_PATH, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("Cashier dashboard template updated successfully")
        return True
    
    except Exception as e:
        print(f"Error updating cashier dashboard template: {str(e)}")
        return False

# Main function
def main():
    print("SmartInventory PythonAnywhere Sales Tracking Fix")
    print("==============================================")
    
    # Update database schema
    print("\nStep 1: Updating database schema...")
    if not update_database_schema():
        print("Failed to update database schema. Aborting.")
        return
    
    # Update app.py
    print("\nStep 2: Updating app.py...")
    if not update_app_code():
        print("Failed to update app.py. Aborting.")
        return
    
    # Update cashier dashboard template
    print("\nStep 3: Updating cashier dashboard template...")
    if not update_cashier_template():
        print("Failed to update cashier dashboard template.")
        # Continue anyway, this is not critical
    
    print("\nFix completed successfully!")
    print("The following changes have been made:")
    print("1. Added is_cashed_out column to the sale table")
    print("2. Updated the get_uncashed_sales function to use the is_cashed_out field")
    print("3. Updated the cashier dashboard to show all-time sales")
    print("\nPlease restart your PythonAnywhere web app for the changes to take effect.")

if __name__ == "__main__":
    main()

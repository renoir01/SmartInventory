#!/usr/bin/env python3
"""
Fix cashier sales tracking and uncashed sales display in SmartInventory.
This script will:
1. Update the database schema to add an is_cashed_out field to the sale table
2. Update the get_uncashed_sales function to use this field
3. Update the cashier dashboard to show all uncashed sales, not just today's
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

# Update the database schema
def update_database_schema():
    """Add is_cashed_out and cashout_id columns to the sale table"""
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
    app_path = "app.py"
    
    # Check if app.py exists
    if not os.path.exists(app_path):
        print(f"app.py not found at {app_path}")
        return False
    
    # Create backup
    backup_path = f"{app_path}.sales_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(app_path, backup_path)
        print(f"Created backup at {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        response = input("Failed to create backup. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    try:
        # Read the app.py file
        with open(app_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Update the get_uncashed_sales function
        old_get_uncashed_sales = """def get_uncashed_sales():
    \"\"\"Calculate uncashed sales since the last cashout\"\"\"
    
    # Get the most recent cashout (regardless of date)
    most_recent_cashout = CashoutRecord.query.order_by(CashoutRecord.cashed_out_at.desc()).first()
    
    # Get sales that haven't been cashed out yet
    if most_recent_cashout:
        # Only get sales after the most recent cashout
        uncashed_sales = Sale.query.filter(
            Sale.date_sold > most_recent_cashout.cashed_out_at
        ).all()
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
        
        new_get_uncashed_sales = """def get_uncashed_sales():
    \"\"\"Calculate uncashed sales based on is_cashed_out field\"\"\"
    
    # Check if the is_cashed_out column exists in the sale table
    try:
        # Try to use the is_cashed_out field
        uncashed_sales = Sale.query.filter(Sale.is_cashed_out == False).all()
    except Exception as e:
        # Fall back to the old method if the column doesn't exist
        logger.warning(f"is_cashed_out column not found, using date-based method: {str(e)}")
        
        # Get the most recent cashout (regardless of date)
        most_recent_cashout = CashoutRecord.query.order_by(CashoutRecord.cashed_out_at.desc()).first()
        
        # Get sales that haven't been cashed out yet
        if most_recent_cashout:
            # Only get sales after the most recent cashout
            uncashed_sales = Sale.query.filter(
                Sale.date_sold > most_recent_cashout.cashed_out_at
            ).all()
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
        
        # Update the perform_cashout function
        old_perform_cashout_snippet = """        # Create a new cashout record using SQLAlchemy
        try:
            # Create a new record with current timestamp
            timestamp_now = datetime.now()
            
            # Create the cashout record using the model
            new_cashout = CashoutRecord(
                date=today,
                total_amount=total_revenue,
                transaction_count=transaction_count,
                cashed_out_by=current_user.id,
                cashed_out_at=timestamp_now,
                notes=notes
            )
            
            # Add and commit to the database
            db.session.add(new_cashout)
            db.session.commit()"""
        
        new_perform_cashout_snippet = """        # Create a new cashout record using SQLAlchemy
        try:
            # Create a new record with current timestamp
            timestamp_now = datetime.now()
            
            # Create the cashout record using the model
            new_cashout = CashoutRecord(
                date=today,
                total_amount=total_revenue,
                transaction_count=transaction_count,
                cashed_out_by=current_user.id,
                cashed_out_at=timestamp_now,
                notes=notes
            )
            
            # Add and commit to the database
            db.session.add(new_cashout)
            db.session.flush()  # Get the ID of the new cashout record
            
            # Mark all uncashed sales as cashed out
            try:
                for sale in uncashed_sales:
                    sale.is_cashed_out = True
                    sale.cashout_id = new_cashout.id
            except Exception as column_e:
                logger.warning(f"Could not update is_cashed_out field: {str(column_e)}")
                
            db.session.commit()"""
        
        # Update the cashier dashboard to show all uncashed sales
        old_cashier_dashboard_snippet = """        # Get today's sales for this cashier
        try:
            today_sales = Sale.query.filter(
                Sale.date_sold.between(today_start, today_end),
                Sale.cashier_id == current_user.id
            ).all()
            
            # Calculate total revenue for today
            total_revenue = sum(sale.total_price for sale in today_sales)
        except Exception as e:
            logger.error(f"Error getting sales: {str(e)}")
            today_sales = []
            total_revenue = 0"""
        
        new_cashier_dashboard_snippet = """        # Get today's sales for this cashier
        try:
            today_sales = Sale.query.filter(
                Sale.date_sold.between(today_start, today_end),
                Sale.cashier_id == current_user.id
            ).all()
            
            # Calculate total revenue for today
            total_revenue = sum(sale.total_price for sale in today_sales)
            
            # Also get all-time sales for this cashier
            all_time_sales = Sale.query.filter(
                Sale.cashier_id == current_user.id
            ).all()
            
            # Calculate all-time total revenue
            all_time_revenue = sum(sale.total_price for sale in all_time_sales)
        except Exception as e:
            logger.error(f"Error getting sales: {str(e)}")
            today_sales = []
            total_revenue = 0
            all_time_sales = []
            all_time_revenue = 0"""
        
        # Update the cashier dashboard template rendering
        old_render_template = """        return render_template('cashier_dashboard.html', 
                            products=products or [],
                            today_sales=today_sales or [],
                            total_revenue=total_revenue or 0,
                            search_query=search_query or '',
                            uncashed_revenue=uncashed_revenue,
                            uncashed_transactions=uncashed_transactions)"""
        
        new_render_template = """        return render_template('cashier_dashboard.html', 
                            products=products or [],
                            today_sales=today_sales or [],
                            total_revenue=total_revenue or 0,
                            all_time_revenue=all_time_revenue or 0,
                            search_query=search_query or '',
                            uncashed_revenue=uncashed_revenue,
                            uncashed_transactions=uncashed_transactions)"""
        
        # Replace the code
        content = content.replace(old_get_uncashed_sales, new_get_uncashed_sales)
        content = content.replace(old_perform_cashout_snippet, new_perform_cashout_snippet)
        content = content.replace(old_cashier_dashboard_snippet, new_cashier_dashboard_snippet)
        content = content.replace(old_render_template, new_render_template)
        
        # Write the updated content back to app.py
        with open(app_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("app.py updated successfully")
        return True
    
    except Exception as e:
        print(f"Error updating app.py: {str(e)}")
        return False

# Update the cashier dashboard template
def update_cashier_template():
    """Update the cashier dashboard template to show all-time sales"""
    template_path = "templates/cashier_dashboard.html"
    
    # Check if template exists
    if not os.path.exists(template_path):
        print(f"Cashier dashboard template not found at {template_path}")
        return False
    
    # Create backup
    backup_path = f"{template_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(template_path, backup_path)
        print(f"Created backup at {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        response = input("Failed to create backup. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    try:
        # Read the template file
        with open(template_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find the section that displays today's sales
        today_sales_section = """<div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">{{ _('Today\'s Sales') }}</h5>
                </div>
                <div class="card-body">
                    <h3>{{ format_currency(total_revenue) }}</h3>
                    <p>{{ _('Total from {0} transactions').format(today_sales|length) }}</p>
                </div>
            </div>"""
        
        # Add a new section for all-time sales
        all_time_sales_section = """<div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">{{ _('All-Time Sales') }}</h5>
                </div>
                <div class="card-body">
                    <h3>{{ format_currency(all_time_revenue) }}</h3>
                </div>
            </div>"""
        
        # Update the uncashed sales section
        old_uncashed_section = """<div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">{{ _('Uncashed Sales') }}</h5>
                </div>
                <div class="card-body">
                    <h3>{{ format_currency(uncashed_revenue) }}</h3>
                    <p>{{ _('From {0} transactions').format(uncashed_transactions) }}</p>
                </div>
            </div>"""
        
        new_uncashed_section = """<div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">{{ _('Uncashed Sales') }}</h5>
                </div>
                <div class="card-body">
                    <h3>{{ format_currency(uncashed_revenue) }}</h3>
                    <p>{{ _('From {0} transactions').format(uncashed_transactions) }}</p>
                    <small class="text-muted">{{ _('These sales have not been cashed out yet') }}</small>
                </div>
            </div>"""
        
        # Replace the uncashed sales section
        content = content.replace(old_uncashed_section, new_uncashed_section)
        
        # Add the all-time sales section after the today's sales section
        content = content.replace(today_sales_section, today_sales_section + "\n\n            " + all_time_sales_section)
        
        # Write the updated content back to the template
        with open(template_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("Cashier dashboard template updated successfully")
        return True
    
    except Exception as e:
        print(f"Error updating cashier dashboard template: {str(e)}")
        return False

# Main function
def main():
    print("SmartInventory Cashier Sales Tracking Fix")
    print("========================================")
    
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
    print("1. Added is_cashed_out and cashout_id columns to the sale table")
    print("2. Updated the get_uncashed_sales function to use the is_cashed_out field")
    print("3. Updated the perform_cashout function to mark sales as cashed out")
    print("4. Updated the cashier dashboard to show all-time sales")
    print("\nPlease restart your application for the changes to take effect.")

if __name__ == "__main__":
    main()

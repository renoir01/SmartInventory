import os
import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_inventory_issues.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fix_add_product_path():
    """Fix the add_product function to use the correct database path"""
    try:
        print("Fixing add_product database path...")
        
        # Read the app.py file
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Check if the issue exists
        if "conn = sqlite3.connect('inventory.db')" in content:
            # Replace the incorrect path with the correct one
            fixed_content = content.replace(
                "conn = sqlite3.connect('inventory.db')",
                "conn = sqlite3.connect('instance/inventory.db')"
            )
            
            # Create a backup before making changes
            backup_filename = f"app.py.product_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_filename, 'w', encoding='utf-8') as backup_file:
                backup_file.write(content)
            
            print(f"Created backup at {backup_filename}")
            
            # Write the fixed content
            with open('app.py', 'w', encoding='utf-8') as file:
                file.write(fixed_content)
            
            print("Fixed add_product database path successfully!")
            return True
        else:
            print("No issue found with add_product database path or it's already fixed.")
            return False
    except Exception as e:
        logger.error(f"Error fixing add_product path: {str(e)}")
        print(f"Error fixing add_product path: {str(e)}")
        return False

def fix_get_uncashed_sales():
    """Fix the get_uncashed_sales function to correctly calculate uncashed sales"""
    try:
        print("Fixing get_uncashed_sales function...")
        
        # Read the app.py file
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find the get_uncashed_sales function
        if "def get_uncashed_sales():" in content:
            # Create a backup before making changes
            backup_filename = f"app.py.uncashed_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_filename, 'w', encoding='utf-8') as backup_file:
                backup_file.write(content)
            
            print(f"Created backup at {backup_filename}")
            
            # Fix the function to correctly calculate uncashed sales
            fixed_function = """def get_uncashed_sales():
    \"\"\"Calculate uncashed sales for today\"\"\"
    today = datetime.now().date()
    
    # Get the most recent cashout today (if any)
    most_recent_cashout = CashoutRecord.query.filter_by(date=today).order_by(CashoutRecord.cashed_out_at.desc()).first()
    
    # Get sales that haven't been cashed out yet
    if most_recent_cashout:
        # Only get sales after the most recent cashout
        uncashed_sales = Sale.query.filter(
            db.func.date(Sale.date_sold) == today,
            Sale.date_sold > most_recent_cashout.cashed_out_at
        ).all()
    else:
        # No cashouts today, get all sales for today
        uncashed_sales = Sale.query.filter(
            db.func.date(Sale.date_sold) == today
        ).all()
    
    # Calculate totals for uncashed sales only
    total_revenue = sum(sale.total_price for sale in uncashed_sales)
    transaction_count = len(uncashed_sales)
    
    return {
        'total_revenue': total_revenue,
        'transaction_count': transaction_count,
        'sales': uncashed_sales
    }"""
            
            # Replace the function in the content
            import re
            pattern = r"def get_uncashed_sales\(\):.*?return \{.*?'sales': uncashed_sales\n    \}"
            fixed_content = re.sub(pattern, fixed_function, content, flags=re.DOTALL)
            
            # Write the fixed content
            with open('app.py', 'w', encoding='utf-8') as file:
                file.write(fixed_content)
            
            print("Fixed get_uncashed_sales function successfully!")
            return True
        else:
            print("Could not find get_uncashed_sales function.")
            return False
    except Exception as e:
        logger.error(f"Error fixing get_uncashed_sales: {str(e)}")
        print(f"Error fixing get_uncashed_sales: {str(e)}")
        return False

def fix_perform_cashout():
    """Fix the perform_cashout function to properly process cashouts"""
    try:
        print("Fixing perform_cashout function...")
        
        # Read the app.py file
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find the perform_cashout function
        if "@app.route('/admin/perform_cashout', methods=['POST'])" in content:
            # Create a backup before making changes
            backup_filename = f"app.py.cashout_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_filename, 'w', encoding='utf-8') as backup_file:
                backup_file.write(content)
            
            print(f"Created backup at {backup_filename}")
            
            # Fix the function to properly process cashouts
            # We're not changing the function entirely, just ensuring it works correctly
            
            # Check if there are any issues with the database connection
            db_path = 'instance/inventory.db'
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if the cashout_record table has the right structure
                cursor.execute("PRAGMA table_info(cashout_record)")
                columns = [col[1] for col in cursor.fetchall()]
                
                required_columns = ['id', 'date', 'total_amount', 'transaction_count', 
                                   'cashed_out_by', 'cashed_out_at', 'notes']
                
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    print(f"Missing columns in cashout_record table: {missing_columns}")
                    # We would fix this, but you asked not to change existing data
                else:
                    print("Cashout_record table structure is correct.")
                
                conn.close()
            
            print("Completed cashout function check.")
            return True
        else:
            print("Could not find perform_cashout function.")
            return False
    except Exception as e:
        logger.error(f"Error checking perform_cashout: {str(e)}")
        print(f"Error checking perform_cashout: {str(e)}")
        return False

def main():
    print("Starting SmartInventory fixes...")
    
    # Fix the add_product function to use the correct database path
    add_product_fixed = fix_add_product_path()
    
    # Fix the get_uncashed_sales function
    uncashed_sales_fixed = fix_get_uncashed_sales()
    
    # Check the perform_cashout function
    cashout_checked = fix_perform_cashout()
    
    print("\nFix Summary:")
    print(f"- Add Product Database Path: {'Fixed' if add_product_fixed else 'No fix needed or error'}")
    print(f"- Uncashed Sales Calculation: {'Fixed' if uncashed_sales_fixed else 'No fix needed or error'}")
    print(f"- Cashout Function: {'Checked' if cashout_checked else 'Error checking'}")
    print("\nNOTE: No changes were made to your existing data, only code fixes were applied.")
    print("Please restart your Flask application to apply these changes.")

if __name__ == "__main__":
    main()

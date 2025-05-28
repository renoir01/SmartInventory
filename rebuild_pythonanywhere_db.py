import sqlite3
import os
import sys
import shutil
from datetime import datetime
import re

# Path to the database
DB_PATH = 'inventory.db'

def backup_database():
    """Create a backup of the current database"""
    if os.path.exists(DB_PATH):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{DB_PATH}.backup_{timestamp}"
        try:
            shutil.copy2(DB_PATH, backup_path)
            print(f"Created database backup at {backup_path}")
            return True
        except Exception as e:
            print(f"Failed to create database backup: {e}")
            return False
    return True  # No database to backup

def parse_log_data(log_data):
    """Parse the log data to extract sales information"""
    sales_data = {}
    cashier_data = {}
    
    # Extract sales information
    sales_pattern = r"Today's sales: (\d+), revenue: RWF (\d+\.\d+)"
    for match in re.finditer(sales_pattern, log_data):
        count = int(match.group(1))
        revenue = float(match.group(2))
        if count > 0:
            sales_data[count] = revenue
    
    # Extract cashier information
    cashier_pattern = r"Cashier (\w+): (\d+) sales, total: RWF (\d+\.\d+)"
    for match in re.finditer(cashier_pattern, log_data):
        cashier = match.group(1)
        count = int(match.group(2))
        total = float(match.group(3))
        if cashier not in cashier_data or count > cashier_data[cashier]['count']:
            cashier_data[cashier] = {'count': count, 'total': total}
    
    # Extract product names
    product_names = set()
    product_pattern = r"units of ([^\\n]+)"
    for match in re.finditer(product_pattern, log_data):
        product_name = match.group(1).strip()
        if product_name:
            product_names.add(product_name)
    
    return {
        'sales_data': sales_data,
        'cashier_data': cashier_data,
        'product_names': product_names
    }

def rebuild_database(log_data=None):
    """Rebuild the database with the correct schema and restore data from logs if available"""
    # Create a backup first
    backup_database()
    
    try:
        # Connect to the database (will create it if it doesn't exist)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create the user table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create the product table with all required columns
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            purchase_price REAL DEFAULT 0,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            low_stock_threshold INTEGER DEFAULT 5,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_packaged BOOLEAN DEFAULT 0,
            units_per_package INTEGER DEFAULT 1,
            individual_price REAL DEFAULT 0,
            individual_stock INTEGER DEFAULT 0
        )
        ''')
        
        # Create the sale table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            profit REAL,
            cashier_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES product (id),
            FOREIGN KEY (cashier_id) REFERENCES user (id)
        )
        ''')
        
        # Create the monthly_profit table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_profit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            total_revenue REAL NOT NULL,
            total_profit REAL NOT NULL,
            total_cost REAL DEFAULT 0,
            sale_count INTEGER DEFAULT 0,
            date_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(month, year)
        )
        ''')
        
        # Create the cashout_record table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cashout_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cashier_id INTEGER,
            admin_id INTEGER,
            note TEXT,
            FOREIGN KEY (cashier_id) REFERENCES user (id),
            FOREIGN KEY (admin_id) REFERENCES user (id)
        )
        ''')
        
        # Check if admin user exists
        cursor.execute("SELECT * FROM user WHERE username = 'renoir01'")
        admin_exists = cursor.fetchone()
        
        # Add admin user if it doesn't exist
        if not admin_exists:
            from werkzeug.security import generate_password_hash
            admin_password = generate_password_hash('Renoir@654')
            cursor.execute(
                "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
                ('renoir01', admin_password, 'admin')
            )
            print("Created admin user: renoir01 with password: Renoir@654")
        
        # Check if cashier user exists
        cursor.execute("SELECT * FROM user WHERE username = 'epi'")
        cashier_exists = cursor.fetchone()
        
        # Add cashier user if it doesn't exist
        if not cashier_exists:
            from werkzeug.security import generate_password_hash
            cashier_password = generate_password_hash('Epi@654')
            cursor.execute(
                "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
                ('epi', cashier_password, 'cashier')
            )
            print("Created cashier user: epi with password: Epi@654")
        
        # If log data is provided, try to restore products from it
        if log_data:
            parsed_data = parse_log_data(log_data)
            product_names = parsed_data['product_names']
            
            # Add products from the log data
            if product_names:
                print(f"Found {len(product_names)} product names in logs")
                for name in product_names:
                    # Check if product already exists
                    cursor.execute("SELECT id FROM product WHERE name = ?", (name,))
                    if not cursor.fetchone():
                        # Add the product with default values
                        cursor.execute('''
                        INSERT INTO product (name, description, category, purchase_price, price, stock, low_stock_threshold)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (name, '', 'Unknown', 20.0, 50.0, 10, 5))
                        print(f"Added product: {name}")
            
            # Add sample products if no products were found in logs
            if not product_names:
                # Sample products
                sample_products = [
                    ('Milkway', 'Chocolate bar', 'Sweets', 23.0, 50.0, 12, 10),
                    ('Rice', 'Premium quality rice', 'Grains', 20.0, 35.0, 100, 20),
                    ('Beans', 'Fresh beans', 'Grains', 15.0, 25.0, 80, 15),
                    ('Sugar', 'White sugar', 'Groceries', 10.0, 18.0, 120, 30),
                    ('Salt', 'Iodized salt', 'Groceries', 5.0, 8.0, 150, 40),
                    ('Cooking Oil', 'Vegetable cooking oil', 'Groceries', 30.0, 45.0, 50, 10)
                ]
                
                for product in sample_products:
                    cursor.execute('''
                    INSERT INTO product (name, description, category, purchase_price, price, stock, low_stock_threshold)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', product)
                
                print(f"Added {len(sample_products)} sample products")
        else:
            # Add sample products if no log data is provided
            sample_products = [
                ('Milkway', 'Chocolate bar', 'Sweets', 23.0, 50.0, 12, 10),
                ('Rice', 'Premium quality rice', 'Grains', 20.0, 35.0, 100, 20),
                ('Beans', 'Fresh beans', 'Grains', 15.0, 25.0, 80, 15),
                ('Sugar', 'White sugar', 'Groceries', 10.0, 18.0, 120, 30),
                ('Salt', 'Iodized salt', 'Groceries', 5.0, 8.0, 150, 40),
                ('Cooking Oil', 'Vegetable cooking oil', 'Groceries', 30.0, 45.0, 50, 10)
            ]
            
            for product in sample_products:
                cursor.execute('''
                INSERT INTO product (name, description, category, purchase_price, price, stock, low_stock_threshold)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', product)
            
            print(f"Added {len(sample_products)} sample products")
        
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        
        print("Database rebuilt successfully")
        return True
    except Exception as e:
        print(f"Error rebuilding database: {e}")
        return False

def main():
    """Main function"""
    print("Rebuilding PythonAnywhere database...")
    
    # Ask if log data is available
    log_input = input("Do you have log data to parse? (y/n): ")
    
    if log_input.lower() == 'y':
        log_file = input("Enter the path to the log file (or paste log data directly and end with Ctrl+D or Ctrl+Z): ")
        
        log_data = ""
        if os.path.exists(log_file):
            # Read from file
            with open(log_file, 'r') as f:
                log_data = f.read()
        else:
            # Read from stdin
            print("Enter log data (end with Ctrl+D on Unix or Ctrl+Z on Windows):")
            log_data = log_file + "\n"
            try:
                while True:
                    line = input()
                    log_data += line + "\n"
            except EOFError:
                pass
        
        rebuild_database(log_data)
    else:
        rebuild_database()

if __name__ == "__main__":
    main()

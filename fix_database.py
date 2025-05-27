import sqlite3
import os
import json
from datetime import datetime
from app import app, db, Product, Sale, User, MonthlyProfit

def backup_database():
    """Create a backup of the current database"""
    db_path = 'new_inventory.db'
    backup_path = f'new_inventory_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    if os.path.exists(db_path):
        # Copy the database file
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"Database backup created at {backup_path}")
        return True
    else:
        print(f"Database file {db_path} not found. No backup created.")
        return False

def export_data():
    """Export all data from the database to JSON files"""
    conn = sqlite3.connect('new_inventory.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Export users
    cursor.execute("SELECT * FROM user")
    users = [dict(row) for row in cursor.fetchall()]
    with open('users_backup.json', 'w') as f:
        json.dump(users, f, indent=2)
    print(f"Exported {len(users)} users")
    
    # Export products
    cursor.execute("SELECT * FROM product")
    products = [dict(row) for row in cursor.fetchall()]
    with open('products_backup.json', 'w') as f:
        json.dump(products, f, indent=2)
    print(f"Exported {len(products)} products")
    
    # Export sales
    cursor.execute("SELECT * FROM sale")
    sales = [dict(row) for row in cursor.fetchall()]
    with open('sales_backup.json', 'w') as f:
        json.dump(sales, f, indent=2)
    print(f"Exported {len(sales)} sales")
    
    conn.close()
    return True

def recreate_database():
    """Recreate the database with the correct schema"""
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables with updated schema...")
        db.create_all()
        
        print("Database tables recreated successfully.")
        return True

def import_data():
    """Import data from JSON files back into the database"""
    with app.app_context():
        # Import users
        try:
            with open('users_backup.json', 'r') as f:
                users = json.load(f)
            
            for user_data in users:
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    password_hash=user_data['password_hash'],
                    role=user_data['role']
                )
                db.session.add(user)
            
            db.session.commit()
            print(f"Imported {len(users)} users")
        except Exception as e:
            print(f"Error importing users: {str(e)}")
            db.session.rollback()
        
        # Import products
        try:
            with open('products_backup.json', 'r') as f:
                products = json.load(f)
            
            for product_data in products:
                product = Product(
                    id=product_data['id'],
                    name=product_data['name'],
                    description=product_data.get('description', ''),
                    category=product_data.get('category', 'Uncategorized'),
                    purchase_price=product_data.get('purchase_price', 0),
                    price=product_data['price'],
                    stock=product_data.get('stock', 0),
                    low_stock_threshold=product_data.get('low_stock_threshold', 10),
                    date_added=datetime.fromisoformat(product_data['date_added']) if 'date_added' in product_data and product_data['date_added'] else datetime.utcnow(),
                    # New fields with default values
                    is_packaged=False,
                    units_per_package=1,
                    individual_price=0,
                    individual_stock=0
                )
                db.session.add(product)
            
            db.session.commit()
            print(f"Imported {len(products)} products")
        except Exception as e:
            print(f"Error importing products: {str(e)}")
            db.session.rollback()
        
        # Import sales
        try:
            with open('sales_backup.json', 'r') as f:
                sales = json.load(f)
            
            for sale_data in sales:
                sale = Sale(
                    id=sale_data['id'],
                    product_id=sale_data['product_id'],
                    quantity=sale_data['quantity'],
                    total_price=sale_data['total_price'],
                    cashier_id=sale_data['cashier_id'],
                    date_sold=datetime.fromisoformat(sale_data['date_sold']) if 'date_sold' in sale_data and sale_data['date_sold'] else datetime.utcnow()
                )
                db.session.add(sale)
            
            db.session.commit()
            print(f"Imported {len(sales)} sales")
        except Exception as e:
            print(f"Error importing sales: {str(e)}")
            db.session.rollback()
        
        return True

def calculate_monthly_profits():
    """Calculate monthly profits from sales data"""
    with app.app_context():
        try:
            # Clear existing monthly profit data
            MonthlyProfit.query.delete()
            db.session.commit()
            
            # Get all sales
            sales = Sale.query.all()
            
            # Group sales by year and month
            monthly_data = {}
            for sale in sales:
                year = sale.date_sold.year
                month = sale.date_sold.month
                key = (year, month)
                
                if key not in monthly_data:
                    monthly_data[key] = {
                        'revenue': 0,
                        'cost': 0,
                        'profit': 0,
                        'count': 0
                    }
                
                # Calculate profit for this sale
                purchase_price = sale.product.purchase_price or 0
                cost = purchase_price * sale.quantity
                profit = sale.total_price - cost
                
                # Update monthly data
                monthly_data[key]['revenue'] += sale.total_price
                monthly_data[key]['cost'] += cost
                monthly_data[key]['profit'] += profit
                monthly_data[key]['count'] += 1
            
            # Create monthly profit records
            for (year, month), data in monthly_data.items():
                monthly_profit = MonthlyProfit(
                    year=year,
                    month=month,
                    total_revenue=data['revenue'],
                    total_cost=data['cost'],
                    total_profit=data['profit'],
                    sale_count=data['count']
                )
                db.session.add(monthly_profit)
            
            db.session.commit()
            print(f"Created {len(monthly_data)} monthly profit records")
            return True
        except Exception as e:
            print(f"Error calculating monthly profits: {str(e)}")
            db.session.rollback()
            return False

def fix_database():
    """Fix the database by recreating it with the correct schema while preserving data"""
    print("Starting database fix process...")
    
    # Step 1: Create a backup
    if not backup_database():
        print("Failed to create backup. Aborting.")
        return False
    
    # Step 2: Export data
    if not export_data():
        print("Failed to export data. Aborting.")
        return False
    
    # Step 3: Recreate database
    if not recreate_database():
        print("Failed to recreate database. Aborting.")
        return False
    
    # Step 4: Import data
    if not import_data():
        print("Failed to import data. Aborting.")
        return False
    
    # Step 5: Calculate monthly profits
    if not calculate_monthly_profits():
        print("Failed to calculate monthly profits.")
        # Continue anyway
    
    print("Database fix process completed successfully!")
    return True

if __name__ == '__main__':
    fix_database()

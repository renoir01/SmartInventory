import sqlite3
from datetime import datetime

def add_custom_products():
    """Add specific products to the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # Check if the product table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not cursor.fetchone():
            print("Product table doesn't exist in the database")
            return False
        
        # Clear existing products if needed
        clear_existing = input("Do you want to clear existing products? (y/n): ")
        if clear_existing.lower() == 'y':
            cursor.execute("DELETE FROM product")
            print("Existing products cleared")
        
        # Your specific products
        # Format: (name, description, category, purchase_price, price, stock, low_stock_threshold)
        custom_products = [
            # Add your specific products here
            ('Milkway', 'Chocolate bar', 'Sweets', 23.0, 50.0, 12, 10),
            # Example: ('Product Name', 'Description', 'Category', purchase_price, selling_price, stock, low_stock_threshold)
            # Add more products as needed
        ]
        
        # Add option to input products interactively
        add_more = input("Do you want to add products interactively? (y/n): ")
        if add_more.lower() == 'y':
            while True:
                print("\nEnter product details (leave name empty to finish):")
                name = input("Product name: ")
                if not name:
                    break
                
                description = input("Description: ")
                category = input("Category: ")
                
                try:
                    purchase_price = float(input("Purchase price: "))
                    price = float(input("Selling price: "))
                    stock = int(input("Stock quantity: "))
                    low_stock_threshold = int(input("Low stock threshold: "))
                    
                    custom_products.append((name, description, category, purchase_price, price, stock, low_stock_threshold))
                    print(f"Added {name} to the list")
                except ValueError:
                    print("Invalid input. Please enter numbers for prices and quantities.")
        
        # Insert the products
        for product in custom_products:
            cursor.execute('''
            INSERT INTO product (name, description, category, purchase_price, price, stock, low_stock_threshold, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*product, datetime.now()))
        
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        
        print(f"Added {len(custom_products)} products to the database")
        return True
    except Exception as e:
        print(f"Error adding products: {e}")
        return False

if __name__ == "__main__":
    print("Adding custom products to the database...")
    add_custom_products()

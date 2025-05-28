import sqlite3
import json
import os
from datetime import datetime

def export_products_to_json():
    """Export products from the local database to a JSON file"""
    db_path = 'inventory.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        cursor = conn.cursor()
        
        # Check if the product table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not cursor.fetchone():
            print("Product table doesn't exist in the database")
            return False
        
        # Get all column names from the product table
        cursor.execute("PRAGMA table_info(product)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build a query that selects all available columns
        columns_str = ', '.join(columns)
        
        # Get all products
        cursor.execute(f"SELECT {columns_str} FROM product")
        rows = cursor.fetchall()
        
        if not rows:
            print("No products found in the database")
            return False
        
        # Convert rows to a list of dictionaries
        products = []
        for row in cursor.fetchall():
            product = {}
            for col in columns:
                product[col] = row[col]
            products.append(product)
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"products_export_{timestamp}.json"
        
        # Write the products to a JSON file
        with open(filename, 'w') as f:
            json.dump(products, f, indent=4)
        
        print(f"Exported {len(products)} products to {filename}")
        
        # Also create an SQL script that can be used to insert the products
        sql_filename = f"products_import_{timestamp}.sql"
        with open(sql_filename, 'w') as f:
            f.write("-- SQL script to import products\n")
            f.write("-- Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
            
            for product in products:
                # Create column names and values strings
                col_names = ', '.join(product.keys())
                placeholders = ', '.join(['?' for _ in product.keys()])
                values = ', '.join([repr(str(val)) if isinstance(val, str) else str(val) if val is not None else 'NULL' for val in product.values()])
                
                # Write the INSERT statement
                f.write(f"INSERT INTO product ({col_names}) VALUES ({values});\n")
            
            f.write("\n-- End of script\n")
        
        print(f"Created SQL import script at {sql_filename}")
        
        # Create a Python script that can be used to import the products
        py_filename = f"import_products_{timestamp}.py"
        with open(py_filename, 'w') as f:
            f.write("# Python script to import products\n")
            f.write("# Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
            f.write("import sqlite3\n")
            f.write("import json\n\n")
            
            f.write("def import_products():\n")
            f.write("    try:\n")
            f.write("        # Connect to the database\n")
            f.write("        conn = sqlite3.connect('inventory.db')\n")
            f.write("        cursor = conn.cursor()\n\n")
            
            f.write("        # Insert each product\n")
            for product in products:
                # Create column names and values strings
                col_names = ', '.join(product.keys())
                placeholders = ', '.join(['?' for _ in product.keys()])
                values = [str(val) if val is not None else None for val in product.values()]
                values_str = ', '.join([repr(val) for val in values])
                
                # Write the INSERT statement
                f.write(f"        cursor.execute(\"INSERT INTO product ({col_names}) VALUES ({placeholders})\", {values_str})\n")
            
            f.write("\n        # Commit the changes and close the connection\n")
            f.write("        conn.commit()\n")
            f.write("        conn.close()\n")
            f.write("        print(\"Products imported successfully\")\n")
            f.write("    except Exception as e:\n")
            f.write("        print(f\"Error importing products: {e}\")\n\n")
            
            f.write("if __name__ == \"__main__\":\n")
            f.write("    import_products()\n")
        
        print(f"Created Python import script at {py_filename}")
        
        return True
    except Exception as e:
        print(f"Error exporting products: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Exporting products from the database...")
    export_products_to_json()

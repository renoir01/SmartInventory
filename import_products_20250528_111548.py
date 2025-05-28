# Python script to import products
# Generated on 2025-05-28 11:15:48

import sqlite3
import json

def import_products():
    try:
        # Connect to the database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()

        # Insert each product

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        print("Products imported successfully")
    except Exception as e:
        print(f"Error importing products: {e}")

if __name__ == "__main__":
    import_products()

import sqlite3
import os
import glob
from datetime import datetime
import shutil

def find_backup_databases():
    """Find all backup database files in the current directory"""
    # Look for all files that might be database backups
    backup_files = glob.glob("*.db.*") + glob.glob("*backup*") + glob.glob("*old*")
    
    if not backup_files:
        print("No backup database files found")
        return []
    
    print(f"Found {len(backup_files)} potential backup files:")
    for i, file in enumerate(backup_files):
        print(f"{i+1}. {file}")
    
    return backup_files

def check_database_for_products(db_path):
    """Check if a database file contains products"""
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found")
        return 0
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the product table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not cursor.fetchone():
            print(f"Product table doesn't exist in {db_path}")
            conn.close()
            return 0
        
        # Count products
        cursor.execute("SELECT COUNT(*) FROM product")
        count = cursor.fetchone()[0]
        
        # Get a sample of products
        cursor.execute("SELECT id, name, category, price FROM product LIMIT 5")
        sample = cursor.fetchall()
        
        conn.close()
        
        print(f"Database {db_path} contains {count} products")
        if sample:
            print("Sample products:")
            for product in sample:
                print(f"  - ID: {product[0]}, Name: {product[1]}, Category: {product[2]}, Price: {product[3]}")
        
        return count
    except Exception as e:
        print(f"Error checking {db_path}: {e}")
        return 0

def restore_from_backup(backup_path, target_db='inventory.db'):
    """Restore data from a backup database"""
    if not os.path.exists(backup_path):
        print(f"Backup file {backup_path} not found")
        return False
    
    # Create a backup of the current database
    if os.path.exists(target_db):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = f"{target_db}.before_restore_{timestamp}"
        try:
            shutil.copy2(target_db, current_backup)
            print(f"Created backup of current database at {current_backup}")
        except Exception as e:
            print(f"Warning: Failed to backup current database: {e}")
    
    try:
        # Connect to both databases
        backup_conn = sqlite3.connect(backup_path)
        backup_cursor = backup_conn.cursor()
        
        target_conn = sqlite3.connect(target_db)
        target_cursor = target_conn.cursor()
        
        # Check if product table exists in backup
        backup_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not backup_cursor.fetchone():
            print(f"Product table doesn't exist in backup {backup_path}")
            return False
        
        # Get schema of product table in backup
        backup_cursor.execute("PRAGMA table_info(product)")
        backup_columns = backup_cursor.fetchall()
        backup_column_names = [col[1] for col in backup_columns]
        
        # Check if product table exists in target
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
        if not target_cursor.fetchone():
            print("Product table doesn't exist in target database, creating it...")
            
            # Create product table in target with same schema as backup
            column_defs = []
            for col in backup_columns:
                name = col[1]
                type_name = col[2]
                not_null = "NOT NULL" if col[3] else ""
                default = f"DEFAULT {col[4]}" if col[4] is not None else ""
                pk = "PRIMARY KEY" if col[5] else ""
                column_defs.append(f"{name} {type_name} {not_null} {default} {pk}".strip())
            
            create_table_sql = f"CREATE TABLE product ({', '.join(column_defs)})"
            target_cursor.execute(create_table_sql)
        
        # Get schema of product table in target
        target_cursor.execute("PRAGMA table_info(product)")
        target_columns = target_cursor.fetchall()
        target_column_names = [col[1] for col in target_columns]
        
        # Find common columns
        common_columns = [col for col in backup_column_names if col in target_column_names]
        
        if not common_columns:
            print("No common columns found between backup and target")
            return False
        
        # Get products from backup
        backup_cursor.execute(f"SELECT {', '.join(common_columns)} FROM product")
        products = backup_cursor.fetchall()
        
        if not products:
            print("No products found in backup")
            return False
        
        # Clear existing products in target if requested
        clear_existing = input("Do you want to clear existing products in the target database? (y/n): ")
        if clear_existing.lower() == 'y':
            target_cursor.execute("DELETE FROM product")
            print("Cleared existing products from target database")
        
        # Insert products into target
        placeholders = ', '.join(['?' for _ in common_columns])
        insert_sql = f"INSERT INTO product ({', '.join(common_columns)}) VALUES ({placeholders})"
        
        for product in products:
            target_cursor.execute(insert_sql, product)
        
        # Commit changes
        target_conn.commit()
        
        print(f"Successfully restored {len(products)} products from backup")
        
        # Close connections
        backup_conn.close()
        target_conn.close()
        
        return True
    except Exception as e:
        print(f"Error restoring from backup: {e}")
        return False

def main():
    """Main function to restore from backup"""
    print("Looking for backup databases...")
    backup_files = find_backup_databases()
    
    if not backup_files:
        print("No backup files found. Cannot restore data.")
        return
    
    # Check each backup for products
    print("\nChecking backup files for products...")
    backups_with_products = []
    
    for backup in backup_files:
        product_count = check_database_for_products(backup)
        if product_count > 0:
            backups_with_products.append((backup, product_count))
    
    if not backups_with_products:
        print("No products found in any backup files")
        return
    
    # Sort backups by product count (most products first)
    backups_with_products.sort(key=lambda x: x[1], reverse=True)
    
    print("\nBackups with products:")
    for i, (backup, count) in enumerate(backups_with_products):
        print(f"{i+1}. {backup} - {count} products")
    
    # Ask which backup to restore from
    try:
        choice = int(input("\nEnter the number of the backup to restore from (0 to cancel): "))
        if choice == 0:
            print("Restoration cancelled")
            return
        
        if 1 <= choice <= len(backups_with_products):
            selected_backup = backups_with_products[choice-1][0]
            print(f"Restoring from {selected_backup}...")
            restore_from_backup(selected_backup)
        else:
            print("Invalid choice")
    except ValueError:
        print("Invalid input")

if __name__ == "__main__":
    main()

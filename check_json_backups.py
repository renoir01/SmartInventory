import json
import os
import sys
from datetime import datetime

def check_json_file(file_path):
    """Check the contents of a JSON file and print summary information"""
    try:
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist")
            return False
            
        print(f"\n===== Checking JSON file: {file_path} =====")
        print(f"File size: {os.path.getsize(file_path) / 1024:.2f} KB")
        print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(file_path))}")
        
        # Try to load the JSON data
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                
                if isinstance(data, list):
                    print(f"JSON contains a list with {len(data)} items")
                    
                    # If it's a list of products, show some samples
                    if len(data) > 0 and isinstance(data[0], dict):
                        keys = list(data[0].keys())
                        print(f"First item keys: {keys}")
                        
                        # Check if this looks like product data
                        product_keys = ['id', 'name', 'price', 'category', 'stock']
                        has_product_keys = any(key in keys for key in product_keys)
                        
                        if has_product_keys:
                            print("This appears to be product data")
                            print(f"Sample items:")
                            for i, item in enumerate(data[:5]):
                                print(f"  {i+1}. {item}")
                            
                            if len(data) > 5:
                                print(f"  ... and {len(data) - 5} more items")
                        
                elif isinstance(data, dict):
                    print(f"JSON contains a dictionary with {len(data)} keys")
                    print(f"Keys: {list(data.keys())}")
                    
                    # If it has a 'products' key, check that
                    if 'products' in data and isinstance(data['products'], list):
                        products = data['products']
                        print(f"Found 'products' key with {len(products)} items")
                        
                        if len(products) > 0:
                            print(f"Sample products:")
                            for i, product in enumerate(products[:5]):
                                print(f"  {i+1}. {product}")
                            
                            if len(products) > 5:
                                print(f"  ... and {len(products) - 5} more products")
                else:
                    print(f"JSON contains data of type: {type(data)}")
                
                return True
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {str(e)}")
                return False
    except Exception as e:
        print(f"Error checking JSON file: {str(e)}")
        return False

def main():
    # List of JSON files to check
    json_files = [
        "products_backup.json",
        "sales_backup.json",
        "users_backup.json",
        "products_export_20250528_111548.json"
    ]
    
    print("SmartInventory JSON Backup Checker")
    print("==================================")
    
    found_data = False
    
    for json_file in json_files:
        if os.path.exists(json_file):
            result = check_json_file(json_file)
            found_data = found_data or result
        else:
            print(f"\nFile {json_file} not found, skipping...")
    
    if not found_data:
        print("\nNo product data found in any of the JSON files.")
        print("Consider checking for other JSON files or database exports.")
    
    print("\nJSON check completed!")

if __name__ == "__main__":
    main()

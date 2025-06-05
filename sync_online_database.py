import os
import sys
import requests
import sqlite3
import datetime
import subprocess
import logging
from getpass import getpass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sync_database.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def backup_local_database():
    """Create a backup of the local database before syncing"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"inventory.db.backup_{timestamp}"
        
        if os.path.exists("inventory.db"):
            import shutil
            shutil.copy2("inventory.db", backup_filename)
            logger.info(f"Local database backed up to {backup_filename}")
            print(f"Local database backed up to {backup_filename}")
            return True
        else:
            logger.warning("No local database found to backup")
            print("No local database found to backup")
            return False
    except Exception as e:
        logger.error(f"Error backing up local database: {str(e)}")
        print(f"Error backing up local database: {str(e)}")
        return False

def download_database_from_pythonanywhere(username, api_token):
    """
    Download the database file from PythonAnywhere using their API
    
    Note: This requires an API token from PythonAnywhere
    """
    try:
        # Define the API endpoint for file download
        api_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/files/path"
        headers = {"Authorization": f"Token {api_token}"}
        
        # Path to the database file on PythonAnywhere (adjust as needed)
        db_path = "/home/{username}/SmartInventory/inventory.db"
        db_path = db_path.format(username=username)
        
        # Make the API request
        response = requests.get(
            f"{api_url}{db_path}",
            headers=headers,
            stream=True
        )
        
        if response.status_code == 200:
            # Save the downloaded file
            with open("inventory_online.db", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info("Successfully downloaded database from PythonAnywhere")
            print("Successfully downloaded database from PythonAnywhere")
            return True
        else:
            logger.error(f"Failed to download database: {response.status_code} - {response.text}")
            print(f"Failed to download database: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error downloading database: {str(e)}")
        print(f"Error downloading database: {str(e)}")
        return False

def replace_local_with_online_db():
    """Replace the local database with the downloaded one"""
    try:
        if os.path.exists("inventory_online.db"):
            if os.path.exists("inventory.db"):
                os.remove("inventory.db")
            
            import shutil
            shutil.copy2("inventory_online.db", "inventory.db")
            logger.info("Local database replaced with online version")
            print("Local database replaced with online version")
            return True
        else:
            logger.error("Online database file not found")
            print("Online database file not found")
            return False
    except Exception as e:
        logger.error(f"Error replacing local database: {str(e)}")
        print(f"Error replacing local database: {str(e)}")
        return False

def verify_database():
    """Verify the database structure and content"""
    try:
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\nDatabase Tables:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Count records in key tables
        tables_to_check = ['user', 'product', 'sale', 'monthly_profit', 'cashout_record']
        print("\nRecord Counts:")
        
        for table in tables_to_check:
            if (table,) in tables or (table.lower(),) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"- {table}: {count} records")
                except sqlite3.OperationalError:
                    # Try lowercase if the first attempt fails
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table.lower()}")
                        count = cursor.fetchone()[0]
                        print(f"- {table}: {count} records")
                    except:
                        print(f"- {table}: Unable to count records")
            else:
                print(f"- {table}: Table not found")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error verifying database: {str(e)}")
        print(f"Error verifying database: {str(e)}")
        return False

def main():
    print("\n===== SmartInventory Database Synchronization Tool =====\n")
    print("This tool will help you sync your local database with your online deployment.")
    print("WARNING: This will replace your local database with the online version.")
    print("A backup of your local database will be created before proceeding.\n")
    
    proceed = input("Do you want to proceed? (yes/no): ").strip().lower()
    if proceed != 'yes':
        print("Operation cancelled.")
        return
    
    # Backup local database
    print("\nStep 1: Backing up local database...")
    if not backup_local_database():
        print("Failed to backup local database. Aborting for safety.")
        return
    
    # Get PythonAnywhere credentials
    print("\nStep 2: Downloading online database...")
    print("You'll need your PythonAnywhere username and API token.")
    print("You can generate an API token at: https://www.pythonanywhere.com/account/#api_token")
    
    username = input("PythonAnywhere username: ").strip()
    api_token = getpass("API token (input will be hidden): ")
    
    if not download_database_from_pythonanywhere(username, api_token):
        print("Failed to download online database. Aborting.")
        return
    
    # Replace local database with online version
    print("\nStep 3: Replacing local database with online version...")
    if not replace_local_with_online_db():
        print("Failed to replace local database. Aborting.")
        return
    
    # Verify the database
    print("\nStep 4: Verifying database structure and content...")
    verify_database()
    
    print("\nDatabase synchronization completed successfully!")
    print("Your local database now matches the online version.")
    print("You can now run your application with the synchronized database.")

if __name__ == "__main__":
    main()

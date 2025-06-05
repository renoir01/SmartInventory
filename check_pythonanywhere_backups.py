import os
import sys
import requests
import json
import datetime
from getpass import getpass

def check_pythonanywhere_backups(username, api_token):
    """
    Check for available backups on PythonAnywhere
    """
    try:
        # Define the API endpoint for listing backups
        api_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/files/sharing/"
        headers = {"Authorization": f"Token {api_token}"}
        
        # Make the API request to list backups
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            print("Successfully connected to PythonAnywhere API")
            
            # List available backups
            print("\nChecking for available backups...")
            
            # PythonAnywhere stores backups in /user-backup/ directory
            backup_api_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/files/path/user-backup/"
            backup_response = requests.get(backup_api_url, headers=headers)
            
            if backup_response.status_code == 200:
                backups = backup_response.json()
                print(f"Found {len(backups)} backup directories:")
                
                for backup in backups:
                    if backup['type'] == 'directory':
                        print(f"- {backup['name']} (Directory)")
                
                return True
            else:
                print(f"Failed to list backups: {backup_response.status_code} - {backup_response.text}")
                return False
        else:
            print(f"Failed to connect to PythonAnywhere API: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error checking backups: {str(e)}")
        return False

def restore_from_backup(username, api_token, backup_date, db_path):
    """
    Restore database from a specific backup date
    """
    try:
        # Define the API endpoint for file download
        api_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/files/path"
        headers = {"Authorization": f"Token {api_token}"}
        
        # Path to the database file in the backup (adjust as needed)
        backup_db_path = f"/user-backup/{backup_date}/home/{username}/{db_path}"
        
        # Make the API request to download the backup
        response = requests.get(
            f"{api_url}{backup_db_path}",
            headers=headers,
            stream=True
        )
        
        if response.status_code == 200:
            # Save the downloaded backup
            backup_filename = f"inventory_backup_{backup_date}.db"
            with open(backup_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Successfully downloaded backup from {backup_date} to {backup_filename}")
            return True
        else:
            print(f"Failed to download backup: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error restoring from backup: {str(e)}")
        return False

def main():
    print("\n===== PythonAnywhere Backup Checker =====\n")
    print("This tool will help you check for available backups on PythonAnywhere.")
    print("You'll need your PythonAnywhere username and API token.")
    print("You can generate an API token at: https://www.pythonanywhere.com/account/#api_token\n")
    
    username = input("PythonAnywhere username: ").strip()
    api_token = getpass("API token (input will be hidden): ")
    
    if not check_pythonanywhere_backups(username, api_token):
        print("\nFailed to check backups. Please verify your credentials and try again.")
        return
    
    print("\nTo restore from a backup, you'll need to specify the backup date and the path to your database file.")
    print("Example backup date format: 2025-05-27")
    print("Example database path: SmartInventory/inventory.db")
    
    restore = input("\nDo you want to restore from a backup? (yes/no): ").strip().lower()
    if restore != 'yes':
        print("Operation cancelled.")
        return
    
    backup_date = input("Enter the backup date (YYYY-MM-DD): ").strip()
    db_path = input("Enter the path to your database file (relative to your home directory): ").strip()
    
    if restore_from_backup(username, api_token, backup_date, db_path):
        print("\nBackup restoration completed!")
        print("You can now use the restored database file.")
    else:
        print("\nFailed to restore from backup.")

if __name__ == "__main__":
    main()

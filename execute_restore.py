import os
import sys
import subprocess
import datetime

def main():
    print("\n===== SmartInventory Database Recovery Tool =====\n")
    print("This tool will help you restore your database from available backups.")
    print("It will use the restore_from_backup.py script that's already on your PythonAnywhere account.\n")
    
    # Check if we're running on PythonAnywhere
    on_pythonanywhere = os.path.exists('/home/renoir0')
    
    if on_pythonanywhere:
        print("Detected PythonAnywhere environment.")
        
        # List available database backups
        print("\nChecking for database backups...")
        backup_files = [f for f in os.listdir('.') if (f.endswith('.db.backup') or 
                                                     f.endswith('.db.old') or 
                                                     'backup' in f.lower() and f.endswith('.db'))]
        
        if backup_files:
            print(f"Found {len(backup_files)} potential backup files:")
            for i, backup in enumerate(backup_files, 1):
                file_size = os.path.getsize(backup) / 1024  # Size in KB
                mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(backup))
                print(f"{i}. {backup} ({file_size:.1f} KB, modified: {mod_time})")
            
            # Ask which backup to use
            try:
                choice = int(input("\nEnter the number of the backup to restore (0 to cancel): "))
                if choice == 0:
                    print("Operation cancelled.")
                    return
                
                selected_backup = backup_files[choice-1]
                print(f"\nSelected backup: {selected_backup}")
                
                # Execute the restore_from_backup.py script
                print(f"\nRunning restore_from_backup.py with {selected_backup}...")
                subprocess.run([sys.executable, 'restore_from_backup.py', selected_backup])
                
                print("\nRestore operation completed. Please check your database to verify the restoration.")
                
            except (ValueError, IndexError) as e:
                print(f"Invalid selection: {str(e)}")
                return
        else:
            print("No database backup files found in the current directory.")
    else:
        print("This script is designed to be run on PythonAnywhere.")
        print("Please upload and run this script on your PythonAnywhere account.")
        print("\nAlternatively, you can:")
        print("1. Log in to PythonAnywhere")
        print("2. Navigate to your SmartInventory directory")
        print("3. Run the existing restore_from_backup.py script with a backup file")
        print("   Example: python restore_from_backup.py new_inventory_backup_20250527_214054.db")

if __name__ == "__main__":
    main()

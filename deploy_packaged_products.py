#!/usr/bin/env python
"""
Deploy Packaged Products Feature to GitHub Repository
This script copies the packaged products feature to the GitHub repository
"""
import os
import shutil
import subprocess
import datetime

# Files to copy to the GitHub repository
FILES_TO_COPY = [
    ('app.py', 'app.py'),
    ('static/css/style.css', 'static/css/style.css'),
    ('templates/add_product.html', 'templates/add_product.html'),
    ('templates/edit_product.html', 'templates/edit_product.html'),
    ('templates/cashier_dashboard.html', 'templates/cashier_dashboard.html')
]

# GitHub repository path
GITHUB_REPO_PATH = r'C:\Users\user\Videos\SmartInventory'

def main():
    print("Deploying packaged products feature to GitHub repository...")
    
    # Create timestamp for backup
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure directories exist in the GitHub repository
    for _, dest_path in FILES_TO_COPY:
        dest_dir = os.path.dirname(os.path.join(GITHUB_REPO_PATH, dest_path))
        os.makedirs(dest_dir, exist_ok=True)
    
    # Copy files to GitHub repository
    for src_path, dest_path in FILES_TO_COPY:
        src_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), src_path)
        dest_full_path = os.path.join(GITHUB_REPO_PATH, dest_path)
        
        # Create backup if file exists
        if os.path.exists(dest_full_path):
            backup_path = f"{dest_full_path}.bak_{timestamp}"
            shutil.copy2(dest_full_path, backup_path)
            print(f"Created backup: {backup_path}")
        
        # Copy file
        shutil.copy2(src_full_path, dest_full_path)
        print(f"Copied {src_path} to {dest_path}")
    
    # Git operations
    try:
        # Change to GitHub repository directory
        os.chdir(GITHUB_REPO_PATH)
        
        # Add files
        for _, dest_path in FILES_TO_COPY:
            subprocess.run(['git', 'add', dest_path], check=True)
        
        # Commit changes
        subprocess.run(['git', 'commit', '-m', 'Add packaged products feature to support products sold both in packages and individually'], check=True)
        
        # Push changes
        subprocess.run(['git', 'push'], check=True)
        
        print("\nSuccessfully pushed packaged products feature to GitHub repository.")
        print("\nInstructions for PythonAnywhere deployment:")
        print("1. Log in to your PythonAnywhere account")
        print("2. Open a Bash console")
        print("3. Navigate to your project directory")
        print("4. Run: git pull")
        print("5. Run: flask db upgrade (to apply database migrations for the new fields)")
        print("6. Reload your web app from the Web tab")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during Git operations: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

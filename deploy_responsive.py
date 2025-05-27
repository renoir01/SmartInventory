#!/usr/bin/env python
"""
Deploy Responsive Design Improvements to PythonAnywhere
This script copies the responsive design improvements to the GitHub repository
"""
import os
import shutil
import subprocess
import datetime

# Files to copy to the GitHub repository
FILES_TO_COPY = [
    ('static/css/responsive-fixes.css', 'static/css/responsive-fixes.css'),
    ('static/css/style.css', 'static/css/style.css'),
    ('templates/base.html', 'templates/base.html')
]

# GitHub repository path
GITHUB_REPO_PATH = r'C:\Users\user\Videos\SmartInventory'

def main():
    print("Deploying responsive design improvements to GitHub repository...")
    
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
        subprocess.run(['git', 'add', 'static/css/responsive-fixes.css', 'static/css/style.css', 'templates/base.html'], check=True)
        
        # Commit changes
        subprocess.run(['git', 'commit', '-m', 'Add responsive design improvements for mobile devices'], check=True)
        
        # Push changes
        subprocess.run(['git', 'push'], check=True)
        
        print("\nSuccessfully pushed responsive design improvements to GitHub repository.")
        print("\nInstructions for PythonAnywhere deployment:")
        print("1. Log in to your PythonAnywhere account")
        print("2. Open a Bash console")
        print("3. Navigate to your project directory")
        print("4. Run: git pull")
        print("5. Reload your web app from the Web tab")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during Git operations: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()

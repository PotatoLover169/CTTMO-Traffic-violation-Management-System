#!/usr/bin/env python
import re
import os
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the file before making changes"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.bak_{timestamp}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as source_file:
            content = source_file.read()
            
        with open(backup_path, 'w', encoding='utf-8') as backup_file:
            backup_file.write(content)
            
        print(f"Created backup at {backup_path}")
        return True, content
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        return False, None

def fix_escaped_quotes(file_path):
    """Find and fix the escaped quotes in the file"""
    success, content = backup_file(file_path)
    if not success:
        return False
    
    # Fix the escaped quotes in signature_refused
    content = content.replace(r"\'signature_refused\'", "'signature_refused'")
    
    # Fix the escaped quotes in refusal_note
    content = content.replace(r"\'refusal_note\'", "'refusal_note'")
    
    # Fix the escaped empty strings
    content = content.replace(r"\'\'", "''")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Successfully fixed escaped quotes in {file_path}")
        return True
    except Exception as e:
        print(f"Error writing to file: {str(e)}")
        return False

if __name__ == "__main__":
    file_path = "traffic_violation_system/views.py"
    if os.path.exists(file_path):
        if fix_escaped_quotes(file_path):
            print("Done! The syntax errors have been fixed.")
        else:
            print("Failed to fix the syntax errors.")
    else:
        print(f"File not found: {file_path}") 
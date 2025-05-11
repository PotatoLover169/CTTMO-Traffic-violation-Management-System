#!/usr/bin/env python
"""
Script to apply the signature refusal fix to the views.py file.

This script will:
1. Find the issue_ticket function in views.py
2. Add code to handle signature refusal
3. Update the ticket_data dictionary to include signature refusal information
"""

import re
import os
import sys
import shutil
from datetime import datetime

# Path to the views.py file
VIEWS_PY_PATH = 'traffic_violation_system/views.py'
BACKUP_PATH = f'traffic_violation_system/views.py.bak_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

def backup_file(file_path, backup_path):
    """Create a backup of the file before making changes."""
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")

def apply_signature_refusal_fix():
    """Apply the signature refusal fix to the views.py file."""
    # Create a backup of the original file
    backup_file(VIEWS_PY_PATH, BACKUP_PATH)
    
    # Read the content of the file
    with open(VIEWS_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add code to handle signature refusal
    # Look for the pattern where we need to insert the signature refusal code
    signature_pattern = r'(# Handle signature if provided\s+signature_input = request\.POST\.get\(\'signature_data\'\))'
    
    signature_refusal_code = """
            # Handle signature refusal if applicable
            signature_refused = request.POST.get('signature_refused') == 'true'
            if signature_refused:
                violation.signature_refused = True
                violation.refusal_note = request.POST.get('refusal_note', '')
                print(f"Violator refused to sign: {violation.refusal_note}")
                signature_data = None
                violation.save()
            else:
                # Initialize signature_data as None
                signature_data = None

                \g<1>"""
    
    content = re.sub(signature_pattern, signature_refusal_code, content)
    
    # 2. Update the ticket_data dictionary
    # Look for the pattern where we need to add the signature refusal fields
    ticket_data_pattern = r'(\'signature_data\': signature_data,)(\s+)(\'enforcer_name\': request\.user\.get_full_name\(\),)'
    
    signature_refusal_fields = r'\1\2\'signature_refused\': violation.signature_refused,\2\'refusal_note\': violation.refusal_note or \'\',\2\3'
    
    content = re.sub(ticket_data_pattern, signature_refusal_fields, content)
    
    # Write the modified content back to the file
    with open(VIEWS_PY_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully applied signature refusal fix to {VIEWS_PY_PATH}")
    print("Please verify the changes and restart the server.")

if __name__ == "__main__":
    # Check if the file exists
    if not os.path.exists(VIEWS_PY_PATH):
        print(f"Error: {VIEWS_PY_PATH} not found.")
        sys.exit(1)
    
    # Apply the fix
    apply_signature_refusal_fix() 
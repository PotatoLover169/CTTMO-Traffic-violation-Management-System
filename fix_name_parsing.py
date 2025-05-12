#!/usr/bin/env python
"""
Script to fix name parsing in traffic_violation_system/views.py
This script modifies the code that parses full names to handle multi-word first names.
"""

import re

# File to modify
file_path = 'traffic_violation_system/views.py'

# Read the file content
with open(file_path, 'r') as f:
    content = f.read()

# Find the problematic section using a regular expression pattern
pattern = r"""if not first_name and not last_name and data_result\.get\('fullName'\):
\s+names = data_result\['fullName'\]\.split\(' ', 1\)
\s+first_name = names\[0\]
\s+last_name = names\[1\] if len\(names\) > 1 else ''"""

# The improved code to handle multi-word first names
replacement = """if not first_name and not last_name and data_result.get('fullName'):
                        # Improved handling for multi-word first names
                        full_name = data_result['fullName'].strip()
                        name_parts = full_name.split()
                        if len(name_parts) > 1:
                            # Assume last part is surname, everything else is first name
                            last_name = name_parts[-1]
                            first_name = ' '.join(name_parts[:-1])
                        else:
                            # If only one word, treat as first name
                            first_name = full_name
                            last_name = ''"""

# Make the replacement
new_content = re.sub(pattern, replacement, content)

# Check if the replacement was successful
if new_content != content:
    # Write the modified content back to the file
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("Successfully updated the name parsing logic!")
else:
    print("Pattern not found or replacement failed. No changes made.")
    
    # Let's try with a simpler pattern
    simple_pattern = "names = data_result['fullName'].split(' ', 1)"
    if simple_pattern in content:
        print(f"Found simple pattern: {simple_pattern}")
        line_number = content.split('\n').index([l for l in content.split('\n') if simple_pattern in l][0]) + 1
        print(f"Found at line {line_number}")
    else:
        print("Even simple pattern not found.") 
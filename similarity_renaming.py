#!/usr/bin/env python3

# Rename files that have too similar names and thus may cause conflict 
# further down an automation / microservices pipeline.
# Usage: 
# similarity_renaming.py <directory> <file extension>
# E.g.:
# similarity_renaming.py . .jpg
# Renamed user_1.jpg to user_1_qxrl2j.jpg
# Renamed user_2.jpg to user_2_wtntep.jpg

import os
import sys
import random
import string
import re

def generate_random_suffix(length=6):
    """Generate a random alphanumeric suffix."""
    letters_and_digits = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

def clean_filename(filename):
    """Remove digits and special characters from filenames, keep letters only."""
    return re.sub(r'[^a-zA-Z]', '', filename)

def find_similar_files(files):
    """Find files with similar names by cleaning and comparing their names."""
    cleaned_names = {}
    for file in files:
        base_name = os.path.splitext(file)[0]
        cleaned_name = clean_filename(base_name)
        if cleaned_name in cleaned_names:
            cleaned_names[cleaned_name].append(file)
        else:
            cleaned_names[cleaned_name] = [file]
    return {key: value for key, value in cleaned_names.items() if len(value) > 1}

def rename_files(directory, extension):
    """Rename files that are similar by appending a unique random suffix."""
    all_files = [f for f in os.listdir(directory) if f.endswith(extension)]
    similar_files = find_similar_files(all_files)
    
    for group in similar_files.values():
        for filename in group:
            new_name = f"{os.path.splitext(filename)[0]}_{generate_random_suffix()}{extension}"
            old_file = os.path.join(directory, filename)
            new_file = os.path.join(directory, new_name)
            os.rename(old_file, new_file)
            print(f"Renamed {filename} to {new_name}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python rename_files.py <directory> <file_extension>")
        sys.exit(1)
    
    dir_path = sys.argv[1]
    file_ext = sys.argv[2]
    if not file_ext.startswith('.'):
        file_ext = '.' + file_ext

    rename_files(dir_path, file_ext)

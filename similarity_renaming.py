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
import argparse
import random
import string
import re

def generate_random_suffix(length=6):
    """Generate a random alphanumeric suffix."""
    letters_and_digits = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

def insert_suffix(filename, suffix, before_special_char=False):
    """Insert suffix according to the specified mode."""
    if before_special_char:
        # Split the filename at the first occurrence of a non-alphabetic character after an alphabetic character
        parts = re.split(r'([a-zA-Z]+)(?=[^a-zA-Z]|$)', filename, maxsplit=1)
        if len(parts) >= 3:
            return parts[0] + parts[1] + suffix + parts[2]
    return filename + suffix

def rename_files(directory, extension, before_special_char=False):
    """Rename files by appending a unique random suffix."""
    for filename in os.listdir(directory):
        if filename.endswith(extension):
            base_name, ext = os.path.splitext(filename)
            if before_special_char:
                new_name = insert_suffix(base_name, f"{generate_random_suffix()}_", before_special_char) + ext
            else:
                new_name = insert_suffix(base_name, f"_{generate_random_suffix()}", before_special_char) + ext
            old_file = os.path.join(directory, filename)
            new_file = os.path.join(directory, new_name)
            os.rename(old_file, new_file)
            print(f"Renamed {filename} to {new_name}")

def main():
    parser = argparse.ArgumentParser(description='Rename files by appending a random suffix.')
    parser.add_argument('directory', type=str, help='Directory containing the files')
    parser.add_argument('extension', type=str, help='File extension to match for renaming')
    parser.add_argument('-b', '--before-special-char', action='store_true',
                        help='Insert the random string immediately after the alphabetic portion of the filename.')

    args = parser.parse_args()

    # Ensure the file extension starts with a dot
    if not args.extension.startswith('.'):
        args.extension = '.' + args.extension

    rename_files(args.directory, args.extension, args.before_special_char)

if __name__ == "__main__":
    main()

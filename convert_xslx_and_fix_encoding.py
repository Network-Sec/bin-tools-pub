#!/usr/bin/env python3

# Script will iterate over a folder full of .xls, xlsx, csv and a few more file formats
# It will try to convert those to .txt and also try to fix faulty encoding in content 
# and filenames: "ªã¯¨âì  ªª ã­âë" (example faulty filename encoding) 
# Works quite well for the majority - it's intended to fix thousands of files, os a few
# percent won't work and that's ok. Script got one strange bug that we didn't
# care fixing, nesting target/target/target/.. for some files. As it does a great job otherwise
# we left it like that, cause you can easily move the files afterwards.

import os
import shutil
import chardet
import pandas as pd
import re

# Directory setup
src_directory = os.path.abspath('.')  # Use your actual source directory path
dst_directory = os.path.abspath('target')  # Ensure this is the correct target path

def is_problematic_filename(filename):
    # Detect problematic filenames: sequences of non-ASCII characters might indicate encoding issues
    return re.search(r'[\x80-\xff]{3,}', filename) is not None

def try_decode_with_fallback(byte_string, encodings=['utf-8', 'windows-1251', 'koi8-r', 'latin1']):
    for encoding in encodings:
        try:
            return byte_string.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    # Fallback if all decodings fail
    return byte_string.decode('utf-8', errors='replace'), 'utf-8 (fallback)'

def normalize_filename(filename):
    if not is_problematic_filename(filename):
        return filename  # Return as-is if the filename doesn't seem problematic
    
    byte_string = filename.encode('latin1')  # Re-encode to bytes
    normalized, used_encoding = try_decode_with_fallback(byte_string)
    return normalized

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def guess_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(50000)  # Read first 50KB to guess encoding
    result = chardet.detect(raw_data)
    return result['encoding']

def convert_file(file_path, target_folder):
    encoding = guess_encoding(file_path)
    base, ext = os.path.splitext(file_path)
    filename = os.path.basename(base)
    normalized_filename = normalize_filename(filename)
    new_path = os.path.join(target_folder, f"{normalized_filename}{ext}".replace('.xlsx', '.txt').replace('.xls', '.txt'))

    if os.path.exists(new_path) and os.path.getsize(new_path) > 0:
        print(f"Skipping {os.path.relpath(new_path, dst_directory)}, already converted.")
        return

    try:
        if ext.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
            df.to_csv(new_path, index=False, encoding='utf-8')
        elif ext.lower() == '.csv':
            # Read CSV with detected encoding and save as UTF-8
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            with open(new_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(content)
        elif ext.lower() == '.txt':
            # Read and write text files with explicit UTF-8 encoding to avoid charmap errors
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            with open(new_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(content)
    except Exception as e:
        print(f"Error converting {os.path.relpath(new_path, dst_directory)}: {e}")

def process_files(start_path, destination_path):
    for root, dirs, files in os.walk(start_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, start_path)
            target_folder = os.path.join(destination_path, relative_path)
            ensure_dir(target_folder)  # Make sure the target directory exists
            convert_file(file_path, target_folder)

# Ensure the destination directory exists
ensure_dir(dst_directory)

# Start processing
process_files(src_directory, dst_directory)

print("Processing complete.")

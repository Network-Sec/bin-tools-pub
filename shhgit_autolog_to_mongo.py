#!/usr/bin/env python3

# Note that we customized our version of shhgit, unsure if the autolog file is produced by default in the format we expect here, probably not? Sorry....

import pymongo
import os
import time
import csv
from datetime import datetime, timedelta
import hashlib
import json
from pymongo import MongoClient
import shutil
import sys
from tabulate import tabulate
import re
import requests
from time import sleep

# MongoDB setup
client = pymongo.MongoClient('mongodb://...')  # Connect to remote MongoDB, can be replaced with localhost
db = client['...']  # Database where you want to insert documents
collection = db['...']  # Assuming 'events' is your collection

# Get today's date for the CSV file
yesterday_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
today_date = datetime.today().strftime('%Y-%m-%d')
tomorrow_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')

csv_filename = f'/shhgit_downloads/auto_log.csv'

# Track the position in the file
last_position = 0

def generate_log_file_path():
    """Generate the log file path based on the current date and time."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"/tmp/autolog_{timestamp}.log"

# Initialize the log file
log_file_path = generate_log_file_path()

def get_terminal_size():
    """Get the current terminal size (rows and columns)."""
    size = shutil.get_terminal_size()
    return size.columns, size.lines

# Initial values for terminal size and entries count
cached_columns, cached_rows = get_terminal_size()
cached_entries_count = 0
all_entries = []

def generate_hash(entry):
    """Generate a unique hash for the db_entry."""
    entry_string = json.dumps(entry, sort_keys=True, default=str)
    return hashlib.sha256(entry_string.encode('utf-8')).hexdigest()

def safe_string(value):
    """Ensure the value is a string and handle None values."""
    return str(value) if value is not None else ""

def format_and_print_table(entries, cached_columns, cached_rows, cached_entries_count):
    """Print entries in a formatted table, adjusting for terminal size."""
    columns, rows = get_terminal_size()

    headers = ["Project name", "Category", "Matching file", "Match Text"]
    table_data = []

    # Print only if new entries were added or terminal size changed
    if (columns, rows) != (cached_columns, cached_rows) or cached_entries_count != len(entries):
        for entry in entries:
            project_name = safe_string(entry.get("Project name", ""))
            category = safe_string(entry.get("Category", ""))
            matching_file = safe_string(entry.get("Matching file", ""))
            
            # Construct Match Text for display
            if entry.get("Category") == "User Info":
                login = entry.get("login", "")
                name = entry.get("name", "")
                email = entry.get("email", "")
                
                # Use login or fallback to name if login is missing
                username = login if login else name
                match_text = ', '.join(filter(None, [username, email]))  # Combine non-empty fields
            else:
                match_text = safe_string(entry.get("Match Text", ""))
            
            # Truncate fields if necessary
            formatted_entry = [
                project_name[:columns//4-3] + '...' if len(project_name) > columns//4 else project_name,
                category[:columns//4-3] + '...' if len(category) > columns//4 else category,
                matching_file[:columns//4-3] + '...' if len(matching_file) > columns//4 else matching_file,
                match_text[:columns//4-3] + '...' if len(match_text) > columns//4 else match_text
            ]
            table_data.append(formatted_entry)

        # Print and log table content at once
        if table_data:
            table_content = tabulate(table_data, headers=headers, tablefmt="grid")
            with open(log_file_path, "w") as log_file:  # Open log file in write mode to write only once
                log_file.write(table_content + "\n\n")
            os.system('clear')
            print(table_content)

    return columns, rows, len(entries)

def add_entry_to_db(row, cached_columns, cached_rows, cached_entries_count, all_entries):
    """Add a new entry to the MongoDB collection with a unique hash."""
    db_entry = {
        "Project name": row['Project name'],
        "Category": row['Category'],
        "Matching file": row['Matching file'],
        "Match Text": row['Match Text']
    }

    # Generate and add unique hash
    unique_hash = generate_hash(db_entry)
    db_entry["unique_hash"] = unique_hash

    # Check if the entry already exists by hash
    if not collection.find_one({"unique_hash": unique_hash}):
        collection.insert_one(db_entry)
        #print(f"[+] Added: {db_entry}")
        all_entries.append(db_entry)
    else:
        print(f"[-] Duplicate entry skipping: {db_entry['Match Text']}")

    # Format and print the table
    return format_and_print_table(all_entries, cached_columns, cached_rows, cached_entries_count)

def fetch_and_update_api_data(user_info):
    """Fetch additional API data from dynamically detected GitHub URLs and update the user_info."""
    api_responses = {}

    # Regex pattern to match GitHub API URLs
    url_pattern = re.compile(r'https://api\.github\.com/[^\s",{}]+')
    
    # Search for all API URLs in the user_info dictionary
    for key, value in user_info.items():
        if isinstance(value, str) and url_pattern.match(value):
            # Clean up the URL to remove placeholders
            url = re.sub(r'{[^}]*}', '', value)
            
            try:
                sleep(3)
                response = requests.get(url)
                if response.status_code == 200:
                    api_responses[key] = response.json()
                else:
                    print(f"Failed to fetch {url}, status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Request failed for {url}: {e}")
    
    # Return the dictionary of API responses
    return api_responses

def handle_user_info(row):
    """Process and add 'User Info' entries to the MongoDB collection with JSON keys."""
    import json

    # Parse the JSON text in 'Match Text'
    user_info = json.loads(row['Match Text'])

    # Fetch additional data from GitHub API URLs dynamically
    #api_data = fetch_and_update_api_data(user_info)

    # Create the db_entry with individual JSON fields and include API data
    db_entry = {
        "Project name": row['Project name'],
        "Category": row['Category'],
        "Matching file": row['Matching file']
    }
    db_entry.update({k: v for k, v in user_info.items() if v is not None})
    #db_entry.update(api_data)

    # Generate and add unique hash
    unique_hash = generate_hash(db_entry)
    db_entry["unique_hash"] = unique_hash

    # Check if the entry already exists by hash
    if not collection.find_one({"unique_hash": unique_hash}):
        collection.insert_one(db_entry)
        all_entries.append(db_entry)
    else:
        print(f"[-] Duplicate entry skipping: {db_entry.get('login', 'No login')}")

    # Format and print the table
    global cached_columns, cached_rows, cached_entries_count
    cached_columns, cached_rows, cached_entries_count = format_and_print_table(all_entries, cached_columns, cached_rows, cached_entries_count)

def process_line(line):
    """Process a line from the CSV file and insert it into the MongoDB collection."""
    global cached_columns, cached_rows, cached_entries_count, all_entries

    reader = csv.DictReader([line], fieldnames=["Project name", "Category", "Matching file", "Match Text"])
    for row in reader:
        if row['Project name'] or row['Category'] or row['Matching file'] or row['Match Text']:
            if row['Category'] == "User Info":
                handle_user_info(row)
            else:
                cached_columns, cached_rows, cached_entries_count = add_entry_to_db(row, cached_columns, cached_rows, cached_entries_count, all_entries)

def monitor_csv():
    """Continuously monitor the CSV file for new entries and process them."""
    global last_position
    
    if not os.path.exists(csv_filename):
        print(f"[-] File {csv_filename} not found. Retrying...")
        time.sleep(5)  # Retry after a delay if the file isn't found yet
        return
    
    with open(csv_filename,  'r', encoding='utf-8', errors='ignore') as f:
        f.seek(last_position)
        for line in f:
            process_line(line)
        last_position = f.tell()

if __name__ == '__main__':
    while True:
        monitor_csv()
        time.sleep(2)  # Adjust the sleep time as necessary to control the frequency of checks

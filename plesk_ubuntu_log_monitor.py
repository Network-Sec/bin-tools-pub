#!/usr/bin/env python3

# On Plesk Ubuntu servers, it can be hard to keep an eye on rotated logs, cross domain
# The script provides a simplified, realtime output
# You may need to increase inodes: sysctl fs.inotify.max_user_watches=524288

# Example Output:
# 36.110.137.0    2024-03-12 15:22:37 network-sec.de                 Firefox/72 (Ubuntu)           
# 114.119.150.0   2024-03-12 15:22:37 network-sec.de                 Bot (Spider Desktop)          
# 52.167.144.0    2024-03-12 15:22:37 network-sec.de                 Bot (Spider Desktop)          
# 106.42.108.0    2024-03-12 15:22:37 network-sec.de                 Opera/63 (Windows)            
# 92.116.149.0    2024-03-12 15:22:37 blog.network-sec.de            Firefox/123 (Windows)         
# 149.88.102.0    2024-03-12 15:22:37 blog.network-sec.de            Firefox/123 (Windows)         
# 18.191.199.0    2024-03-12 15:22:37 blog.network-sec.de            Chrome/102 (Windows)          
# 85.206.169.0    2024-03-12 15:22:38 profile.network-sec.de         Other/ (Other)                
# 45.95.243.0     2024-03-12 15:22:38 profile.network-sec.de         Other/ (Other)     

import os
import sys
import gzip
import time
from datetime import datetime, timedelta
import argparse
import re
from user_agents import parse

# Regular expression to match the beginning of a line with an IP address
ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')

# Parse command line arguments for verbose output
parser = argparse.ArgumentParser(description='Log Monitor Script')
parser.add_argument('-v', '--verbose', action='store_true', help='Display full log line.')
args = parser.parse_args()

# Configurable parameters
log_dirs = ["/var/www/vhosts/network-sec.de/logs/", "/var/log/passenger/"]
time_window = timedelta(hours=1)  # Time window for IP uniqueness
interval = 10  # Interval to rerun the script, in seconds

# A dictionary to store the last time an IP was seen
unique_ips_last_seen = {}

def get_recent_log_files(directory, number_of_files=50):  # Increased number
    all_logs = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.gz', 'log', '_log')):
                full_path = os.path.join(root, file)
                all_logs.append((full_path, os.path.getmtime(full_path)))

    all_logs.sort(key=lambda x: x[1], reverse=True)
    return [log[0] for log in all_logs[:number_of_files]]



def read_log_file(file_path):
    """Read log file content, handle gzipped files."""
    try:
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt') as f:
                return f.readlines()
        else:
            with open(file_path, 'r') as f:
                return f.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

def is_valid_ip(line):
    """Check if the line starts with a valid IP address using regex."""
    return ip_pattern.match(line) is not None

def simplify_user_agent(user_agent_string):
    """Use the user_agents library to parse and simplify the User-Agent string."""
    ua = parse(user_agent_string)
    
    if ua.is_bot:
        return f"Bot ({ua.device.brand or 'Unknown'} {ua.device.model or 'Model'})"
    else:
        browser = ua.browser.family
        browser_version = '.'.join(filter(None, [ua.browser.version_string.split('.')[0]]))
        os = ua.os.family
        return f"{browser}/{browser_version} ({os})"

def extract_log_datetime(log_line):
    """Extracts the datetime from a log line and returns it as a datetime object."""
    datetime_match = re.search(r'\[(\d{2})/(\w{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2})', log_line)
    if datetime_match:
        day, month, year, hour, minute, second = datetime_match.groups()
        month_number = datetime.strptime(month, '%b').month  # Convert month abbreviation to number
        log_datetime = datetime(int(year), month_number, int(day), int(hour), int(minute), int(second))
        return log_datetime  # Return the datetime object directly
    else:
        return None  # Or handle as appropriate, e.g., by returning a 'default' datetime or None

def process_logs(logs, domain, time_window=timedelta(minutes=20)):
    log_entries = []  # Store tuples of (datetime, formatted_output)

    for line in logs:
        try:
            if not is_valid_ip(line):
                continue
            
            ip = line.split()[0]
            log_datetime = extract_log_datetime(line)
            if not log_datetime:
                continue  # Skip if datetime extraction failed

            if ip in unique_ips_last_seen:
                last_seen_log_time = unique_ips_last_seen[ip]
                if (log_datetime - last_seen_log_time) <= time_window:
                    continue  # Skip this IP as it's within the time window

            unique_ips_last_seen[ip] = log_datetime  # Update with the new log datetime

            user_agent_match = re.search(r'"([^"]+)"$', line)
            user_agent_summary = 'Unknown'
            if user_agent_match:
                user_agent_summary = simplify_user_agent(user_agent_match.group(1))

            formatted_output = f"{ip:<15} {log_datetime.strftime('%Y-%m-%d %H:%M:%S')} {domain:<30} {user_agent_summary}"
            log_entries.append((log_datetime, formatted_output))

        except Exception as e:
            print(f"Error processing line: {e}")

    # Sort log entries by datetime, ensuring chronological order
    log_entries.sort(key=lambda entry: entry[0])

    return log_entries

def monitor_logs():
    """Monitor log directories for the most recent and relevant logs."""
    log_entries = []
    for directory in log_dirs:
        log_files = get_recent_log_files(directory)
        for log_file in log_files:
            logs = read_log_file(log_file)
            domain = os.path.basename(os.path.dirname(log_file))  # Extract domain
            if domain in ["logs", "passenger"]:  # Adjust this condition based on your folder structure
                domain = "network-sec.de"  # Root domain name for logs outside specific subdomains
            log_entries.extend(process_logs(logs, domain))

    log_entries.sort(key=lambda entry: entry[0])

    # Print sorted log entries
    for _, entry in log_entries:
        print(entry)

while True:
    monitor_logs()
    time.sleep(interval)

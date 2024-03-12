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

def process_logs(logs, domain):
    """Process logs to find and output new unique IPs, using user_agents library for User-Agent categorization."""
    for line in logs:
        try:
            if not is_valid_ip(line):
                continue
            
            parts = line.split()
            ip = parts[0]
            current_time = datetime.now()

            if ip in unique_ips_last_seen and (current_time - unique_ips_last_seen[ip]) <= time_window:
                continue

            unique_ips_last_seen[ip] = current_time
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

            # Extract the User-Agent string from the log line
            user_agent_match = re.search(r'"([^"]+)"$', line)
            user_agent_summary = 'Unknown'
            if user_agent_match:
                user_agent_summary = simplify_user_agent(user_agent_match.group(1))

            if args.verbose:
                formatted_output = f"{ip:<15} {formatted_time} {domain:<30} {user_agent_summary:<30} ---- {line.strip()}"
            else:
                formatted_output = f"{ip:<15} {formatted_time} {domain:<30} {user_agent_summary:<30}"

            print(formatted_output)

        except Exception as e:
            print(f"Error processing line: {e}")


def monitor_logs():
    """Monitor log directories for the most recent and relevant logs."""
    for directory in log_dirs:
        log_files = get_recent_log_files(directory)
        for log_file in log_files:
            logs = read_log_file(log_file)
            domain = os.path.basename(os.path.dirname(log_file))  # Extract domain
            if domain in ["logs", "passenger"]:  # Adjust this condition based on your folder structure
                domain = "network-sec.de"  # Root domain name for logs outside specific subdomains
            process_logs(logs, domain)

while True:
    monitor_logs()
    time.sleep(interval)

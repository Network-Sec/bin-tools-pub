#!/usr/bin/env python3

import os
import requests

VERBOSE = False

# Get the directory where the script is stored
script_dir = os.path.dirname(os.path.abspath(__file__))

# Services filename - should be in the same dir as the script or you would need to change some code
services_filename = 'whats_my_IP_services.txt'

# Backup filenames
services_backup_filename = 'whats_my_IP_services_backup.txt'
last_index_backup_filename = 'last_index_backup.txt'

#### ----------------------------- NOTE ----------------------------- ####
## These are the defaults, you can change them here or inside the file. ##
#  The script will create the file if it does not exist, otherwise it    #
## will keep the file and don't change it.                              ##
#### ---------------------------------------------------------------- ####

# Create the list of services file, if it does not exist
default_services = [
    "https://api.ipify.org",
    "https://ipinfo.io/ip",
    "https://icanhazip.com",
    "https://ifconfig.me/ip",
    "https://ident.me",
    "https://ip.seeip.org",
    "https://checkip.amazonaws.com",
    "https://wtfismyip.com/text",
    "https://ipapi.co/ip",
    "https://myexternalip.com/raw",
    "https://www.trackip.net/ip",
    "https://bot.whatismyipaddress.com",
    "https://ipecho.net/plain",
    "https://eth0.me/",
    "https://myip.dnsomatic.com",
    "https://ip.tyk.nu",
    "https://l2.io/ip",
    "https://curlmyip.net",
    "https://getmyipaddress.org",
    "https://checkip.dyndns.org/plain"
]

# Set a reasonable timeout for HTTP requests (in seconds)
HTTP_TIMEOUT = 5

def backup_file(filename, backup_filename):
    file_path = os.path.join(script_dir, filename)
    backup_path = os.path.join(script_dir, backup_filename)
    if os.path.exists(file_path):
        os.rename(file_path, backup_path)

def restore_file(backup_filename, filename):
    backup_path = os.path.join(script_dir, backup_filename)
    file_path = os.path.join(script_dir, filename)
    if os.path.exists(backup_path):
        os.rename(backup_path, file_path)

def initialize_service_file(filename=services_filename, services=[]):
    file_path = os.path.join(script_dir, filename)
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            for service in services:
                file.write(service + '\n')

def read_service_list(filename):
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r') as file:
            services = [line.strip() for line in file if line.strip()]
            # Validate the URLs
            services = [service for service in services if service.startswith("http")]
        return services
    except Exception as e:
        if VERBOSE: 
            print(f"Error reading service list: {e}")
        return []

def store_last_used_index(index, filename='last_index.txt'):
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'w') as file:
            file.write(str(index))
    except Exception as e:
        print(f"Error storing last used index: {e}")

def load_last_used_index(filename='last_index.txt'):
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r') as file:
            return int(file.read().strip())
    except Exception as e:
        if VERBOSE: 
            print(f"Error loading last used index: {e}")
        return -1  # Start from the first URL if the index file does not exist or is invalid

def get_current_ip(service_url):
    try:
        response = requests.get(service_url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()  # Raise an error on bad status
        return response.text.strip(), service_url
    except Exception as e:
        if VERBOSE: 
            print(f"Failed to get IP from {service_url}: {e}")
        return None, service_url

def main():
    # Initialize the services file if it does not exist
    initialize_service_file(services_filename, default_services)

    # Read and validate the service list
    services = read_service_list(services_filename)
    if not services:
        raise Exception("No valid services available to check IP.")

    # Backup the current services file
    backup_file(services_filename, services_backup_filename)

    # Load and validate the last used index
    last_index = load_last_used_index()
    if last_index < 0 or last_index >= len(services):
        last_index = -1

    next_index = (last_index + 1) % len(services)
    
    current_ip = None
    attempts = 0

    while current_ip is None and attempts < len(services):
        current_ip, service_url = get_current_ip(services[next_index])
        if current_ip is None:
            next_index = (next_index + 1) % len(services)
            attempts += 1
            if attempts == len(services):  # Prevent infinite loop if all services fail
                raise Exception("All services are down or unreachable.")
    
    print(f"Service used: {service_url} | Current IP: {current_ip}")

    # Backup the current last index file
    backup_file('last_index.txt', last_index_backup_filename)

    # Store the new last used index
    store_last_used_index(next_index)

if __name__ == '__main__':
    main()


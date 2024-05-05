#!/usr/bin/env python3

import os
import requests

# Get the directory where the script is stored
script_dir = os.path.dirname(os.path.abspath(__file__))

# Services filename - should be in same dir as the script or you would need to change some code
services_filename = 'whats_my_IP_services.txt'

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

#### ----------------------------- NOTE ----------------------------- ####
## These are the defaults, you can change them here or inside the file. ##
#  The script will create the file if it does not exist, otherwise it    #
## will keep the file and don't change it.                              ##
#### ---------------------------------------------------------------- ####

def initialize_service_file(filename=services_filename, services=[]):
    file_path = os.path.join(script_dir, filename)
    # Check if the file exists
    if not os.path.exists(file_path):
        # If the file does not exist, create it and write the services
        with open(file_path, 'w') as file:
            for service in services:
                file.write(service + '\n')

def read_service_list(filename):
    file_path = os.path.join(script_dir, filename)
    with open(file_path, 'r') as file:
        services = [line.strip() for line in file if line.strip()]
    return services

def store_last_used_index(index, filename='last_index.txt'):
    file_path = os.path.join(script_dir, filename)
    with open(file_path, 'w') as file:
        file.write(str(index))

def load_last_used_index(filename='last_index.txt'):
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return -1  # Start from the first URL if the index file does not exist

def get_current_ip(service_url):
    try:
        response = requests.get(service_url)
        response.raise_for_status()  # Raise an error on bad status
        return response.text.strip(), service_url
    except Exception as e:
        print(f"Failed to get IP from {service_url}")
        return None, service_url

def main():
    # Initialize the services file if it does not exist
    initialize_service_file(services_filename, default_services)

    services = read_service_list(services_filename)
    last_index = load_last_used_index()
    next_index = (last_index + 1) % len(services)
    
    current_ip = None
    while current_ip is None:
        current_ip, service_url = get_current_ip(services[next_index])
        if current_ip is None:
            next_index = (next_index + 1) % len(services)
            if next_index == last_index:  # Prevent infinite loop if all services fail
                raise Exception("All services are down or unreachable.")
    
    print(f"Service used: {service_url} | Current IP: {current_ip}")
    store_last_used_index(next_index)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3

# Simple script to add kismet API devices to mongoDB
# Nothing fancy, maybe the beginning of another great journey

import requests
from pymongo import MongoClient
import time

# MongoDB setup
client = MongoClient('mongodb://user:pwd@host:27017/db?authSource=admin')
db = client['wifiprint']
db_wifi = db['wifiprint_w']
db_bluetooth = db['wifiprint_b']

def fetch_data_from_kismet():
    # Assuming Kismet's running on localhost:2501
    url = 'http://localhost:2501/devices/views/all/devices.json?user=...&password=...'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def process_and_store_data(data):
    count = 0
    for device in data:
        # Example filter condition, adjust based on actual device structure
        devtype = device['kismet.device.base.type'].lower()
        if 'wifi' in devtype or 'wi-fi' in devtype:
            count += 1
            db_wifi.devices.insert_one(device)
        elif device['kismet.device.base.type'] == 'bluetooth':
            db_bluetooth.devices.insert_one(device)
    print("[…] added ", count)

while True:
    data = fetch_data_from_kismet()
    if data:
        print("[+] Adding...")
        process_and_store_data(data)
    time.sleep(10)  

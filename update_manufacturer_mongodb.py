#!/usr/bin/env python3

# This is one of our microservices / sidecar scripts for our intel and analytics plattform BlackViz Wifi
# Updates device manufacturer based on first 3 octets in mongoDB
# Needs prepped oui.txt (see wordlists or download yourself)

from pymongo import MongoClient, UpdateOne
from bson.objectid import ObjectId
from datetime import datetime

# Connect to MongoDB
db_client = MongoClient('mongodb://localhost:27017/')
db = db_client['wifi_dumps'] 
collection = db['wifi_data'] 

# Load prepped OUI data
def load_oui_data(oui_file):
    oui_dict = {}
    with open(oui_file, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                mac_prefix, manufacturer = line.split(maxsplit=1)
                oui_dict[mac_prefix.upper()] = manufacturer.strip()
    return oui_dict

# Lookup manufacturer
def lookup_manufacturer(mac, oui_dict):
    if type(mac) == list:
        mac = mac[0]
    oui = mac[:8].upper()  # Extract OUI (first 8 characters)
    return oui_dict.get(oui, None)

# Update MongoDB entries in bulk
def update_manufacturers(db, oui_dict):
    entries = collection.find()

    bulk_updates = []

    for entry in entries:
        if entry.get('bssid') == "Unknown":
            continue
        updated = False
        if 'bssid' in entry and not 'manufacturer' in entry:
            manufacturer = lookup_manufacturer(entry['bssid'], oui_dict)
            print(entry['bssid'], " |", manufacturer)
            if manufacturer:
                entry['manufacturer'] = manufacturer
                updated = True

        # Update client-level station MAC manufacturers
        if 'clients' in entry:
            for client in entry['clients']:
                if 'station_mac' in client and not 'manufacturer' in client:
                    manufacturer = lookup_manufacturer(client['station_mac'], oui_dict)
                    print(client['station_mac'], " |", manufacturer)
                    if manufacturer:
                        client['manufacturer'] = manufacturer
                        updated = True

        # Prepare bulk update
        if updated:
            bulk_updates.append(UpdateOne({"_id": entry["_id"]}, {"$set": entry}))

    # Apply bulk updates
    if bulk_updates:
        result = collection.bulk_write(bulk_updates)
        print(f"Bulk update completed. Matched: {result.matched_count}, Modified: {result.modified_count}")

if __name__ == '__main__':
    # Path to the prepped OUI file
    oui_file = 'oui.txt'  # Replace with the path to your prepped OUI file

    # Load OUI data
    oui_dict = load_oui_data(oui_file)

    # Update manufacturers in the database
    update_manufacturers(db, oui_dict)

    print("Manufacturer update completed.")

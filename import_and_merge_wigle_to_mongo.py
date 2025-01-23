#!/usr/bin/env python3

# This is one of our microservice / sidecar tools for your BlackViz WiFi plattform (unreleased)
# Imports wigle csv export, pulls addresses from openstreetmap.org and tries merging with existing objects in mongoDB, or adding new records
# Some TODOs remaing... at some point we'll move these scripts into it's own repo

import argparse
from pymongo import MongoClient
import requests
import csv

# MongoDB connection
client = MongoClient("mongodb://....")
db = client["wifi_dumps"]
collection = db["wifi_data"]

# Geocoding API settings
GEOCODE_API_URL = "https://nominatim.openstreetmap.org/reverse"
GEOCODE_API_PARAMS = {
    "format": "json",
    "addressdetails": 1,
}
GEO_headers = {
    "Accept": "application/json",
    "User-Agent": "curl/7.64.1"
}

def process_csv_line(line):
    """Parse a CSV line into a dictionary."""
    record = {k: v for k, v in line.items() if v.strip()}  # Remove empty keys
    return record

def merge_arrays(existing, new):
    """Merge arrays with unique values."""
    if isinstance(existing, list):
        return list(set(existing + [new]))
    elif existing:
        return list(set([existing, new]))
    else:
        return [new]

def geocode(latitude, longitude):
    """Convert latitude and longitude into structured address components."""
    if not latitude or not longitude:
        return None

    response = requests.get(GEOCODE_API_URL, params={**GEOCODE_API_PARAMS, "lat": latitude, "lon": longitude}, headers=GEO_headers)
    print("Response:", response.status_code, response.headers, response.request.url)

    if response:
        data = response.json()
        address = data.get("address", {})
        house_number = ''
        if address.get("house_number"):
            house_number = address.get("house_number")
        if address.get("housenumber"):
            house_number = address.get("housenumber")
        return {
            "housenumber": house_number,
            "street": address.get("road"),
            "postalcode": address.get("postcode"),
            "region": address.get("state"),
            'neighbourhood': address.get("neighbourhood"), 
            'suburb': address.get("suburb"), 
            'city': address.get("city"),
            'country': address.get("country")
        }

    return None

def update_or_add_entry(record):
    """Update an existing entry or add a new one."""
    print("----------- RECORD ----------")
    print(record)

    mac = record.get("MAC").upper() if record.get("MAC") else None
    ssid = record.get("SSID")

    # Stage 1: Match by MAC
    query = {"$or": [
        {"bssid": mac}
    ]}

    geocoded_address = geocode(record.get("CurrentLatitude"), record.get("CurrentLongitude"))
    if (geocoded_address):
        print("Found address", geocoded_address)

    dbentries = list(collection.find(query))

    if not len(dbentries):
        # Stage 2: Match by SSID
        print("BSSID not found...")
        query = {"essid": ssid}
        dbentries = list(collection.find(query).limit(100))

    if dbentries:
        print("Found DB entries", len(dbentries))
    else:
        print("No entries found")

    if dbentries:
        for dbentry in dbentries:
            if dbentry.get('bssid') and "Unknown" in dbentry.get('bssid'):
                continue
            print("Updating", dbentry.get('bssid'), dbentry.get('essid'))

            # Update existing entry
            updates = {}

            # Update `wigle`
            if "wigle" not in dbentry:
                updates["wigle"] = [record]
            else:
                wigle_entries = dbentry["wigle"]
                if record not in wigle_entries:
                    wigle_entries.append(record)
                    updates["wigle"] = wigle_entries

            # Update main fields
            if mac:
                merged_bssid = merge_arrays(dbentry.get("bssid", []), mac)
                updates["bssid"] = list(set(merged_bssid))
            if ssid:
                merged_essid = merge_arrays(dbentry.get("essid", []), ssid)
                updates["essid"] = list(set(merged_essid))

            if "FirstSeen" in record:
                fseen = merge_arrays(dbentry.get("first_seen", []), record["FirstSeen"])
                updates["first_seen"] = list(set(fseen))
                lseen = merge_arrays(dbentry.get("last_seen", []), record["FirstSeen"])
                updates["last_seen"] = list(set(lseen))
            if "Channel" in record:
                cn = merge_arrays(dbentry.get("channel", []), record["Channel"])
                updates["channel"] = list(set(cn))
            if "Type" in record:
                updates["network_type"] = record["Type"]

            # Add latitude and longitude only if not preexisting
            if not dbentry.get("latitude"):
                updates["latitude"] = record.get("CurrentLatitude")
            if not dbentry.get("longitude"):
                updates["longitude"] = record.get("CurrentLongitude")

            # Geocode if latitude and longitude are available

            if geocoded_address:
                other_locations = dbentry.get("other_locations", [])
                other_locations.append(geocoded_address)
                updates["other_locations"] = other_locations
                # Check for each key in geocoded_address
                address_keys_to_update = {}
                conflicting_address = {}

                for key, value in geocoded_address.items():
                    if not dbentry.get(key):  # Key doesn't exist in dbentry
                        address_keys_to_update[key] = value
                    elif dbentry.get(key) != value:  # Key exists but value differs
                        conflicting_address[key] = dbentry[key]

                # If there are conflicts, add existing address to other_locations
                if conflicting_address:
                    other_locations.append(conflicting_address)
                    updates["other_locations"] = other_locations

                # Overwrite dbentry address items with new values
                updates.update(address_keys_to_update)

            # Add remaining keys as lowercase to root level
            for key, value in record.items():
                if key not in ["MAC", "SSID", "FirstSeen", "Channel", "Type", "CurrentLatitude", "CurrentLongitude"]:
                    updates[key.lower()] = value

            # Perform update
            print("Updates:", updates)
            updated_record = collection.update_one({"_id": dbentry["_id"]}, {"$set": updates})
    else:
        # Add as new entry
        new_entry = {
            "bssid": [mac] if mac else [],
            "essid": [ssid] if ssid else [],
            "first_seen": [record.get("FirstSeen", "")],
            "last_seen": [record.get("FirstSeen", "")],
            "channel": [record.get("Channel", "")],
            "latitude": record.get("CurrentLatitude"),
            "longitude": record.get("CurrentLongitude"),
            "network_type": record.get("Type"),
            "wigle": [record],
        }
        if geocoded_address:
            new_entry["other_locations"] = [geocoded_address]
            for key, value in geocoded_address.items():
                new_entry[key] = value

        for key, value in record.items():
            if key not in ["MAC", "SSID", "FirstSeen", "Channel", "Type", "CurrentLatitude", "CurrentLongitude"]:
                new_entry[key.lower()] = value

        print("New entry:", new_entry)
        collection.insert_one(new_entry)

def main():
    parser = argparse.ArgumentParser(description="Process a CSV file and update MongoDB.")
    parser.add_argument("csv_file", help="Path to the CSV file.")
    args = parser.parse_args()

    # Read CSV file
    with open(args.csv_file, "r") as file:
        lines = file.readlines()

        # Remove the first line if it starts with 'WigleWifi'
        if lines[0].startswith('WigleWifi'):
            lines = lines[1:]

        # Use csv.DictReader with the filtered lines
        reader = csv.DictReader(lines)
        rows = list(reader)
        for line in rows:
            csv_record = process_csv_line(line)
            update_or_add_entry(csv_record)

if __name__ == "__main__":
    main()

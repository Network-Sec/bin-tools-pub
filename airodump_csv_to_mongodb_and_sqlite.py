#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import os
import sqlite3
from pymongo import MongoClient

# MongoDB and SQLite connection details
MONGO_URI = "mongodb://...."
MONGO_DB_NAME = "wifidumps"
SQLITE_DB_PATH = "wifidumps.db"


def connect_databases():
    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URI)  # Connect to MongoDB
    mongo_db = mongo_client[MONGO_DB_NAME]  # Access the database
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)  # Connect to SQLite
    sqlite_cursor = sqlite_conn.cursor()  # Create a cursor for SQLite
    
    # Create tables in SQLite if they don't exist
    
    # Updated client_data table schema
    sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS client_data (
        station_mac TEXT,
        first_seen TEXT,
        last_seen TEXT,
        power INTEGER,
        num_packets INTEGER,
        bssid TEXT,
        probed_essids TEXT,
        PRIMARY KEY (station_mac, first_seen)
    )''')
    
    # Updated station_data table schema
    sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS station_data (
        bssid TEXT,  -- Added column for BSSID
        first_seen TEXT,
        last_seen TEXT,
        channel INTEGER,  -- Added column for channel
        speed INTEGER,  -- Added column for speed
        privacy TEXT,  -- Added column for privacy
        cipher TEXT,  -- Added column for cipher
        authentication TEXT,  -- Added column for authentication
        power INTEGER,  -- Added column for power
        beacon_count INTEGER,  -- Added column for # of beacons
        iv INTEGER,  -- Added column for # of IV
        lan_ip TEXT,  -- Added column for LAN IP
        id_length INTEGER,  -- Added column for ID length
        essid TEXT,  -- Added column for ESSID
        key TEXT,  -- Added column for key
        PRIMARY KEY (bssid, first_seen)
    )''')
    
    # Commit the table creation if needed
    sqlite_conn.commit()
    
    # Return database connections
    return mongo_db, sqlite_conn, sqlite_cursor

import re

def parse_csv(file_path):
    with open(file_path, 'r') as csv_file:
        client_data = []
        station_data = []

        section = None
        headers = None

        for line in csv_file:
            line = line.strip()  # Remove leading/trailing whitespace
            if not line:  # Skip empty lines
                continue

            # Detect sections by headers
            if line.startswith("BSSID"):
                section = "station"
                headers = re.split(r",\s*", line.strip())  # Split headers by commas, allow for surrounding spaces
                headers = [header.strip() for header in headers]  # Normalize header whitespaces
                continue
            elif line.startswith("Station MAC"):
                section = "client"
                headers = re.split(r",\s*", line.strip())  # Split headers by commas, allow for surrounding spaces
                headers = [header.strip() for header in headers]  # Normalize header whitespaces
                continue

            if section == "client" or section == "station":
                # Split row values while preserving the last column (Probed ESSIDs)
                values = re.split(r",\s*", line.strip(), len(headers) - 1)  # Only split up to the second-last column
                row_dict = {headers[i]: values[i].strip() if i < len(values) else None for i in range(len(headers))}
                
                if section == "client":
                    client_data.append(row_dict)
                elif section == "station":
                    station_data.append(row_dict)

        return client_data, station_data


def parse_hashes(file_path):
    try:
        with open(file_path, 'r') as hash_file:
            hashes = [line.strip() for line in hash_file.readlines()]
        return hashes
    except:
        return None

def ensure_list(value):
    """Ensure the value is a list."""
    if isinstance(value, list):
        return value
    elif value is None or value == "":
        return []
    else:
        return [value]

def update_mongodb(db, station_data, client_data, hashes):
    device_collection = db["wifi_data"]

    # Update station data in MongoDB
    for station in station_data:
        print(f"Processing AP: {station}")

        # Extract variables
        bssid = station.get("BSSID")
        essid = station.get("ESSID")
        channel = ensure_list(station.get("channel"))
        speed = station.get("Speed")
        privacy = station.get("Privacy")
        cipher = station.get("Cipher")
        authentication = station.get("Authentication")
        power = ensure_list(station.get("Power"))
        first_seen = ensure_list(station.get("First time seen"))
        last_seen = ensure_list(station.get("Last time seen"))
        beacon_count = station.get("# beacons")
        iv = station.get("# IV")
        lan_ip = station.get("LAN IP")
        id_length = station.get("ID-length")
        key = station.get("Key")

        # Match hashes based on the bssid or related extracted info
        station_hashes = []
        if hashes:
            for hash_line in hashes:
                extracted_mac_or_ssid = extract_station_mac_from_hash(hash_line)
                if extracted_mac_or_ssid and extracted_mac_or_ssid in essid:
                    station_hashes.append(hash_line)

        # Identify existing device in MongoDB using BSSID
        entry = device_collection.find_one({"bssid": bssid})

        if entry:
            entry["bssid"] = list(set(ensure_list(entry.get("bssid")) + [bssid]))
            entry["channel"] = list(set(ensure_list(entry.get("channel")) + channel))
            entry["power"] = list(set(ensure_list(entry.get("power")) + power))
            entry["first_seen"] = list(set(ensure_list(entry.get("first_seen")) + first_seen))
            entry["last_seen"] = list(set(ensure_list(entry.get("last_seen")) + last_seen))
            entry["essid"] = essid
            entry["device_type"] = "station"
            entry["hashes"] = list(set(ensure_list(entry.get("hashes")) + station_hashes))
            entry["beacon_count"] = beacon_count
            entry["iv"] = iv
            entry["lan_ip"] = lan_ip
            entry["id_length"] = id_length
            entry["key"] = key
        else:
            entry = {
                "bssid": bssid,
                "essid": essid,
                "channel": channel,
                "power": power,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "speed": speed,
                "privacy": privacy,
                "cipher": cipher,
                "authentication": authentication,
                "device_type": "station",
                "beacon_count": beacon_count,
                "iv": iv,
                "lan_ip": lan_ip,
                "id_length": id_length,
                "key": key,
                "hashes": station_hashes
            }

        # Push updated data to MongoDB
        try:
            device_collection.update_one({"bssid": bssid}, {"$set": entry}, upsert=True)
        except:
            print("Couldnt update, entry")

    # Update client data in MongoDB
    today = datetime.date.today()
    unknown = "Unknown_" + today.strftime('%Y_%m_%d')
    u_first_seen = u_last_seen = today.strftime('%Y-%m-%d')
    beacon_station_bssid = "00:00:00:" + today.strftime('%y:%m:%d')
    for client in client_data:
        print(f"Processing client: {client}")

        # Extract variables
        station_mac = client.get("Station MAC")
        associated_ap = client.get("BSSID").strip()
        probed_essids = ensure_list(client.get("Probed ESSIDs", "").split(',') if client.get("Probed ESSIDs") else [])    
        power = ensure_list(client.get("Power"))
        first_seen = ensure_list(client.get("First time seen"))
        last_seen = ensure_list(client.get("Last time seen"))
        packets = ensure_list([client.get("# packets")])

        # Debugging output for client variables
        print(f"""
        Debugging Client Variables:
        Station MAC: {station_mac}
        Associated AP: {associated_ap}
        Probed ESSIDs: {probed_essids}
        Power: {power}
        First Seen: {first_seen}
        Last Seen: {last_seen}
        Packets: {packets}
        """)

        if associated_ap == "(not associated)":
            associated_ap = unknown

            for essid in probed_essids:
                entry = device_collection.find_one({"essid": essid, "attributes": "beacon_station"})

                if entry:
                    # Beacon station exists, update client data
                    existing_client = next((c for c in entry["clients"] if c["station_mac"] == station_mac), None)
                    if existing_client:
                        # Update existing client data
                        existing_client["probed_essids"] = list(set(existing_client.get("probed_essids", []) + probed_essids))
                        existing_client["power"] = list(set(existing_client.get("power", []) + power))
                        existing_client["first_seen"] = list(set(existing_client.get("first_seen", []) + first_seen))
                        existing_client["last_seen"] = list(set(existing_client.get("last_seen", []) + last_seen))
                        existing_client["packets"] = list(set(existing_client.get("packets", []) + packets))
                    else:
                        # Add new client to existing beacon station
                        entry["clients"].append({
                            "station_mac": station_mac,
                            "probed_essids": probed_essids,
                            "power": power,
                            "first_seen": first_seen,
                            "last_seen": last_seen,
                            "packets": packets,
                            "device_type": "client"
                        })
                    device_collection.update_one({"_id": entry["_id"]}, {"$set": {"clients": entry["clients"]}})
                else:
                    # Create a new beacon station
                    new_entry = {
                        "essid": essid,
                        "bssid": beacon_station_bssid,
                        "first_seen": [u_first_seen],
                        "last_seen": [u_last_seen],
                        "device_type": "station",
                        "attributes": "beacon_station",
                        "clients": [{
                            "station_mac": station_mac,
                            "probed_essids": probed_essids,
                            "power": power,
                            "first_seen": first_seen,
                            "last_seen": last_seen,
                            "packets": packets,
                            "device_type": "client"
                        }]
                    }
                    device_collection.insert_one(new_entry)
                    # Case 1: Handle "Unknown" associated AP
                    if associated_ap == unknown:
                        entry = device_collection.find_one({"essid": unknown})

                        if not entry:
                            entry = {
                                "essid": unknown,
                                "bssid": "00:00:00:00:00:00",
                                "device_type": "station",
                                "first_seen": [u_first_seen],
                                "last_seen": [u_last_seen],
                                "clients": []
                            }
                            device_collection.insert_one(entry)

                        # Check for existing client in the entry
                        existing_client = None
                        if entry.get("clients"):
                            for c in entry["clients"]:
                                if c["station_mac"] == station_mac:
                                    existing_client = c
                                    break

                        if existing_client:
                            # Update existing client data
                            existing_client["probed_essids"] = list(set(ensure_list(existing_client.get("probed_essids", [])) + probed_essids))
                            existing_client["power"] = list(set(ensure_list(existing_client.get("power", [])) + power))
                            existing_client["first_seen"] = list(set(ensure_list(existing_client.get("first_seen", [])) + first_seen))
                            existing_client["last_seen"] = list(set(ensure_list(existing_client.get("last_seen", [])) + last_seen))
                            existing_client["packets"] = list(set(ensure_list(existing_client.get("packets", [])) + packets))
                        else:
                            # Add new client data
                            entry["clients"].append({
                                "station_mac": station_mac,
                                "probed_essids": probed_essids,
                                "power": power,
                                "first_seen": first_seen,
                                "last_seen": last_seen,
                                "packets": packets,
                                "device_type": "client"
                            })

                        # Push updated "Unknown" entry to MongoDB
                        try:
                            device_collection.update_one({"bssid": unknown}, {"$set": {"clients": entry["clients"]}}, upsert=True)
                        except:
                            print("Couldnt update", entry)

                    # Case 2: Handle clients associated with a specific AP
                    else:
                        entry = device_collection.find_one({"bssid": associated_ap})

                        if not entry:
                            # Case 3: Create a new station entry if it doesn't exist, including the client data
                            entry = {
                                "bssid": associated_ap,
                                "device_type": "station",
                                "clients": [{
                                    "station_mac": station_mac,
                                    "probed_essids": probed_essids,
                                    "power": power,
                                    "first_seen": first_seen,
                                    "last_seen": last_seen,
                                    "packets": packets,
                                    "device_type": "client"
                                }]
                            }
                            device_collection.insert_one(entry)
                        else:
                            # Case 2: Check for existing client in the entry
                            existing_client = None
                            if entry.get("clients"):
                                for c in entry["clients"]:
                                    if c["station_mac"] == station_mac:
                                        existing_client = c
                                        break

                            if existing_client:
                                # Update existing client data
                                existing_client["probed_essids"] = list(set(ensure_list(existing_client.get("probed_essids", [])) + probed_essids))
                                existing_client["power"] = list(set(ensure_list(existing_client.get("power", [])) + power))
                                existing_client["first_seen"] = list(set(ensure_list(existing_client.get("first_seen", [])) + first_seen))
                                existing_client["last_seen"] = list(set(ensure_list(existing_client.get("last_seen", [])) + last_seen))
                                existing_client["packets"] = list(set(ensure_list(existing_client.get("packets", [])) + packets))
                            else:
                                # Add new client data
                                print(entry)
                                if not entry.get("clients"):
                                    entry["clients"] = []

                                entry["clients"].append({
                                    "station_mac": station_mac,
                                    "probed_essids": probed_essids,
                                    "power": power,
                                    "first_seen": first_seen,
                                    "last_seen": last_seen,
                                    "packets": packets,
                                    "device_type": "client"
                                })

                            # Push updated entry to MongoDB
                            try:
                                device_collection.update_one({"bssid": associated_ap}, {"$set": {"clients": entry["clients"]}}, upsert=True)
                            except:
                                print("Couldnt update", entry)

def update_sqlite(cursor, conn, client_data, station_data, hashes):
    # Insert clients
    for client in client_data:
        station_mac = client.get("Station MAC")
        first_seen = client.get("First time seen")
        last_seen = client.get("Last time seen")
        power = client.get("Power")
        num_packets = client.get("# packets", 0)  # Default to 0 if None
        bssid = client.get("BSSID")
        probed_essids = client.get("Probed ESSIDs", "")

        cursor.execute('''INSERT INTO client_data 
                          (station_mac, first_seen, last_seen, power, num_packets, bssid, probed_essids) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                       (station_mac, first_seen, last_seen, power, num_packets, bssid, probed_essids))

    # Insert stations
    for station in station_data:
        bssid = station.get("BSSID")
        first_seen = station.get("First time seen")
        last_seen = station.get("Last time seen")
        channel = station.get("channel")
        speed = station.get("Speed")
        privacy = station.get("Privacy", "")  # Set default value if None
        cipher = station.get("Cipher", "")  # Set default value if None
        authentication = station.get("Authentication", "")  # Set default value if None
        power = station.get("Power")
        beacon_count = station.get("# beacons", 0)  # Set default value if None
        iv = station.get("# IV", 0)  # Set default value if None
        lan_ip = station.get("LAN IP", "")  # Set default value if None
        id_length = station.get("ID-length", 0)  # Set default value if None
        essid = station.get("ESSID", "")  # Set default value if None
        key = station.get("Key", "")  # Set default value if None

        cursor.execute('''INSERT INTO station_data 
                          (bssid, first_seen, last_seen, channel, speed, privacy, cipher, authentication, power, beacon_count, iv, lan_ip, id_length, essid, key) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (bssid, first_seen, last_seen, channel, speed, privacy, cipher, authentication, power, beacon_count, iv, lan_ip, id_length, essid, key))

    conn.commit()

def extract_station_mac_from_hash(hash_line):
    segments = hash_line.split('*')
    if len(segments) > 3 and segments[0].startswith('WPA'):
        ssid_hex = segments[5]
        ssid_python = bytes.fromhex(ssid_hex).decode('utf-8', 'replace')
        # Assuming station MAC could be part of the hash (modify if needed)
        return ssid_python  # Adjust if you identify a station MAC in the hash
    return None

def main():
    parser = argparse.ArgumentParser(description="Process airodump CSV and hash files into databases.")
    parser.add_argument("--csv", required=True, help="Path to the airodump CSV file.")
    parser.add_argument("--hashes", required=True, help="Path to the hashes file.")
    args = parser.parse_args()

    # Parse files
    client_data, station_data = parse_csv(args.csv)
    hashes = parse_hashes(args.hashes)

    # Connect to databases
    mongo_db, sqlite_conn, sqlite_cursor = connect_databases()

    # Update MongoDB and SQLite
    update_mongodb(mongo_db, station_data, client_data, hashes)
    update_sqlite(sqlite_cursor, sqlite_conn, client_data, station_data, hashes)

    print("Databases updated successfully.")

if __name__ == "__main__":
    main()

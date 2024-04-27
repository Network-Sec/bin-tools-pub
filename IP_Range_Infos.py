#!/usr/bin/env python3

# Download Databases and CSV from:
# CSV : https://datahub.io/core/geoip2-ipv4  
# MMDB: https://github.com/P3TERX/GeoLite.mmdb  

import maxminddb
import csv
import ipaddress
import os
import argparse
import sys
from tabulate import tabulate
from termcolor import colored

# Constants for the MMDB and CSV files
FOLDER_PATH = "/mnt/d/IP_Ranges/"
ASN_DB_PATH = os.path.join(FOLDER_PATH, "GeoLite2-ASN.mmdb")
CITY_DB_PATH = os.path.join(FOLDER_PATH, "GeoLite2-City.mmdb")
COUNTRY_DB_PATH = os.path.join(FOLDER_PATH, "GeoLite2-Country.mmdb")

def load_mmdb(db_path):
    try:
        return maxminddb.open_database(db_path)
    except Exception as e:
        print(colored(f"Error loading {db_path}: {e}", 'red'))
        sys.exit(1)

def query_mmdb(db, ip, lang='en'):
    try:
        result = db.get(ip)
        if not result:
            return {"Error": f"No data found for IP {ip}"}
        return flatten_json(result, lang)
    except Exception as e:
        return {"Error": str(e)}

def flatten_json(data, lang='en', parent_key='', sep='_'):
    items = {}
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            if 'names' in v and isinstance(v['names'], dict):
                if lang in v['names']:
                    items[new_key] = v['names'][lang]  # Only add specified language
            else:
                items.update(flatten_json(v, lang, new_key, sep))
        else:
            items[new_key] = v
    return items


def load_csv_files():
    csv_files = [f for f in os.listdir(FOLDER_PATH) if f.endswith('.csv')]
    csv_data = {}
    for file in csv_files:
        with open(os.path.join(FOLDER_PATH, file), mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                network = ipaddress.ip_network(row['network'], strict=False)
                csv_data[network] = row
    return csv_data

def query_csv(csv_data, ip_network):
    results = []
    for network, data in csv_data.items():
        if network.overlaps(ip_network):
            results.append(data)
    return results if results else [{"Error": "No CSV data found for this range"}]

def get_ip_range(ip):
    ip_net = ipaddress.ip_network(ip, strict=False)
    first_ip = ip_net[0]
    last_ip = ip_net[-1]
    return str(first_ip), str(last_ip)

def flatten_json(data, lang='en', parent_key='', sep='_'):
    items = {}

    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            if 'names' in v and isinstance(v['names'], dict):
                # Extracting names based on selected language
                items[new_key] = v['names'].get(lang, v['names'].get('en', 'N/A'))
            else:
                # Recursive processing for nested dictionaries
                items.update(flatten_json(v, lang, new_key, sep))
        elif isinstance(v, list):
            if k == 'subdivisions':
                # Special handling for 'subdivisions' key
                for i, item in enumerate(v):
                    if 'names' in item and isinstance(item['names'], dict):
                        items[f"{new_key}_{i}"] = item['names'].get(lang, item['names'].get('en', 'N/A'))
                    else:
                        items.update(flatten_json(item, lang, f"{new_key}_{i}", sep))
            elif all(isinstance(i, dict) for i in v):  # Check if all items are dictionaries
                # Flatten each dictionary in the list and extract the name in the selected language
                items[new_key] = [flatten_json(item, lang, '', sep) for item in v]
            else:
                items[new_key] = ', '.join(map(str, v))
        else:
            items[new_key] = v

    return items

def hashable(v):
    if isinstance(v, list):
        return tuple(hashable(i) for i in v)
    elif isinstance(v, dict):
        return tuple((k, hashable(vv)) for k, vv in v.items())
    else:
        return v
    
def display_results(title, results, headers, summarize):
    print(colored(title, 'blue', attrs=['bold']))
    table = []

    if isinstance(results, dict):
        if summarize:
            # Summarize results by grouping consecutive IPs with identical data
            grouped_results = {}
            for ip in sorted(results.keys(), key=lambda x: ipaddress.ip_address(x)):
                data_tuple = tuple((k, hashable(v)) for k, v in results[ip].items())
                if data_tuple not in grouped_results:
                    grouped_results[data_tuple] = [ip]
                else:
                    grouped_results[data_tuple].append(ip)

            for data_tuple, ips in grouped_results.items():
                first_ip = ips[0]
                last_ip = ips[-1]
                data = dict(data_tuple)
                table.append([first_ip, last_ip] + [data.get(header, 'N/A') for header in headers[2:]])
        else:
            # Display each IP with its data
            for ip in sorted(results.keys(), key=lambda x: ipaddress.ip_address(x)):
                data = results[ip]
                table.append([ip] + [data.get(header, 'N/A') for header in headers[1:]])

    elif isinstance(results, list):
        # For CSV, display the CIDR range
        for data in results:
            network = data['network']
            table.append([network] + [data.get(header, 'N/A') for header in headers[1:]])

    if summarize and isinstance(results, dict):
        headers = ['From IP', 'To IP'] + headers[2:]
    else:
        headers = ['IP'] + headers[1:]

    print(tabulate(table, headers, tablefmt='grid'))

def parse_arguments():
    parser = argparse.ArgumentParser(description="Query IP address or range against local MMDB databases and CSV data.")
    parser.add_argument('ip', help="IP address or CIDR range to query")
    parser.add_argument('--language', default='en', help="Preferred language for names, default is English")
    parser.add_argument('-s', '--summarize', action='store_true', help="Summarize consecutive IPs with identical data")
    parser.add_argument('-l', '--location', action='store_true', help="Output only city table info (including lat and long location). When specifying one or more tables, only those will be searched. When ommiting any table, all will be searched.")
    parser.add_argument('-c', '--country', action='store_true', help="Output only country table info.")
    parser.add_argument('-a', '--asn', action='store_true', help="Output only asn table info. ASN is best when looking for companies or institutions")
    parser.add_argument('-r', '--ranges', action='store_true', help="Output only ranges (CSV) table info. Ranges will provide fastest results but only broad infos, like country")
    return parser.parse_args()

def main():
    args = parse_arguments()

    specified = False
    if args.location or args.country or args.asn or args.ranges:
        specified = True

    ip_input = args.ip
    preferred_language = args.language
    summarize = args.summarize

    try:
        ip_network = ipaddress.ip_network(ip_input, strict=False)
    except ValueError as e:
        print(colored(f"Invalid IP address or range: {e}", 'red'))
        return

    # Querying data
    csv_results = None
    if not specified or args.ranges:
        csv_data = load_csv_files()
        csv_results = query_csv(csv_data, ip_network)

    asn_results = None
    if not specified or args.asn:
        asn_db = load_mmdb(ASN_DB_PATH)
        asn_results = {str(ip): query_mmdb(asn_db, str(ip), preferred_language) for ip in ip_network}
        asn_db.close()

    city_results = None
    if not specified or args.location:
        city_db = load_mmdb(CITY_DB_PATH)
        city_results = {str(ip): query_mmdb(city_db, str(ip), preferred_language) for ip in ip_network}
        city_db.close()

    country_results = None
    if not specified or args.country:
        country_db = load_mmdb(COUNTRY_DB_PATH)
        country_results = {str(ip): query_mmdb(country_db, str(ip), preferred_language) for ip in ip_network}
        country_db.close()

    # Define headers based on the context - this is not clean yet, but it works
    if summarize:
        base_headers = ['From IP', 'To IP']
    else:
        base_headers = ['IP']

    # Displaying results
    if csv_results:
        try:
            csv_headers = ['IP'] + list(csv_results[0].keys())[1:]
            display_results('CSV Data', csv_results, csv_headers, summarize)
        except:
            print("No CSV Data found")
    if asn_results:
        asn_headers = base_headers.copy()
        first_asn_result = next(iter(asn_results.values()))
        asn_headers += list(first_asn_result.keys())
        display_results('ASN Data', asn_results, asn_headers, summarize)
    if city_results:
        city_headers = base_headers.copy()
        first_city_result = next(iter(city_results.values()))
        city_headers += list(first_city_result.keys())
        display_results('City Data', city_results, city_headers, summarize)
    if country_results:
        country_headers = base_headers.copy()
        first_country_result = next(iter(country_results.values()))
        country_headers += list(first_country_result.keys())
        display_results('Country Data', country_results, country_headers, summarize)

if __name__ == "__main__":
    main()

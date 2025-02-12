#!/usr/bin/env python3

# We grabbed and saved all infos-by-country via Burp Intruder, for each country, into one outfile (voip.xml.txt)
# The script parses this file, resolves all infos, redirect links to provider, pricing and downloads the XML config
# for each provider. Result is a neat json list of many VOIP providers by Country and their config infos (SIP endpoints, Port etc.)

import json
import requests
import re
import os
from bs4 import BeautifulSoup
import pycountry

# Input and output files
input_file = "voip.xml.txt"
output_file = "voip_providers.json"
xml_output_dir = "voip_xml_configs"

# Create directory for XML files
os.makedirs(xml_output_dir, exist_ok=True)

# Function to follow redirects and get final URL
def get_final_url(url):
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=10,
        )
        return response.url
    except requests.RequestException:
        return None

# Function to download and save XML file
def download_xml(url, filename):
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
    except requests.RequestException:
        pass
    return False

# Function to get country name from ISO code
def get_country_name(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code.upper())
        return country.name if country else ""
    except Exception:
        return ""

# Parse the input file
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# Use BeautifulSoup to parse the XML-like file
soup = BeautifulSoup(content, "xml")
items = soup.find_all("item")

# Process each item
country_data = {}

for item in items:
    # Extract the URL to get the country code
    url = item.find("url").text
    match = re.search(r"/getproviderlist/([a-z]{2})/windows/json", url)
    if not match:
        continue
    country_code = match.group(1)

    # Extract the JSON response
    response = item.find("response").text
    json_start = response.find("[")
    json_end = response.rfind("]") + 1
    if json_start == -1 or json_end == -1:
        continue

    try:
        providers = json.loads(response[json_start:json_end])
    except json.JSONDecodeError:
        continue

    # Initialize country entry if not exists
    if country_code not in country_data:
        country_data[country_code] = {
            "country_name": get_country_name(country_code),
            "providers": [],
        }

    # Process each provider
    for provider in providers:
        provider_info = {
            "id": provider["id"],
            "provider_name": provider["provider_name"],
            "url_get_desktop_config_xml": provider["url_get_desktop_config_xml"],
            "url_signup": get_final_url(provider["url_signup"]),
            "url_rates": get_final_url(provider["url_rates"]),
        }

        # Generate XML filename
        xml_filename = os.path.join(
            xml_output_dir,
            f"{country_code}_{re.sub(r'[^a-zA-Z0-9_]', '_', provider['provider_name'])}.xml",
        )
        if download_xml(provider["url_get_desktop_config_xml"], xml_filename):
            provider_info["xml_file"] = xml_filename
        else:
            provider_info["xml_file"] = None

        country_data[country_code]["providers"].append(provider_info)

# Save the output as JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(country_data, f, indent=4, ensure_ascii=False)

print(f"Processing complete. Output saved to {output_file}.")

#!/usr/bin/env python3

# Boilerplate to find and process HTML inputs fast and easy

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

target_url = "http://192.168.2.57"
response = requests.get(target_url)
soup = BeautifulSoup(response.text, "html.parser")

# Find all links
links = [urljoin(target_url, link.get("href")) for link in soup.find_all("a")]

# Find all forms
forms = soup.find_all("form")

# Loop through the forms and extract form details
for form in forms:
    action = form.get("action")
    method = form.get("method")
    inputs = []

    # Extract input fields
    for input_field in form.find_all("input"):
        input_name = input_field.get("name")
        input_type = input_field.get("type")
        inputs.append((input_name, input_type))

    # Process the form data, send requests, and test for vulnerabilities
    # Implement your custom vulnerability testing logic here

#!/usr/bin/env python3

import requests
from datetime import datetime
import json
import os, re 
import subprocess

# Query should be a public url with the image to reverse search
query = ""
maxResultPages = 50
folder = "/tmp/img/"

# SerpAPI key
serpAPIkey = ""

def sanitize_filename(title, url):
    # Use a regular expression to find the file extension
    extension_match = re.search(r"\.(jpg|jpeg|png|gif|bmp|webp|img|svg|tiff)", url, re.IGNORECASE)
    extension = extension_match.group(0) if extension_match else '.jpg'  # Default to .jpg if no extension found

    # Replace spaces and illegal characters in the title
    sanitized_title = re.sub(r'[^\w\s-]', '', title.replace(" ", "_"))

    # Limit the length of the filename
    max_length = 200
    if len(sanitized_title) > max_length:
        sanitized_title = sanitized_title[:max_length]

    return sanitized_title + extension

def download_image(image_url, folder_path):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(folder_path, image_url.split("/")[-1])
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
    return False

def download_image_with_wget(image_url, folder_path, title):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filename = sanitize_filename(title, image_url)
    file_path = os.path.join(folder_path, filename)

    command = f"timeout -k 25 25 wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 0 -q -O \"{file_path}\" --content-disposition -e robots=off --trust-server-names -nc --max-redirect=5 {image_url}" 
    
    try:
        subprocess.run(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while downloading {image_url}: {e}")

def yandex_image_search(api_key, query, max_pages):
    base_url = "https://serpapi.com/search.json"
    params = {
        "engine": "yandex_images",
        "url": query,
        "api_key": api_key,
        "output": "json"
    }

    for page in range(max_pages):
        print(f"Fetching page {page + 1}")
        params["p"] = page
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch page {page + 1}")
            continue

        data = response.json()
        now = datetime.now()
        with open("yand.json" + now.strftime("%Y-%m-%d_%H-%M-%S"), "w") as f:
            f.write(json.dumps(data, indent=4))

        for image_result in data["image_results"]:
            title = image_result["title"]
            print("[+]", title)

            print("Width", image_result["original_image"]["width"], " Height", image_result["original_image"]["height"])

            imgurl = image_result["original_image"]["link"]
            print(imgurl)
            print()
            
            download_image_with_wget(imgurl, folder, title)
            # download_image(imgurl, folder)
                  
yandex_image_search(serpAPIkey, query, maxResultPages)

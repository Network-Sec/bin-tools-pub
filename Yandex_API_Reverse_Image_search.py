#!/usr/bin/env python3

import requests
from datetime import datetime
import json
import os
import subprocess

# Query should be a public url with the image to reverse search
query = ""
maxResultPages = 50
folder = "/tmp/img/"

# SerpAPI key
serpAPIkey = ""

# Some image pathes are problematic on output, see alternative below using wget
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

def download_image_with_wget(image_url, folder_path):
    # Ensure the folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Construct the wget command
    command = f"wget -P {folder_path} --content-disposition -e robots=off --trust-server-names -nc --max-redirect=3 '{image_url}'"
    
    try:
        subprocess.run(command, shell=True, check=True)
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
            print(image_result["title"])
            print("Width", image_result["original_image"]["width"], " Height", image_result["original_image"]["height"])
            imgurl = image_result["original_image"]["link"]
            print(imgurl)
            download_image_with_wget(image_url, folder)
            # download_image(imgurl, folder)
                  
yandex_image_search(serpAPIkey, query, maxResultPages)

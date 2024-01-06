#!/usr/bin/env python3

import requests
from datetime import datetime
import json

# Query should be a public url with the image to reverse search
query = ""

# SerpAPI key
serpAPIkey = ""

maxResultPages = 50

def yandex_image_search(api_key, query, max_pages):
    base_url = "https://serpapi.com/search.json"
    params = {
        "engine": "yandex",
        "text": query,
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

        if "organic_results" in data:
            for result in data["organic_results"]:
                if "link" in result:
                    print(result["link"])
                  
yandex_image_search(serpAPIkey, query, maxResultPages)

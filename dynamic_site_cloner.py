#!/usr/bin/env python3

# Modern static website cloner. 
# The way it works is a bit different, it starts with a local copy of the startsite, then serves it in a python server
# You need to open that local python-served website copy in a browser, based on the errors, missing files etc. the tool
# will try to download assets and replace code bit by bit, till a good, local copy is working, has all assets. It may 
# need a few attempts and a few manual touchups, but in general, when the source site code isn't too bad, it works quite
# well and a lot better than other tools. 

# - You may need to add custom headers, cookies, etc. so the site will load and work
# - You need to start by creating a dir (/websites/mysite), copy this script into the dir
# - Ooen the page in browser, copy source and save it as index.html into the dir
# - Start the script
# - Open localhost:9095 in browser, watch the script work - when it stops, reload
# - Handling of fonts isn't ideal yet
# - svg may cause issues, as well as embedded data

import os
import re
import requests
import urllib.request 
from urllib.parse import urlparse, urljoin
from http.server import HTTPServer, SimpleHTTPRequestHandler
import hashlib

# Configuration
BASE_DIR = "~/Websites/www"  # Set your base directory here
STATIC_URL = "https://<target.site>"

COOKIES = ""

# Directory structure
JS_DIR = os.path.join(BASE_DIR, "js")
CSS_DIR = os.path.join(BASE_DIR, "css")
IMG_DIR = os.path.join(BASE_DIR, "img")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

# Ensure directories exist
for directory in [JS_DIR, CSS_DIR, IMG_DIR, FONTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Utility Functions
def file_exists(file_path, content=None):
    """Checks if a file exists and optionally compares its content hash."""
    if not os.path.exists(file_path):
        return False
    if content:
        with open(file_path, 'rb') as f:
            existing_hash = hashlib.md5(f.read()).hexdigest()
        new_hash = hashlib.md5(content).hexdigest()
        return existing_hash == new_hash
    return True

def rewrite_file_paths(old_url, new_url):
    """Rewrites URLs in local HTML and CSS files."""
    for dirpath, _, filenames in os.walk(BASE_DIR):
        for filename in filenames:
            if filename.endswith(('.html', '.css')):
                file_path = os.path.join(dirpath, filename)
                with open(file_path, 'r+', encoding='utf-8') as f:
                    content = f.read()
                    new_content = content.replace(old_url, new_url)
                    if content != new_content:
                        f.seek(0)
                        f.write(new_content)
                        f.truncate()
                        print(f"Rewritten in {file_path}: {old_url} -> {new_url}")

# Custom HTTP Server
class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if not os.path.exists(self.translate_path(self.path)):
            self.log_error("File not found: %s", self.path)
            self.handle_missing_asset(self.path)
        else:
            super().do_GET()

    def handle_missing_asset(self, path):
        parsed_url = urlparse(path)
        if parsed_url.scheme in ('http', 'https'):
            return  # Ignore external URLs
        
        full_url = urljoin(STATIC_URL, path)
        print(f"Downloading missing asset: {full_url}")
        self.download_file(full_url, path)

    def download_file(self, url, local_path):
        try:
            filename = os.path.basename(urlparse(url).path)
            if not filename or filename.endswith('.mp4'):
                return  # Skip MP4 files
            
            req = urllib.request.Request(url)
            req.add_header("Cookie", COOKIES)
            req.add_header("User-Agent", "Mozilla/5.0")
            response = urllib.request.urlopen(req)
            
            if response.getcode() not in [200]:
                print(f"Skipping {url} - HTTP {response.getcode()}")
                return  # Skip if response is not OK

            content = response.read()
            
            if 'application/javascript' in response.info().get_content_type() or filename.endswith('.js'):
                file_path = os.path.join(JS_DIR, filename)
            elif 'text/css' in response.info().get_content_type() or filename.endswith('.css'):
                file_path = os.path.join(CSS_DIR, filename)
            elif response.info().get_content_type().startswith('image/'):
                file_path = os.path.join(IMG_DIR, filename)
            elif filename.endswith('woff2'):
                file_path = os.path.join(FONTS_DIR, filename)
            else:
                return
            
            if not file_exists(file_path, content):
                with open(file_path, 'wb') as f:
                    f.write(content)
                print(f"Downloaded: {file_path}")
                rewrite_file_paths(url, f"/{os.path.relpath(file_path, BASE_DIR)}")
        
        except urllib.error.HTTPError as e:
            print(f"Error downloading {url}: HTTP {e.code}")
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")

def run(server_class=HTTPServer, handler_class=CustomHTTPRequestHandler, port=9095):
    os.chdir(BASE_DIR)  # Ensure server serves from the correct directory
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Serving local site on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    if not os.path.exists(os.path.join(BASE_DIR, "index.html")):
        print("Error: index.html not found in script directory.")
    else:
        run()

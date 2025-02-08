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
import time

# Configuration
BASE_DIR = "~/Websites/www"  # Set your base directory here
STATIC_URL = "https://<target.site>"

COOKIES = "token=..."

JS_DIR = os.path.join(BASE_DIR, "js")
CSS_DIR = os.path.join(BASE_DIR, "css")
IMG_DIR = os.path.join(BASE_DIR, "img")

# Ensure directories exist
os.makedirs(JS_DIR, exist_ok=True)
os.makedirs(CSS_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Check if the requested file exists
        if not os.path.exists(self.translate_path(self.path)):
            self.log_error("File not found: %s", self.path)
            self.handle_404(self.path)
        else:
            super().do_GET()

    def handle_404(self, path):
        # Determine if the URL starts with STATIC_URL or if it is an external URL
        parsed_url = urlparse(path)
        if len(path) < 5:
            return
        else:
            print(f"Downloading ", end="")
        if path.startswith(STATIC_URL):
            print(path)
            self.download_file(path)
        elif parsed_url.scheme in ('http', 'https'):
            print("not, ignoring external url")
            return
        else:
            full_url = urljoin(STATIC_URL, path)
            print(full_url)
            self.download_file(full_url, path)

    def download_file(self, url, path):
        try:
            # Determine file type and download the file
            req = urllib.request.Request(url)
            cookie_header = COOKIES
            req.add_header("Cookie", cookie_header)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
            req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
            req.add_header("Accept-Language", "en-US,en;q=0.5")
            req.add_header("Connection", "keep-alive")
            req.add_header("Referer", url)
            req.add_header("Upgrade-Insecure-Requests", "1")
            response = urllib.request.urlopen(req)
            content_type = response.info().get_content_type()
            content = response.read()
            filename = urlparse(url).path.split('/')[-1]
            print(f"Download filename: {filename} | file_path: ", end="")
            if filename.endswith('woff2'):
                file_path = os.path.join(BASE_DIR, 'fonts', filename)
                print(file_path)
                self.rewrite_local_paths(url, file_path, path)
                if os.path.exists(file_path):
                    return
                with open(file_path, 'wb') as f:
                    f.write(content)

            if 'application/javascript' in content_type or filename.endswith('js'):
                # Save JavaScript files
                file_path = os.path.join(BASE_DIR, 'js', filename)
                print(file_path)
                self.rewrite_local_paths(url, file_path, path)
                if os.path.exists(file_path):
                    return
                with open(file_path, 'wb') as f:
                    f.write(content)
                

            elif 'text/css' in content_type or filename.endswith('css'):
                # Save CSS files
                file_path = os.path.join(BASE_DIR, 'css', filename)
                print(file_path)
                self.rewrite_local_paths(url, file_path, path)
                if os.path.exists(file_path):
                    return
                with open(file_path, 'wb') as f:
                    f.write(content)
                

            elif content_type.startswith('image/') or filename.endswith('svg') or filename.endswith('jpg') or filename.endswith('png') or filename.endswith('jpeg') or filename.endswith('gif') or filename.endswith('webp') or filename.endswith('gif'):
                file_path = os.path.join(BASE_DIR, 'img', filename)
                print(file_path)
                self.rewrite_image_paths(url, file_path, path)
                if os.path.exists(file_path):
                    return
                with open(file_path, 'wb') as f:
                    f.write(content)
                
            elif path.endswith('/'):
                print(f"Subpage download url: {url} path: {path}")
                self.download_subpage(url, path)

        except Exception as e:
            self.log_error("Error downloading file: %s", str(e))

    def rewrite_local_paths(self, url, local_path, org_url):
        # Extract the filename from the URL
        url_file = urlparse(url).path.split('/')[-1]

        if url_file.endswith(('.js')):
            replacement_path = f'/js/{url_file}'
        elif url_file.endswith(('.css')):
            replacement_path = f'/css/{url_file}'
        elif url_file.endswith(('.woff2')):
            replacement_path = f''
        else:
            return
        print(f"Rewriting: {url_file} with replacement path: {replacement_path}")
        # Rewrite URLs in HTML/CSS files
        for dirpath, _, filenames in os.walk(BASE_DIR):
            for filename in filenames:
                if filename.endswith(('.html', '.css')):
                    file_path = os.path.join(dirpath, filename)
                    print(f"Seeking in: {file_path}")
                    with open(file_path, 'r+') as f:
                        content = f.read()

                        # Case 2: Check if the URL starts with STATIC_URL
                        if not url.startswith(STATIC_URL):
                            # Create the STATIC_URL version of the URL
                            static_url_version = STATIC_URL + url
                            print(f"Seeking static: {static_url_version}")
                            new_content = content.replace(static_url_version, replacement_path)
                        print(f"Seeking unmodified: {org_url}")
                        new_content = content.replace(org_url, replacement_path)

                        f.seek(0)
                        f.write(new_content)
                        print(f"Replaced in: {file_path}")
                        f.truncate()

    def rewrite_image_paths(self, url, local_path, org_url):
        # Extract the filename from the URL
        url_file = urlparse(url).path.split('/')[-1]

        # Determine the replacement path based on the file type
        replacement_path = f'/img/{url_file}' if url_file.endswith(('.svg','.png', '.jpg', '.jpeg', '.gif', 'webp', 'gif')) else ''

        if not replacement_path:
            return
        print(f"Rewriting: {url_file} with replacement path: {replacement_path}")
        # Rewrite image paths in HTML/CSS files
        for dirpath, _, filenames in os.walk(BASE_DIR):
            for filename in filenames:
                if filename.endswith(('.html', '.css')):
                    file_path = os.path.join(dirpath, filename)
                    with open(file_path, 'r+') as f:
                        content = f.read()

                        if not url.startswith(STATIC_URL):
                            # Create the STATIC_URL version of the URL
                            static_url_version = STATIC_URL + url
                            print(f"Seeking static: {static_url_version}")
                            new_content = content.replace(static_url_version, replacement_path)
                        print(f"Seeking unmodified: {org_url}")
                        new_content = content.replace(org_url, replacement_path)

                        f.seek(0)
                        f.write(new_content)
                        print(f"Replaced in: {file_path}")
                        f.truncate()


    def download_subpage(self, url, path):
        try:
            # Ensure path ends with '/'
            if not path.endswith('/'):
                path += '/'
            
            # Create directory structure for the subpage
            local_dir = os.path.join(BASE_DIR, path.lstrip('/'))
            os.makedirs(local_dir, exist_ok=True)

            # Determine filename (index.html for subpages)
            file_path = os.path.join(local_dir, "index.html")
            print(f"Saving subpage to: {file_path}")
            
            # Download and save the HTML file
            req = urllib.request.Request(url)
            cookie_header = COOKIES
            req.add_header("Cookie", cookie_header)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
            req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
            req.add_header("Accept-Language", "en-US,en;q=0.5")
            req.add_header("Connection", "keep-alive")
            req.add_header("Referer", url)
            req.add_header("Upgrade-Insecure-Requests", "1")
            response = urllib.request.urlopen(req)
            content = response.read().decode('utf-8')  # Assuming HTML is utf-8
            
            # Rewrite STATIC_URL in the downloaded content
            content = content.replace(STATIC_URL, "")
            
            # Save the modified content to index.html
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Rewrite HTML links for local subpage paths
            self.rewrite_html_links(file_path, path)

        except Exception as e:
            self.log_error(f"Error downloading subpage: {str(e)}")

    def rewrite_html_links(self, file_path, path):
        """Rewrites all links to point to local /subpage/index.html files."""
        try:
            with open(file_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                
                # Replace '/subpage/' with '/subpage/index.html'
                if path.endswith('/'):
                    new_path = path + 'index.html'
                else:
                    new_path = path + '/index.html'
                
                content = content.replace(f"{path}", new_path)
                
                # Write the updated content back to the file
                f.seek(0)
                f.write(content)
                f.truncate()

            print(f"Rewrote HTML links in {file_path}")
        except Exception as e:
            self.log_error(f"Error rewriting HTML links in {file_path}: {str(e)}")

def run(server_class=HTTPServer, handler_class=CustomHTTPRequestHandler, port=9095):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Serving on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()

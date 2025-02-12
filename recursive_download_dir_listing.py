import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import logging

# Configure logging
logging.basicConfig(filename='downloader.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def normalize_url(url):
    """Ensure the URL has a scheme and correct format."""
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    parsed = urlparse(url)
    if not parsed.path.endswith('/'):
        url += '/'
    return url

def is_valid_url(url, base_url):
    """Check if the URL is valid and belongs to the same domain."""
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return parsed_url.netloc == parsed_base.netloc and not url.startswith('mailto:')

def get_links(url):
    """Fetch all links from a directory listing page."""
    try:
        print("Requesting", url)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            if is_valid_url(full_url, url):
                links.append(full_url)
                print(full_url)
        return links
    except requests.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return []

def create_local_directory_structure(base_dir, path):
    """Create local directories to mirror the remote structure."""
    local_path = os.path.join(base_dir, path.lstrip('/'))
    if not os.path.exists(local_path):
        os.makedirs(local_path, exist_ok=True)
    return local_path

def download_file(url, local_path):
    """Download a file from a URL to a local path."""
    try:
        logging.info(f"Started downloading {url}")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Finished downloading {url}")
    except requests.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")

def save_progress(base_dir, progress):
    """Save the progress protocol to a JSON file."""
    progress_file = os.path.join(base_dir, 'progress.json')
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=4)

def load_progress(base_dir):
    """Load the progress protocol from a JSON file."""
    progress_file = os.path.join(base_dir, 'progress.json')
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            print("Found existing progress file")
            return json.load(f)
    return {'files': [], 'directories': []}

def enumerate_and_download(base_url, base_dir):
    """Recursively enumerate and download all files and directories."""
    progress = load_progress(base_dir)
    visited_dirs = set(progress['directories'])
    files_to_download = set(progress['files'])

    def _enumerate(url):
        print("Enumerating:", url)
        if url in visited_dirs:
            return
        visited_dirs.add(url)
        links = get_links(url)
        for link in links:
            if link.endswith('/'):
                local_dir = create_local_directory_structure(base_dir, urlparse(link).path)
                _enumerate(link)
                progress['directories'].append(link)
            else:
                if link not in files_to_download:
                    files_to_download.add(link)
                    progress['files'].append(link)
        save_progress(base_dir, progress)

    _enumerate(base_url)

    for file_url in files_to_download:
        file_path = urlparse(file_url).path.lstrip('/')
        local_path = os.path.join(base_dir, file_path)
        if not os.path.exists(local_path):
            download_file(file_url, local_path)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <URL>")
        sys.exit(1)

    raw_url = sys.argv[1]
    base_url = normalize_url(raw_url)
    parsed = urlparse(base_url)
    base_dir = parsed.netloc or parsed.path.split('/')[0]
    
    # Create base directory if needed
    os.makedirs(base_dir, exist_ok=True)
    
    enumerate_and_download(base_url, base_dir)
    print("Download completed.")

if __name__ == "__main__":
    main()

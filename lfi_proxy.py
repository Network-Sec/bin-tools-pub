#!/usr/bin/env python3

# Simple python proxy that takes a target url, an LFI path and optionally a http / socks proxy on the way out
# Intended to use with tools like gobuster that may strip the LFI part. 
# Includes possibility to change headeres dynamically, for some CTF scenarios

import argparse
from aiohttp import web, ClientSession
from aiohttp_socks import ProxyConnector
from urllib.parse import urlparse, urlunparse
import hashlib

# Fixed listening port
LISTEN_PORT = 13131

# Command line argument parsing
parser = argparse.ArgumentParser(description="LFI Proxy Tool")
parser.add_argument("--lfi-path", type=str, required=True, help="LFI base path to append")
parser.add_argument("--target-url", type=str, required=True, help="Target URL to forward requests to")
parser.add_argument("--proxy", type=str, default=None, help="Optional forward proxy (HTTP or SOCKS)")

# Parse arguments
args = parser.parse_args()

def modify_headers(headers):
    # Example header modification logic
    if "Some-Header" in headers:
        param = headers["Some-Header"]
        headers["Checksum"] = hashlib.md5(param.encode('utf-8')).hexdigest()
    return headers

async def handle_request(request):
    # Parse and rebuild the target URL including the port
    parsed_target_url = urlparse(args.target_url)
    target_url_with_port = urlunparse((parsed_target_url.scheme, parsed_target_url.netloc,
                                       parsed_target_url.path + args.lfi_path + request.path_qs,
                                       parsed_target_url.params, parsed_target_url.query,
                                       parsed_target_url.fragment))

    # Create a session with proxy if specified
    connector = ProxyConnector.from_url(args.proxy) if args.proxy else None

    # Modify headers
    modified_headers = modify_headers(dict(request.headers))

    # Forward the request to the target URL with modified headers
    async with ClientSession(connector=connector) as session:
        async with session.request(request.method, target_url_with_port,
                                   headers=modified_headers, data=await request.read()) as resp:
            # Log the request and response
            print(f"[*] {request.path} => {request.method} {target_url_with_port} => {resp.status}")

            # Return the response back to the client
            return web.Response(status=resp.status, body=await resp.read(), headers=resp.headers)

# Setup the web application
app = web.Application()
app.router.add_route('*', '/{tail:.*}', handle_request)

# Run the web server on the fixed port
web.run_app(app, port=LISTEN_PORT)



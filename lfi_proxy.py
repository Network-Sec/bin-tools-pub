#!/usr/bin/env python3

# Simple python proxy that takes a target url, an LFI path and optionally a http / socks proxy on the way out
# Intended to use with tools like gobuster that may strip the LFI part. 
# Includes possibility to change headeres dynamically, for some CTF scenarios

import asyncio
from aiohttp import web, ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector
from urllib.parse import urlparse, urlunparse
import hashlib
import argparse
import ssl

# Command line argument parsing
parser = argparse.ArgumentParser(description="LFI Proxy Tool")
parser.add_argument("--lfi-path", type=str, default="", required=False, help="LFI base path to append, i.e.: /../.. (no trailing slash))")
parser.add_argument("--target-url", type=str, required=True, help="Target URL to forward requests to")
parser.add_argument("--proxy", type=str, default=None, required=True, help="Optional forward proxy (HTTP or SOCKS)")
parser.add_argument("--max-connections", type=int, default=10, help="Maximum number of concurrent connections")
parser.add_argument("--listen-port", type=int, default=13131, required=False, help="listen different port (default 13131)")
parser.add_argument("-k", action="store_true", help="Allow insecure SSL connections (accepts self-signed certs)")

# Parse arguments
args = parser.parse_args()

# Listen port
LISTEN_PORT = args.listen_port

# Connection limit
semaphore = asyncio.Semaphore(args.max_connections)

def modify_headers(headers, key, new_value):
    # Example header modification logic
    if key in headers:
        headers[key] = new_value
    
    # Do CTF stuff here   
    # headers["Checksum"] = hashlib.md5(param.encode('utf-8')).hexdigest()

    return headers

def create_ssl_context(insecure=False):
    ssl_context = ssl.create_default_context()
    if insecure:
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context

async def handle_request(request):
    async with semaphore:  # Limit the number of concurrent connections
        try:
            # Parse and rebuild the target URL including the port
            parsed_target_url = urlparse(args.target_url)
            target_url  = parsed_target_url.scheme + "://" 
            target_url += parsed_target_url.netloc + parsed_target_url.path

            while target_url.endswith("/"):
                target_url = target_url[:-1]

            if args.lfi_path: 
                target_url += args.lfi_path

            if not target_url.endswith("/"):
                target_url += "/"

            parsed_path = request.path_qs + parsed_target_url.params + parsed_target_url.query + parsed_target_url.fragment
            
            while parsed_path.startswith("/"):
                parsed_path = parsed_path[1:]

            target_url += parsed_path

            while target_url.endswith("/"):
                target_url = target_url[:-1]

            # Modify headers
            modified_headers = modify_headers(dict(request.headers), "Host", parsed_target_url.hostname)

             # Create a custom SSL context
            ssl_context = create_ssl_context(args.k)

            # Create a session with proxy and pass the hostname for SNI
            connector = ProxyConnector.from_url(args.proxy, ssl=ssl_context)

            async with ClientSession(connector=connector) as session:
                async with session.request(request.method, target_url, headers=modified_headers, data=await request.read(), 
                                           ssl=ssl_context) as resp:

                    # Log the request and response
                    print(f"[*] {request.path} => {request.method} {target_url} => {resp.status}")

                    # Return the response back to the client
                    return web.Response(status=resp.status, body=await resp.read(), headers=resp.headers)
        except Exception as e:
            print(f"Error handling request: {e}")
            return web.Response(status=500, text="Internal Server Error")

# Setup the web application
app = web.Application()
app.router.add_route('*', '/{tail:.*}', handle_request)

# Run the web server on the fixed port
web.run_app(app, port=LISTEN_PORT)


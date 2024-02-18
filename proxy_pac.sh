#!/bin/bash

# Define paths for the proxy lists
SOCKS5_LIST="socks5.txt"
SOCKS4_LIST="socks4.txt"
HTTP_LIST="http.txt"

# URLs for the proxy lists
SOCKS5_URL="https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt"
SOCKS4_URL="https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt"
HTTP_URL="https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"

# Download the proxy lists
curl $SOCKS5_URL -o $SOCKS5_LIST
curl $SOCKS4_URL -o $SOCKS4_LIST
curl $HTTP_URL -o $HTTP_LIST

# Generate the PAC file
PAC_FILE="auto_proxy.pac"
{
    echo "function FindProxyForURL(url, host) {"
    echo -n "    return \""
    # Add SOCKS5 proxies
    while IFS= read -r line; do
        echo -n "SOCKS5 $line; "
    done < "$SOCKS5_LIST"
    # Add SOCKS4 proxies
    while IFS= read -r line; do
        echo -n "SOCKS4 $line; "
    done < "$SOCKS4_LIST"
    # Add HTTP(S) proxies
    while IFS= read -r line; do
        echo -n "PROXY $line; "
    done < "$HTTP_LIST"
    echo "DIRECT\";"
    echo "}"
} > $PAC_FILE

echo "PAC file generated at $PAC_FILE"
python3 -m http.server 9009

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

# Output file for Proxychains
PROXYCHAINS_CONF="proxychains-append.conf"

# Clear the output file to avoid appending to old content
> $PROXYCHAINS_CONF

# Process SOCKS5 proxies
while IFS= read -r line; do
    # Convert colon to whitespace and prepend with "socks5 "
    echo "socks5 ${line//:/ }" >> $PROXYCHAINS_CONF
done < "$SOCKS5_LIST"

# Process SOCKS4 proxies
while IFS= read -r line; do
    # Convert colon to whitespace and prepend with "socks4 "
    echo "socks4 ${line//:/ }" >> $PROXYCHAINS_CONF
done < "$SOCKS4_LIST"

# Process HTTP(S) proxies - assuming you want to include these as well
while IFS= read -r line; do
    # Convert colon to whitespace and prepend with "http "
    echo "http ${line//:/ }" >> $PROXYCHAINS_CONF
done < "$HTTP_LIST"

echo "Proxychains file created: $PROXYCHAINS_CONF"

python3 -m http.server 9009

#!/bin/bash

# Like the proxy_pac.sh but it will test
# each server before adding it. This takes
# a while and may not be succesfull, but
# if it does, the result is a high-quality list

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

# Testing URL
TEST_URL="http://httpbin.org/ip"

# Generate the PAC file
PAC_FILE="auto_proxy.pac"
{
    echo "function FindProxyForURL(url, host) {"
    echo -n "    return \""
    
    # Function to test each proxy and echo it if good
    test_proxy() {
        local proxy_type=$1
        local proxy=$2
        response=$(curl --proxy $proxy_type://$proxy --max-time 1 -s $TEST_URL)
        if [[ "$response" == *origin* ]]; then
            echo -n "$proxy_type $proxy; "
        fi
    }

    # Test and add SOCKS5 proxies
    while IFS= read -r line; do
        test_proxy "SOCKS5" "$line"
    done < "$SOCKS5_LIST"
    
    # Test and add SOCKS4 proxies
    while IFS= read -r line; do
        test_proxy "SOCKS4" "$line"
    done < "$SOCKS4_LIST"
    
    # Test and add HTTP(S) proxies
    while IFS= read -r line; do
        test_proxy "http" "$line"
    done < "$HTTP_LIST"

    echo "DIRECT\";"
    echo "}"
} > $PAC_FILE

echo "PAC file generated at $PAC_FILE"
rm $SOCKS5_LIST $SOCKS4_LIST $HTTP_LIST
python3 -m http.server

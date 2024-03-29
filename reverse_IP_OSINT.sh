#!/bin/bash

# Script combines some services that don't need API keys to 
# provide practical Threat Intelligence Output
# Add more services as needed

# Check if an IP address is passed as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <IP Address>"
    exit 1
fi

IP="$1"

# Processing IP
echo "----------------- Processing IP: $IP -----------------"

# Reverse DNS lookup
echo "[+] dig result for $IP"
dig -x $IP +short @8.8.8.8
echo "" # Blank line for readability

# Domain information from site.ip138.com
echo "[+] Domain information from site.ip138.com for $IP"
curl -s "https://site.ip138.com/$IP" -H "User-Agent: Mozilla/5.0" | pup 'div.result.result2 ul#list li a[href] text{}'
echo ""

# SAN and CN from the certificate
echo "[+] SAN and CN from the certificate for $IP"
echo $IP | tlsx -san -cn -silent
echo ""

# Domain information from ipchaxun.com
echo "[+] Domain information from ipchaxun.com for $IP"
curl -s "https://ipchaxun.com/$IP/" -H "User-Agent: Mozilla/5.0" | pup 'div#J_domain p a text{}'
echo "" #

# Domain information from rapiddns.io
echo "[+] Domain information from rapiddns.io for $IP"
curl -s "https://rapiddns.io/s/52.178.17.2" -H "User-Agent: Mozilla/5.0" | pup 'div#result div.row div.col-lg-12 table#table tbody tr td:nth-of-type(1) text{}'
echo ""

# Add more requests as needed

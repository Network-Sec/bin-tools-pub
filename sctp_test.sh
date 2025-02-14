#!/bin/bash

TARGET=$1

# Scan SCTP ports
echo "Scanning SCTP ports..."
sudo timeout 5 masscan -p 2000,2001,2427,2727,2905,2910,3868,5060,5061 $TARGET  --max-rate=10000 --rate=10000 --banners --wait 0 --retries 0

# Scan SIP ports
echo ""
echo "Scanning SIP ports..."
sudo nmap -sU -p 2000,2001,2427,2727,2905,2910,3868,5060,5061 --script=sip-methods,sip-enum-users $TARGET

echo ""
echo "nmap –O"
sudo nmap –O -p 2000,2001,2427,2727,2905,2910,3868,5060,5061 $TARGET

# Test SS7 MAP vulnerabilities
echo ""
echo "Testing SS7 MAP vulnerabilities..."
python3 ~/bin/sctpscan.py $TARGET --quiet

echo ""
echo "snmpwalk"
snmpwalk -c public -v 1 $ip 

echo ""
echo "svwar OPTIONS"
sipvicious_svwar -e111-123 -m OPTIONS $ip;

echo "Finished target $1"
echo ""

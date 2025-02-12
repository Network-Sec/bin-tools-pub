#!/bin/bash

TARGET=$1

# Scan SCTP ports
echo "Scanning SCTP ports..."
sudo timeout 5 masscan -p 2427,2727,2905,2910,3868,5060,5061 $TARGET --max-rate=10000 --rate=10000 --banners --wait 0 --retries 0

# Scan SIP ports
echo ""
echo "Scanning SIP ports..."
sudo nmap -sU -p 2427,2727,2905,2910,3868,5060,5061 --script=sip-methods,sip-enum-users,sip-brute --script-args creds.global='admin:password' $TARGET

# Test SS7 MAP vulnerabilities
echo ""
echo "Testing SS7 MAP vulnerabilities..."
python3 ~/bin/sctpscan.py $TARGET --quiet

echo "Finished target $1"
echo ""

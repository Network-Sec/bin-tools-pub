#!/bin/bash

# Script combines some services that don't need API keys to 
# provide practical Threat Intelligence Output
# Add more services as needed

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <IP Address or CIDR>"
    exit 1
fi

INPUT="$1"
IS_CIDR=false

process_ip() {
    local IP=$1

    
    if [[ "$IP" =~ \.0$ || "$IP" =~ \.255$ ]]; then
        echo "Skipping network/broadcast address: $IP"
        return
    fi

    echo "----------------- Processing IP: $IP -----------------"

    
    echo "[+] dig result for $IP"
    dig -x $IP +short @8.8.8.8
    echo ""

    
    echo "[+] Domain information from site.ip138.com for $IP"
    timeout 10 curl -s "https://site.ip138.com/$IP" -H "User-Agent: Mozilla/5.0" | pup 'div.result.result2 ul#list li a[href] text{}'
    echo ""

    
    echo "[+] Domain information from ipchaxun.com for $IP"
    timeout 10 curl -s "https://ipchaxun.com/$IP/" -H "User-Agent: Mozilla/5.0" | pup 'div#J_domain p a text{}'
    echo ""

    if [[ $IS_CIDR=false ]]; 
    then 
        
        echo "[+] SAN and CN from the certificate for $IP"
        echo $IP | tlsx -san -cn -silent
        echo ""

        
        echo "[+] Domain information from rapiddns.io for $IP"
        timeout 10 curl -s "https://rapiddns.io/s/$IP" -H "User-Agent: Mozilla/5.0" | pup 'div#result div.row div.col-lg-12 table#table tbody tr td:nth-of-type(1) text{}'
        echo ""
    fi
}


process_cidr() {
    local CIDR=$1
    # echo "Using direct CIDR support for services."

    
    echo "[+] SAN and CN from the certificate for $CIDR"
    echo $CIDR | tlsx -san -cn -silent
    echo ""

    
    echo "[+] Domain information from rapiddns.io for $CIDR"
    timeout 10 curl -s "https://rapiddns.io/s/$CIDR" -H "User-Agent: Mozilla/5.0" | pup 'div#result div.row div.col-lg-12 table#table tbody tr td:nth-of-type(1) text{}'
    echo ""
}


expand_cidr() {
    local cidr=$1

    
    local baseip=$(echo $cidr | cut -d/ -f1)
    local mask=$(echo $cidr | cut -d/ -f2)
    local ip_int=0
    local shift=24
    for octet in $(echo $baseip | tr '.' ' '); do
        ip_int=$(($ip_int + ($octet << $shift)))
        let shift-=8
    done

    local num_ips=$((1 << (32 - mask)))
    for i in $(seq 1 $((num_ips - 2))); do  
        local ip_num=$(($ip_int + i))
        local octet1=$(($ip_num >> 24 & 255))
        local octet2=$(($ip_num >> 16 & 255))
        local octet3=$(($ip_num >> 8 & 255))
        local octet4=$(($ip_num & 255))
        local next_ip="$octet1.$octet2.$octet3.$octet4"
        process_ip $next_ip
    done
}


if echo "$INPUT" | grep -q "/"; then
    IS_CIDR=true
    # echo "CIDR detected, using appropriate services..."
    process_cidr $INPUT
    expand_cidr $INPUT
else
    process_ip $INPUT
fi

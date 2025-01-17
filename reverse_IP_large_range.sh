#!/bin/bash

# Script can enumerate a /8 range without risk of getting blocked due to too many requests
# We do that by downloading a list of most known public DNS resolvers and querying each only 1 time

if [[ ! -f ./public_dns_servers.txt ]];
then
        wget https://raw.githubusercontent.com/trickest/resolvers/refs/heads/main/resolvers-extended.txt
        cat resolvers-extended.txt | cut -d " " -f 1 > public_dns_servers.txt
fi

# Edit the first number or the range start / end of each block
parallel 'echo 123.{1}.{2}.{3}; dig -x $(echo 123.{1}.{2}.{3}) @{4}  +short | tee -a /mnt/d/IP_Ranges/vodafon_residential_92_116.txt ' ::: $(seq 1 255) ::: $(seq 1 255) ::: $(seq 1 255) :::+ $(cat ./public_dns_servers.txt)

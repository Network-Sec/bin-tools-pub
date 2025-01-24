#!/bin/bash

# Little helper script that copies latest 5 days of hashes and beacon dumps from
# our airodump devices to local, combines both in unique sets so we can get cracking
# Note that it needs another script from our bin tools and also relies on *.beacons.txt
# which are beaconfiles that were automatically created on the devices from airodump's output
# We use beacons as one short-list approach to find "human input error" passwords quickly

outputDate=$(date +"%d_%m_%y") 
remoteDate=$(date +"%Y-%m-%d")

# Initialize an empty array
last_5_days=()

# Loop to generate last 5 days
for i in {0..4}; do
    day=$(date -d "$remoteDate -$i day" +"%Y-%m-%d")
    last_5_days+=("$day")
done

# Loop through the array and echo each day
for day in "${last_5_days[@]}"; 
do
    echo "Copying: $day"
    scp -i ~/.ssh/kali1 "root@192.168.2.70:/opt/wifidump_backups/$day*" .
    scp -i ~/.ssh/kali2 "root@192.168.2.44:/opt/wifidump_backups/$day*" .
done

cat *.beacons.txt | sort -u > "beacons_$outputDate.tmp"; cat "beacons_$outputDate.tmp" | sort | uniq > "beacons_$outputDate.txt"  

cat *.hc | sort  > "hashes_$outputDate.tmp"; 

for line in $(hashdump_to_ssid.py  "hashes_$outputDate.tmp"  | sort -u | cut -d ":" -f 1); 
do 
    tac  "hashes_$outputDate.tmp" | grep -m 1 "$line" >> "hashes_uniq_$outputDate.txt"
done

echo "Beacons Length:"
wc -l "beacons_$outputDate.txt" 
echo
echo "Hashes Length:"
wc -l "hashes_uniq_$outputDate.txt"
echo
echo "Hashes List:"
hashdump_to_ssid.py "hashes_uniq_$outputDate.txt"

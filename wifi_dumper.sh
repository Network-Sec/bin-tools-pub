#!/bin/bash

# Automation script for hash and additional info capture and preparation

cd /opt
rt_adapter=$(airmon-ng | grep Realtek | grep -Po "wlan\d")
rt_commasep=$(airmon-ng | grep Realtek | grep -Po "wlan\d" | tr '\n' ',' | sed 's/,$//g')

echo "Going for $rt_commasep"

airmon-ng check kill
for adpt in $rt_adapter;
do
    airmon-ng start $adpt
done

airodump-ng "$rt_commasep"  --wps --uptime  --beacons --output-format logcsv,csv,pcap,kismet -w "/opt/$(date +%Y-%m-%d_%H-%M-%S)"

for f in $(ls *.cap); do
    echo "Processing $f"
    f=$(echo -n $f)
    hcxpcapngtool -o "$f.hc" "$f"
    mv $f wifidump_backups
done

mv *.csv /opt/wifidump_backups/

for f in $(grep -HnaiR "Probed ESSIDs" *.csv | cut -d ":" -f 1); do
    awk '/Probed ESSIDs/ {found=1; next} found' $f | cut -d ',' -f 7-99 | grep -P "[^\s]" >> beacons_tmp
done
cat beacons_tmp | tr ' ' '\n' | grep -P "[^\s]" | sort -u | awk '{print; gsub(/,/, "\n", $0); print}' | grep -P "[^\s]" | sort -u | uniq  > beacons.txt

for adpt in $rt_adapter;
do
    airmon-ng stop $adpt
done

systemctl restart wpa_supplicant
NetworkManager
systemctl restart bluetooth

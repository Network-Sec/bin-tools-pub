#!/bin/bash

cd /opt
rt_adapter=$(airmon-ng | grep Realtek | grep -Po "wlan\d")
rt_commasep=$(airmon-ng | grep Realtek | grep -Po "wlan\d" | tr '\n' ',' | sed 's/,$//g')

echo "Going for $rt_commasep"

airmon-ng check kill
for adpt in $rt_adapter; 
do
    airmon-ng start $adpt
done

datest=$(date +%Y-%m-%d_%H-%M-%S)

airodump-ng "$rt_commasep"  --wps --uptime --manufacturer --beacons --output-format logcsv,csv,pcap,kismet -w "/opt/$datest"

for adpt in $rt_adapter; 
do
    airmon-ng stop $adpt
done

systemctl restart wpa_supplicant
NetworkManager
systemctl restart bluetooth

# airodump adds -01
datetm="$datest-01"

hcxpcapngtool -o "/opt/wifidump_backups/$datetm.cap.hc" "/opt/$datetm.cap"
mv "/opt/$datetm.cap" /opt/wifidump_backups/
mv "/opt/$datetm.csv" /opt/wifidump_backups/
mv "/opt/$datetm.kismet.csv" /opt/wifidump_backups/
mv "/opt/$datetm.log.csv" /opt/wifidump_backups/

cd /opt/wifidump_processing
source bin/activate
./csv_to_db.py --csv "/opt/wifidump_backups/$datetm.csv" --hashes "/opt/wifidump_backups/$datetm.cap.hc"
deactivate
cd /opt

for f in $(grep -HnaiR "Probed ESSIDs" /opt/wifidump_backups/*.csv | cut -d ":" -f 1); do 
    awk '/Probed ESSIDs/ {found=1; next} found' $f | cut -d ',' -f 7-99 | grep -P "[^\s]" >> beacons_tmp
done
cat beacons_tmp | tr ' ' '\n' | grep -P "[^\s]" | sort -u | awk '{print; gsub(/,/, "\n", $0); print}' | grep -P "[^\s]" | sort -u | uniq  > "/opt/wifidump_backups/$datetm.beacons.txt"



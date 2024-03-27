#!/bin/bash

# Script made for Nethunter on rooted phone, so you can edit your /root/bin/... scripts
# outside the Nethunter root shell, e.g. with CodeEditor. 

# You should need to:
# apt install install inotify-tools rsync

# and then add this script to crontab as: 
# * * * * *  /bin/bash /root/bin/nethunter_chroot_bin_file_sync.sh > /dev/null 2>&1

# Now it will monitor and sync files between Android and chroot file system, also
# fixing permissions each time, so you can comfortably edit scripts. 

app_dir="/sdcard/kali_bin"
kali_dir="/root/bin"
pid_file="/var/run/sync_dirs.pid"

sync_to_kali() {
    rsync -avu --chmod=ugo+rwx "$app_dir/" "$kali_dir/"
    find "$kali_dir" -type f -exec chmod +x {} \;
}

sync_to_app() {
    rsync -avu "$kali_dir/" "$app_dir/"
    chmod -R 777 "$app_dir"
}

# Check if the script is already running
if [ -f "$pid_file" ]; then
    pid=$(cat "$pid_file")
    if kill -0 "$pid" > /dev/null 2>&1; then
        echo "Sync script is already running."
        exit 1
    else
        echo "$$" > "$pid_file"
    fi
else
    echo "$$" > "$pid_file"
fi

# Cleanup PID file on exit
trap "rm -f -- '$pid_file'" EXIT

# Initial sync on script start
sync_to_kali
sync_to_app

# Setup inotifywait to monitor directories
inotifywait -mqr -e create -e modify -e delete -e move "$app_dir" "$kali_dir" | while read path action file; do
    echo "Detected $action on $file in $path."
    
    if [[ "$path" == "$app_dir"* ]]; then
        echo "Syncing to Kali..."
        sync_to_kali
    else
        echo "Syncing to App..."
        sync_to_app
    fi
done

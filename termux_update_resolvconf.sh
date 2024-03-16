#!/bin/bash

# Script for Termux that replaces all instances of /etc/resolv.conf with 
# the Termux compatible path. Does so in regular Python libs and venvs

# The new resolv.conf path in Termux
NEW_RESOLV_CONF_PATH="/data/data/com.termux/files/usr/etc/resolv.conf"

# Create the new resolv.conf file if it doesn't exist
if [ ! -f "$NEW_RESOLV_CONF_PATH" ]; then
    echo "Creating $NEW_RESOLV_CONF_PATH with default nameserver 8.8.8.8"
    mkdir -p $(dirname "$NEW_RESOLV_CONF_PATH")
    echo "nameserver 8.8.8.8" > "$NEW_RESOLV_CONF_PATH"
fi

# Function to update resolver.py files
update_resolver() {
    local resolver_path="$1"
    echo "Updating resolver path in $resolver_path"
    sed -i "s|/etc/resolv.conf|$NEW_RESOLV_CONF_PATH|g" "$resolver_path"
}

# Export function to be accessible by find's exec command
export -f update_resolver
export NEW_RESOLV_CONF_PATH

# Starting directory for the search
START_DIR="/data/data/com.termux/files"

# Find and update resolver.py recursively from the start directory
find "$START_DIR" -type f -name "resolver.py" -exec bash -c 'update_resolver "$0"' {} \;

echo "All done!"

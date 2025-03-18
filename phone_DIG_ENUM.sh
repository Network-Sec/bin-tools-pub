#!/bin/bash

# Once upon a time...  read it up, if you care. DIG and Phonenrs used to be a thing, at least in some peoples imagination. We tried to scrape together
# what's left of the idea, will not work very often

# Function to reverse a string and add dots
reverse_and_add_dots() {
    local number=$1
    reversed=$(echo "$number" | rev)
    dotted=$(echo "$reversed" | sed 's/./&./g')  # Add dots between each character
    dotted=${dotted%?}  # Remove trailing dot
    echo "$dotted"
}

# Check if at least one phone number is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <phone_number> [additional_numbers...]"
    echo "Example: $0 441751234356 491725551234 491725561234"
    exit 1
fi

# List of ENUM servers (IPs & domains for redundancy)
enum_servers=(
    "185.124.68.123"
    "185.124.68.124"
    "enum.opentelecoms.net"
    "enum.sipbooth.net"
    "enum.voxbone.com"
    "nrenum.net"
    "publicenum.powerdns.com"
    "globalenum.syniverse.com"
    "enum.ag-projects.com"
    "enum.ripe.net"
)

# Function to perform ENUM lookup
perform_enum_lookup() {
    local query=$1
    local server=$2
    local port=$3
    echo "Querying: $query.e164.arpa on $server:$port"
    dig @$server -p $port IN NAPTR "$query.e164.arpa"
}

# Process each phone number
for number in "$@"; do
    echo "Processing: $number"
    echo "================================"

    enum_query=$(reverse_and_add_dots "$number")  # Reverse number for ENUM

    # Try each ENUM server on ports 53 and 5353
    for server in "${enum_servers[@]}"; do
        for port in 53 5353; do
            perform_enum_lookup "$enum_query" "$server" "$port"
            
            # If the last command succeeded, move to the next number
            if [ $? -eq 0 ]; then
                echo "Success on $server:$port, moving to next number."
                break 2  # Exit both loops (server + port)
            fi
        done
    done

    echo "================================"
    echo -e "\n"
done

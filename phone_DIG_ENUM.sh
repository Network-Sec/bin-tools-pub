#!/bin/bash

# Once upon a time...  read it up, if you care. DIG and Phonenrs used to be a thing, at least in somebody's imagination. 

### This is the official E.164 ENUM DNS structure as defined by the ITU (International Telecommunication Union) and managed by various ENUM registries. ###
### 9.8.7.6.5.4.3.2.1.4.4.e164.arpa ###
### There are alternative formats we added in the latest commit as well ### 

# We tried to scrape together, what's left of the idea. Won't work very often or for most numbers
# Finally we parallelized to speed things up, go back in commit history to get the unparallel version. 

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

# List of ENUM servers (IPs for redundancy)
enum_servers=(
    "1.1.1.1" "1.0.0.1" "8.8.8.8" "8.8.4.4" "208.67.222.222"
    "208.67.220.220" "9.9.9.9" "149.112.112.112" "144.76.157.242"
    "94.247.43.254" "84.200.69.80" "84.200.70.40" "8.26.56.26"
    "8.20.247.20" "185.228.168.9" "185.228.169.9" "176.103.130.130"
    "176.103.130.131" "76.76.19.19" "76.223.122.150" "195.46.39.39"
    "195.46.39.40" "77.88.8.88" "77.88.8.2" "156.154.70.5"
    "156.154.71.5" "91.239.100.100" "89.233.43.71" "104.197.28.121"
    "104.155.237.225" "76.76.2.4" "76.76.10.4" "38.132.106.139"
    "194.187.251.67" "208.76.50.50" "208.76.51.51" "108.61.201.119"
    "159.69.198.101" "146.255.56.98" "89.234.186.112" "159.69.114.157"
    "80.241.218.68" "213.196.191.96" "84.16.252.137" "84.16.252.147"
    "80.67.169.12" "80.67.169.40" "158.64.1.29" "200.1.123.46"
    "185.124.68.123" "185.124.68.124" "enum.opentelecoms.net"
    "enum.sipbooth.net" "enum.voxbone.com" "nrenum.net"
    "publicenum.powerdns.com" "globalenum.syniverse.com"
    "enum.ag-projects.com" "enum.ripe.net"
)

# Additional ENUM root domains (for querying with ENUM servers)
enum_zones=(
    "e164.org"
    "e164.telefonica.de"
    "enum.telio.no"
    "e164.info"
    "nrenum.net"
    "enumdata.org"
    "e164enum.net"
    "e164enum.info"
    "sipbroker.com"
    "e164.dnsbl.nominum.com"
)

# Function to perform ENUM lookup with timeout
perform_enum_lookup() {
    local query=$1
    local server=$2
    local zone=$3
    echo "Querying: $query.$zone on $server"
    
    # Perform the query and filter for a successful response
    result=$(timeout 3 dig @$server -p 53 IN NAPTR "$query.$zone" +short 2>&1)
    
    # Check if the response contains NAPTR records
    if [[ "$result" =~ "NAPTR" ]]; then
        echo "Success on $server:$zone"
        # Display only the relevant NAPTR record details
        echo "$result" | grep "NAPTR"  # Filter and display NAPTR records
    fi
}

# Export function so it's available for parallel
export -f perform_enum_lookup

# Process each phone number
for number in "$@"; do
    echo "Processing: $number"
    echo "================================"

    enum_query=$(reverse_and_add_dots "$number")  # Reverse number for ENUM

    # Use parallel to query each ENUM zone on each server
    for zone in "${enum_zones[@]}"; do
        # Use parallel to query each ENUM zone on each server
        printf "%s\n" "${enum_servers[@]}" | parallel -j10 "perform_enum_lookup '$enum_query' {} '$zone'"
    done

    echo "================================"
    echo -e "\n"
done

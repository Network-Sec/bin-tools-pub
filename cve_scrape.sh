#!/bin/bash

# Note: This script was part of a tutorial and shows an example implementation
# using a microservices approach and two of my custom tools - along with other
# commonly used automation bash tools, often used in Ethical Hacking and Bug Bounty.

# Please: Don't hammer "cvedetails.com" with requests, as I wrote earlier, this is an example. 

# Verbosity
# to make debugging on bash easier, outputting individual parts per level
# and not in the traditional way, outputting more and more with a higher level
VERBOSITY_LEVEL=0

BASEURL="https://www.cvedetails.com"
URL="https://www.cvedetails.com/vulnerability-search.php?f=1&vendor=&product=&cweid=&cvssscoremin=&cvssscoremax=&hasexp=1&publishdatestart=&publishdateend=&updatedatestart=&updatedateend=&cisaaddstart=&cisaaddend=&cisaduestart=&cisadueend=&opt_ac%5B%5D=Low&opt_pr%5B%5D=None&opt_pr%5B%5D=Low&opt_pr%5B%5D=High&opt_c%5B%5D=Low&opt_c%5B%5D=High&opt_i%5B%5D=Low&opt_i%5B%5D=High&opt_a%5B%5D=Low&opt_a%5B%5D=High&page=1"
LIST_SELECTOR="div#searchresults > div.row"
LOOP_SELECTOR="div.row"
FIELD_SELECTOR="a:text a:href .cvesummarylong:text"
EXPLOIT_SELECTOR="a.ssc-ext-link attr{href}" 

# Get initial search result list for latest CVEs with known exploits
cve_search=$(httpx-cli $URL --headers "User-Agent" "Mozilla/5.0")

[[ $VERBOSITY_LEVEL -eq 1 ]] && echo "CVE-Search: $cve_search"

# Extract the info we want (see FIELD_SELECTOR) into json
cve_list_json=$(echo $cve_search | tr -d '\n' | pup "$LIST_SELECTOR" | htmlq.py -l "$LOOP_SELECTOR" -s "$FIELD_SELECTOR" -j -u "$BASEURL") 

[[ $VERBOSITY_LEVEL -eq 1 ]] && echo "CVE-List: $cve_list_json"

# Extract all links from the existing JSON
exploits=$(echo "$cve_list_json" | jq -r '.[]."a:href"')

# Loop through each link and fetch content
for link in $exploits; do
    [[ $VERBOSITY_LEVEL -eq 2 ]] && echo "Link: $link"

    # Use httpx-cli to fetch the content of the link
    link_content=$(httpx-cli "$link" --headers "User-Agent" "Mozilla/5.0")

    [[ $VERBOSITY_LEVEL -eq 3 ]] && echo "Link-Content: $link_content"
   
    # Use pup to extract the desired links from the content (adjust the selector)
    extracted_exploits=$(echo "$link_content" | tr -d "\n" | pup "$EXPLOIT_SELECTOR")

    [[ $VERBOSITY_LEVEL -eq 3 ]] && echo "Extracted Exploits: $extracted_exploits"

    # Add the extracted links as a new "ref" field to the corresponding JSON object
    exploits_json='"Exploits":'$(printf '%s\n' "${extracted_exploits[@]}" | jq -R . | jq -s . | tr -d '\n')

    [[ $VERBOSITY_LEVEL -eq 2 ]] && echo "Exploits JSON: $exploits_json"

    # Add the link list as json array to the CVE data
    cve_list_json=$(jq "map(if .\"a:href\" == \"$link\"  then . + { ${exploits_json} } else . end)" <<< "$cve_list_json")

    [[ $VERBOSITY_LEVEL -eq 4 ]] && echo "Resulting JSON: $cve_list_json"

    # Find and extract code
    for exp_code_url in $extracted_exploits; do
        # Check if it's a GitHub links, which we need to treat differently. Ignore for now
        if [[ $exp_code_url = *github* ]]; then
            [[ $VERBOSITY_LEVEL -eq 4 ]] && echo "Skipping GitHub URL...";
            continue
        fi

        [[ $VERBOSITY_LEVEL -eq 4 ]] && echo "Extracting code from: $exp_code_url"

        exp_html=$(httpx-cli "$exp_code_url" --headers "User-Agent" "Mozilla/5.0")

        [[ $VERBOSITY_LEVEL -eq 5 ]] && echo "Extracted HTML: $exp_html" | head -n 60

        code_and_score=$(echo "$exp_html" | code_scoring.py)
        
        [[ $VERBOSITY_LEVEL -eq 5 ]] && echo "Code and Score: $code_and_score"

        # This went beyond the scope of this script, jq will complain about too long argument list
        # If you want to use the extracted code, I suggest writing it to a file and adding the filename to the json, or adding it to a DB - which I will do next
        #if [[ ! -z "$code_and_score" && "$code_and_score" != '[]' && "$code_and_score" != '{}' ]]; then
            # Add the code as b64 to the CVE data
        #    cab_b64=$(echo "$code_and_score" | base64 -w 0)
        #    cve_list_json=$(jq "map(if .\"a:href\" == \"$link\"  then . + { \"ExploitCode\":\"$cab_b64\" } else . end)" <<< "$cve_list_json")
        #fi
    done
done

# Get cmdline args
while getopts j:t: opt
do
   case $opt in
       j) echo "$cve_list_json" > "$OPTARG";;
       t) echo "$cve_list_json" | jsonq.py -t > "$OPTARG";;
    esac
done

# Print the updated JSON 
#  echo "$cve_list_json" 

# Print the updated JSON as Table
echo "$cve_list_json" | jsonq.py -t

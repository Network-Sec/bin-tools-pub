#!/bin/bash

# Usage: github_search_downloader.sh "Defcon 31"
# The script will search GitHub for the keyword(s), enumerate the user of the repos found,
# and then try to download all repos and gists from that user. Note that API calls may quickly 
# lead to rate limiting issues. You can provide an API key and login to get wider limits.

# IMPORTANT: Set your download-folder here and provide enough disk space!
final_dir="/tmp/Github"

urlencode() {
    python3 -c "import sys, urllib.parse as ul; url = sys.stdin.read().strip(); parsed = ul.urlsplit(url); encoded_query = ul.quote(parsed.query, safe='=&'); print(f'{parsed.scheme}://{parsed.netloc}{parsed.path}?{encoded_query}')"
}
export -f urlencode
export GIT_TERMINAL_PROMPT=0

# Check if a keyword is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <search_keyword>"
    exit 1
fi

keyword=$1
cache_dir="${final_dir}/downloader_cache"
result_file="${cache_dir}/results_${keyword}.json"

# Create the necessary directories
mkdir -p "$cache_dir"

# Function to handle rate limiting
handle_rate_limit() {
    reset_time=$(curl -sI https://api.github.com/rate_limit | grep -Fi X-RateLimit-Reset | awk '{print $2}')
    current_time=$(date +%s)
    sleep_time=$((reset_time - current_time + 10)) # Add 10 seconds buffer
    echo "Rate limit exceeded. Sleeping for $sleep_time seconds..."
    sleep "$sleep_time"
}

# Search for the keyword if not cached
if [[ ! -f "$result_file" ]]; then
    echo "Searching GitHub for keyword: $keyword"
    search_url=$(echo "https://api.github.com/search/repositories?q=$keyword&per_page=100" | urlencode)
    result=$(curl -s "$search_url")
    if [[ "$(echo $result | jq -r '.message')" == "API rate limit exceeded" ]]; then
        handle_rate_limit
        result=$(curl -s "$search_url")
    fi
    echo "$result" > "$result_file"
else
    echo "Using cached search results for keyword: $keyword"
fi

# Extract unique usernames from search results
usernames=($(jq -r '.items[].owner.login' < "$result_file" | sort | uniq))

# Clone repositories and gists for each username
for username in "${usernames[@]}"; do
    echo "Processing user: $username"
    user_repo_dir="${final_dir}/${username}"
    user_gist_dir="${final_dir}/${username}_gists"

    # Clone repositories
    mkdir -p "$user_repo_dir"
    cd "$user_repo_dir"
    repo_url="https://api.github.com/users/$username/repos?per_page=1000"
    repos=$(curl -s "$repo_url" | jq -r '.[].clone_url')
    for repo in $repos; do
        repo_name=$(basename "$repo" .git)
        if [[ ! -d "$repo_name" ]]; then
            echo "Cloning repository: $repo"
            git clone "$repo"
        else
            echo "Repository $repo_name already exists, skipping."
        fi
    done

    # Clone gists
    mkdir -p "$user_gist_dir"
    cd "$user_gist_dir"
    gist_url="https://api.github.com/users/$username/gists?per_page=100"
    gists=$(curl -s "$gist_url" | jq -c '.[] | {file: .files | to_entries[0].key, raw_url: .files | to_entries[0].value.raw_url}')
    for gist in $gists; do
        file=$(echo $gist | jq -r '.file' | tr '.' '_')
        raw_url=$(echo $gist | jq -r '.raw_url')
        echo "Downloading gist: $file"
        wget -O "./${file}" "$raw_url"
    done

    echo "Finished processing user: $username"
done

# Clean up cache
rm -rf "$cache_dir"

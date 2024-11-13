#!/bin/bash

username=$1
output_dir="$username"
per_page=100
page=1
repos=()

# Create a directory for the user’s repos if it doesn't exist
[[ ! -e "$output_dir" ]] && mkdir "$output_dir"

# Fetch all repo URLs and store them in an array
while : ; do
  response=$(curl -s "https://api.github.com/users/$username/repos?per_page=$per_page&page=$page" | jq -r '.[].clone_url')
  [[ -z "$response" ]] && break
  repos+=($response)
  ((page++))
done

# Print all fetched repositories for confirmation
echo "Fetched repositories:"
printf '%s\n' "${repos[@]}"

# Change to output directory
cd "$output_dir" || exit

# Loop over each repository URL
for repo in "${repos[@]}"; do
  repo_name=$(basename "$repo" .git)

  # Check if the directory already exists
  if [[ -d "$repo_name" ]]; then
    # Check if the directory is empty
    if [[ -z "$(ls -A "$repo_name")" ]]; then
      echo "$repo_name directory is empty. Re-cloning..."
      GIT_TERMINAL_PROMPT=0 timeout 120s git clone "$repo"
    else
      # If it’s a valid git repository, attempt to pull updates
      if [[ -d "$repo_name/.git" ]]; then
        echo "Updating $repo_name..."
        cd "$repo_name" && GIT_TERMINAL_PROMPT=0 git pull && cd ..
      else
        echo "$repo_name exists but is not a valid git repo. Skipping..."
      fi
    fi
  else
    # Clone the repo if the directory does not exist
    echo "Cloning $repo_name..."
    GIT_TERMINAL_PROMPT=0 timeout 120s git clone "$repo"
  fi
done

# Return to original directory
cd ..

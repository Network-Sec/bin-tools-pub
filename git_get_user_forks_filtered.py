#!/usr/bin/env python3

import sqlite3
import requests
import time
import json
import re

# GitHub API setup
API_URL = "https://api.github.com"
API_TOKEN = ""  # Replace with your GitHub token, or leave empty
HEADERS = {"Authorization": f"token {API_TOKEN}"} if API_TOKEN else {}
SLEEP_TIME = 2  # Throttle between requests

# Database setup
DB_FILE = "github_repos_recurse.db"
conn = sqlite3.connect(DB_FILE)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA foreign_keys = ON;")

def setup_database():
    """Set up tables for JSON storage and structured data."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS json_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            data JSON
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS repo_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT,
            repo_name TEXT,
            description TEXT,
            forked_from TEXT,
            json_ref INTEGER,
            FOREIGN KEY (json_ref) REFERENCES json_data(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS visited_users (
            username TEXT PRIMARY KEY
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            username TEXT PRIMARY KEY,
            last_repo TEXT
        )
    """)

def fetch_user_info(username):
    """Fetch user info and handle rate limit errors."""
    try:
        response = requests.get(f"{API_URL}/users/{username}", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 403:
            print("Rate limit hit. Waiting 20 seconds...")
            time.sleep(20)
            return fetch_user_info(username)
        else:
            print(f"HTTP error for user {username}: {err}")
    return None

def fetch_repos(username, filter_values=None):
    """Fetch user's repos with pagination and optional filtering."""
    repos = []
    page = 1
    while True:
        try:
            # Fetch up to 100 repos per page to reduce the number of requests
            response = requests.get(
                f"{API_URL}/users/{username}/repos?type=forks",
                headers=HEADERS,
                params={"per_page": 100, "page": page}
            )
            response.raise_for_status()
            page_repos = response.json()
            
            # Break the loop if there are no more repositories
            if not page_repos:
                break

            # Apply filtering if filter_values is provided
            if filter_values:
                page_repos = [
                    repo for repo in page_repos
                    if any(value.lower() in repo["name"].lower() for value in filter_values)
                ]
                
            repos.extend(page_repos)
            page += 1
            time.sleep(SLEEP_TIME)  # Throttle API requests

        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 403:
                print("Rate limit hit. Waiting 20 seconds...")
                time.sleep(20)
                continue
            else:
                print(f"HTTP error for repos of {username}: {err}")
                break
    return repos

def save_to_db(username, user_info, repos, filter_values=None):
    """Save JSON data and structured data to DB with optional filtering."""
    # Insert JSON user data
    conn.execute("INSERT INTO json_data (username, data) VALUES (?, ?)", (username, json.dumps(user_info)))
    json_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    repo_count = 0
    for repo in repos:
        # Filter repos based on name only
        if filter_values and not any(value.lower() in repo["name"].lower() for value in filter_values):
            continue

        repo_info = {
            "repo_name": repo["name"],
            "description": repo["description"],
            "forked_from": repo.get("parent", {}).get("owner", {}).get("login") if repo.get("fork") else None
        }
        
        # Insert repo information in both tables
        conn.execute("INSERT INTO repo_info (owner, repo_name, description, forked_from, json_ref) VALUES (?, ?, ?, ?, ?)",
                     (username, repo_info["repo_name"], repo_info["description"], repo_info["forked_from"], json_id))
        
        repo_count += 1
    conn.commit()
    print(f"Saved {repo_count} repos for user {username}")

def fetch_repo_details(repo_url):
    """Fetch detailed information about a repository."""
    try:
        response = requests.get(repo_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repo details: {e}")
        return None

def recursive_fetch(username, filter_values=None):
    """Main function to recursively fetch data for a user and their forks."""
    
    # Load previously visited users to avoid reprocessing
    visited_users = set(row[0] for row in conn.execute("SELECT username FROM visited_users").fetchall())
    queue = list(set(username.split(',')))  # Split comma-separated usernames and add to queue
    processed_initial_users = set(queue) 
    total_users_processed = 0

    while queue:
        current_user = queue.pop(0)
        
        # Skip if user is already visited
        if current_user in visited_users and current_user not in processed_initial_users:
            print(f"User {current_user} already visited, skipping.")
            continue
        
        # Ensure initial users are processed at least once more
        if current_user in processed_initial_users:
            processed_initial_users.remove(current_user)  # Remove from the "process once more" list

        # Mark as visited and insert into the database
        visited_users.add(current_user)
        conn.execute("INSERT OR IGNORE INTO visited_users (username) VALUES (?)", (current_user,))
        conn.commit()

        # Fetch user and repo data
        user_info = fetch_user_info(current_user)
        if user_info is None:
            print(f"Skipping user {current_user} due to missing data.")
            continue
        repos = fetch_repos(current_user, filter_values=filter_values)

        # Save filtered or unfiltered data to DB
        save_to_db(current_user, user_info, repos, filter_values=filter_values)
        
        # Process forked repos to queue their sources
        for repo in repos:
            if repo.get("fork") and "url" in repo:
                repo_details = fetch_repo_details(repo["url"])
                
                if repo_details and "parent" in repo_details:
                    # The parent is the direct source of the fork
                    forked_from_user = repo_details["parent"]["owner"]["login"]
                    if forked_from_user not in visited_users and forked_from_user not in queue:
                        print(f"Adding {forked_from_user} to the queue from forked repo {repo['name']}")
                        queue.append(forked_from_user)
                        print("Queue:", queue)

        # Update the total processed count and output status
        total_users_processed += 1
        print(f"Processed user: {current_user} | Repos: {len(repos)} | Total users processed: {total_users_processed} | Queue length: {len(queue)}")

        # Throttle API requests
        time.sleep(SLEEP_TIME)

def resume_from_checkpoint(username, filter_values=None):
    """Resume processing from the last checkpoint for a user."""
    cursor = conn.execute("SELECT last_repo FROM checkpoints WHERE username = ?", (username,))
    checkpoint = cursor.fetchone()
    if checkpoint:
        print(f"Resuming from repo: {checkpoint[0]}")
    else:
        recursive_fetch(username, filter_values=filter_values)

def main(username, filter_value=None):
    # Split filter_value by commas
    filter_values = [value.strip() for value in filter_value.split(",")] if filter_value else None
    setup_database()
    resume_from_checkpoint(username, filter_values=filter_values)
    conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch and process GitHub user repos recursively.")
    parser.add_argument("username", type=str, help="GitHub username to start with")
    parser.add_argument("--filter", type=str, help="Optional filter value for repo names (comma separated for OR filtering)")
    args = parser.parse_args()
    main(args.username, filter_value=args.filter)

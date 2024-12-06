# Very generic fuzzing script, bit too slow atm to test everythin as we would like to... 
# Initial commit, works but too slow / too broad
# Improved speed, removed some verbs - adjust to target as needed

import socket
import re
import requests
import itertools
from collections import defaultdict
import sys

ports = [18181, 3000, 7000, 7250, 36866, 3001, 1086, 1092]
prefixes = ["", "/apps/"]
faulty_paths = ["/major>", "/xml>", "/test", "/example", "/random", "/<invalid>", "/\\"]
fuzz_paths = []# ["/" + "A" * (2 ** n) for n in range(2, 17)]
initial_paths = set(faulty_paths + fuzz_paths)
http_verbs = [
    "GET", "INDEX",
    "OPTIONS", 
    "POST", "PUT", "TRACE"
]
protocols = ["http", "ftp", "gopher", "rtsp"]
auth_usernames = ["admin", "root", "webos", "lg", "lgadmin"]
auth_passwords = ["1234", "admin", "root", "password", "12345", "webos", "lg", "lgadmin"]
auth_combos = list(itertools.product(auth_usernames, auth_passwords))
rtsp_methods = ["OPTIONS", "DESCRIBE", "SETUP", "PLAY"]

def load_fuzz_paths(fuzz_file="fuzz.txt"):
    try:
        with open(fuzz_file, "r") as f:
            paths = [line.strip() for line in f.readlines()]
        return set(paths)
    except FileNotFoundError:
        return set()

initial_paths.update(load_fuzz_paths())

def extract_paths(response):
    paths = set()
    path_pattern = r"/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+"
    matches = re.findall(path_pattern, response.text)
    paths.update(matches)
    return paths

def make_request(protocol, host, port, prefix, path, verb, auth=None):
    if protocol in ["http", "https"]:
        url = f"{protocol}://{host}:{port}{prefix}{path}"
        headers = {}
        if auth:
            headers["Authorization"] = f"Basic {auth}"
        try:
            response = requests.request(verb, url, headers=headers, timeout=0.25)
            return response
        except requests.exceptions.RequestException:
            return None
    elif protocol == "rtsp":
        for i, method in enumerate(rtsp_methods):
            auth_header = f"Authorization: Basic {auth}" if auth else ""
            for template in req_templates:
                request = template(method, i, port, auth_header)
                try:
                    with socket.create_connection((host, port), timeout=0.25) as s:
                        s.sendall(request)
                        response = s.recv(4096).decode()
                        return response
                except (socket.error, socket.timeout):
                    pass
    return None

all_paths = set(initial_paths)
new_paths = set()
max_feedback_length = 0
iteration = 0

# Initialize response counters
response_counters = {"no_response": 0, "status_code": 0, "has_content": 0}

# Reset counters at the start of each iteration
response_counters = {key: 0 for key in response_counters}

while True:
    iteration += 1
    current_new_paths = set()
    print(f"--- Iteration {iteration} ---")

    # First, scan all known paths (initial + previously discovered)
    paths_to_scan = list(all_paths) if iteration == 1 else list(new_paths)
    for protocol in protocols:
        for port in ports:
            for path in paths_to_scan:
                for prefix in prefixes:
                    for verb in (http_verbs if protocol in ["http", "https"] else rtsp_methods):
                        for auth in [None] + [f"{u}:{p}" for u, p in auth_combos]:
                            # Build the current feedback string
                            feedback = f"  Protocol: {protocol}, Port: {port}, Prefix: {prefix}, Path: {path}, Verb: {verb}, Auth: {auth or 'None'}"
                            padding = max(0, max_feedback_length - len(feedback))

                            cfb = f"{counter_feedback}{' ' * max_feedback_length}\r"

                            # Overwrite previous feedback line
                            sys.stdout.write(f"\r{feedback}{' ' * padding} {cfb}")
                            sys.stdout.flush()
                            max_feedback_length = max(max_feedback_length, len(feedback))

                            # Make the HTTP request or RTSP request
                            response = make_request(protocol, "192.168.2.9", port, prefix, path, verb, auth)

                            # Update response counters based on the response
                            if response:
                                response_counters["status_code"] += 1
                                if response.headers or response.text:
                                    response_counters["has_content"] += 1
                            else:
                                response_counters["no_response"] += 1

                            # Print the response counters on a new line, but overwrite it using \r
                            counter_feedback = (
                                f"No Response: {response_counters['no_response']} | "
                                f"Responses w. Status Code: {response_counters['status_code']} | "
                                f"Responses w. Content: {response_counters['has_content']}"
                            )                   


    # After scanning known paths, prepare for the next iteration
    if current_new_paths:
        print(f"Found {len(current_new_paths)} new path(s).")
        new_paths = current_new_paths
        all_paths.update(current_new_paths)
    else:
        print("No new paths found, stopping.")
        break


print("\n--- Final List of Paths ---")
for path in sorted(all_paths):
    print(f"  {path}")

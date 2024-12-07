# Very generic fuzzing script, bit too slow atm to test everythin as we would like to... 
# Initial commit, works but too slow / too broad
# Improved speed, removed some verbs - adjust to target as needed
# Adjusted output to run on Windows / Powershell (see commented sys.stdout) which doesn't support \r
import socket
import re
import requests
import itertools
from collections import defaultdict
import sys

host = "192.168.2.9"
ports = [18181, 3000, 7000, 7250, 36866, 3001, 1086, 1092]
prefixes = ["", "/apps/"]
faulty_paths = ["/major>", "/xml>", "/test", "/example", "/random", "/<invalid>", "/\\"]
fuzz_paths = []# ["/" + "A" * (2 ** n) for n in range(2, 17)]
initial_paths = set(faulty_paths + fuzz_paths)
http_verbs = ["GET"]#, "INDEX","OPTIONS","POST", "PUT", "TRACE"]
protocols = ["http", "ftp", "gopher", "rtsp"]
auth_usernames = ["admin", "root", "webos", "lg", "lgadmin"]
auth_passwords = ["1234", "admin", "root", "password", "12345", "webos", "lg", "lgadmin"]
auth_combos = list(itertools.product(auth_usernames, auth_passwords))
rtsp_methods = ["OPTIONS", "DESCRIBE", "SETUP", "PLAY"]
req_templates = [
    lambda method, i, port, auth: f"{method} rtsp://{host}:{port} RTSP/1.0\r\nCSeq: {i+1}\r\n{auth}\r\n\r\n".encode(),
    lambda method, i, port, auth: f"{method} rtsp://{host}:{port} RTSP/1.0\r\nCSeq: {i+1}\r\n\r\n".encode()
]

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

    #print(response)

    # If response is a CaseInsensitiveDict (headers), extract relevant headers
    if isinstance(response, requests.structures.CaseInsensitiveDict):
        for header, value in response.items():
            if isinstance(value, str):  # Ensure the value is a string before applying regex
                matches = re.findall(r"/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+", value)
                paths.update(matches)
    # If the response is a string (body content), search it directly
    elif isinstance(response, str):
        matches = re.findall(r"/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=%]+", response)
        paths.update(matches)
    return paths

def make_request(protocol, host, port, prefix, path, verb, auth=None):
    if protocol in ["http", "https"]:
        url = f"{protocol}://{host}:{port}{prefix}{path}"
        headers = {}
        if auth:
            headers["Authorization"] = f"Basic {auth}"
        try:
            response = requests.request(verb, url, headers=headers, timeout=0.125)
            return response
        except requests.exceptions.RequestException:
            return None
    elif protocol == "rtsp":
        for i, method in enumerate(rtsp_methods):
            auth_header = f"Authorization: Basic {auth}" if auth else ""
            for template in req_templates:
                request = template(method, i, port, auth_header)
                try:
                    with socket.create_connection((host, port), timeout=0.125) as s:
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
response_counters = {"no_response": 0, "status_code": 0, "has_content": 0, "has_body": 0, "PathsInHeader": 0, "PathsInBody": 0}
counter_feedback = (
    f"No Response: {response_counters['no_response']} | "
    f"Responses w. Status Code: {response_counters['status_code']} | "
    f"Responses w. Content: {response_counters['has_content']} | "
    f"Responses w. Body: {response_counters['has_body']} | "
    f"Paths in header: {response_counters['PathsInHeader']} | "
    f"Paths in body: {response_counters['PathsInBody']} "
)

# Reset counters at the start of each iteration
response_counters = {key: 0 for key in response_counters}
feedback = None
padding = None
cfb = None

while True:
    iteration += 1
    print(f"--- Iteration {iteration} ---")
    print(f"Scanning {len(all_paths) + len(new_paths)} total path(s) on {len(ports)} ports with {len(http_verbs)} HTTP verbs...")

    # First, scan all known paths (initial + previously discovered)
    paths_to_scan = list(all_paths) if iteration == 1 else list(new_paths)
    current_new_paths = set()
    for protocol in protocols:
        for port in ports:
            
            for path in paths_to_scan:
                for prefix in prefixes:
                    for verb in (http_verbs if protocol in ["http", "https"] else rtsp_methods):
                        for auth in [None]: # + [f"{u}:{p}" for u, p in auth_combos]:

                            feedback = f"  Protocol: {protocol}, Port: {port}, Prefix: {prefix}, Path: {path}, Verb: {verb}, Auth: {auth or 'None'}"
                            padding = max(0, max_feedback_length - len(feedback))

                            cfb = f"{counter_feedback}" #{' ' * max_feedback_length}"

                            # Overwrite previous feedback line
                            #sys.stdout.write(f"\r{feedback}{' ' * padding} {cfb}", end="")
                            #sys.stdout.flush()
                            max_feedback_length = max(max_feedback_length, len(feedback))

                            # Make the HTTP request or RTSP request
                            response = make_request(protocol, host, port, prefix, path, verb, auth)

                            # Update response counters based on the response
                            if response:
                                response_counters["status_code"] += 1
                                if response.headers or response.text:
                                    response_counters["has_content"] += 1

                                # Extract paths from headers if available
                                if response.headers:
                                    newpths = extract_paths(response.headers)  # Now handles CaseInsensitiveDict
                                    response_counters['PathsInHeader'] += len(newpths)
                                    current_new_paths.update(newpths)

                                # Extract paths from the body if available
                                if response.text:
                                    response_counters['has_body'] += +1
                                    newpths = extract_paths(response.text)  # Handles the body content
                                    response_counters['PathsInBody'] += len(newpths)
                                    current_new_paths.update(newpths)

                            else:
                                response_counters["no_response"] += 1

                            counter_feedback = (
                                f"No Response: {response_counters['no_response']} | "
                                f"Responses w. Status Code: {response_counters['status_code']} | "
                                f"Responses w. Content: {response_counters['has_content']} | "
                                f"Responses w. Body: {response_counters['has_body']} | "
                                f"Paths in header: {response_counters['PathsInHeader']} | "
                                f"Paths in body: {response_counters['PathsInBody']} "
                            )
                print(f"{feedback} {cfb}")
    # After scanning known paths, prepare for the next iteration
    if current_new_paths:
        print(f"Found {len(current_new_paths)} new path(s).")
        new_paths.update(current_new_paths)
    else:
        print("No new paths found, stopping.")
        break


print("\n--- Final List of Paths ---")
for path in sorted(all_paths):
    print(f"  {path}")


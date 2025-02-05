#!/usr/bin/env python3
# Simple Python Port scanner with Top-1000 default ports
# Works on public VPN

import socket
import argparse
import concurrent.futures

# Default ports (Nmap top 1000 + requested list)
DEFAULT_PORTS = [
    80, 23, 443, 21, 22, 25, 3389, 110, 445, 139, 143, 53, 135, 3306, 8080, 1723, 111, 995, 993, 5900, 1025, 587, 8888,
    199, 1720, 465, 548, 113, 81, 6001, 10000, 514, 5060, 179, 1026, 2000, 8443, 8000, 32768, 554, 26, 1433, 49152, 2001,
    515, 8008, 49154, 1027, 5666, 646, 5000, 5631, 631, 49153, 8081, 2049, 88, 79, 5800, 106, 2121, 1110, 49155, 6000,
    513, 990, 5357, 427, 49156, 543, 544, 5101, 144, 7, 389, 8009, 3128, 444, 9999, 5009, 7070, 5190, 3000, 5432, 1900,
    3986, 13, 1029, 9, 5051, 6646, 49157, 1028, 873, 1755, 2717, 4899, 9100, 119, 37, 1000, 3001, 5001, 82, 10010, 1030,
    9090, 2107, 1024, 2103, 6004, 1801, 5050, 19, 8031, 1041, 255, 1049, 1048, 2967, 1053, 3703, 1056, 1065, 1064, 1054,
    17, 808, 3689, 1031, 1044, 1071, 5901, 100, 9102, 8010, 2869, 1039, 5120, 4001, 9000, 2105, 636, 1038, 2601, 1, 7000
]

def scan_port(target, port, timeout):
    """Attempts to verify an open port with connection & banner grabbing."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((target, port)) == 0:  # Check if port is open
                try:
                    s.send(b"\r\n")  # Try to get a response
                    banner = s.recv(1024).decode().strip()  # Grab banner
                except Exception:
                    banner = "Unknown service"

                print(f"[+] Open: {target}:{port} ({banner})")
    except Exception as e:
        print(f"[-] Error scanning {port}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Python Port Scanner with Banner Grabbing")
    parser.add_argument("-t", "--target", required=True, help="Target IP or hostname")
    parser.add_argument("-p", "--ports", default=",".join(map(str, DEFAULT_PORTS)), help="Comma-separated ports")
    parser.add_argument("--timeout", type=float, default=1, help="Connection timeout per port (default: 1s)")
    parser.add_argument("--threads", type=int, default=200, help="Number of parallel threads (default: 200)")

    args = parser.parse_args()
    target = args.target
    ports = list(map(int, args.ports.split(",")))
    timeout = args.timeout
    threads = args.threads

    print(f"Scanning {target} on {len(ports)} ports with {threads} threads...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(lambda port: scan_port(target, port, timeout), ports)

    print("Scan complete.")

if __name__ == "__main__":
    main()

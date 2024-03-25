#!/usr/bin/env python3

import argparse
import subprocess

def extract_ssids_from_dump(file_path):
    with open(file_path, 'r', encoding='utf-8') as dump_file:
        for line in dump_file:
            segments = line.strip().split('*')
            if len(segments) > 3 and segments[0].startswith('WPA'):
                ssid_hex = segments[5]
                ssid_python = bytes.fromhex(ssid_hex).decode('utf-8', 'replace')
                print(f"{ssid_hex}:{ssid_python}")

def main():
    parser = argparse.ArgumentParser(description="Extract SSIDs from a WPA*02 format dump file.")
    parser.add_argument("file", help="The path to the dump file containing WPA*02 formatted lines.")

    args = parser.parse_args()
    extract_ssids_from_dump(args.file)

if __name__ == "__main__":
    main()




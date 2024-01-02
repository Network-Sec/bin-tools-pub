#! /usr/bin/env python3

# An alternative jq processor
# v.0.0.1 - only JSON to Table conversion

import argparse
import sys
import re
from bs4 import BeautifulSoup
from math import floor
from tabulate import tabulate
import textwrap
import tty
import termios
import os
import json

def get_terminal_width():
    try:
        with open('/dev/tty') as tty_file:
            tty.setraw(tty_file.fileno())
            return os.get_terminal_size().columns
    except Exception as e:
        return 120  

def format_table(data, omit_headers):
    headers = data[0].keys() if data else []
    formatted_data = []
    col_base = 10

    for entry in data:
        formatted_row = []

        for key in headers:
            value = entry[key]

            if isinstance(value, list):
                # Handle arrays by joining text content with newlines
                value = "\n".join(map(str, value))
            else:
                value = str(value)

            formatted_row.append(value)

        formatted_data.append(formatted_row)

    # Define table options
    table_format = "grid"
    numalign = "center"
    stralign = "center"
    colalign = ("left", "center", "left", "left")
    floatfmt = ".2f"
    intfmt = ",d"
    colwidth = [col_base * 2, col_base * 2, col_base * 4, col_base * 6]

    # Format the table
    formatted_table = tabulate(formatted_data, headers=headers, tablefmt=table_format, numalign=numalign, stralign=stralign, colalign=colalign, floatfmt=floatfmt, intfmt=intfmt, maxcolwidths=colwidth)

    return formatted_table

def convert_json_to_table(json_data):
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        print("Invalid JSON input:", e.msg)
        sys.exit(1)

    if not isinstance(data, list):
        print("JSON input should be a list of dictionaries")
        sys.exit(1)

    if not data:
        print("No data to convert")
        sys.exit(0)

    formatted_table = format_table(data, False)

    return formatted_table

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='jsonq - maybe someday a jq alternative')
    parser.add_argument('-t', '--table', required=False, action='store_true', help='Print JSON as a table')
    args = parser.parse_args()

    json_input = sys.stdin.read().strip()

    if args.table:
        table_output = convert_json_to_table(json_input)
        print(table_output)

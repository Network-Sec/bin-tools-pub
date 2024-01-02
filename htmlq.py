#!/usr/bin/env python3

# An alternative to "pup" - a simple HTML processor
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

def extract_data(html, loop_selector, selectors, url_root=""):
    data = []
    soup = BeautifulSoup(html, 'html.parser')
    loop_elements = soup.select(loop_selector)
    url_selectors = ['a:href', 'img:src', 'link:href', 'script:src', 'audio:src', 'embed:src', 'iframe:src', 'source:src', 'track:src', 'video:src', 'area:href', 'object:data', 'form:action', 'input:formaction', 'blockquote:cite', 'q:cite', 'ins:cite', 'del:cite', 'a:data-href', 'button:data-href', 'area:data-href', 'a:data-src', 'button:data-src', 'img:data-src', 'source:data-src', 'video:data-src', 'link:href', 'script:src', 'audio:src', 'embed:src', 'iframe:src', 'source:src', 'track:src', 'video:src', 'area:href', 'object:data', 'form:action', 'input:formaction', 'blockquote:cite', 'q:cite', 'ins:cite', 'del:cite', 'a:data-href', 'button:data-href', 'area:data-href', 'a:data-src', 'button:data-src', 'img:data-src', 'source:data-src', 'video:data-src']

    for element in loop_elements:
        if not element:
            continue

        entry = {}

        for selector in selectors:
            html_sel, part_sel = selector.split(":")
            try:
                selections = element.select(html_sel)
            except:
                pass
            
            if not selections:
                selections = element.find_all(html_sel)

            if not selections:
                continue
            
            for sel in selections:
                if part_sel == "text":
                    text = sel.get_text(strip=True)

                    # Replace unwanted chars that can mess up JSON
                    # Don't ask me why a single quote can mess up a double-quoted JSON
                    # field, but they do sometimes...
                    text = text.replace("'", "").replace("´", "").replace("`", "").replace('"', "")         
                else:
                    text = sel[part_sel]
                
                # Check if we should add a root url
                if url_root and selector in url_selectors and not text.startswith("http"):
                    text = url_root + text

                entry[selector] = text
        data.append(entry)

    return data

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
    col_base = 10 # int(floor((get_terminal_width() / 100) * 20) - 1) # Not sure why this screws itself

    for entry in data:
        formatted_row = [str(entry[key]) for key in headers]
        formatted_data.append(formatted_row)

    # Define options
    table_format = "grid"
    numalign = "center"
    stralign = "center"
    colalign = ("left", "center", "left")
    floatfmt = ".2f"
    intfmt = ",d"
    # colwidth = [20, 20, 60]
    colwidth = [col_base * 2, col_base * 6, col_base * 6]

    # Format the table
    formatted_table = tabulate(formatted_data, headers=headers, tablefmt=table_format, numalign=numalign, stralign=stralign, colalign=colalign, floatfmt=floatfmt, intfmt=intfmt, maxcolwidths=colwidth)

    return formatted_table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTML Data Extraction')
    parser.add_argument('-j', '--json', required=False, action='store_true', help='Output as JSON')
    parser.add_argument('-l', '--loop', required=False, help='Loop selector')
    parser.add_argument('-s', '--selectors', required=False, help='Selectors (space-separated)')
    parser.add_argument('-t', '--table', required=False, action='store_true', help='Print as table')
    parser.add_argument('-o', '--omit', required=False, action='store_true', help='Omit Field names in list output')
    parser.add_argument('-u', '--urlroot', required=False, help='You can provide the base url, so it will be added before relative URLs')
    args = parser.parse_args()

    html_input = sys.stdin.read()

    # When no selectors, no loop and no table output is present, exit
    if not args.selectors and not args.loop:
        print("Error: you need to define loop and selector(s)")
        exit(0)

    loop_selector = args.loop
    selectors = args.selectors.split()
    
    # Check if we need to add a root URL
    if args.urlroot:
        url_root = args.urlroot
        result = extract_data(html_input, loop_selector, selectors, url_root)
    else:
        result = extract_data(html_input, loop_selector, selectors)

    # Output as table
    if args.table:
        table = format_table(result, args.omit)
        print()
        print(table)
        print()

    # Output as JSON
    elif args.json:
        print(json.dumps(result))
    
    # Output as plain text
    else:
        for entry in result:
            for key, value in entry.items():
                if not args.ommit:
                    print(f'{key}: {value}')
                else:
                    print(f'{value}')
            print()

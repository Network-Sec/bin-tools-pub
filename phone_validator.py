#!/usr/bin/env python3

import sys
import os
import phonenumbers
from phonenumbers import geocoder
import re
import random
import argparse
import shutil

VERBOSE = False

# Define the threshold for the number of valid phone numbers in a file 
# to be considered a phonebook
PHONEBOOK_THRESHOLD = 0.05

# Define the maximum widths for each column
phone_max = 20
country_max = 28
city_max = 28
valid_max = 9

# ANSI color codes
color_default = "\033[39m"
color_bright_yellow = "\033[93m"
color_bright_blue = "\033[94m"
color_green = "\033[92m"
color_red = "\033[91m"

def format_header():
    phone_header = "Phone Number"
    country_header = "Country"
    city_header = "City"
    validity_header = "Validity"

    ws_phone = " " * (phone_max - len(phone_header))
    ws_country = " " * (country_max - len(country_header))
    ws_city = " " * (city_max - len(city_header))
    ws_validity = " " * (valid_max - len(validity_header))

    header = f"| {phone_header}{ws_phone} | {country_header}{ws_country} | {city_header}{ws_city} | {validity_header}{ws_validity} |"
    separator = "|:" + "-"*phone_max + "-|:" + "-"*country_max + "-|:" + "-"*city_max + "-|:" + "-"*valid_max + "-|"
    return header, separator

def strip_ansi_codes(s):
    return re.sub(r'\033\[[0-9;]*m', '', s)

def format_row(phone_number, country, city, validity):
    visible_phone_length = len(strip_ansi_codes(phone_number))
    visible_country_length = len(strip_ansi_codes(country))
    visible_city_length = len(strip_ansi_codes(city))
    visible_validity_length = len(strip_ansi_codes(validity))

    ws_phone = " " * (phone_max - visible_phone_length)
    ws_country = " " * (country_max - visible_country_length)
    ws_city = " " * (city_max - visible_city_length)
    ws_validity = " " * (valid_max - visible_validity_length)
    
    row = f"| {phone_number}{ws_phone} | {country}{ws_country} | {city}{ws_city} | {validity}{ws_validity} |"
    return row

def standardize_phone_number(number):
    # Remove all non-digit characters except the extension separator
    number = re.sub(r'[^\d+]', '', number)
    return number

def split_extension(number):
    # Match and split the extension if it exists
    match = re.search(r'(.+?)-(\d{1,3})$', number)
    if match:
        base_number = match.group(1)
        extension = match.group(2)
        return base_number, extension
    return number, None

def validate_phone_number(number):
    try:
        # If the number does not start with '+', add it assuming it to be an international number
        if not number.startswith('+'):
            number = '+' + number

        parsed_number = phonenumbers.parse(number)
        if not phonenumbers.is_valid_number(parsed_number):
            return number, "", "", "invalid"
        
        country = geocoder.country_name_for_number(parsed_number, "en")
        city = geocoder.description_for_number(parsed_number, "en")
        
        return number, country, city, "valid"
    except phonenumbers.NumberParseException:
        return number, "", "", "invalid"

# Better for large files - but can be slow for small files
def readby_linenumber(thefile, whatlines):
  return [x for i, x in enumerate(thefile) if i in whatlines]

def find_phonebooks(directory, allow_blank, move_files=None):
    if move_files:
        print(f"[!] Moving files to {move_files}")

    # Case where we want to test for phone numbers with spaces
    phone_regex = re.compile(r'\b\d+(?:\s\d+)?\b')
    
    # Case where we want to test for phone numbers without spaces
    if not allow_blank:
        phone_regex = re.compile(r'\b\d{2,}\b')

    valid_phonebook_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if VERBOSE:
                print(f"[?] Checking {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = []
                    for i in range(3000):
                        line = f.readline()
                        if not line:
                            break
                        lines.append(line)
                    
                    if len(lines) > 300:
                        lines = random.sample(lines, 300)
                    
                    found_numbers = []
                    for line in lines:
                        candidates = phone_regex.findall(line)
                        for candidate in candidates:
                            found_numbers.append(candidate.strip())
                    
                    valid_count = 0
                    for number in found_numbers:
                        standardized_number = standardize_phone_number(number)
                        base_number, _ = split_extension(standardized_number)
                        _, _, _, validity = validate_phone_number(base_number)
                        if validity == "valid":
                            valid_count += 1
                    
                    # How many numbers relative to the number of lines
                    valid_ratio = valid_count / 300

                    if VERBOSE:
                        print(f"[+] Found {valid_count} valid phone numbers in {file_path}, ratio: {valid_ratio}")

                    if valid_ratio > PHONEBOOK_THRESHOLD:
                        print(file_path)
                        valid_phonebook_files.append(file_path)
                        if move_files:
                            shutil.move(file_path, os.path.join(move_files, os.path.basename(file_path)))

            except Exception as e:
                continue
        

def main():
    parser = argparse.ArgumentParser(description="Validate international phone numbers and print results in a markdown table.\n\nExamples:\n\n  phone_validator.py +14155552671\n  phone_validator.py +14155552671 +14155552672\n  cat numbers.txt | phone_validator.py\n  phone_validator.py -f numbers.txt\n  echo +14155552671 | phone_validator.py\n", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('numbers', nargs='*', help='Phone numbers to validate. Can be provided as arguments or via stdin.')
    parser.add_argument('-f', '--file', type=argparse.FileType('r'), help='File containing phone numbers to validate, one per line.')
    parser.add_argument('--find-phonebooks', type=str, help='Directory to search for phonebook files.')
    parser.add_argument('--move-files', type=str, help='Directory to move phonebook files if found.')
    parser.add_argument('--allow-blank', action='store_true', help='Allow single blank spaces as part of phone numbers.')

    args = parser.parse_args()

    if args.find_phonebooks:
        find_phonebooks(args.find_phonebooks, args.allow_blank, args.move_files)
        sys.exit(0)
    
    phone_numbers = []
    
    if args.file:
        phone_numbers = [line.strip() for line in args.file]
    elif not sys.stdin.isatty():
        phone_numbers = [line.strip() for line in sys.stdin]
    else:
        phone_numbers = args.numbers

    if not phone_numbers:
        parser.print_help()
        sys.exit(1)

    header, separator = format_header()
    print(header)
    print(separator)
    
    for number in phone_numbers:
        # Standardize the phone number
        standardized_number = standardize_phone_number(number)
        
        # Detect and handle internal extensions
        base_number, extension = split_extension(standardized_number)
        
        base_number, country, city, validity = validate_phone_number(base_number)
        
        # Format colors
        country_colored = f"{color_bright_yellow}{country}{color_default}"
        city_colored = f"{color_bright_blue}{city}{color_default}"
        validity_colored = f"{color_green}{validity}{color_default}" if validity == "valid" else f"{color_red}{validity}{color_default}"
        
        if extension:
            base_number = f"{base_number}-{extension}"
        
        print(format_row(base_number, country_colored, city_colored, validity_colored))

if __name__ == "__main__":
    main()

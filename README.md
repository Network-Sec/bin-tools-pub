# My "bin folder" tools
Tools I created as FOSS.


## htmlq.py
To see examples how I use `htmlq` and `jsonq` - see the script: `cve_scrape.sh`.
```bash
$ htmlq.py -h
usage: htmlq.py [-h] [-j] -l LOOP -s SELECTORS [-t] [-o] [-u URLROOT]

HTML Data Extraction

options:
  -h, --help            show this help message and exit
  -j, --json            Output as JSON
  -l LOOP, --loop LOOP  Loop selector
  -s SELECTORS, --selectors SELECTORS
                        Selectors (space-separated)
  -t, --table           Print as table
  -o, --omit            Omit Field names in list output
  -u URLROOT, --urlroot URLROOT
                        You can provide the base url, so it will be added before relative URLs
```

## jsonq.py

### Example Table Output
```bash
+----------------+----------------------+------------------------------------------+--------------------------------------------------------------+
| CVE-2023-28503 | https://www.cvedetai | Rocket Software UniData versions prior   | https://nvd.nist.gov/vuln/detail/CVE-2023-28503              |
|                | ls.com/cve/CVE-2023- | to 8.2.4 build 3003 and UniVerse         | https://www.cve.org/CVERecord?id=CVE-2023-28503 https://www. |
|                |        28503/        | versions prior to 11.3.5 build 1001 or   | rapid7.com/db/modules/exploit/linux/misc/unidata_udadmin_aut |
|                |                      | 12.2.1 build 2002 suffer from an         | h_bypass http://packetstormsecurity.com/files/171854/Rocket- |
|                |                      | authentication bypass vulnerability,     | Software-Unidata-udadmin_server-Authentication-Bypass.html   |
|                |                      | where a special username with a          | https://www.rapid7.com/blog/post/2023/03/29/multiple-        |
|                |                      | deterministic password can be leveraged  | vulnerabilities-in-rocket-software-unirpc-server-fixed/      |
|                |                      | to bypass authentication checks and      |                                                              |
|                |                      | execute OS commands as the root user.    |                                                              |
+----------------+----------------------+------------------------------------------+--------------------------------------------------------------+
| CVE-2023-28502 | https://www.cvedetai | Rocket Software UniData versions prior   | https://nvd.nist.gov/vuln/detail/CVE-2023-28502              |
|                | ls.com/cve/CVE-2023- | to 8.2.4 build 3003 and UniVerse         | https://www.cve.org/CVERecord?id=CVE-2023-28502 https://www. |
|                |        28502/        | versions prior to 11.3.5 build 1001 or   | rapid7.com/db/modules/exploit/linux/misc/unidata_udadmin_pas |
|                |                      | 12.2.1 build 2002 suffer from a stack-   | sword_stack_overflow                                         |
|                |                      | based buffer overflow in the udadmin     | http://packetstormsecurity.com/files/171853/Rocket-Software- |
|                |                      | service that can lead to remote code     | Unidata-8.2.4-Build-3003-Buffer-Overflow.html                |
|                |                      | execution as the root user.              | https://www.rapid7.com/blog/post/2023/03/29/multiple-        |
|                |                      |                                          | vulnerabilities-in-rocket-software-unirpc-server-fixed/      |
+----------------+----------------------+------------------------------------------+--------------------------------------------------------------+
| CVE-2023-28252 | https://www.cvedetai | Windows Common Log File System Driver    | https://nvd.nist.gov/vuln/detail/CVE-2023-28252              |
|                | ls.com/cve/CVE-2023- | Elevation of Privilege Vulnerability     | https://www.cve.org/CVERecord?id=CVE-2023-28252 https://www. |
|                |        28252/        |                                          | rapid7.com/db/modules/exploit/windows/local/cve_2023_28252_c |
|                |                      |                                          | lfs_driver                                                   |
|                |                      |                                          | http://packetstormsecurity.com/files/174668/Windows-Common-  |
|                |                      |                                          | Log-File-System-Driver-clfs.sys-Privilege-Escalation.html    |
|                |                      |                                          | https://msrc.microsoft.com/update-                           |
|                |                      |                                          | guide/vulnerability/CVE-2023-28252                           |
+----------------+----------------------+------------------------------------------+--------------------------------------------------------------+
```
## fuzzlib.py
fuzzlib.py - encoding and fuzzing toolkit

- The script / lib is intended to be imported, still there's a main function at the end with an example implementation, meaning you can use it as-is / standalone
- I made this lib for usage as cli tool (quickly do some encoding stuff) as well as larger projects (e.g. XSS fuzzer)
- Both lib and fuzzer below are made async for best performance

### Usage Example
You should import this as a lib and could then utilize individual functions, or call
```python
encode_all_formats('"><svg onload=myXSStest>...')
```

which will process your string into a variety of encodings and other things practical for burp-suiting around...  
It's worth noting, that lots of encodings / conversion won't make much sense, unless there's a specific scenario, meaning a certain tech stack that will allow to use some type of encoding as a bypass or otherwise valuable addition to your exploit. fuzzlib in that regard is also a "lazy solution", meaning: Throwing spaghetti at the wall, see what sticks. 
```python
# Some of the functions that `encode_all_formats()` calls..

# - double-quote to single-quote variants
change_double_quotes(base)

# - quotes to ticks
change_quotes(base)

# - escaped quotes
escape_quotes(base)
escape_quotes(change_quotes(base))

# - url-encode
url_encode(base)
    
# - html-entity-encoded
html_encode_key(base)

# ...and many more - see source code for full list
```

## Redteam Homoglyph Generator
Including detection check (confusables.is_dangerous()). 

These days, Homoglyph attacks are among the top, bread & butter TTP of any APT. However, from the Blueteam side it's also recognized and (should be) implemented as defense in depth, e.g. all major browsers have built-in methods to counteract this type of attack. Yet, especially punny code conversion may be safe in browser (given that the user validates the link again, after clicking it, not everybody will) - but not safe in MUA, which might display the confusable.

An easy evasion of the browser punnycode conversion may be use of a long link with many params and some type of (open) redirect, so it won't be visible immediately - but that's just a guess at the moment, I haven't put a lot of thought and effort into this topic yet, I'm sure there's much more knowledge to be discovered.

I see Email addresses as the most dangerous vector, cause an attacker might be able to produce an exact representation of the address of a colleague, friend, business partner, high reputation address like microsoft.com etc.

We know countless, real attacks using this technique at some point.

```bash
$ python3 hggenerator.py --codebox --homoglyphs --max_homoglyphs 2  "network-sec.de"
+------------+-----------------+--------------+
|    Method  |     Variant     | Is Dangerous |
+------------+-----------------+--------------+
| homoglyphs |  𝐧etwork-sec.de |      No      |
|            |  n℮twork-sec.de |      No      |
|            |  ne𝐭work-sec.de |      No      |
|            |  netɯork-sec.de |      No      |
|            |  netwᴏrk-sec.de |      No      |
|            |  netwoꭇk-sec.de |      No      |
|            |  networ𝐤-sec.de |      No      |
|            |  network˗sec.de |      No      |
|            |  network-ƽec.de |      No      |
|            |  network-s℮c.de |      No      |
|            |  network-seᴄ.de |      No      |
|            |  network-sec․de |      No      |
|            |  network-sec.ⅆe |      No      |
|            |  network-sec.d℮ |      No      |
| codebox    |  ոetwork-sec.de |     Yes      |
|            |  ռetwork-sec.de |     Yes      |
|            |  nеtwork-sec.de |     Yes      |
|            |  nҽtwork-sec.de |     Yes      |
|            | neｔwork-sec.de |      No      |
|            |  ne𝐭work-sec.de |      No      |
|            |  netɯork-sec.de |      No      |
|            |  netѡork-sec.de |     Yes      |
|            |  netwoгk-sec.de |     Yes      |
|            |  netwoᴦk-sec.de |     Yes      |
|            | networｋ-sec.de |      No      |
|            |  networ𝐤-sec.de |      No      |
|            |  network˗sec.de |      No      |
+------------+-----------------+--------------+
```

## Python Cmd library - XXE / LFI pseudoshell
https://docs.python.org/3/library/cmd.html   

[xxe-lfi-cmd_shell.py](xxe-lfi-cmd_shell.py)  
So much more fun than editing requests in Burp or cUrl.  

## Python Proxy for LFI / Path Traversal 
People these days... proxy everything over Burp anyway - this is an alternative and especially useful when you want keep the `Path Traversal` of the URL intact, maybe on top want to modify the requests, while you run `feroxbuster` over a `SOCKS` on the way out, but cannot afford BurpPro. 

You could of course still proxy over Burp, on your way in or out of this little custom tool. 

[lfi_proxy.py](lfi_proxy.py)

## input_spider.py
```
usage: input_spider.py [-h] [--show-method] [--show-status] [--json] [--stick-to-input] [-v] start_url

Spider a website and list all URLs with forms.

positional arguments:
  start_url         The URL to start spidering from.

options:
  -h, --help        show this help message and exit
  --show-method     Show the HTTP method (GET/POST) before URLs.
  --show-status     Show the HTTP status code for each URL.
  --json            Output results in JSON format.
  --stick-to-input  Skip testing availability for HTTP/HTTPS protocols and IP/Hostname resolution.
  -v, --verbose     Enable verbose output.
```

### What it does
- Spider a `Domain` (or IP, URL)
- Find inputs
- Output URL with input params for further test-automation
- Test http / https availability
- Make IP <-> Hostname resolution and test both 

### Output only the URLs with params
Note that random values are added, as most forms wont submit without values. The output always contains a clean version as well. Some params have default values, this will come in a future version. From experience I know, in `Pentesting` inputs, the `default values` can become very important, without you often cannot submit succesfully. 

```bash
$ input_spider.py webhistory.info
https://webhistory.info?searchDomain=ZDlZzz4W&domain-regex=pomq0iLK&setcookie=Du6Sq3tG&server=mbUsZW82&individualResults=mQzzTky5&special-headers=VdapK4Gx&searchURL=K09u1A3w&searchServer=kSrDw7vc&ignore-server-case=xcvEef1q&startDate=GFGi8hcd
https://webhistory.info?searchDomain=&domain-regex=&setcookie=&server=&individualResults=&special-headers=&searchURL=&searchServer=&ignore-server-case=&startDate=
```

### JSON output
```bash
$ input_spider.py --json  webhistory.info
{
    "webhistory.info": [
        {
            "method": "GET",
            "status_code": 200,
            "domain": "webhistory.info",
            "protocol": "https",
            "url_with_values": "https://webhistory.info?searchDomain=RB5aqUvY&domain-regex=DB5Z87tE&setcookie=Cpx4A0yA&server=t8NpXz83&individualResults=tDhA5mHN&special-headers=gD6jGq0J&searchURL=8tL35VAi&searchServer=99nbOUNn&ignore-server-case=DC0pfrVW&startDate=BRradGTH",
            "url_without_values": "https://webhistory.info?searchDomain=&domain-regex=&setcookie=&server=&individualResults=&special-headers=&searchURL=&searchServer=&ignore-server-case=&startDate=",
            "params": [
                "searchDomain",
                "domain-regex",
                "setcookie",
                "server",
                "individualResults",
                "special-headers",
                "searchURL",
                "searchServer",
                "ignore-server-case",
                "startDate"
            ]
        }
    ]
}
```

### Show Method and Status Code
of the resulting URL
```bash
$ input_spider.py --show-method --show-status  webhistory.info
[GET] 200 https://webhistory.info?searchDomain=UpOLiMwS&domain-regex=cRdkv5IH&setcookie=U4hL68A7&server=OtiKkP9X&individualResults=Fnwsskqz&special-headers=LdqOVU6n&searchURL=ndKg0wFC&searchServer=SPzIDSfY&ignore-server-case=IzjVcwiL&startDate=KgTCAVxe
[GET] 200 https://webhistory.info?searchDomain=&domain-regex=&setcookie=&server=&individualResults=&special-headers=&searchURL=&searchServer=&ignore-server-case=&startDate=
```


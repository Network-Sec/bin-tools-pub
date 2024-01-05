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

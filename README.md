# Our "bin folder" tools
Tools we created as FOSS.

You'll find a lot more infos in our Blog:   
https://blog.network-sec.de/  

For OSINT and Recon, IP enumeration etc., have a look at this article:   
https://blog.network-sec.de/post/open_source_intelligence_2024_eu_version/

## A Word On Quality
We'd like to note, not all the tools listed below are our most interesting projects, and - sorry for that - the descriptions below might be outdated. Take the notes here as a pointer into a direction, most tools have either a help function (-h), or a short info as comment inside the script header. 

The reason, why this happened is the following: After several years in Offensive Security we completely changed our online presence and the way, how we output information from our Security Research and projects. Formerly we had a kind of "Notebook", made primarely for ourselfs and not for other people. When you look into your own notes, you may quickly realize, other people might not understand, what you did there. Since 2024 we tried to make a more comprehensive Blog, and to make our scripts more stable and generic. 

TL;DR: The Infos below are mostly copy & pasted from our former Notebook and thus ain't that pretty.  

However: This content is still made for professionals, who can do most of these things by themselfs, who can read code and update scripts for their purposes. We never wanted to address or entertain a larger audience. If you dive into the world of Ethical Hacking, you'll know that even CVE PoCs often have Script Kiddie Protection built in - meaning they don't just work like consumer software, but need adaptation from a cybersecurity professional, and this is intended by the author(s). As much as we would enjoy an even "higher quality", it would also bring the risk of mis-use by people, who don't know or care, what they're doing.

That "risk factor" is not the main reason, why things are like that. But it is the main reason, why we're ok with it. 

## Traceroute-Whois
Custom Traceroute - Whois combo which is often surprisingly useful (DFIR, Network Pentesting, Debugging...)

```powershell
$ tracert_whois.ps1 172.217.18.14 -whois -timeout 2
Tracing route to 172.217.18.14  over a maximum of 30 hops:

Hop RoundtripTime  Address          Hostname
1   5,66           192.168.178.1    fritz.box

Whois Information
------------------
                                              Contact                        Name                           Organisation
Contact                                       administrative
Name                                          General Manager
Organisation                                  Intercap Registry Inc.
Address                                       Cayman Islands (the)
Phone                                         +1 833 436 8462
Email                                         admin@intercap.inc

                                              Contact                        Name                           Organisation
Contact                                       technical
Name                                          CTO
Organisation                                  CentralNic
Address                                       United Kingdom of Great Britain and Northern Ireland (the)
Phone                                         +44 20 33 88 0600
Email                                         tld.ops@centralnic.com
Nameserver                                    D.NIC.BOX
Nameserver IPV4                               212.18.249.139
Nameserver IPV6                               2a04:2b00:13ff:0:0:0:0:139

2   6,7            92.11.9.1                  f..<censored>....versatel.de

Whois Information
------------------
                                              Contact                        Name                           Organisation
Address                                       Germany
Phone                                         +49 69 27235 0
Email                                         ianacontact@denic.de

                                              Contact                        Name                           Organisation
Contact                                       technical
Name                                          Business Services
Organisation                                  DENIC eG
Address                                       Germany
Phone                                         +49 69 27235 272
Email                                         dbs@denic.de
Nameserver                                    Z.NIC.DE
Nameserver IPV4                               194.246.96.1
Nameserver IPV6                               2a02:568:fe02:0:0:0:0:de

3   9,44           12.14.4.1    kar1..<censored - wtf, karl?>...versatel.de
<karls info censored>
4   10,35          2.4.24.19    N/A
5   12,23          2.4.4.14    N/A
6   10,75          8.70.25.51  N/A
7   10,12          2.53.6.37   N/A
8   10,92          2.17.1.4    f<censored>.net
``` 
Naturally we only receive the whois info of the next `Authority`, yet it provides you with a fast overview, names, not numbers, where you're at - we could add real `ASN` resolution and more gimmicks, for us it strikes the balances between speed, single-script call and informative output, just a quick overview where you're at. 

## Recursively search GitHub
When you have an API key you can adjust the throttles to make it faster. The DB stuff doesn't fully work yet (checkpoints, etc.) but it's good enough for us right now... know that it's rather improvised on the spot, there's likely better tools for this exact purpose. 

```bash
$ git_get_user_forks_filtered.py "<username1>,<username2>,<username3>" --filter cve,backdoor,rat,exploit,rce,kernel,vuln,evil,firmware,pwn,privesc,privileg,escalation,lfi,remote,phish,jailbreak,poc,exp,evasion,evade,amsi,bypass,pentest,sharp,potato,unhook,bof,bad,shellcode

 Adding neverlasty to the queue from forked repo CVE-2021-3156
 Queue: ['Zhilakai123', 'Xylaraetha', 'Glintzenberg', 'Namarothias', 'Lunawhisper', 'Vesperlysia', 'Aurorionixx', 'Khaosstar23', 'Mythrilweaver', 'Etherealmouse42', 'neverlasty']
 Adding kurl3r to the queue from forked repo exploit_me
```

The script intentionally doesn't save repos to disk, it's for finding / enumerating users on a subject matter.

## Clone everything from user
API limit may hit, prepare your dump-space

```bash
$ git_clone_complete_user.sh android-rooting-tools
```

One of the nicer ones, deals with existing dirs and some errors. 

## Reverse IP OSINT
Very handy tool

```bash
$ reverse_IP_OSINT.sh 217.160.0.256
----------------- Processing IP: 217.160.0.256 -----------------
[+] dig result for 217.160.0.256
217-160-0-256.elastic-ssl.ui-r.com.

[+] Domain information from site.ip138.com for 217.160.0.256
[...cut...]

[+] Domain information from ipchaxun.com for 217.160.0.256
[...cut...]

[+] SAN and CN from the certificate for 217.160.0.256
[...cut...]

[+] Domain information from rapiddns.io for 217.160.0.256
```

## IP_Range_Infos.py
Using freely available MMDB data to enumerate CIDR ranges for ASN, Companies, Institutions, Locations, etc.  
You must download the data (see script header) and provide the folder of the data to the script for it to do anything. 

```
$ IP_Range_Infos.py -h
usage: IP_Range_Infos.py [-h] [--language LANGUAGE] [-s] [-l] [-c] [-a] [-r] ip

Query IP address or range against local MMDB databases and CSV data.

positional arguments:
  ip                   IP address or CIDR range to query

options:
  -h, --help           show this help message and exit
  --language LANGUAGE  Preferred language for names, default is English
  -s, --summarize      Summarize consecutive IPs with identical data
  -l, --location       Output only city table info (including lat and long location). When specifying one or more tables, only those will be searched. When ommiting any table, all will be searched.
  -c, --country        Output only country table info.
  -a, --asn            Output only asn table info. ASN is best when looking for companies or institutions
  -r, --ranges         Output only ranges (CSV) table info. Ranges will provide fastest results but only broad infos, like country
```

#### Example Output
This query only took a few seconds. Note that you need a wider screen or higher screen resolution, to correctly display the table. You can also zoom out using "Ctrl -".

![IP_range_infos2](https://github.com/Network-Sec/bin-tools-pub/assets/85315993/d609bd8d-2710-4fa3-8719-f6841552cf6d)

## htmlq.py
To see examples how we used `htmlq` and `jsonq` - see the script: `cve_scrape.sh`.
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
- We made this lib for usage as cli tool (quickly do some encoding stuff) as well as larger projects (e.g. XSS fuzzer)
- Both lib and fuzzer below are made async for best performance

### Usage Example
<video width="1920" height="1080" loop="" controls=""><source src="videos/projects/fuzzlib.py_demo_on_WebsecurityAcademy.mp4" type="video/mp4">Your browser does not support the video tag.</video>

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

We see Email addresses as the most dangerous vector, cause an attacker might be able to produce an exact representation of the address of a colleague, friend, business partner, high reputation address like microsoft.com etc.

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

## Stager Helpers

### convert_ps1_hex.py
Takes bare or b64 powershell stager input - replaces flagged evasion with a real one, uses hex as bypass. `agent connected`


# people_grep.sh
Parallel processing of txt files, looking for possible name combinations. 

### Updates
- Added name reverse (for all ranges)
- Added optional datafolder arg

## Install
```bash
$ sudo apt install parallel egrep
# Edit script to point at your data folder
$ chmod +x people_grep.sh
```

## Usage 

### Broad Search
```bash
$ people_grep.sh olivere smithers
Searching with pattern: o[,:._+\-]*smithers
Searching with pattern: osmithers
Searching with pattern: oli[,:._+\-]*smithers
Searching with pattern: olismithers
Searching with pattern: oli[,:._+\-]*smither
Searching with pattern: olismither
Searching with pattern: oli[,:._+\-]*smithe
Searching with pattern: olismithe
Searching with pattern: oli[,:._+\-]*smith
Searching with pattern: olismith
Searching with pattern: oliv[,:._+\-]*smit
Searching with pattern: olivsmit
Searching with pattern: olive[,:._+\-]*smit
Searching with pattern: olivesmit
Searching with pattern: olive[,:._+\-]*smi
Searching with pattern: olivesmi
Searching with pattern: oliver[,:._+\-]*smi
Searching with pattern: oliversmi
Searching with pattern: olivere[,:._+\-]*smi
Searching with pattern: oliveresmi
Searching with pattern: olivere[,:._+\-]*smithers
Searching with pattern: oliveresmithers
```

### Narrow Search
```bash
$ people_grep.sh -n olivere smithers
Searching with pattern: o[,:._+\-]*smithers
Searching with pattern: osmithers
Searching with pattern: olivere[,:._+\-]*smithers
Searching with pattern: oliveresmithers
```

### Smallest Range
```bash
$ people_grep.sh -s olivere smithers
```

### Custom Folder
```bash
$ people_grep.sh olivere smithers /mnt/d/mydata/
```

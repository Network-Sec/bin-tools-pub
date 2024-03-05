#!/bin/bash

# Script made during my CTF / OSCP phase - does a bunch of auto-recon mainly intended for HackTheBox, but easily adoptable for Pentesting

# Notes: if you want to use this script you probably need to make
# some modifications, here's how..
# 1.) Check on a shell what language the "jobs" returns, cause it uses
# the OS language and then the condition fails. In english it's usually "Running"
# 2.) The script changes into one of two directories depending on the --retired
# parameter is given or not, around line 68
IFS=$'\n'

# Reset
Color_Off='\033[0m'       # Text Reset

# Regular Colors
Black='\033[0;30m'        # Black
Red='\033[0;31m'          # Red
Green='\033[0;32m'        # Green
Yellow='\033[0;33m'       # Yellow
Blue='\033[0;38m'         # Blue
Purple='\033[0;35m'       # Purple
Cyan='\033[0;36m'         # Cyan
White='\033[0;37m'        # White

# Meassure and output duration
SECONDS=0

if [ "$#" -lt 1 ]; 
then
        echo "Missing argument! Try: myrecon optimum --retired"
        exit 1
fi

boxUrl="$1"
boxName=$(echo $1 | grep -o -e "^[a-z0-9]*")
boxIP=$(cat /etc/hosts | grep -i $boxUrl | awk '{print $1}')
boxProtocol="http://"
boxHasWordPress=0

function echoHints() {
        if [[ "$1" != "--nohints" ]];
        then
                echo "[*] Starting deeper nmap on previously discovered ports" 
                echo -e "${Cyan}[*] While you wait, here's some things to make sure you don't forget:"
                echo "[*] 1. READ the code of websites, javascript includes, comments, etc."
                echo "[*] 2. Search for each service on searchsploit AND google like this:"
                echo "[*]     wordpress pluginname CVE or vsftp version CVE. Search for both CVE and exploit."
                echo "[*]     If you find something, next search for the same + git or blog or PoC."
                echo "[*] 3. Try to use all services as actually inteded, try Anonymous and default creds everywhere."
                echo "[*] 4. Always re-check, box may be down in the meantime, VPN may be gone faulty."
                echo "[*] 5. You need to have your apache up and running."
                echo "[*] 6. Still haven't found anything? Time to check your cheat-sheet."
                echo "[*] 7. Don't trust wpscan. Never trust one single tool."
                echo "[*] 8. Proxy stuff and tunneling can be complicated, take your time."
                echo "[*] 9. Try to make that exploit actually work or try to understand what it does."
                echo "[*] 10. Use apropriate protocols. Svn may use svn://, rsync uses rsync://, php has some fun filter://" 
                echo "[*]     and file:// things and if you're really bored, gopher:// is always there for you!"
                echo "[*] 11. There are wordlists for specific VULNS and services. E.g. /usr/share/dirb/wordlists/vulns/coldfusion.txt " 
                echo "[*] 12. Early on you should lay out all possible paths in front of you, each possible exploit code," 
                echo "[*]     each vulndb description, each service, so you can make an informed descision. " 
                echo "[*] 13. If you have authenticated exploits, go enumerate users."
                echo "[*] 14. Can't find anything? Instead of being idle it's worth bustin out subdirs! ${Color_Off}"
        fi
}

function nmapAllPorts() {
        if [[ -f "all_ports" ]];
        then
                echo "[*] Found previous nmap all_ports, skipping"
        else
                echo "[*] Starting nmap scan on all ports"
                sudo nmap -sV -sC -p $foundPorts $boxIP -o all_ports --max-retries 3 &>/dev/null 
                echo "[*] Finished nmap scan on all ports"
        fi
        if [[ $(grep -o "methods: .*" all_ports | grep -i "put") ]] || [[ $(grep -o "options: .*" all_ports | grep -i "put") ]];
        then
                echo -e "${Red}[*] PUT found in http methods! Try uploading a file with curl.${Color_Off}"
        fi

        if [[ $(grep -o "methods: .*" all_ports | grep -i "move") ]] || [[ $(grep -o "options: .*" all_ports | grep -i "move") ]];
        then
                echo -e "${Red}[*] MOVE found in http methods! Try moving / renaming a file with curl.${Color_Off}"
        fi

        if [[ $(grep -i "wordpress" all_ports) ]];
        then
                echo -e "${Red}[*] Found WordPress consider running wpcan. ${Color_Off}"
                echo -e "${Cyan}wpscan --url "$boxProtocol$boxUrl:$httpPort" --plugins-detection aggressive -e ap,at,u1-25 --api-token iH7aST8W0jjsyhyKedv5ASk3TsLGdMUX6Oq98K8Tu2w --disable-tls-checks --enumerate u -o wpscan-"$httpPort".txt ${Color_Off}"
                boxHasWordPress=1
        fi
}

function nmapVulnScan() {
        if [[ -f script_vuln ]];
        then
                echo "[*] Found previous nmap vuln scripts scan, skipping"
        else
                echo -e "${Color_Off}[*] Starting nmap vuln scripts scan"
                sudo nmap --script='vuln' -p $foundPorts -o script_vuln "$boxUrl" --max-retries 3 &>/dev/null &
        fi
}


subDir=""
if [[ "$2" != "--nodir" ]];
then
        if [[ "$2" == "--retired" ]];
        then
                subDir="Retired/"
        fi

        if [[ "$2" == "--oscp" ]];
        then
                subDir=""
                if [[ $(echo $boxUrl | egrep -o "^[0-9]") ]];
                then
                        boxIP=$boxUrl
                fi
                cd /home/crunchy/OSCP/$boxIP
        else
                # Changing into working directory
                cd "/home/crunchy/HTB/$subDir/$boxName"
        fi
else 
        boxIP=$boxUrl
fi
# Todo: Add option -p for multiple / different ports, some boxes run http
# on other ports than 80

echo -e "${Blue}[*] Running tests on $boxUrl at IP $boxIP ${Color_Off}"
boxOS=$(ping -c 4 $boxIP | egrep -o "ttl=[0-9]*" | grep -o "[0-9]*" | head -n 1)
if [[ $boxOS -ge 63 ]] &&  [[ $boxOS -lt 125 ]];
then
        boxOS="Linux"
elif [[ $boxOS -ge 127 ]];
then
        boxOS="Windows"
else
        echo "Host seems down, exiting..."
        exit 1
fi
echo "[*] Box appears to be up and running OS $boxOS"

boxServer=$(whatweb "$boxIP")
if [[ $boxServer ]];
then
        echo "[*] whatweb returned $boxServer"
        echo $boxServer > whatweb.txt
fi

fileExt=""
# dirbusting extensions depending on OS
if [[ $boxOS == "Linux" ]];
then
        fileExt=".html,.htm,.php,.jpg,.png,.gif,.txt,.me,.md,.zip,.pdf,.js"
else
        fileExt=".html,.php,.jpg,.png,.gif,.asp,.aspx,.txt,.me,.md,.zip,.pdf,.js"
fi

# The entire script relies heavily on nmap, but masscan is 
# a good second option and failsafe
# echo "[*] Starting masscan on all ports in background"
# masscan 10.10.10.203 -p 0-65535 | tee > "masscan-$boxIP.txt" &>/dev/null &

if [[ -f "quick_ports" ]];
then
        echo "[*] Found previous nmap quick scan, skipping"
else
        echo -n "[*] Starting nmap quick scan on all ports..."
        sudo nmap -p- -o quick_ports "$boxUrl" --max-retries 3 &>/dev/null &
        while [[ $(jobs | grep "Läuft") ]] ; 
        do
                echo -n "."
                sleep 20
        done
        echo -e "\n[*] nmap quick scan finished" 
fi
foundPorts=$(cat quick_ports | grep -o -e "^[0-9]*" | awk '{ printf "%s,",$0 }' | sed s/,$//)
echo -e "${Red}[*] Found ports: $foundPorts ${Color_Off}"

if [[ -f "nmap_udp" ]];
then
        echo "[*] Found previous nmap UDP scan, skipping"
else
        echo -n "[*] Starting nmap UDP scan on top 1000 ports..."
        sudo nmap --version-intensity 0 -F -sU $boxIP -o nmap_udp --max-retries 3 &>/dev/null 
        while [[ $(jobs | grep "Läuft") ]] ; 
        do
                echo -n "."
                sleep 20
        done
        echo -e "\n[*] nmap UDP scan finished" 
fi
foundUDPPorts=$(cat nmap_udp | grep -o -e "^[0-9]*" | awk '{ printf "%s,",$0 }' | sed s/,$//)
echo -e "${Red}[*] Found UDP ports: $foundUDPPorts ${Color_Off}"

if [[ $(echo $foundUDPPorts | grep -E ',161,|,161$|^161,') ]];
then
        echo "{Red}[*] Found SNMP Server, run nmap brute script manually! ${Color_Off}"
        echo -e "{Red}[*] sudo nmap -sU --script snmp-brute -p 161 $boxIP -o nmap_SNMP --max-retries 2 &>/dev/null ${Color_Off}"
fi

if [[ $(echo $foundPorts | grep -E ',53,|,53$|^53,') ]];
then
        # Attempting DNS lookups zone transfer
        echo "[*] Found DNS Server, attempting DNS recon"
        dig "$boxUrl" "@$boxIP" > dns-recon.txt
        dig axfr "$boxUrl" "@$boxIP" >> dns-recon.txt
        host -l "$boxUrl" "$boxIP" >> dns-recon.txt
fi

if [[ $(echo $foundPorts | grep -E ',445,|,445$|^445,') ]];
then
        # Attempting basic Samba recon
        echo "[*] Found Samba Server, attempting recon"
        echo "[*] You should check if Kerberos PreAuth is disabled, you may get a hash:"
        echo "[*] GetNPUsers.py box-domain/ -dc-ip $boxIP -request +-+-+ don't forget the slash!"
        echo "[*] Hashcat mode is usually 18200"
        smbclient -L //$boxIP/ -U "Anonymous" -N > smbclient.txt 
        smbclient -L //$boxIP/ -N >> smbclient.txt 
        smbclient -L //$boxIP/ -U "Guest" -N >> smbclient.txt 
        cme smb $boxIP > crackmapexec.txt

        if [[ $boxOS == "Windows" ]];
        then
                enum4linux-ng $boxIP > enum4linux-ng.txt
                if [[ $(cat enum4linux-ng.txt | grep -i "username" | awk '{print $2}' | sort -u | grep -vi "username") ]];
                then
                        cat enum4linux-ng.txt | grep -i "username" | awk '{print $2}' | sort -u | grep -vi "username" > valid-usernames.txt
                        for name in $(cat valid-usernames.txt); 
                        do
                                echo "[*] Attempting user: $name without password and with username as password" >> smbclient-valid-usernames.txt 
                                smbclient -L //$boxIP/ -U $name -N >> smbclient-valid-usernames.txt 
                                smbclient -L //$boxIP/ -U $name%$name -N >> smbclient-valid-usernames.txt 
                        done

                fi
                if [[ $(cat enum4linux-ng.txt | grep -i "groupname" | awk '{print $2}' | sort -u | grep -vi "groupname") ]];
                then
                        cat enum4linux-ng.txt | grep -i "groupname" | awk '{print $2}' | sort -u | grep -vi "groupname" > valid-groupnames.txt
                fi
        fi
fi

httpPort=0
declare -a http_Ports
if [[ $(echo $foundPorts | grep -E ',80,|,80$|^80,') ]];
then
        httpPort=80
        http_Ports+=(80)
fi

echo "[*] Here's some commands for you to run manually: "
echo "[*] sudo nmap --version-intensity 0 -F -sU $boxIP -o nmap_udp_man -v --max-retries 2 -+-+- you can try --top-ports N to scan only N most popular ports."
echo "[*] gobuster dir -w /usr/share/seclists/Discovery/Web-Content/quickhits.txt -u $boxProtocol$boxUrl -b 500,404 -s 200,301,302,303,400,401,402,403 --wildcard -o gobuster-quickhits-man-$httpPort.txt -k -t 30 -e -l -x $fileExt"
echo "[*] dirsearch -w //usr/share/seclists/Discovery/Web-Content/raft-large-words.txt -r -R 2 -e * -u $boxProtocol$boxUrl --plain-text-report=dirsearch-raft-large-w-extensions-man.txt"
echo "[*] feroxbuster -w /usr/share/seclists/Discovery/Web-Content/raft-medium-words.txt -u $boxProtocol$boxUrl --statuscodes 200,301,302,303,400,401,402,403 -o feroxbuster-raft-medium-w-extensions-$httpPort-$boxUrl-man.txt -t 300 -k -x $(echo $fileExt | sed 's/\.//g') -d 3 "

echo "[*] nikto -host $boxIP -port $httpPort -vhost $boxUrl -output nikto-man.txt"
if [[ $httpPort -eq 0 ]];
then
        echo "[*] Nothing on port 80, probing other ports for http"
        for port in $(cat quick_ports | grep -o -e "^[0-9]*");
        do
                success=FALSE
                boxProtocol="http://"

                if [[ $httpPort -eq 443 ]];
                then
                        boxProtocol="https://"
                fi

                timeout 30s curl -sS "$boxProtocol$boxIP:$port" &> /dev/null && success=TRUE
                if [[ $success == TRUE ]]; 
                then
                        wget -r "$boxProtocol$boxIP:$port" --timeout=120 --tries=3 &>/dev/null 
                        echo "[*] Success on port $port using IP $boxIP" 
                        if [[ ! " ${http_Ports[@]} " =~ $port ]];
                        then
                                http_Ports+=($port)
                        fi
                else
                        echo "[*] Nothing on port $port using IP $boxIP" 
                fi

                if [[ $boxIP != $boxUrl ]];
                then
                        success=FALSE
                        timeout 30s curl -sS "$boxProtocol$boxUrl:$port" &> /dev/null && success=TRUE
                        if [[ $success == TRUE ]];
                        then
                                wget -r "$boxProtocol$boxUrl:$port" --timeout=120 --tries=3 &>/dev/null
                                echo "[*] Success on port $port using $boxProtocol$boxUrl" 
                                if [[ ! " ${http_Ports[@]} " =~ $port ]];
                                then
                                        http_Ports+=($port)
                                fi
                        else
                                echo "[*] Nothing on port $port using $boxProtocol$boxUrl" 
                        fi
                fi
        done
fi

duration=$SECONDS
echo -e "${Cyan}[*] $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed.${Color_Off}"
firstRun=1

numberOfHTTP_ports=${#http_Ports[@]}

if [[ numberOfHTTP_ports -eq 0 ]];
then
        # No http ports, so not much recon we can do...
        # maybe add SMB / Windows Recon in the future
        nmapAllPorts
        nmapVulnScan
else 
        for pi in "${http_Ports[@]}";
        do 
                httpPort=$pi
                boxProtocol="http://"

                if [[ $httpPort -eq 443 ]];
                then
                        boxProtocol="https://"
                        echo "[*] Trying to download https certificate of $boxUrl - make sure to check subdomains yourself!"
                        timeout 5 openssl s_client -connect "$boxUrl:$httpPort" &> "$boxUrl-$httpPort"-https-cert.txt
                fi

                echo "[*] Working on Port $httpPort"
                if [[ $httpPort -gt 0 ]];
                then
                        foundCGI=FALSE
                        cgi_bin_dir="$boxProtocol$boxIP:$httpPort/cgi-bin/"
                        if [[ $(curl -s -o /dev/null -w "%{http_code}" $cgi_bin_dir) != "404" ]];
                        then
                                timeout 30s curl -sS $cgi_bin_dir &> /dev/null && foundCGI=TRUE
                        fi

                        cgi_bin_dir="$boxProtocol$boxUrl:$httpPort/cgi-bin/"
                        if [[ $foundCGI == FALSE && $(curl -s -o /dev/null -w "%{http_code}" $cgi_bin_dir) != "404" ]];
                        then
                                timeout 30s curl -sS $cgi_bin_dir &> /dev/null && foundCGI=TRUE
                        fi

                        if [[ $foundCGI == TRUE ]]; 
                        then
                                foundCGI=FALSE
                                echo -e "${Yellow}[*] Possibly found cgi-bin directory: $cgi_bin_dir - check for shellshock${Color_Off}"
                                echo -e "${Yellow}[*] Busting out $cgi_bin_dir using common.txt, but you should also${Color_Off}"
                                echo -e "${Yellow}[*] check yourself. Common file extensions are: cgi,bin,sh,php,pl ${Color_Off}"
                                gobuster dir -w /usr/share/seclists/Discovery/Web-Content/common.txt -u $cgi_bin_dir -b 500,404,303,400,401,402,403 -s 200,301,302 --wildcard -o cgi-bin.txt -k -t 30 -e -l -x cgi,bin,sh,php,pl &>/dev/null 
                        fi

                        if [[ -f  "gobuster-quickhits-"$httpPort-$boxUrl".txt" ]];
                        then
                                echo "[*] Found previous gobuster quickhits scan, skipping."
                        else
                                echo "[*] Starting gobuster quickhits.txt"
                                gobuster dir -w /usr/share/seclists/Discovery/Web-Content/quickhits.txt -u "$boxProtocol$boxUrl:$httpPort" -b 500,404 -s 200,301,302,303,400,401,402,403 --wildcard -o gobuster-quickhits-"$httpPort-$boxUrl".txt -k -t 30 -e -l &>/dev/null &
                        fi

                        # Check if port 80 was set but download hasn't happened yet
                        if [[ ! -d $boxUrl ]];
                        then
                                echo "[*] Downloading main website on port $httpPort"
                                wget -r "$boxProtocol$boxUrl:$httpPort" --timeout=120 --tries=3 &>/dev/null &
                        fi

                        echo -n "[*] first batch running..." 
                        while [[ $(jobs | grep "Läuft") ]] ; 
                        do
                                echo -n "."
                                sleep 20
                        done
                        echo  -e "\n[*] first batch finished!" 
                        # killall gobuster &>/dev/null

                        duration=$SECONDS
                        echo -e "${Cyan}[*] $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed.${Color_Off}"
                fi

                if [[ firstRun ]];
                then
                        # try to pass the command line arg without further check, lets see if it works
                        echoHints $3

                        # Running this one in foreground
                        nmapAllPorts
                        nmapVulnScan
                fi

                if [[ $httpPort -gt 0 ]];
                then
                        if [[ -f "dirsearch-raft-med-w-extensions-"$httpPort-$boxUrl".txt" ]];
                        then
                                echo "[*] Found previous dirsearch raft-medium-words.txt scan, skipping"
                        else
                                echo "[*] Starting dirsearch raft-medium-words.txt and WFUZZ vhosts using bitquark-subdomains-top100000.txt"

                                # trying to speed up things using feroxbuster instead didn't work out because
                                # the tool errors pretty often
                                # Increase file descriptor limit for feroxbuster
                                ulimit -n 1000000 &>/dev/null
                                # feroxbuster -w /usr/share/seclists/Discovery/Web-Content/raft-medium-words.txt -u "$boxProtocol$boxUrl:$httpPort" --statuscodes 200,301,302,303,400,401,402,403 -o feroxbuster-raft-medium-w-extensions-"$httpPort-$boxUrl".txt -t 300 -k -x $(echo $fileExt | sed 's/\.//g') -d 3 &>/dev/null &

                                dirsearch -w //usr/share/seclists/Discovery/Web-Content/raft-medium-words.txt -r -R 2 -e $(echo $fileExt | sed 's/\.//g') -u "$boxProtocol$boxUrl:$httpPort" --plain-text-report=dirsearch-raft-med-w-extensions-"$httpPort-$boxUrl".txt &>/dev/null &
                        fi

                        if [[ firstRun && $4 != "--nosubdomain" ]];
                        then
                                if [[ -f "wfuzz-vhosts-bitquark.txt" ]];
                                then
                                        echo "[*] Found previous subdomain scan, skipping"
                                else
                                        if [[ $boxIP != $boxUrl ]];
                                        then
                                                # Get initial wordcount to compare subdomain is different
                                                boxLen=$(curl "$boxProtocol$boxUrl:$httpPort" -s | wc | awk '{print $2}')
                                                wfuzz -f wfuzz-vhosts-bitquark.txt -w /usr/share/seclists/Discovery/DNS/bitquark-subdomains-top100000.txt -H "Host: FUZZ.$boxUrl" --hw "$boxLen" -t 20 "$boxIP" &>/dev/null &
                                        else
                                                echo "[*] Box url is just an IP - skipping wfuzz subdomain scan"
                                        fi
                                fi
                        fi

                        if [[ $(jobs | grep "Läuft") ]];
                        then
                                echo -n "[*] second batch running..." 
                                while [[ $(jobs | grep "Läuft") ]] ; 
                                do
                                        echo -n "."
                                        sleep 20
                                done
                                echo "[*] second batch finished!" 
                        else
                                echo "[*] second batch finished!" 
                        fi

                        duration=$SECONDS
                        echo -e "${Cyan}[*] $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed.${Color_Off}"

                        if [[ -f gobuster-dir-2.3-med-"$httpPort-$boxUrl".txt ]];
                        then
                                echo "[*] Found previous gobuster directory-list-2.3-medium.txt scan, skipping"
                        else
                                echo "[*] Starting longer gobuster directory-list-2.3-medium.txt"
                                gobuster dir -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -u "$boxProtocol$boxUrl:$httpPort" -b 500,404 -s 200,301,302,303,400,401,402,403 --wildcard -o gobuster-dir-2.3-med-"$httpPort-$boxUrl".txt -k -l -t 30 -e  &>/dev/null &
                        fi

                        if [[ firstRun ]];
                        then
                                # Nikto sometimes hangs, thus using timeout again and saving the output with tee
                                echo "[*] Starting nikto webscanner"
                                if [[ $boxIP != $boxUrl ]]
                                then
                                        timeout 1200s nikto -host "$boxProtocol$boxIP" -port "$httpPort" -vhost "$boxUrl" -output nikto.txt &>/dev/null &
                                else
                                        timeout 1200s nikto -host "$boxProtocol$boxIP" -port "$httpPort" -output nikto.txt &>/dev/null &
                                fi
                        fi

                        echo -n "[*] third batch running..." 
                        while [[ $(jobs | grep "Läuft") ]] ; 
                        do
                                echo -n "."
                                sleep 20 
                        done
                        echo -e "\n[*] third batch finished!" 
                        # killall dirsearch wfuzz &>/dev/null

                        duration=$SECONDS
                        echo -e "${Cyan}[*] $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed.${Color_Off}"

                        if [[ $(grep -i "wordpress" script_vuln) ]] && [[ ! $boxHasWordPress ]];
                        then
                                echo -e "${Red}[*] Found WordPress consider running wpcan. ${Color_Off}"
                                echo -e "${Cyan}wpscan --url "$boxProtocol$boxUrl:$httpPort" --plugins-detection aggressive -e ap,at,u1-25 --api-token iH7aST8W0jjsyhyKedv5ASk3TsLGdMUX6Oq98K8Tu2w --disable-tls-checks ${Color_Off}"
                        fi

                        if [[ -f gobuster-common-"$httpPort-$boxUrl".txt ]];
                        then
                                echo "[*] Found previous gobuster common.txt with file-extensions scan, skipping"
                        else
                                echo "[*] Starting longer gobuster common.txt with file-extensions"
                                gobuster dir -w /usr/share/wordlists/dirb/common.txt -u "$boxProtocol$boxUrl:$httpPort" -b 500,404 -s 200,301,302,303,400,401,402,403 --wildcard -o gobuster-common-"$httpPort-$boxUrl".txt -k -l -t 30 -e -x "$fileExt" &>/dev/null &

                                echo -n "[*] fourth batch running..." 
                                while [[ $(jobs | grep "Läuft") ]]; 
                                do
                                        echo -n "."   
                                        sleep 20
                                done
                                # killall gobuster &>/dev/null
                        fi
                        echo -e "\n[*] fourth batch finished!" 
                else
                        echo "[*] Finished."
                fi
                firstRun=0
        done 
fi
duration=$SECONDS
echo -e "${Cyan}[*] $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed.${Color_Off}"

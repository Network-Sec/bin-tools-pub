# Custom Traceroute - Whois combo which is often surprisingly useful
# Usage Example:
# > whois.ps1 172.217.18.14 -whois -timeout 2

# Define the command line params and defaults
param (
    [Parameter(Mandatory=$false, Position=0)]
    [string]$targetHost,

    [Parameter(Mandatory=$false)]
    [Alias('maxhops')]
    [int]$maximumHops,

    [Parameter(Mandatory=$false)]
    [Alias('dns')]
    [Switch]$dnsLookup,

    [Parameter(Mandatory=$false)]
    [Alias('whois')]
    [Switch]$whoisLookup,

    [Parameter(Mandatory=$false)]
    [Alias("t")]
    [int]$timeout = 1000
)

# Set default values if parameters not specified
if (-not $PSBoundParameters.ContainsKey('targetHost')) {
    $targetHost = '8.8.8.8'
}
if (-not $PSBoundParameters.ContainsKey('maximumHops')) {
    $maximumHops = 30
}
if (-not $PSBoundParameters.ContainsKey('dnsLookup')) {
    $dnsLookup = $false
}
if (-not $PSBoundParameters.ContainsKey('whoisLookup')) {
    $whoisLookup = $false
}
if (-not $PSBoundParameters.ContainsKey('timeout')) {
    $timeout = 1000
}

# Add a type for the Whois lookup
Add-Type -TypeDefinition @"
using System;
using System.IO;
using System.Net.Sockets;
public class Whois {
    public static string Lookup(string server, string query) {
        using (var client = new TcpClient(server, 43))
        using (var stream = client.GetStream())
        using (var sr = new StreamReader(stream))
        using (var sw = new StreamWriter(stream)) {
            sw.WriteLine(query);
            sw.Flush();
            return sr.ReadToEnd();
        }
    }
}
"@

# Retrieve Whois data from a server
function Get-WhoisData($server, $query){
    Write-Debug "Fetching Whois data from $server"
    $data = [Whois]::Lookup($server, $query)
    Write-Debug "Received data: $data"
    return $data
}
function Get-IPAddress {
    param(
        [Parameter(Mandatory=$true)]
        [string]$HostName
    )

    $IPV4Regex = "^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    $IPV6Regex = "^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$"

    if ($HostName -match $IPV4Regex -or $HostName -match $IPV6Regex) {
        return $HostName
    } else {
        try {
            $IPs = [System.Net.Dns]::GetHostAddresses($HostName)
            foreach ($IP in $IPs) {
                if ($IP.AddressFamily -eq 'InterNetwork') { # Check if the address is IPV4
                    return $IP.IPAddressToString
                }
            }
        } catch {
            Write-Error "Unable to resolve IP for domain: $HostName"
        }
    }

    return $null
}

# Create new Whois entries from the data lines
function New-WhoisEntries($whoisDataLines){
    $whoisEntries = New-Object 'System.Data.DataTable'
    $columns = @('Contact', 'Name', 'Organisation', 'Address', 'Phone', 'Email', 'Nameserver', 'Nameserver IPV4', 'Nameserver IPV6')

    foreach ($column in $columns) {
        $whoisEntries.Columns.Add($column) | Out-Null
    }

    $tempRow = $null

    foreach($line in $whoisDataLines -split "\n"){
        Write-Debug "Processing line: $line"
        if ($line -match "(?i)(^contact):\s*(.+)") {
            if ($null -ne $tempRow) { $whoisEntries.Rows.Add($tempRow) } 
            $tempRow = $whoisEntries.NewRow()
            $tempRow["Contact"] = $Matches[2]
        }
        if ($null -ne $tempRow){
            if ($line -match "(?i)(^name):\s*(.+)") { 
                $tempRow["Name"] = $Matches[2]
            }

            if ($line -match "(?i)(^organisation):\s*(.+)") {
                $tempRow["Organisation"] = $Matches[2]
            }

            if ($line -match "(?i)(^address):\s*(.+)") { 
                $tempRow["Address"] = $Matches[2]
            }

            if ($line -match "(?i)(^phone):\s*(.+)") { 
                $tempRow["Phone"] = $Matches[2]
            }

            if ($line -match "(?i)(^e-mail):\s*(.+)") { 
                $tempRow["Email"] = $Matches[2]
            } 
            
            if ($line -match "(?i)(^nserver):\s*(.+)") {
                $nserver = $Matches[2] -split " "
                $tempRow["Nameserver"] = $nserver[0]
                $tempRow["Nameserver IPV4"] = $nserver[1]
                if ($nserver.Length -ge 3) {
                    $tempRow["Nameserver IPV6"] = $nserver[2]
                }
            }
        }
    }
    
    # Add the last row if not null
    if ($null -ne $tempRow) { $whoisEntries.Rows.Add($tempRow) }
    return $whoisEntries
}

# Start debugging
$DebugPreference = "Continue"

# Stop debugging
$DebugPreference = "SilentlyContinue"

# Get all current TLDs
$response = Invoke-WebRequest -Uri 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt'
$tlds = $response.Content -split "`n"

# Get IP of target
$targetIP = Get-IPAddress -HostName $targetHost
$outputIP = $false

if ($targetHost -ne $targetIP) {
    $outputIP = $true
}

Write-Host "Tracing route to $targetHost" $(if ($outputIP) { "(" + $targetIP + ")" }) "over a maximum of $maximumHops hops:`n"
Write-Host ("{0,-3} {1,-14} {2,-16} {3,-50}" -f "Hop", "RoundtripTime", "Address", "Hostname")

# Define a byte buffer (32 bytes of data)
$byteBuffer = [byte[]](1..32)

for ($i = 1; $i -le $maximumHops; $i++) {
    # Create a Ping object
    $ping = New-Object System.Net.NetworkInformation.Ping

    # Create PingOptions object, set TTL
    $pingOptions = New-Object System.Net.NetworkInformation.PingOptions($i, $true)

    # Create a Stopwatch object and start it
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    # Send the ping with a timeout of 1000 milliseconds
    $pingReply = $ping.Send($targetHost, $timeout, $byteBuffer, $pingOptions)

    # Stop the Stopwatch object
    $stopwatch.Stop()

    # Calculate the roundtrip time in milliseconds
    $roundtripTime = $stopwatch.Elapsed.TotalMilliseconds

    # Perform DNS reverse lookup
    $hostName     = "N/A"
    $authorityDns = "N/A"
    $parentDomain = "N/A"
    $authorityIp  = "N/A"
    if ($dnsLookup -or $whoisLookup) {
        try {
            $hostEntry = [System.Net.Dns]::GetHostEntry($pingReply.Address)
            $hostName = $hostEntry.HostName
            if ($hostName -eq "") {
                $hostName = "N/A"
            }
            $parentDomain = $hostName.Split('.')[($hostName.Split('.').Count - 2)..($hostName.Split('.').Count - 1)] -join '.'
        }
        catch {
            try {
                # If Reverse IP lookup fails, try Authority DNS lookup
                $dnsQuery = Resolve-DnsName -Name "$($pingReply.Address)" -DnsOnly -Type SOA -ErrorAction SilentlyContinue
                $authorityDns = $dnsQuery.NameHost
                $authorityIp = $dnsQuery.IPAddress
            }  catch {
                $hostName = "N/A"
            }
        }
    }

    # Output the reply details
    Write-Host ("{0,-3} {1,-14} {2,-16} {3,-50}" -f $i, [Math]::Round($roundtripTime, 2), $($pingReply.Address), $hostName)

    $query = "N/A"
    if ($authorityDns -ne "N/A") {
        $query = $authorityDns
    }
    if ($hostName -ne "N/A") {
        $query = $hostName
    }
    if ($parentDomain -ne "N/A") {
        $query = $parentDomain
    }

    if ($whoisLookup -and $hostName -ne "N/A" -and $tlds -contains $query.Split(".")[-1]) {
        try {
            # Start the Whois lookup
            $server = "whois.iana.org"
            if ($query -ne "N/A") {
                $data = Get-WhoisData $server $query
                $whoisEntries = New-WhoisEntries $data

                # Print the Whois information
                Write-Host "`nWhois Information"
                Write-Host "------------------"
                foreach($entry in $whoisEntries){
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "", "Contact", "Name", "Organisation")
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "Contact", $entry.Contact, "", "")
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "Name", $entry.Name, "", "")
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "Organisation", $entry.Organisation, "", "")
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "Address", $entry.Address, "", "")
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "Phone", $entry.Phone, "", "")
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "Email", $entry.Email, "", "")
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "Nameserver", $entry.Nameserver, "", "")
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "Nameserver IPV4", $entry."Nameserver IPV4", "", "")
                    Write-Host ("{0,-45} {1,-30} {2,-30} {3,-30}" -f "Nameserver IPV6", $entry."Nameserver IPV6", "", "")
                    Write-Host "`n"
                }

            }
        }
        catch {
            # Do nothing
        }
    }
    if ($($pingReply.Address) -eq $targetHost -or $($pingReply.Address) -eq $targetIP -or $hostName -eq $targetHost) {
        break
    }
}

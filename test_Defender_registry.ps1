# Script used in researching Defender and Tamper Protection
# Use at your own risk, may render system into weird state. 
# This is a RESEARCH script, not a Pentest script, it's more
# like fuzzing and not doing things specific or intentionally

$basePath = "HKLM:\SOFTWARE\Microsoft\Windows Defender"

# Get all keys and subkeys
$keys = Get-ChildItem -Path $basePath -Recurse

foreach ($key in $keys) {
    # Correctly construct the registry path
    $path = $key.PSPath

    try {
        $properties = Get-ItemProperty -Path $path -ErrorAction Stop

        foreach ($property in $properties.PSObject.Properties) {
            $name = $property.Name
            $originalValue = $property.Value
            # Placeholder value determination logic goes here
            $newValue = 1

            # Try to set a new value
            Set-ItemProperty -Path $path -Name $name -Value $newValue -ErrorAction Stop
            Write-Host "Successfully changed $name in $path to $newValue."

            # Attempt to revert back to the original value
            Set-ItemProperty -Path $path -Name $name -Value $originalValue
            Write-Host "Reverted $name in $path back to its original value."
        }
    } catch {
        Write-Warning "Direct modification failed for $path. Error: $_"

        # Attempt to modify the corresponding policy entry if direct modification fails
        $policiesPath = $path -replace 'Microsoft\\Windows Defender', 'Policies\\Microsoft\\Windows Defender'
        try {
            # Placeholder for new value; adjust based on logic and original value type
            $newValue = 1
            
            # Try to set a new value under Policies
            Set-ItemProperty -Path $policiesPath -Name $name -Value $newValue -ErrorAction Stop
            Write-Host "Successfully changed $name in $policiesPath to $newValue via GPO approach."

            # No revert action here, as the policy might not have had an original value

        } catch {
            Write-Warning "Failed to modify $name in $policiesPath via GPO approach. Error: $_"
        }
    }
}

#!/bin/bash

# Adjust folder as needed - script is recursive
# for subfolders, looking for all .txt files
datafolder="/mnt/d/datafolder/"
narrowSearch=false

# Check for optional '-n' parameter
while getopts ":n" opt; do
  case $opt in
    n)
      narrowSearch=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Remove the options from the positional parameters
shift $((OPTIND-1))

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 [-n] firstName lastName"
    exit 1
fi

firstName=$1
lastName=$2

# Define separators, handling the hyphen correctly
separators="[,:._+\-]*" # Place the hyphen at the end
noSeparator=""

patterns=()

# Function to add patterns
add_pattern() {
    local fName=$1
    local lName=$2
    patterns+=("${fName}${separators}${lName}")
    patterns+=("${fName}${noSeparator}${lName}") # Case with no special char
}

# Narrow search patterns
if [ "$narrowSearch" = true ]; then
    # Edge case with optional special char and no special char
    add_pattern "${firstName:0:1}" "$lastName"
    # Full name with optional special char and no special char
    add_pattern "$firstName" "$lastName"
else
    # General search logic
    patterns+=("${firstName:0:1}${separators}${lastName}") # Special edge case
    patterns+=("${firstName:0:1}${noSeparator}${lastName}") # Without special char
    for i in {1..9}; do
        fNameLen=$(( (${#firstName} * i + 9) / 10 ))
        lNameLen=$(( (${#lastName} * (10 - i) + 9) / 10 ))

        [ $fNameLen -lt 3 ] && fNameLen=3
        [ $lNameLen -lt 3 ] && lNameLen=3

        fNameLen=$(( fNameLen > ${#firstName} ? ${#firstName} : fNameLen ))
        lNameLen=$(( lNameLen > ${#lastName} ? ${#lastName} : lNameLen ))

        fNameSlice="${firstName:0:$fNameLen}"
        lNameSlice="${lastName:0:$lNameLen}"
        add_pattern "$fNameSlice" "$lNameSlice"
    done
    add_pattern "$firstName" "$lastName" # Full name case
fi

# Process patterns and enable colored output
for pattern in "${patterns[@]}"; do
    echo "Searching with pattern: $pattern"
    find "$datafolder" -type f -name "*.txt" -print0 | parallel -0 egrep --color=always -iH "$pattern"
done

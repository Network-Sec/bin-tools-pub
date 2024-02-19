#!/bin/bash

# Adjust folder as needed - script is recursive
# for subfolders, looking for all .txt files
datafolder="/mnt/d/datafolder/"
narrowSearch=false
smallSearch=false

# Check for '-n' or '-s' parameters
while getopts ":ns" opt; do
  case $opt in
    n)
      narrowSearch=true
      ;;
    s)
      smallSearch=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Remove the options from the positional parameters
shift $((OPTIND-1))

if [ "$#" -le 1 ]; then
    echo "Usage: $0 [-n|-s] firstName lastName <optional folder>"
    exit 1
fi

firstName=$1
lastName=$2

# Define separators, handling the hyphen correctly
separators="[,:._+\-]*" # Place the hyphen at the end
noSeparator=""

patterns=()

# Function to add patterns including both name directions
add_pattern() {
    local fName=$1
    local lName=$2
    # First name followed by last name
    patterns+=("${fName}${separators}${lName}")
    patterns+=("${fName}${noSeparator}${lName}")
    # Last name followed by first name
    patterns+=("${lName}${separators}${fName}")
    patterns+=("${lName}${noSeparator}${fName}")
}

# Narrow search patterns
if [ "$narrowSearch" = true ]; then
    add_pattern "${firstName:0:1}" "$lastName"
    add_pattern "$firstName" "$lastName"
elif [ "$smallSearch" = true ]; then
    # For small search, only use complete first and last name with and without separators
    add_pattern "$firstName" "$lastName"
else
    # General search logic
    patterns+=("${firstName:0:1}${separators}${lastName}")
    patterns+=("${firstName:0:1}${noSeparator}${lastName}")
    patterns+=("${lastName}${separators}${firstName:0:1}")
    patterns+=("${lastName}${noSeparator}${firstName:0:1}")
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
    add_pattern "$firstName" "$lastName"
fi

if [ -n "$3" ]; then
    datafolder="$3"
fi

# Process patterns and enable colored output
for pattern in "${patterns[@]}"; do
    echo "Searching with pattern: $pattern"
    find "$datafolder" -type f -name "*.txt" -print0 | parallel -0 egrep --color=always -iH "$pattern"
done

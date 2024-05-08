#!/usr/bin/env python3

# Inteded to be used with wordlists that will be self-combined 
# (each word of the list with each word of the list)
# As broad-spectrum list we often create lists that contain things like
# a b c... aa ab ac... 001 002 003... dictword1 dictword2 dictword3...
# To use them efficiently, it's best to sort them like the script does.
# We recommend one manual aftertouch, move the numbers somewhere into the middle
# Enjoy your fuzz!

import sys

def custom_sort(word):
    # Determine the sorting key.
    # - is_number: to ensure that characters are sorted before numbers.
    # - len(word): to sort by length.
    # - word: to sort lexicographically within the same length.
    is_number = word.isdigit()
    # We'll use an inverse boolean to ensure characters come first.
    return (is_number, len(word), word)

def sort_wordlist(wordlist):
    # Sort using the custom key
    return sorted(wordlist, key=custom_sort)

def main(filenames=None):
    words = []
    if filenames:
        # Process each file.
        for filename in filenames:
            with open(filename, 'r') as f:
                words.extend(line.strip() for line in f if line.strip())
    else:
        # Process standard input.
        words.extend(line.strip() for line in sys.stdin if line.strip())

    # Sort the words and print each on a new line
    sorted_words = sort_wordlist(words)
    for word in sorted_words:
        print(word)

if __name__ == "__main__":
    # Process files listed in command line arguments or stdin if no arguments.
    main(sys.argv[1:] if len(sys.argv) > 1 else None)
 

#!/usr/bin/env python3

##############################################################################################
###### Analyses HTML input from stdin or URL via cmd params and creates a score,       #######
###### if the content likely is code or not                                            #######
##############################################################################################

import requests
import argparse
from bs4 import BeautifulSoup,NavigableString
import sys
import html
import re
import json
from pprint import pprint
import string

# Store stdin so we can redirect it back after reading
# This is important for pdb debugging
original_stdin = sys.stdin

import html

# TODO: We could sort these lists better between low- and high-rank keywords. "if" will be
# in many regular texts, while "xor", "jne" or "+=" won't-

# List of code keywords
code_keywords = ['cmp', 'super', 'mul', 'div', 'while', 'call', 'push', 'else', 'nonlocal', 'break', 'except', 'finally', 'if', 'yield', 'await', 'je', 'print', 'sub', 'for', 'try', 'continue', 'with', 'mod', 'import', 'self', 'add', 'jne', 'None', 'not', 'lambda', 'pop', 'def', 'jl', 'test', 'as', 'is', 'global', 'mov', 'xor', 'from', 'del', 'False', 'elif', 'exec', 'assert', 'jmp', 'ret', 'async', 'jge', 'return', 'eval', 'nop', 'in', 'jg', 'jle', 'True', 'raise', 'pass', 'and', 'class', 'or']

# List of high-rank code keywords and symbols
high_rank_keywords = [
    'if', 'else', 'elif', 'while', 'for', 'do', 'switch', 'case', 'break', 'continue', 'return',
    'int', 'float', 'double', 'char', 'string', 'bool', 'true', 'false', 'null', 'void',
    'or', 'and', 'xor', 'not',
    'mov', 'rax', 'eax', 'rip', 'eip', 'rbp', 'ebp', 'rsp', 'esp', 'rdi', 'edi', 'rsi', 'esi',
    'function', 'class', 'struct', 'enum', 'public', 'private', 'protected', 'static', 'final',
    'try', 'catch', 'throw', 'finally', 'new', 'delete', 'include', 'import', 'require', 'define',
    'print', 'printf', 'println', 'cout', 'cin', 'scanf', 'printf', 'fprintf', 'sprintf', 'scanf',
    'def', ';\n', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '^', '<<', '>>', '+=',
    '=>', '##', '${', '$[', '#{'
]

# Define lists of characters in regular text and code
chars_text = string.ascii_letters + string.digits + string.whitespace + ".,;!?-()\"&|[]\t"
chars_code = chars_text + string.punctuation 

def classify_text(input_text):
    # Initialize an empty list to store the results
    results = []

    for item in input_text:
        # Initialize variables to count characters in regular text and code
        text_count = 0
        code_count = 0

        # Iterate through characters in the item
        for char in item:
            if char in chars_text:
                text_count += 1
            if char in chars_code:
                code_count += 1

        # Iterate through words in the item
        for word in item.split():
            if word in code_keywords:
                code_count += 1
            if word in high_rank_keywords:
                code_count += 10

        score = text_count / code_count 

        is_code = score < 0.85

        # Create a dictionary for the result
        result = {'text': item, 'is_code': is_code}

        # Append the result to the list of results
        results.append(result)

    return results

def extract_text_from_html(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    text = soup.strings

    blocks = []
    current_block = ''  

    for item in text:
        if len(item) < 2:
            if current_block:
                blocks.append(current_block) 
                current_block = ''  
        else:
            current_block += item  + '\n'

    if current_block:
        blocks.append(current_block + '\n') 
  
    return blocks

# Analyze an HTML document from a URL
def get_html_url(url):
    # Issue a web request and prepare the HTML document
    response = requests.get(url)
    if response.status_code != 200:
        print("Status Code:", response.status_code)
        print(response.text)
        exit(0)
    return response.text

def main():
    parser = argparse.ArgumentParser(description='Code Recognition in HTML docs')
    parser.add_argument('-u', '--url', help='URL of the HTML document to analyze')
    parser.add_argument('-f', '--file', help='Path to an HTML file to analyze')
    args = parser.parse_args()
    
    html_content = ""

    if args.url:
        html_content = get_html_url(args.url)
    elif args.file:
        with open(args.file, 'r') as file:
            html_content = file.read()
    else:
        # Read HTML content from stdin (pipe)
        html_content = ''.join(sys.stdin.read())

        # Debugging needs to have stdin closed again
        sys.stdin = original_stdin

    # Extract text from HTML
    extracted_text = extract_text_from_html(html_content)

    # Classify text snippets as code or regular text
    classified_text = classify_text(extracted_text)
    for result in classified_text:
        if result['is_code']:
            print(result['text'])
    exit(0)

if __name__ == "__main__":
    main()

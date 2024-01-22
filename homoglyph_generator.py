#!/usr/bin/env python3

### First release version - needs some improvements   ###
### - Add check if input_string != output_string      ###
### - Add test for "Browser reaction" (punnycode etc) ###

import argparse
from prettytable import PrettyTable
from homoglyphs import Homoglyphs
from confusable_homoglyphs import confusables

def parse_args():
    parser = argparse.ArgumentParser(description='Generate homoglyphs for an input string.')
    parser.add_argument('input_string', help='The input string to generate homoglyphs for.')
    parser.add_argument('--max_homoglyphs', type=int, default=3, help='Maximum number of homoglyph substitutions to make in the string.')
    parser.add_argument('--homoglyphs', action='store_true', help='Use the homoglyphs library.')
    parser.add_argument('--codebox', action='store_true', help='Use the codebox/homoglyph project.')
    return parser.parse_args()

def load_codebox_homoglyphs():
    with open('homoglyph/raw_data/char_codes.txt', 'r') as f:
        char_codes = f.readlines()

    homoglyphs = {}
    for line in char_codes:
        line = line.strip()
        if line and not line.startswith("#"):
            codepoints = line.split(",")
            homoglyphs[codepoints[0]] = [chr(int(cp, 16)) for cp in codepoints[1:]]

    return homoglyphs

def generate_homoglyphs_homoglyphs(input_string, max_homoglyphs):
    hg = Homoglyphs()
    for idx in range(len(input_string)):
        char = input_string[idx]
        variants = hg.get_combinations(char)[:max_homoglyphs]
        for variant in variants:
            yield input_string[:idx] + variant + input_string[idx+1:]

def generate_homoglyphs_codebox(input_string, max_homoglyphs):
    homoglyphs = load_codebox_homoglyphs()
    for idx in range(len(input_string)):
        char = input_string[idx]
        codepoint = format(ord(char), 'x')
        if codepoint in homoglyphs:
            for hg in homoglyphs[codepoint][:max_homoglyphs]:
                yield input_string[:idx] + hg + input_string[idx+1:]

def is_dangerous_string(input_string):
    return 'Yes' if confusables.is_dangerous(input_string) else 'No'

if __name__ == '__main__':
    args = parse_args()

    table = PrettyTable(['Method', 'Variant', 'Is Dangerous'])

    if args.homoglyphs:
        homoglyphs = list(generate_homoglyphs_homoglyphs(args.input_string, args.max_homoglyphs))
        for i, homoglyph in enumerate(homoglyphs, start=1):
            method = 'homoglyphs' if i == 1 else ''
            is_dangerous = is_dangerous_string(homoglyph)
            table.add_row([method, homoglyph, is_dangerous])

    if args.codebox:
        codebox = list(generate_homoglyphs_codebox(args.input_string, args.max_homoglyphs))
        for i, variant in enumerate(codebox, start=1):
            method = 'codebox' if i == 1 else ''
            is_dangerous = is_dangerous_string(variant)
            table.add_row([method, variant, is_dangerous])

    print(table)

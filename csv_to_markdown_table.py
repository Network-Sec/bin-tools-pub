#!/usr/bin/env python3

# Example Usage:
# cat test.csv | csv_to_markdown_table.py | less -S
# - Outputs clean markdown table to stdout
# - Fixes some issues with broken csv
# - Tries to make proper sizing and remove empty columns
# - Not all options / args completely implemented

import csv
import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Convert CSV to Markdown with customizable formatting.')
    parser.add_argument('-dl', '--disable_linebreaks', action='store_true', help='Disable line breaks in headers.')
    parser.add_argument('-de', '--disable_ellipsis', action='store_true', help='Disable ellipsis for long data.')
    parser.add_argument('-dc', '--disable_col_removal', action='store_true', help='Disable removal of empty columns.')
    return parser.parse_args()

def calculate_column_widths(headers, data_rows):
    column_widths = [len(header) for header in headers]
    for row in data_rows:
        for i, cell in enumerate(row):
            if i >= len(column_widths):
                column_widths.append(len(cell))  # Extend column widths for extra columns
            else:
                column_widths[i] = max(column_widths[i], len(cell))
    return column_widths

def format_header(header, max_width, disable_linebreaks, disable_ellipsis):
    formatted_header = header
    if len(header) > max_width and not disable_ellipsis:
        formatted_header = header[:max_width - 3] + '...'
    if not disable_linebreaks and len(header) > max_width:
        # Find best place to split the header to prevent breaking words inappropriately
        split_index = header.rfind(' ', 0, max_width)
        if split_index == -1:
            split_index = max_width  # Force split if no spaces
        formatted_header = header[:split_index] + '\n' + header[split_index+1:]
    return formatted_header

def process_headers(headers, column_widths, args):
    return [format_header(header, column_widths[i], args.disable_linebreaks, args.disable_ellipsis) for i, header in enumerate(headers)]

def remove_empty_columns(headers, data_rows, column_widths, disable_col_removal):
    if disable_col_removal:
        return headers, data_rows, column_widths

    valid_columns = [any(row[i].strip() for row in data_rows if i < len(row)) for i in range(len(headers))]
    headers = [h for h, valid in zip(headers, valid_columns) if valid]
    column_widths = [w for w, valid in zip(column_widths, valid_columns) if valid]
    data_rows = [[cell for cell, valid in zip(row, valid_columns) if valid] for row in data_rows]

    return headers, data_rows, column_widths

def generate_markdown(headers, data_rows, column_widths, args):
    headers = process_headers(headers, column_widths, args)
    header_line = '| ' + ' | '.join(headers) + ' |'
    separator_line = '|-' + '-|-'.join('-' * width for width in column_widths) + '-|'
    body_lines = ['| ' + ' | '.join(f"{cell:<{column_widths[i]}}" for i, cell in enumerate(row)) + ' |' for row in data_rows]
    return '\n'.join([header_line, separator_line] + body_lines)

def csv_to_markdown(csv_file, args):
    reader = csv.reader(csv_file)
    headers = next(reader)
    data_rows = list(reader)
    column_widths = calculate_column_widths(headers, data_rows)
    headers, data_rows, column_widths = remove_empty_columns(headers, data_rows, column_widths, args.disable_col_removal)
    return generate_markdown(headers, data_rows, column_widths, args)

if __name__ == "__main__":
    args = parse_args()
    if sys.stdin.isatty():
        print("Please pipe CSV data into the script")
    else:
        print(csv_to_markdown(sys.stdin, args))

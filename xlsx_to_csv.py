#!/usr/bin/env python3

# Simple xlsx file reader and converter
# Usage:
# $ xlsx_to_csv.py test.xlsx --csv test.csv
# Exported content - Copy to test_content.csv

import pandas as pd
import argparse
import os
import re 

def clean_filename(base_name):
    print(base_name)
    base_name = re.sub(r'\s*-\s*Copy', '', base_name)
    print("Clean", base_name)
    return base_name

def print_excel(filename, to_csv=None, show_all=False):
    with pd.ExcelFile(filename) as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)
            
            if to_csv:
                base = os.path.splitext(to_csv)[0]
                csv_filename = clean_filename(f"{base}_{sheet_name}.csv")
                df.to_csv(csv_filename, index=False)
                print(f"Exported {sheet_name} to {csv_filename}")
                
            elif show_all:
                pd.set_option('display.max_rows', None)
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                print(f"Sheet: {sheet_name}")
                df_string = df.to_string(index=False)
                df_string = re.sub(r'\s{2,}', '  ', df_string)
                print(df_string)
                print("\n" + "-"*40 + "\n")
            
            else:
                print(f"Sheet: {sheet_name}")
                print(df.head())
                print("\n" + "-"*40 + "\n")

def main():
    parser = argparse.ArgumentParser(description="View Excel files in the terminal or export them to CSV.")
    parser.add_argument("filename", help="The path to the Excel file to view.")
    parser.add_argument("--csv", help="Export the Excel file to CSV. Provide the base name for the output files.", metavar="BASENAME")
    parser.add_argument("--all", help="Print the entire content of the Excel sheets to stdout.", action="store_true")
    args = parser.parse_args()

    print_excel(args.filename, to_csv=args.csv, show_all=args.all)

if __name__ == "__main__":
    main()


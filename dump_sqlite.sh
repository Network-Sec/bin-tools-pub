#!/bin/bash
# Quickly loop over all files in current folder and try to dump all sqlite database content.
# The script assumes all files are sqlite(3) and makes no further checks - this is intended.
# If you need a filter, cause your folder holds other file types, add it in the "for" loop.

# Directory containing the database files, you can call the script like this: dump_sqlite.sh .
DIR=$1

# Loop through all .db files in the specified directory, or change to e.g. $DIR/*.sqlite3
for dbfile in $DIR/*.*; do
    echo "Database File: $dbfile"

    # Check if the file is a valid SQLite database file by checking if it has any tables
    if sqlite3 "$dbfile" ".tables" | grep -q '.'; then
        # Get a list of all tables in the database file
        tables=$(sqlite3 "$dbfile" ".tables")

        # Loop through each table and print its contents
        for table in $tables; do
            echo "Contents of $table:"
            sqlite3 "$dbfile" "SELECT * FROM $table;"
            echo "-------------------------------------"
        done
    else
        echo "No tables found or not a valid SQLite database."
    fi
    echo "====================================================="
done


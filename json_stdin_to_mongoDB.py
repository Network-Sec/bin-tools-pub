#!/usr/bin/env python3

# Imports JSON from stdin to mongoDB. Creds and collection name are hardcoded
# this is my most-used usecase, cause I don't care about the collection name
# but need to quickly aggregate some data within my workflow on bash.
# Example Usage: ... | jq | json_stdin_to_mongoDB.py Database_April_2024

import sys
import json
import argparse
from pymongo import MongoClient
from bson.json_util import loads

# Hardcoded MongoDB connection string
MONGO_CONN_STRING = 'mongodb://your_mongo_user:your_mongo_password@localhost:27017/'

def main(database_name):
    # Connect to MongoDB
    client = MongoClient(MONGO_CONN_STRING)
    db = client[database_name]
    collection = db.your_collection_name  # Set your collection name here

    # Read JSON input from stdin
    json_input = json.load(sys.stdin)
    identifier = json_input.get('id')  # Assuming 'id' as a unique identifier for documents

    if identifier is None:
        print("No identifier ('id') in input JSON.")
        return

    # Check if the entry already exists
    existing_doc = collection.find_one({'id': identifier})

    if existing_doc:
        update_doc = {}
        for key, new_value in json_input.items():
            old_value = existing_doc.get(key)
            if old_value and new_value != old_value:
                update_doc[key] = [old_value, new_value] if old_value not in [new_value, [new_value]] else old_value
            else:
                update_doc[key] = new_value
        collection.update_one({'id': identifier}, {'$set': update_doc})
        print(f"Document with id {identifier} updated.")
    else:
        collection.insert_one(json_input)
        print(f"New document with id {identifier} inserted.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON input and update MongoDB.")
    parser.add_argument("db_name", help="Name of the MongoDB database")
    args = parser.parse_args()

    main(args.db_name)

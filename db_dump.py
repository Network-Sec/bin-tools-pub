#!/usr/bin/env python3

# Tool to dump several types of databases. 
# Usage: db_dump.py <complete connection string like postgres://user:pass....port/name...>


import os
import sys
import re
import subprocess
import urllib.parse
from urllib.parse import urlparse, parse_qs
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import pymongo
import pandas as pd
from tabulate import tabulate

def parse_database_url(url):
    """Parse database URL and return connection parameters."""
    parsed_url = urlparse(url)
    db_type = parsed_url.scheme
    user = urllib.parse.unquote(parsed_url.username)
    password = urllib.parse.unquote(parsed_url.password)
    host = parsed_url.hostname
    port = parsed_url.port
    path = parsed_url.path.lstrip('/')
    params = parse_qs(parsed_url.query)
    print(db_type, user, password, host, port, path, params)
    return db_type, user, password, host, port, path, params

def fetch_mysql_data(user, password, host, port, database):
    """Fetch data from MySQL database."""

    if port is None or port == '':
        port = 3306

    command = [
        'mysql',
        f'--user={user}',
        f'--password={password}',
        f'--host={host}',
        f'--port={port}',
        '--database', database,
        '-e', 'SHOW TABLES;'
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(result)
    tables = result.stdout.splitlines()
    data = []
    for table in tables:
        if table and table != 'Tables_in_' + database:
            command = [
                'mysql',
                f'--user={user}',
                f'--password={password}',
                f'--host={host}',
                f'--port={port}',
                '--database', database,
                '-e', f'SELECT * FROM {table};'
            ]
            table_result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            rows = table_result.stdout.splitlines()
            if rows:
                data.append((table, [row.split() for row in rows[1:]]))
    return data

def fetch_postgresql_data(user, password, host, port, database):
    """Fetch data from PostgreSQL database."""
    if port is None or port == '':
        port = 5432 

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    with engine.connect() as connection:
        result = connection.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = result.fetchall()
        data = []
        for (table,) in tables:
            table_result = connection.execute(f"SELECT * FROM {table};")
            rows = table_result.fetchall()
            if rows:
                columns = table_result.keys()
                data.append((table, [dict(zip(columns, row)) for row in rows]))
    return data

def fetch_mongodb_data(user, password, host, port, database):
    """Fetch data from MongoDB database."""
    if port is None or port == '':
        port = 27017
        
    client = pymongo.MongoClient(host, port, username=user, password=password, authSource='admin')
    db = client[database]
    collections = db.list_collection_names()
    data = []
    for collection in collections:
        docs = db[collection].find()
        if docs:
            data.append((collection, [doc for doc in docs]))
    return data

def print_data(data):
    """Print database data in a tabulated format."""
    for table, rows in data:
        if rows:
            print(f"\nTable: {table}")
            df = pd.DataFrame(rows)
            print(tabulate(df, headers='keys', tablefmt='grid'))
        else:
            print(f"\nTable: {table} is empty.")

def backup_mysql(user, password, host, port, database):
    """Perform MySQL database backup."""
    command = [
        'mysqldump',
        f'--user={user}',
        f'--password={password}',
        f'--host={host}',
        f'--port={port}',
        database
    ]
    with open(f'{database}_backup.sql', 'wb') as f:
        subprocess.run(command, stdout=f, stderr=subprocess.PIPE)
    
    # Fetch and print data
    data = fetch_mysql_data(user, password, host, port, database)
    print_data(data)

def backup_postgresql(user, password, host, port, database):
    """Perform PostgreSQL database backup."""
    command = [
        'pg_dump',
        f'--username={user}',
        f'--host={host}',
        f'--port={port}',
        '--no-password',
        database
    ]
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    with open(f'{database}_backup.sql', 'wb') as f:
        subprocess.run(command, stdout=f, stderr=subprocess.PIPE, env=env)

    # Fetch and print data
    data = fetch_postgresql_data(user, password, host, port, database)
    print_data(data)

def backup_mongodb(user, password, host, port, database):
    """Perform MongoDB database backup."""
    command = [
        'mongodump',
        f'--username={user}',
        f'--password={password}',
        f'--host={host}',
        f'--port={port}',
        '--authenticationDatabase=admin',
        '--db', database
    ]
    subprocess.run(command, stderr=subprocess.PIPE)

    # Fetch and print data
    data = fetch_mongodb_data(user, password, host, port, database)
    print_data(data)

def main(url):
    db_type, user, password, host, port, database, _ = parse_database_url(url)

    try:
        if db_type == 'mysql':
            backup_mysql(user, password, host, port, database)
        elif 'postgres' in db_type:
            backup_postgresql(user, password, host, port, database)
        elif db_type == 'mongodb':
            backup_mongodb(user, password, host, port, database)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    except OperationalError as e:
        print(f"Failed to connect to the database: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python backup_script.py <database_url>")
        sys.exit(1)
    
    database_url = sys.argv[1]
    main(database_url)

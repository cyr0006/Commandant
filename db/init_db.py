# This script initializes the SQLite database for the Commandant bot.

import sqlite3
import os

os.makedirs("db", exist_ok=True)

conn = sqlite3.connect("db/commandant.db")
cursor = conn.cursor()

cursor.executescript("""
    CREATE TABLE IF NOT EXISTS goal_records (
        username TEXT,
        date TEXT,
        status TEXT DEFAULT '',
        PRIMARY KEY (username, date)
    );

    CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    );
""")

conn.commit()
conn.close()
print("Database created successfully.")
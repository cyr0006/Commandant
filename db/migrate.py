import json
import sqlite3
from database import set_goal_status

with open("../data/get_status.json") as f:
    data = json.load(f)


for username, records in data.items():
    for date, status in records.items():
        set_goal_status(username, date, status)
    print(f"Inserted records for {username}")

print("Mass Migration Done!")
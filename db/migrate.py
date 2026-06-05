import json
import sqlite3
from database import set_goal_status

ID_MAP = {
    "alextheodore":           "000000000000000001",
    "quarkybaryon":           "000000000000000002",
    "arjunj":                 "000000000000000003",
    "zenith0002":             "000000000000000004",
    "gxoff":                  "000000000000000005",
    "inconspicuous_divinity": "000000000000000006",
    "lelouch888":             "000000000000000007",
    "nnunes05":               "000000000000000008",
    "ruthenium3335":          "000000000000000009",
    "mirkwoodranger_":        "000000000000000010",
    "_not_alex_":             "000000000000000011",
    "sparesandwich":          "000000000000000012",
    "noah_f5339":             "000000000000000013",
}

with open("../data/get_status.json") as f:
    data = json.load(f)


with open("../get_status.json", "r") as f:
    data = json.load(f)

for username, records in data.items():
    user_id = ID_MAP.get(username)
    if not user_id:
        print(f"Skipping {username} — no ID mapping")
        continue
    for date, status in records.items():
        set_goal_status(user_id, username, date, status)
        print(f"Migrated {username} ({user_id}) {date} {status}")

print("Migration complete.")
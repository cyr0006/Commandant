import json
import sqlite3
from database import set_goal_status

ID_MAP = {
    "alextheodore":           "689282795255627995",
    "quarkybaryon":           "767603105343864853",
    "arjunj":                 "480169292965478402",
    "zenith0002":             "291434927092793345",
    "gxoff":                  "515072212697612298",
    "inconspicuous_divinity": "690049128683798546",
    "lelouch888":             "818080225593524244",
    "nnunes05":               "367953444943822849",
    "ruthenium3335":          "866255019791482891",
    "mirkwoodranger_":        "699239776687095919",
    "_not_alex_":             "555317016639176705",
    "sparesandwich":          "691788206764589098",
    "noah_f5339":             "885476775063339028",
}

with open("../data/get_status.json") as f:
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
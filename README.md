# Commandant
A Discord bot for tracking daily goal completion across a discord server.
 
## Features
- Mark daily goals as complete or incomplete via #evidence channel
- Leaderboards for weekly, monthly, and all-time performance
- Automatic daily initialisation and end-of-day finalisation
- Weekly summary report posted every Monday

## Commands
| Command | Channel | Description |
|---|---|---|
| `goals complete` / `goals completed` | #evidence | Mark today complete |
| `goals incomplete` / `goals failed` | #evidence | Mark today incomplete |
| `!prev` | #evidence | Mark yesterday complete |
| `!mark YYYY-MM-DD` | #evidence | Mark a specific date complete |
| `!weekly` | anywhere | Calendar week leaderboard |
| `!monthly` | anywhere | Rolling 30-day leaderboard |
| `!alltime` | anywhere | All-time leaderboard |
| `!help` | anywhere | Show commands |
 
## Setup
 
### Requirements
- Python 3.11+
- Discord bot token with `message_content` and `members` intents enabled
### Install
```bash
pip install -r requirements.txt
```
 
### Environment Variables
Create a `.env` file in the project root:
```
DISCORD_TOKEN=your_token_here
```
 
### Initialise the database
```bash
python3 db/init_db.py
```
 
### Run
```bash
python3 main.py
```
 
## Project Structure
```
commandant/
├── bot/
│   ├── client.py       # Discord client, on_ready, on_message
│   ├── commands.py     # Command handlers
│   ├── tasks.py        # Scheduled tasks (daily init, finalize, weekly report)
│   └── utils.py        # Timezone helpers
├── db/
│   ├── database.py     # All DB access functions
│   ├── init_db.py      # Creates the database and tables
│   └── migrate.py      # One-time migration from get_status.json
├── .env
├── main.py
└── requirements.txt
```
 
## Deployment
Runs as a `systemd` service on a Raspberry Pi. The bot uses a local SQLite database at `db/commandant.db`.
 
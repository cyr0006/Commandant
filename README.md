# Commandant
A Discord bot for tracking daily goal completion across a discord server.
 
## Features
- Mark daily goals as complete or incomplete via #evidence channel
- Leaderboards for weekly, monthly, and all-time performance
- Automatic daily initialisation and end-of-day finalisation
- Weekly summary report posted every Monday
- AI persona (via Groq) — chat with it directly, or let it occasionally chime in on its own

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
| `!ai <message>` | anywhere | Chat with the AI persona |
| `!help` | anywhere | Show commands |

## AI Persona
Powered by Groq's chat completions API. Two ways it talks:
- **Direct** — `!ai <message>` always gets a response.
- **Unprompted** — it keeps a rolling buffer of the last 8 messages per channel and occasionally comments on its own, based on a random chance + cooldown (and it won't chime in unprompted more than a few times in a row without someone actually engaging with it). Reply to one of its messages, or `@mention` it, to keep chatting — that back-and-forth is uncapped.

Tunables:
- `persona/groq_client.py` — `SYSTEM_PROMPT` defines the persona's personality/voice.
- `bot/chatter.py` — `HISTORY_SIZE`, `CHIME_CHANCE`, `COOLDOWN_SECONDS`, `AUTO_CHIME_CAP` control how often and how readily it chimes in on its own.
 
## Setup
 
### Requirements
- Python 3.11+
- Discord bot token with `message_content` and `members` intents enabled
- A [Groq](https://console.groq.com) API key (free tier) for the AI persona
- A Supabase project (URL + key) for database backups
### Install
```bash
pip install -r requirements.txt
```
 
### Environment Variables
Create a `.env` file in the project root:
```
DISCORD_TOKEN=your_token_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_api_key
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
│   ├── chatter.py      # Per-channel message history + chime-in/conversation gating
│   ├── tasks.py        # Scheduled tasks (daily init, finalize, weekly report)
│   └── utils.py        # Timezone helpers
├── persona/
│   └── groq_client.py  # Groq client, persona system prompt, response generation
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

## Author
Aryan Cyrus - Aryan.m10@yahoo.com 
 
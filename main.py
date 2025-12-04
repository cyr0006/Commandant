# Commandant - A Discord bot to manage goal tracking and performance
# Author: Aryan Cyrus

#========================= Imports and Setup =========================
import discord
import os
from dotenv import load_dotenv
from datetime import date
import json
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DATA_FILE = "get_status.json"

#========================= Data Loading ==========================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        goal_status = json.load(f)
else:
    goal_status = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(goal_status, f, indent=2)

#========================= Discord Client =========================
class Client(discord.Client):
    async def on_ready(self):
        print(f'logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return
        content = message.content.lower()
        today = str(date.today())
        user_id = str(message.author.name)
        
        #---- Goal Completion ----
        if "goals complete" in content or "goals completed" in content:
            goal_status.setdefault(user_id,{})[today] = "complete"
            save_data()
            await message.channel.send(f"Marked goals as complete for {message.author.name} on {today}.")
        
        #---- Goal failure ----
        elif "goals incomplete" in content or "goals failed" in content:
            goal_status.setdefault(user_id,{})[today] = "incomplete"
            save_data()
            await message.channel.send(f"Marked goals as incomplete for {message.author.name} on {today}.")    
            
        #---- Weekly Leaderboard ----
        elif content.startswith("!weekly"):
            performances = performance_all(7)
            msg_lines = [f"{user}: {count}/7 complete" for user, count in performances.items()]
            await message.channel.send("📊 Weekly performance:\n" + "\n".join(msg_lines))

        #---- Monthly Leaderboard ----
        elif content.startswith("!monthly"):
            performances = performance_all(30)
            msg_lines = [f"{user}: {count}/30 complete" for user, count in performances.items()]
            await message.channel.send("📊 Monthly performance:\n" + "\n".join(msg_lines))

#========================= X-Day Performance Calculation ==========================
def performance_all(n: int = 7):
    results = {}

    for user_key, records in goal_status.items():

        sorted_dates = sorted(records.keys(), reverse=True)

        last_n = sorted_dates[:n]

        complete_count = sum(1 for d in last_n if records[d] == "complete")

        results[user_key] = complete_count

    return results


#========================= Discord Client Run =========================
intents = discord.Intents.default()
intents.message_content = True
client = Client(intents=intents)
client.run(TOKEN)
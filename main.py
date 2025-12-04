import discord
import os
from dotenv import load_dotenv
from datetime import date
import json


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

DATA_FILE = "get_status.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        goal_status = json.load(f)
else:
    goal_status = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(goal_status, f, indent=2)


class Client(discord.Client):
    async def on_ready(self):
        print(f'logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return
        content = message.content.lower()
        today = str(date.today())
        user_id = str(message.author.name)

        if "goals complete" in content or "goals completed" in content:
            goal_status.setdefault(user_id,{})[today] = "complete"
            save_data()
            await message.channel.send(f"Marked goals as complete for {message.author.name} on {today}.")
        
        elif "goals incomplete" in content or "goals failed" in content:
            goal_status.setdefault(user_id,{})[today] = "incomplete"
            save_data()
            await message.channel.send(f"Marked goals as incomplete for {message.author.name} on {today}.")    
            
        elif content.startswith("!streak"):
            performances = last_7_performance_all()
            msg_lines = [f"{user}: {count}/7 complete" for user, count in performances.items()]
            report = "\n".join(msg_lines)
            await message.channel.send(f"📊 Last 7‑day performance:\n{report}")

def last_7_performance_all():
    results = {}

    for user_key, records in goal_status.items():
        sorted_dates = sorted(records.keys(), reverse=True)

        last_7 = sorted_dates[:7]
        complete_count = sum(1 for d in last_7 if records[d] == "complete")

        results[user_key] = complete_count

    return results



intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(TOKEN)
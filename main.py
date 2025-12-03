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
        user_id = str(message.author.id)

        if "goals complete" in content or "goals completed" in content:
            goal_status.setdefault(user_id,{})[today] = "complete"
            save_data()
            await message.channel.send(f"Marked goals as complete for {message.author.name} on {today}.")
        
        elif "goals incomplete" in content or "goals failed" in content:
            goal_status.setdefault(user_id,{})[today] = "incomplete"
            save_data()
            await message.channel.send(f"Marked goals as incomplete for {message.author.name} on {today}.")    
            
        elif content.startswith("!status"):
            # Example command to check a user's record
            user_data = goal_status.get(user_id, {})
            streak = sum(1 for s in user_data.values() if s == "complete")
            await message.channel.send(f"{message.author.display_name}, you have {streak} completions logged.")





intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(TOKEN)
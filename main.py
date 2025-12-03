import discord
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class Client(discord.Client):
    async def on_ready(self):
        print(f'logged on as {self.user}!')

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(TOKEN)
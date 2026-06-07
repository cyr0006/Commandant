import os
import sys
import discord
from dotenv import load_dotenv
from bot.client import Client

#main file loads the .env file and starts the bot client. It also handles rate limiting and other exceptions
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = Client(intents=intents)

if __name__ == "__main__":
    try:
        client.run(TOKEN)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            print("Rate limited. Exiting.")
            sys.exit(1)
        else:
            raise
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
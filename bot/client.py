import re
import discord
from bot.commands import (
    cmd_complete,
    cmd_incomplete,
    cmd_prev,
    cmd_mark,
    cmd_weekly,
    cmd_monthly,
    cmd_alltime,
    cmd_help,
)
from bot.tasks import register_tasks
from db.database import check_weekly_missed_goals

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        register_tasks(self)

    async def on_message(self, message):
        if message.author == self.user:
            return

        content = message.content.lower()
        user_id = str(message.author.id)
        username = message.author.name

        in_evidence = message.channel.name == "evidence"

        if content.startswith("!prev") and in_evidence:
            await cmd_prev(message, user_id, username)

        elif re.search(r"\b(cum|goals complete|goals completed)\b", content) and in_evidence:
            await cmd_complete(message, user_id, username)

        elif ("goals incomplete" in content or "goals failed" in content) and in_evidence:
            await cmd_incomplete(message, user_id, username)
            over, count = check_weekly_missed_goals(user_id)
            if over:
                await message.channel.send(
                    f"⚠️ {username}, you've missed {count} days this week. Let's get back on track!"
                )

        elif content.startswith("!weekly"):
            await cmd_weekly(message)

        elif content.startswith("!monthly"):
            await cmd_monthly(message)

        elif content.startswith("!alltime"):
            await cmd_alltime(message)

        elif content.startswith("!help"):
            await cmd_help(message)

        elif content.startswith("!mark") and in_evidence:
            await cmd_mark(message, user_id, username, content)

        elif content.startswith("!check-tasks"):
            leaderboard = discord.utils.get(self.get_all_channels(), name="leaderboard")
            if leaderboard:
                await message.channel.send("✅ Checked and ran any pending scheduled tasks!")
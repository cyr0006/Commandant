# Commandant - A Discord bot to manage goal tracking and performance
# Author: Aryan Cyrus

#========================= Imports and Setup =========================
import discord
from discord.ext import tasks
import os
from dotenv import load_dotenv
from datetime import date, datetime, timedelta
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
        if not daily_init.is_running():
            #insert a goals entry for today for all users
            daily_init.start()
        if not daily_finalize.is_running():
            #scrutinise goals entry for today for all users
            daily_finalize.start()
        if not weekly_report.is_running():
            #send weekly report every monday at 7am
            weekly_report.start()

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        #---- initialising vars ----
        content = message.content.lower()
        today = str(date.today())
        user_id = str(message.author.name)
        
        #---- Goal Completion ----
        #Goals complete updates latest pending entry to complete
        if "goals complete" in content or "goals completed" in content:
            target_date = update_latest_status(user_id, "complete")
            await message.channel.send(
                f"Marked goals as complete for {message.author.name} on {target_date}."
            )
        #---- Goal failure ----
        #Goals incomplete updates latest pending entry to incomplete
        elif "goals incomplete" in content or "goals failed" in content:
            target_date = update_latest_status(user_id, "incomplete")
            await message.channel.send(
                f"Marked goals as incomplete for {message.author.name} on {target_date}."
            )
        #---- Weekly Leaderboard ----
        elif content.startswith("!weekly"):
            performances = performance_all(7)
            sorted_perf = sorted(performances.items(), key=lambda x: x[1], reverse=True)
            msg_lines = [f"{user}: {count}/7 complete" for user, count in sorted_perf]
            await message.channel.send("📊 Weekly performance:\n" + "\n".join(msg_lines))

        #---- Monthly Leaderboard ----
        elif content.startswith("!monthly"):
            performances = performance_all(30)
            sorted_perf = sorted(performances.items(), key=lambda x: x[1], reverse=True)
            msg_lines = [f"{user}: {count}/30 complete" for user, count in sorted_perf]
            await message.channel.send("📊 Monthly performance:\n" + "\n".join(msg_lines))
        #---- All-Time Leaderboard ----
        elif content.startswith("!alltime"):
            performances = all_time_performance()
            sorted_perf = sorted(
                performances.items(),
                key=lambda x: (x[1][0] / x[1][1]) if x[1][1] > 0 else 0,
                reverse=True
            )
            msg_lines = [
                f"{user}: {complete}/{total} complete ({(complete/total*100):.1f}%)"
                for user, (complete, total) in sorted_perf
            ]
            report = "\n".join(msg_lines)
            await message.channel.send(f"📊 All-time performance:\n{report}")

#========================= Update Latest pending status ==========================
def update_latest_status(user_id: str, status: str):
    goal_status.setdefault(user_id, {})

    sorted_dates = sorted(goal_status[user_id].keys())

    target_date = None
    for d in reversed(sorted_dates):  # check newest first
        if goal_status[user_id][d] == "":
            target_date = d
            break

    if target_date is None:
        target_date = str(date.today())
        if target_date not in goal_status[user_id]:
            goal_status[user_id][target_date] = ""

    goal_status[user_id][target_date] = status
    save_data()
    return target_date
#========================= Weekly preformance update ==========================
@tasks.loop(minutes=1)
async def weekly_report():
    now = datetime.now()
    if now.weekday() == 0 and now.hour == 7 and now.minute == 0:
        channel = discord.utils.get(client.get_all_channels(), name="general")  
        if channel:
            performances = all_time_performance()
            msg_lines = [
                f"{user}: {complete}/{total} complete ({(complete/total*100):.1f}%)"
                for user, (complete, total) in performances.items()
            ]
            report = "\n".join(msg_lines)
            await channel.send(f"📊 Weekly All-Time Report:\n{report}")

#========================= Daily Init ==========================
@tasks.loop(hours=24)
async def daily_init():
    today = str(date.today())
    for user_key in goal_status.keys():
        if today not in goal_status[user_key]:
            goal_status[user_key][today] = ""
    save_data()

@tasks.loop(hours=24)
async def daily_finalize():
    yesterday = str(date.today() - timedelta(days=1))
    for user_key, records in goal_status.items():
        if yesterday in records and records[yesterday] == "":
            records[yesterday] = "incomplete"
    save_data()

#========================= X-Day Performance Calculation ==========================
def performance_all(n: int = 7):
    results = {}

    for user_key, records in goal_status.items():

        sorted_dates = sorted(records.keys(), reverse=True)

        last_n = sorted_dates[:n]

        complete_count = sum(1 for d in last_n if records[d] == "complete")

        results[user_key] = complete_count

    return results

#========================= All-Time Performance Calculation ==========================
def all_time_performance():
    results = {}

    for user_key, records in goal_status.items():
        total_entries = len(records)
        complete_count = sum(1 for status in records.values() if status == "complete")

        results[user_key] = (complete_count, total_entries)

    return results


#========================= Discord Client Run =========================
intents = discord.Intents.default()
intents.message_content = True
client = Client(intents=intents)
client.run(TOKEN)
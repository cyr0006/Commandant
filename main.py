# Commandant - A Discord bot to manage goal tracking and performance
# Author: Aryan Cyrus

#========================= Imports and Setup =========================
import re
import discord
from discord.ext import tasks
import os
from dotenv import load_dotenv
from datetime import date, datetime, time, timedelta, timezone
import json
import requests
import base64
from flask import Flask
from threading import Thread
from zoneinfo import ZoneInfo
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MELBOURNE_TZ = ZoneInfo('Australia/Melbourne')


# GitHub Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_REPO = os.getenv('GITHUB_REPO')
GITHUB_FILE_PATH = os.getenv('GITHUB_FILE_PATH', 'get_status.json')
METADATA_FILE_PATH = 'bot_metadata.json'
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'test')
#========================= GitHub Storage Functions =========================
def load_from_github(file_path=GITHUB_FILE_PATH):
    """Load JSON data from GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{file_path}?ref={GITHUB_BRANCH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            decoded_content = base64.b64decode(content['content']).decode('utf-8')
            return json.loads(decoded_content), content['sha']
        elif response.status_code == 404:
            print(f"File {file_path} not found on GitHub, creating new one...")
            save_to_github({}, file_path=file_path)
            return {}, None
        else:
            print(f"Error loading from GitHub: {response.status_code}")
            return {}, None
    except Exception as e:
        print(f"Exception loading from GitHub: {e}")
        return {}, None

def save_to_github(data, sha=None, file_path=GITHUB_FILE_PATH):
    """Save JSON data to GitHub"""

    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Convert data to JSON string and encode to base64
    json_content = json.dumps(data, indent=2)
    encoded_content = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": f"Update {file_path} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": encoded_content,
        "branch": GITHUB_BRANCH

    }
    
    # If we have a SHA (file exists), include it for update
    if sha:
        payload["sha"] = sha
    
    try:
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            print(f"Successfully saved {file_path} to GitHub")
            return True
        else:
            print(f"Error saving to GitHub: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Exception saving to GitHub: {e}")
        return False

#========================= Metadata Management =========================
metadata, metadata_sha = load_from_github(METADATA_FILE_PATH)

# def get_last_processed_time():
#     """Get the last time we processed messages"""
#     return metadata.get('last_processed', None)

# def set_last_processed_time(timestamp):
#     """Update the last processed timestamp"""
#     global metadata, metadata_sha
#     metadata['last_processed'] = timestamp
#     save_to_github(metadata, metadata_sha, METADATA_FILE_PATH)
#     # Reload to get new SHA
#     metadata, metadata_sha = load_from_github(METADATA_FILE_PATH)

def get_last_daily_init():
    """Get the last date we ran daily_init"""
    return metadata.get('last_daily_init', None)

def set_last_daily_init(date_str):
    """Update last daily_init date"""
    global metadata, metadata_sha
    metadata['last_daily_init'] = date_str
    save_to_github(metadata, metadata_sha, METADATA_FILE_PATH)
    metadata, metadata_sha = load_from_github(METADATA_FILE_PATH)

def get_last_daily_finalize():
    """Get the last date we ran daily_finalize"""
    return metadata.get('last_daily_finalize', None)

def set_last_daily_finalize(date_str):
    """Update last daily_finalize date"""
    global metadata, metadata_sha
    metadata['last_daily_finalize'] = date_str
    save_to_github(metadata, metadata_sha, METADATA_FILE_PATH)
    metadata, metadata_sha = load_from_github(METADATA_FILE_PATH)

def get_last_weekly_report():
    """Get the last date we sent weekly report"""
    return metadata.get('last_weekly_report', None)

def set_last_weekly_report(date_str):
    """Update last weekly report date"""
    global metadata, metadata_sha
    metadata['last_weekly_report'] = date_str
    save_to_github(metadata, metadata_sha, METADATA_FILE_PATH)
    metadata, metadata_sha = load_from_github(METADATA_FILE_PATH)

#========================= Data Loading ==========================
goal_status, current_sha = load_from_github()

def save_data():
    """Save data to GitHub instead of local file"""
    global current_sha
    success = save_to_github(goal_status, current_sha)
    if success:
        # Reload to get new SHA
        _, current_sha = load_from_github()

#========================= Flask Health Check =========================
app = Flask(__name__)

@app.route('/')
def home():
    return "Commandant Bot is running!", 200

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "online"}, 200

def run_flask():
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

#========================= Catch-up Logic =========================
def get_melbourne_date():
    """Get current date in Melbourne timezone"""
    return datetime.now(MELBOURNE_TZ).date()

async def check_and_run_scheduled_tasks(channel):
    """Check if any scheduled tasks need to run"""
    today = get_melbourne_date()
    today_str = str(today)
    yesterday_str = str(today - timedelta(days=1))
    
    # Check daily_init (should run once per day)
    last_init = get_last_daily_init()
    if last_init != today_str or today_str not in goal_status.get('system', {}):
        print(f"Running daily_init for {today_str}")
        run_daily_init()
        set_last_daily_init(today_str)
    
    # Check daily_finalize (should run once per day for yesterday)
    last_finalize = get_last_daily_finalize()
    if last_finalize != today_str:
        print(f"Running daily_finalize for {yesterday_str}")
        run_daily_finalize()
        set_last_daily_finalize(today_str)
    
    # Check weekly_report (Mondays only)
    if today.weekday() == 0:  # Monday
        last_report = get_last_weekly_report()
        # Check if we haven't sent report this week
        if not last_report or last_report < today_str:
            print(f"Running weekly_report for {today_str}")
            await send_weekly_report(channel)
            set_last_weekly_report(today_str)

def run_daily_init():
    """Initialize today's entry for all users"""
    today = str(get_melbourne_date())
    updated = False


    for user_key in goal_status.keys():
        if today not in goal_status[user_key]:
            goal_status[user_key][today] = ""
            updated = True
    if updated:
        save_data()

def run_daily_finalize():
    """Mark yesterday's pending entries as incomplete"""
    yesterday = str(get_melbourne_date() - timedelta(days=1))
    for user_key, records in goal_status.items():
        if yesterday in records and records[yesterday] == "":
            records[yesterday] = "incomplete"
    save_data()

async def send_weekly_report(channel):
    
    """Send the weekly all-time report"""
    performances = all_time_performance()
    if not performances:
        return
    
    sorted_perf = sorted(
    performances.items(),
    key=lambda x: (x[1][0] / x[1][1]) if x[1][1] > 0 else 0,
    reverse=True
    )

    msg_lines = [
        f"{i+1}) {user}: {complete}/{total} complete ({(complete/total*100):.1f}%) "
        f"{'🔥' if (complete/total*100) >= 85 else ('⚠️' if (complete/total*100) < 50 else '✅')}"
        for i, (user, (complete, total)) in enumerate(sorted_perf)
    ]  
    report = "\n".join(msg_lines)
    await channel.send(f"📊 Weekly All-Time Report:\n{report}")

#========================= 2 missed goals =========================
def check_weekly_missed_goals(username: str, max_misses: int = 2) -> bool:
    """Check if user has missed more than max_misses days this week (Mon-Sun)"""
    records = goal_status.get(username, {})
    if not records:
        return False
    
    today = get_melbourne_date()
    
    # Calculate days since Monday (0=Monday, 6=Sunday)
    days_since_monday = today.weekday()


    # Count back to Monday (inclusive)
    print(f"Checking missed goals for {username} from {today} back to Monday")
    miss_count = 0
    for i in range(days_since_monday+1):  # +1 to include today
        date_str = str(today - timedelta(days=i))
        print(date_str)
        if date_str in records:
            if records[date_str] == "incomplete":
                miss_count += 1
    if miss_count > max_misses:
        return True, miss_count
    return False, miss_count


async def notify_misses(user_obj, channel, missed: int = 2):
    """Notify user of n missed goals"""
    if not user_obj:
        print(f"[NOTIFY] Cannot notify - user_obj is None")
        return
    message = f"⚠️ {user_obj.mention}, you have missed your goals for {missed} days this week, king. Let's get back on track!"
    await channel.send(message)
#========================= Discord Client =========================
class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
        # Start Flask health check server
        Thread(target=run_flask, daemon=True).start()
        
        # Get the channels to work with
        channel = discord.utils.get(self.get_all_channels(), name="general")
        evidence = discord.utils.get(self.get_all_channels(), name="evidence")
        goals = discord.utils.get(self.get_all_channels(), name="goals")
        leaderboard = discord.utils.get(self.get_all_channels(), name="leaderboard")

        if not evidence or not leaderboard:
            # Fallback: get first text channel
            for ch in self.get_all_channels():
                if isinstance(ch, discord.TextChannel):
                    channel = ch
                    break
        
        if evidence or leaderboard:
            print(f"Using channel: {evidence.name}")
            
            # Check and run scheduled tasks
            await check_and_run_scheduled_tasks(leaderboard)
            if not check_scheduled_tasks.is_running():
                check_scheduled_tasks.start()

            #begin nagger loop    
            if not nag.is_running():
                nag.start()
        else:
            print("Warning: No suitable channel found")

    async def on_message(self, message):
        global goal_status, current_sha
        goal_status, current_sha = load_from_github() 
        if message.author == self.user:
            return
        
        #---- initialising vars ----
        content = message.content.lower()
        username = str(message.author.name)
        
        #---- Goal Completion ----
        if re.search(r"\b(cum|goals complete|goals completed)\b", content):
            if message.channel.name == "evidence":
                target_date = update_latest_status(username, "complete")
                await message.add_reaction("✅")

        #---- Goal Completion previous day ----
        elif "!prev" in content:
            if message.channel.name == "evidence":
                target_date = update_prev_status(username, "complete")
                await message.add_reaction("✅")
        #---- Goal failure ----
        elif "goals incomplete" in content or "goals failed" in content:
            if message.channel.name == "evidence":
                target_date = update_latest_status(username, "incomplete")
                await message.add_reaction("❌")

                if(check_weekly_missed_goals(username)):
                    await notify_misses(username, message.channel)
        #---- Weekly Leaderboard ----
        #I also have a function which returns sorted the tally for each person for the last n days (for example user1 2/7 goals done, etc)
        elif content.startswith("!weekly"):


            performances = performance_weekly()
            if not performances:
                await message.channel.send("No data available yet!")
                return
            sorted_perf = sorted(performances.items(), key=lambda x: x[1], reverse=True)
            msg_lines = [
                f"{i+1}) {user}: {count}"
                for i, (user, count) in enumerate(sorted_perf)
            ]
            await message.channel.send("📊 Weekly performance:\n" + "\n".join(msg_lines))

        #---- Monthly Leaderboard ----
        elif content.startswith("!monthly"):


            performances = performance_all(30)
            if not performances:
                await message.channel.send("No data available yet!")
                return
            sorted_perf = sorted(performances.items(), key=lambda x: x[1], reverse=True)
            msg_lines = [
                f"{i+1}) {user}: {count}/30 complete ({(count/30*100):.1f}%) "
                f"{'🔥' if count >= 25 else ('⚠️' if count < 20 else '✅')}"
                for i, (user, count) in enumerate(sorted_perf)
            ]
            await message.channel.send("📊 Monthly performance:\n" + "\n".join(msg_lines))
            
        #---- All-Time Leaderboard ----
        elif content.startswith("!alltime"):


            performances = all_time_performance()
            if not performances:
                await message.channel.send("No data available yet!")
                return
            sorted_perf = sorted(
                performances.items(),
                key=lambda x: (x[1][0] / x[1][1]) if x[1][1] > 0 else 0,
                reverse=True
            )

            msg_lines = [
                f"{i+1}) {user}: {complete}/{total} complete ({(complete/total*100):.1f}%) "
                f"{'🔥' if (complete/total*100) >= 85 else ('⚠️' if (complete/total*100) < 50 else '✅')}"
                for i, (user, (complete, total)) in enumerate(sorted_perf)
            ]

            report = "\n".join(msg_lines)
            await message.channel.send(f"📊 All-time performance:\n{report}")
        
        #---- Help commands ----
        elif content.startswith("!help"):
            help_message = (
                "📋 **Bot Commands:**\n"
                "• Type 'goals complete' or 'goals completed' or 'cum' in #evidence to mark today's goals as complete.\n"
                "• Type '!prev' in #evidence to mark yesterday's goals as complete.\n"
                "• Type 'goals incomplete' or 'goals failed' in #evidence to mark today's goals as incomplete.\n"
                "• Type '!weekly' to see the weekly performance leaderboard.\n"
                "• Type '!monthly' to see the monthly performance leaderboard.\n"
                "• Type '!alltime' to see the all-time performance leaderboard.\n"
                "• Type '!mark YYYY-MM-DD' in #evidence to mark goals for a specific date as complete.\n"
                "• Type '!help' to see this help message."
            )
            await message.channel.send(help_message)
        #---- Custom Date Completions ----
        elif content.startswith("!mark"):
            if message.channel.name == "evidence":
                custom_date = content.split(" ")[1]
                if mark_goal_custom_date(username, custom_date, "complete"):
                    await message.add_reaction("✅")
                else:
                    await message.add_reaction("❌")
           
        
        #---- Force Check Tasks (admin command) ----
        elif content.startswith("!check-tasks"):
            await check_and_run_scheduled_tasks(message.channel)
            await message.channel.send("✅ Checked and ran any pending scheduled tasks!")

#========================= Custom Date Goal Marking ==========================
def mark_goal_custom_date(username: str, target_date: str, status: str) -> bool:
    """Update the goal status for a user on a custom date"""
    goal_status.setdefault(username, {})

    if target_date not in goal_status[username]:
        goal_status[username][target_date] = ""
    
    goal_status[username][target_date] = status 
    save_data()

    return True
#========================= Update Latest pending status ==========================
def update_latest_status(username: str, status: str) -> str:
    """Update the latest pending status for a user"""
    goal_status.setdefault(username, {})
    # Get Melbourne time
    tz = ZoneInfo("Australia/Melbourne")
    now = datetime.now(tz)

    #if complete by 4am, count for previous day
    if now.hour < 4:
        target_date = (now - timedelta(days=1)).date()
    else: target_date = now.date()
    target_date_str = str(target_date)

    if target_date_str not in goal_status[username]:
        goal_status[username][target_date_str] = ""

    
    goal_status[username][target_date_str] = status 
    save_data()

    return target_date

def update_prev_status(username: str, status: str) -> str:
    """Update the latest pending status for a user"""
    goal_status.setdefault(username, {})
    # Get Melbourne time
    tz = ZoneInfo("Australia/Melbourne")
    now = datetime.now(tz)

    target_date = (now - timedelta(days=1)).date()
    target_date_str = str(target_date)

    if target_date_str not in goal_status[username]:
        goal_status[username][target_date_str] = ""
    
    goal_status[username][target_date_str] = status 
    save_data()

    return target_date

#========================= X-Day Performance Calculation ==========================
def performance_all(n: int = 7) -> dict:
    results = {}
    for user_key, records in goal_status.items():
        sorted_dates = sorted(records.keys(), reverse=True)
        last_n = sorted_dates[:n]
        complete_count = sum(1 for d in last_n if records[d] == "complete")
        results[user_key] = complete_count
    return results

def performance_weekly() -> dict:
    results = {}
    for user_key, records in goal_status.items():
        sorted_dates = sorted(records.keys(), reverse=True)

        index = None
        for i, d in enumerate(sorted_dates):
            date_obj = datetime.strptime(d, "%Y-%m-%d").date()
            if date_obj.weekday() == 0:  # Monday
                index = i
                break

        if index is None:
            # No Monday found, just use all available dates
            last_n = sorted_dates
        else:
            # Include the Monday itself
            last_n = sorted_dates[:index+2]

        complete_count = sum(1 for d in last_n if records[d] == "complete")
        results[user_key] = f"{complete_count}/{len(last_n)} goals complete"

    return results
#========================= All-Time Performance Calculation ==========================
def all_time_performance() -> dict:
    """
    Lists all time preformance for all users
    """
    results = {}
    for user_key, records in goal_status.items():
        total_entries = len(records)
        complete_count = sum(1 for status in records.values() if status == "complete")
        results[user_key] = (complete_count, total_entries)
    return results

#========================= Scheduled Task Loop ==========================
@tasks.loop(hours=1)  # Check every hour
async def check_scheduled_tasks():
    global goal_status, current_sha
    goal_status, current_sha = load_from_github() 
    
    leaderboard = discord.utils.get(client.get_all_channels(), name="leaderboard")
    if leaderboard:
        await check_and_run_scheduled_tasks(leaderboard)

#========================= Nagger Task Loop ==========================
@tasks.loop(time=[
    time(hour=19, minute=54, tzinfo=MELBOURNE_TZ)  # 14:12 Melbourne
])  # Check every day
async def nag():
    global goal_status, current_sha
    goal_status, current_sha = load_from_github()

    goals = discord.utils.get(client.get_all_channels(), name="goals")
    users = goal_status.keys()

    for username in users:
        user_obj = None
        missed, miss_count = check_weekly_missed_goals(username, 2)
        if(missed):
            for m in goals.guild.members:
                if m.name.lower() == username.lower():
                    user_obj = m
            if user_obj is None:
                print(f"[NAG] Cannot notify - user_obj is None for {username}")
                continue

            await notify_misses(user_obj, goals, miss_count)
#========================= Discord Client Run =========================

intents = discord.Intents.default()
intents.members = True  # Add this line
intents.message_content = True 

client = Client(intents=intents)
client.run(TOKEN)
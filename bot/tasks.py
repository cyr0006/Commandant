# schedules tasks and loops which repeat at certain intervals. 
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, time as dtime
#import supabase for backups
from supabase import create_client
import subprocess


import discord
from discord.ext import tasks
from bot.utils import get_melbourne_date
from db.database import (
    get_all_users,
    init_today_for_all_users,
    finalize_yesterday,
    get_metadata,
    set_metadata,
    performance_last_n_days,
)

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"), 
    os.getenv("SUPABASE_KEY")
    )

def register_tasks(client):
    """Call this from on_ready to start the scheduled task loop"""

    @tasks.loop(hours=1)
    async def check_scheduled_tasks():
        today = get_melbourne_date()
        today_str = str(today)
        yesterday_str = str(today - timedelta(days=1))

        leaderboard = discord.utils.get(client.get_all_channels(), name="leaderboard")
        if not leaderboard:
            return

        # daily_init
        if get_metadata("last_daily_init") != today_str:
            init_today_for_all_users(today_str)
            set_metadata("last_daily_init", today_str)

        # daily_finalize
        if get_metadata("last_daily_finalize") != today_str:
            finalize_yesterday(yesterday_str)
            set_metadata("last_daily_finalize", today_str)

        # weekly report (Mondays only)
        if today.weekday() == 0:
            if get_metadata("last_weekly_report") != today_str:
                await send_weekly_report(leaderboard)
                set_metadata("last_weekly_report", today_str)

    async def send_weekly_report(channel):
        data = performance_last_n_days(7)
        if not data:
            return
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
        lines = [
            f"{i+1}) {user}: {count}/7 "
            f"{'🔥' if count == 7 else ('⚠️' if count < 5 else '✅')}"
            for i, (user, count) in enumerate(sorted_data)
        ]
        await channel.send("📊 Weekly Report:\n" + "\n".join(lines))

    check_scheduled_tasks.start()

    @tasks.loop(time=dtime(hour=3, minute=0))
    async def backup_database():
        filename = f"backup_{datetime.now().strftime('%Y%m%d')}.db"
        
        with open("db/commandant.db", "rb") as f:
            supabase.storage.from_("backups").upload(filename, f)
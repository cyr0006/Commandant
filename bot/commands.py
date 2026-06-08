from datetime import timedelta
from zoneinfo import ZoneInfo
from db.database import (
    set_goal_status,
    performance_last_n_days,
    performance_this_week,
    performance_all_time,
    check_weekly_missed_goals,
)
from bot.utils import get_melbourne_now

async def cmd_complete(message, user_id, username):
    now = get_melbourne_now()
    if now.hour < 4:
        target_date = str((now - timedelta(days=1)).date())
    else:
        target_date = str(now.date())
    set_goal_status(user_id, username, target_date, "complete")
    await message.add_reaction("✅")

async def cmd_incomplete(message, user_id, username):
    now = get_melbourne_now()
    if now.hour < 4:
        target_date = str((now - timedelta(days=1)).date())
    else:
        target_date = str(now.date())
    set_goal_status(user_id, username, target_date, "incomplete")
    await message.add_reaction("❌")

async def cmd_prev(message, user_id, username):
    now = get_melbourne_now()
    target_date = str((now - timedelta(days=1)).date())
    set_goal_status(user_id, username, target_date, "complete")
    await message.add_reaction("✅")

async def cmd_mark(message, user_id, username, content):
    parts = content.split(" ")
    if len(parts) < 2:
        await message.channel.send("Usage: `!mark YYYY-MM-DD`")
        return
    target_date = parts[1]
    try:
        from datetime import datetime
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        await message.channel.send("Invalid date format. Use `YYYY-MM-DD`.")
        return
    set_goal_status(user_id, username, target_date, "complete")
    await message.add_reaction("✅")

async def cmd_weekly(message):
    data = performance_this_week()
    if not data:
        await message.channel.send("No data available yet!")
        return
    sorted_data = sorted(data.items(), key=lambda x: x[1][0], reverse=True)
    lines = [
        f"{i+1}) {user}: {complete}/{total} "
        f"{'🔥' if complete == total else ('⚠️' if complete < total * 0.5 else '✅')}"
        for i, (user, (complete, total)) in enumerate(sorted_data)
    ]
    await message.channel.send("📊 Weekly performance:\n" + "\n".join(lines))

async def cmd_monthly(message):
    data = performance_last_n_days(30)
    if not data:
        await message.channel.send("No data available yet!")
        return
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    lines = [
        f"{i+1}) {user}: {count}/30 ({count/30*100:.1f}%) "
        f"{'🔥' if count >= 25 else ('⚠️' if count < 20 else '✅')}"
        for i, (user, count) in enumerate(sorted_data)
    ]
    await message.channel.send("📊 Monthly performance:\n" + "\n".join(lines))

async def cmd_alltime(message):
    data = performance_all_time()
    if not data:
        await message.channel.send("No data available yet!")
        return
    sorted_data = sorted(
        data.items(),
        key=lambda x: x[1][0] / x[1][1] if x[1][1] > 0 else 0,
        reverse=True
    )
    lines = [
        f"{i+1}) {user}: {complete}/{total} ({complete/total*100:.1f}%) "
        f"{'🔥' if complete/total >= 0.85 else ('⚠️' if complete/total < 0.5 else '✅')}"
        for i, (user, (complete, total)) in enumerate(sorted_data)
    ]
    await message.channel.send("📊 All-time performance:\n" + "\n".join(lines))

async def cmd_help(message):
    help_message = (
        "📋 **Bot Commands:**\n"
        "• `goals complete` / `goals completed` in #evidence — mark today complete\n"
        "• `goals incomplete` / `goals failed` in #evidence — mark today incomplete\n"
        "• `!prev` in #evidence — mark yesterday complete\n"
        "• `!mark YYYY-MM-DD` in #evidence — mark a specific date complete\n"
        "• `!weekly` — calendar week leaderboard\n"
        "• `!monthly` — rolling 30 day leaderboard\n"
        "• `!alltime` — all-time leaderboard\n"
        "• `!help` — show this message\n"
    )
    await message.channel.send(help_message)
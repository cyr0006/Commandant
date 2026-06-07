# This script is for testing the database queries and printing out the results in a readable format. 
# It will show the performance of users over the last 7 days, this week, and all time, as well as any weekly missed goals.
from database import performance_last_n_days, performance_all_time, performance_this_week, check_weekly_missed_goals, get_all_users

def print_section(title):
    print(f"\n{'='*40}")
    print(f"  {title}")
    print('='*40)

print_section("Last 7 Days")
data = performance_last_n_days(7)
for user, count in sorted(data.items(), key=lambda x: x[1], reverse=True):
    bar = '█' * count + '░' * (7 - count)
    print(f"  {user:<20} {bar} {count}/7")

print_section("This Week")
data = performance_this_week()
for user, (complete, total) in sorted(data.items(), key=lambda x: x[1][0], reverse=True):
    pct = (complete/total*100) if total > 0 else 0
    print(f"  {user:<20} {complete}/{total} ({pct:.0f}%)")

print_section("All Time")
data = performance_all_time()
for user, (complete, total) in sorted(data.items(), key=lambda x: x[1][0]/x[1][1] if x[1][1] > 0 else 0, reverse=True):
    pct = (complete/total*100) if total > 0 else 0
    print(f"  {user:<20} {complete}/{total} ({pct:.0f}%)")

print_section("Weekly Missed Goals")
users = get_all_users()
for u in users:
    over, count = check_weekly_missed_goals(u["user_id"])
    flag = "⚠️ " if over else "  "
    print(f"  {flag}{u['username']:<20} {count} misses")
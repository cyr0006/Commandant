#utility functions for date and time management; always melbourne time

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MELBOURNE_TZ = ZoneInfo('Australia/Melbourne')

def get_melbourne_date():
    return datetime.now(MELBOURNE_TZ).date()

def get_melbourne_now():
    return datetime.now(MELBOURNE_TZ)
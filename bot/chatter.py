import random
import time
from collections import defaultdict, deque

HISTORY_SIZE = 8
CHIME_CHANCE = 0.5
COOLDOWN_SECONDS = 1 #20 * 60
CONVERSATION_TURNS = 4

_history = defaultdict(lambda: deque(maxlen=HISTORY_SIZE))
_last_chime = {}
_active_conversations = {}


def record_message(channel_id, username, content):
    content = content.strip()
    if content:
        _history[channel_id].append(f"{username}: {content}")


def get_history_text(channel_id):
    return "\n".join(_history[channel_id])


def should_chime_in(channel_id):
    if len(_history[channel_id]) < HISTORY_SIZE:
        return False
    if time.time() - _last_chime.get(channel_id, 0) < COOLDOWN_SECONDS:
        return False
    return random.random() < CHIME_CHANCE


def mark_chimed(channel_id):
    _last_chime[channel_id] = time.time()


def start_conversation(channel_id, bot_message_id):
    _active_conversations[channel_id] = {
        "turns_left": CONVERSATION_TURNS,
        "last_bot_message_id": bot_message_id,
    }


def matches_conversation(channel_id, message, is_mentioned):
    convo = _active_conversations.get(channel_id)
    if not convo or convo["turns_left"] <= 0:
        return False
    if is_mentioned:
        return True
    reference = message.reference
    return bool(reference and reference.message_id == convo["last_bot_message_id"])


def advance_conversation(channel_id, bot_message_id):
    convo = _active_conversations.get(channel_id)
    if not convo:
        return
    convo["turns_left"] -= 1
    convo["last_bot_message_id"] = bot_message_id
    if convo["turns_left"] <= 0:
        _active_conversations.pop(channel_id, None)

import os
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

# TODO: write your own persona/system prompt here
SYSTEM_PROMPT = "You are a helpful assistant."


async def get_ai_response(prompt: str) -> str:
    chat_completion = await _client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        model="openai/gpt-oss-120b",
    )
    return chat_completion.choices[0].message.content

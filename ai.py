import os
import httpx

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

# --- Configuration ---------------------------------------------------
# Point this at wherever your Hermes Agent instance is running.
# Examples:
#   Local:  "http://localhost:8000/v1"
#   Remote: "https://your-hermes-host.example.com/v1"
BASE_URL = os.environ.get("BASE_URL","http://127.0.0.1:8642/v1")
BASE_URI = os.environ.get("BASE_URI","http://127.0.0.1:8642")
# Hermes needs an API key to authenticate with your underlying
# model provider (e.g. Kimi). If you're running fully local with
# no auth, any placeholder string usually works.
API_KEY = os.environ.get("API_KEY","your_api_key_here")
API_SERVER_KEY = os.environ.get("API_SERVER_KEY", API_KEY)

# Model name as configured/expected by your Hermes setup.
MODEL = os.environ.get("MODEL","deepseek-v4-flash")


client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)


async def send_chat(message: str, history: list | None = None) -> str:
    """Send a single message to Hermes and return the reply text."""
    messages = (history or []) + [{"role": "user", "content": message}]

    response = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    return response.choices[0].message.content or ""

async def send_chat_history(history: list) -> str:
    """Send a single message to Hermes and return the reply text."""
    # Restrict the model to this provided history only.
    system_message: ChatCompletionMessageParam = {
        "role": "system",
        "content": "Answer using only this chat history. Do not use context from other sessions.",
    }
    messages: list[ChatCompletionMessageParam] = [system_message, *history]
    await create_new_hermes_session()
    response = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    return response.choices[0].message.content or ""

async def create_new_hermes_session() -> None:
    """Post /api/sessions to the hermes api."""
    async with httpx.AsyncClient() as http_client:
        await http_client.post(
            f"{BASE_URI}/api/sessions",
            json={},
            headers={"Authorization": f"Bearer {API_SERVER_KEY}"},
        )
    
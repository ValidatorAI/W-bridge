import os

from openai import AsyncOpenAI

# --- Configuration ---------------------------------------------------
# Point this at wherever your Hermes Agent instance is running.
# Examples:
#   Local:  "http://localhost:8000/v1"
#   Remote: "https://your-hermes-host.example.com/v1"
BASE_URL = os.environ.get("BASE_URL","http://127.0.0.1:8642/v1")

# Hermes needs an API key to authenticate with your underlying
# model provider (e.g. Kimi). If you're running fully local with
# no auth, any placeholder string usually works.
API_KEY = os.environ.get("API_KEY","your_api_key_here")

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

# Example
#def example():
#    print("Chatting with Hermes Agent. Type 'quit' to exit.\n")
#    history = []

#    while True:
#        user_input = input("You: ").strip()
#        if user_input.lower() in ("quit", "exit"):
#            break

#        history.append({"role": "user", "content": user_input})
#        reply = send_chat(user_input, history=history[:-1])  # avoid double-adding
#        print(f"Hermes: {reply}\n")

#        history.append({"role": "assistant", "content": reply})
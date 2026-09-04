import asyncio
from typing import Any


# Queue for requests targeting agent.hermes.chat_completions
chat_completions_queue: asyncio.Queue[Any] = asyncio.Queue()

# Queue for requests targeting agent.hermes_logic.send_chat_history
send_chat_history_queue: asyncio.Queue[Any] = asyncio.Queue()


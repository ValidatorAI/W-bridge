import asyncio
import logging
import random
import re
import uuid
from typing import Any, cast

from agent.hermes import create_new_hermes_session
from agent.hermes import sessions_fork
from bus.executors import enqueue_send_chat_history
from bus.queues import prepare_send_chat_history_input
from helpers.helpers import _strip_command_occurrence
from schemas.typed_dict import AttachmentPart, HermesMessage, HermesSessionPayload


logger = logging.getLogger(__name__)


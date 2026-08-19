import asyncio
import logging
import random

from agent.hermes import api_status_summary_get
from bus.executors import run_chat_completation, run_send_chat_history
from bus.queues import chat_completions_queue, send_chat_history_queue


logger = logging.getLogger(__name__)

CRON_INTERVAL_SECONDS = 3

_cron_task: asyncio.Task[None] | None = None
_stop_event: asyncio.Event | None = None


async def _process_chat_completions_once() -> bool:
    try:
        item = chat_completions_queue.get_nowait()
    except asyncio.QueueEmpty:
        logger.debug("chat_completions_queue is empty")
        return False

    try:
        await run_chat_completation(item)
        return True
    finally:
        chat_completions_queue.task_done()


async def _process_send_chat_history_once() -> bool:
    try:
        item = send_chat_history_queue.get_nowait()
    except asyncio.QueueEmpty:
        logger.debug("send_chat_history_queue is empty")
        return False

    try:
        await run_send_chat_history(item)
        return True
    finally:
        send_chat_history_queue.task_done()


async def cron() -> None:
    """Cron job entrypoint.

    Order:
    1) Check whether queue(s) have pending items.
    2) If pending work exists, check Hermes status.
    """
    chat_queue_size = chat_completions_queue.qsize()
    history_queue_size = send_chat_history_queue.qsize()

    if chat_queue_size == 0 and history_queue_size == 0:
        logger.debug("bus.cron tick: no pending queue items")
        return

    logger.info(
        "bus.cron pending items: chat_completions=%s send_chat_history=%s",
        chat_queue_size,
        history_queue_size,
    )

    status = await api_status_summary_get()
    logger.info(
        "Hermes status: overall=%s gateway_busy=%s active_agents=%s active_sessions=%s",
        status.get("overall"),
        status.get("gateway_busy"),
        status.get("active_agents"),
        status.get("active_sessions"),
    )

    if status.get("active_agents") == 0:
        logger.warning("No active agents available in Hermes")
        #check one of que is empty and the other one is not empty
        if chat_queue_size == 0 and history_queue_size > 0:
            logger.warning("send_chat_history_queue has pending items but no active agents")
            await _process_send_chat_history_once()
        elif chat_queue_size > 0 and history_queue_size == 0:
            logger.warning("chat_completions_queue has pending items but no active agents")
            await _process_chat_completions_once()
        else:
            logger.warning("Both queues have pending items but no active agents")
            # generate a random number & choose one of the queues to process
            if random.choice([True, False]):
                logger.warning("Processing chat_completions_queue despite no active agents")
                await _process_chat_completions_once()
            else:
                logger.warning("Processing send_chat_history_queue despite no active agents")
                await _process_send_chat_history_once()

async def _cron_runner() -> None:
    global _stop_event
    if _stop_event is None:
        _stop_event = asyncio.Event()

    logger.info("Bus cron runner started (interval=%ss)", CRON_INTERVAL_SECONDS)
    try:
        while not _stop_event.is_set():
            try:
                await cron()
            except Exception:
                logger.exception("Unhandled error in bus cron tick")

            try:
                await asyncio.wait_for(_stop_event.wait(), timeout=CRON_INTERVAL_SECONDS)
            except TimeoutError:
                continue
    finally:
        logger.info("Bus cron runner stopped")


def start_cron() -> None:
    global _cron_task, _stop_event
    if _cron_task is not None and not _cron_task.done():
        return

    _stop_event = asyncio.Event()
    _cron_task = asyncio.create_task(_cron_runner(), name="bus-cron-runner")


async def stop_cron() -> None:
    global _cron_task, _stop_event
    if _cron_task is None:
        return

    if _stop_event is not None:
        _stop_event.set()

    try:
        await _cron_task
    except asyncio.CancelledError:
        pass
    finally:
        _cron_task = None
        _stop_event = None
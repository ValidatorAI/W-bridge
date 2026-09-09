import asyncio
import logging

from agent.hermes import api_status_summary_get
from bus.executors import run_space_event
from bus.queues import space_events_queue
from helpers.environment import HERMES_MAX_ACTIVE_AGENTS


logger = logging.getLogger(__name__)

CRON_INTERVAL_SECONDS = 3

_cron_task: asyncio.Task[None] | None = None
_stop_event: asyncio.Event | None = None


async def _process_space_events_once() -> bool:
    try:
        item = space_events_queue.get_nowait()
    except asyncio.QueueEmpty:
        logger.debug("space_events_queue is empty")
        return False

    try:
        await run_space_event(item)
        return True
    finally:
        space_events_queue.task_done()


async def cron() -> None:
    """Cron job entrypoint.

    Order:
    1) Check whether the queue has pending items.
    2) If pending work exists, check Hermes status.
    3) Drain one item from the queue each tick.
    """
    space_event_queue_size = space_events_queue.qsize()

    if space_event_queue_size == 0:
        logger.debug("bus.cron tick: no pending queue items")
        return

    logger.info(
        "bus.cron pending items: space_events=%s",
        space_event_queue_size,
    )

    status = await api_status_summary_get()
    logger.info(
        "Hermes status: overall=%s gateway_busy=%s active_agents=%s active_sessions=%s",
        status.get("overall"),
        status.get("gateway_busy"),
        status.get("active_agents"),
        status.get("active_sessions"),
    )

    active_agents = status.get("active_agents")
    if active_agents is None or active_agents >= HERMES_MAX_ACTIVE_AGENTS:
        logger.warning(
            "Skipping space event processing: active_agents=%s >= threshold=%s",
            active_agents,
            HERMES_MAX_ACTIVE_AGENTS,
        )
        return

    await _process_space_events_once()


async def pooling_normal_message_cron() -> None:
    """Secondary cron hook for normal-message polling.

    This function is intentionally a no-op for now because there is no dedicated
    normal-message queue/worker in the bus layer yet.
    """
    logger.debug("bus.pooling_normal_message_cron tick")

async def _cron_runner() -> None:
    global _stop_event
    if _stop_event is None:
        _stop_event = asyncio.Event()

    logger.info("Bus cron runner started (interval=%ss)", CRON_INTERVAL_SECONDS)
    try:
        while not _stop_event.is_set():
            try:
                await cron()
                await pooling_normal_message_cron()
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
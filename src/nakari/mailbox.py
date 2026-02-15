from __future__ import annotations

import asyncio

import structlog

from nakari.models import Event, EventStatus


class Mailbox:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._archive: list[Event] = []
        self._log = structlog.get_logger("mailbox")

    async def put(self, event: Event) -> None:
        await self._queue.put(event)
        self._log.info("event_enqueued", event_id=event.id, type=event.type.value)

    async def get(self) -> Event:
        self._log.debug("waiting_for_event")
        event = await self._queue.get()
        event.status = EventStatus.PROCESSING
        self._log.info("event_dequeued", event_id=event.id, type=event.type.value)
        return event

    def archive(self, event: Event) -> None:
        event.status = EventStatus.COMPLETED
        self._archive.append(event)
        self._log.info("event_archived", event_id=event.id)

    def qsize(self) -> int:
        return self._queue.qsize()

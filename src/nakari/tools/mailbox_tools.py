from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from nakari.config import Config
from nakari.mailbox import Mailbox
from nakari.models import Attachment, Event, EventStatus, EventType
from nakari.tool_registry import ToolRegistry

if TYPE_CHECKING:
    from nakari.loop import LoopState


def register_mailbox_tools(
    registry: ToolRegistry,
    mailbox: Mailbox,
    loop_state: LoopState,
    config: Config,
) -> None:
    async def check_mailbox() -> str:
        event = await mailbox.get()
        loop_state.set_current_event(event)
        return json.dumps(
            {
                "event_id": event.id,
                "type": event.type.value,
                "content": event.content,
                "attachments": [
                    {"mime_type": a.mime_type, "uri": a.uri, "metadata": a.metadata}
                    for a in event.attachments
                ],
                "max_tool_calls": event.max_tool_calls,
                "metadata": event.metadata,
                "suspend_notes": event.suspend_notes,
            },
            ensure_ascii=False,
        )

    async def create_event(
        type: str,
        content: str,
        max_tool_calls: int | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> str:
        parsed_attachments = [
            Attachment(
                mime_type=a["mime_type"],
                uri=a["uri"],
                metadata=a.get("metadata", {}),
            )
            for a in (attachments or [])
        ]
        event = Event(
            type=EventType(type),
            content=content,
            attachments=parsed_attachments,
            max_tool_calls=max_tool_calls or config.default_max_tool_calls,
        )
        await mailbox.put(event)
        return f"Event {event.id} created and enqueued."

    async def suspend_event(notes: str) -> str:
        current = loop_state.current_event
        if not current:
            return "Error: No event currently being processed."
        current.status = EventStatus.SUSPENDED
        current.suspend_notes = notes
        current.metadata["suspend_count"] = current.metadata.get("suspend_count", 0) + 1
        await mailbox.put(current)
        loop_state.clear_current_event()
        return f"Event {current.id} suspended with notes. Re-enqueued."

    async def complete_event(summary: str) -> str:
        current = loop_state.current_event
        if not current:
            return "Error: No event currently being processed."
        current.metadata["completion_summary"] = summary
        mailbox.archive(current)
        loop_state.clear_current_event()
        return f"Event {current.id} completed and archived."

    registry.register(
        name="check_mailbox",
        description=(
            "Get the next event from the mailbox. "
            "If no events are pending, this will wait until one arrives. "
            "Returns event details including type, content, and tool call budget."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        handler=check_mailbox,
    )

    registry.register(
        name="create_event",
        description="Create a new event and add it to the mailbox for later processing.",
        parameters={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["user_text", "self_created", "timer", "system"],
                    "description": "Event type",
                },
                "content": {
                    "type": "string",
                    "description": "Event content/description",
                },
                "max_tool_calls": {
                    "type": ["integer", "null"],
                    "description": "Max tool calls for this event. Null for default.",
                },
                "attachments": {
                    "type": ["array", "null"],
                    "description": "Optional file attachments for the event.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "mime_type": {
                                "type": "string",
                                "description": "MIME type, e.g. audio/wav, video/mp4",
                            },
                            "uri": {
                                "type": "string",
                                "description": "File path or URL",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Optional attachment metadata",
                                "additionalProperties": True,
                            },
                        },
                        "required": ["mime_type", "uri"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["type", "content", "max_tool_calls", "attachments"],
            "additionalProperties": False,
        },
        handler=create_event,
    )

    registry.register(
        name="suspend_event",
        description=(
            "Suspend the current event and put it back in the mailbox with progress notes. "
            "Use when blocked, waiting for information, or reprioritizing."
        ),
        parameters={
            "type": "object",
            "properties": {
                "notes": {
                    "type": "string",
                    "description": "Progress notes describing current state and what remains",
                },
            },
            "required": ["notes"],
            "additionalProperties": False,
        },
        handler=suspend_event,
    )

    registry.register(
        name="complete_event",
        description="Mark the current event as completed. Always provide a brief summary.",
        parameters={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of what was done",
                },
            },
            "required": ["summary"],
            "additionalProperties": False,
        },
        handler=complete_event,
    )

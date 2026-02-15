# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
source .venv/bin/activate
pip install -e ".[dev]"

# Run
nakari                    # or: python -m nakari

# Neo4j (required for memory tools)
docker compose up -d

# Tests
pytest                    # all tests
pytest tests/test_foo.py::test_bar  # single test
pytest -x                 # stop on first failure
```

## Architecture

nakari is an autonomous AI agent built on a **permanent ReAct loop** with a **mailbox-based event system**. The loop never terminates — it sleeps when the mailbox is empty (via `await asyncio.Queue.get()`) and wakes when new events arrive.

### Core Loop (`loop.py`)

```
check_mailbox (blocks if empty) → LLM call with tools → execute tool calls → repeat
```

- LLM must always return tool calls; bare text triggers a nudge message
- Per-event `max_tool_calls` budget enforced at tool execution level (returns error in tool result, doesn't break loop)
- Errors are caught, logged, injected into context as system messages — loop never crashes

### Mailbox (`mailbox.py` + `tools/mailbox_tools.py`)

All input flows through the mailbox as `Event` objects. nakari processes one event at a time:
1. `check_mailbox` — dequeue next event (blocks if empty)
2. Process with any tools
3. `complete_event` or `suspend_event` — then back to step 1

nakari can also `create_event` (self-scheduling) and `suspend_event` (re-enqueue with progress notes).

### Tool System (`tool_registry.py` + `tools/`)

Tools are registered explicitly via `register_*_tools(registry, ...deps)` functions — no decorators. All schemas use OpenAI function calling format with `strict: True` and `additionalProperties: False`.

Four tool categories:
- **mailbox_tools** — event lifecycle (check/create/suspend/complete)
- **memory_tools** — Neo4j Cypher read/write + schema inspection + embeddings
- **reply_tool** — sole communication channel to user (via injected callback)
- **context_tools** — active context compression (separate LLM call for summarization)

### Context Management (`context.py`)

Two-tier compression:
- **Passive**: auto-truncates oldest messages when `context_max_tokens` exceeded, down to `context_target_tokens`. Respects tool_call/tool_result pairs (removes orphaned results).
- **Active**: nakari calls `compress_context` tool → separate LLM summarizes → replaces all messages with summary.

### Memory (`memory.py`)

Neo4j with **no predefined schema**. nakari decides labels, properties, and relationships via raw Cypher. `memory_schema` tool lets it inspect existing structure.

### Wiring (`__main__.py`)

Components are instantiated and wired manually. `asyncio.TaskGroup` runs the ReAct loop and CLI input loop concurrently. A seed `SYSTEM` event bootstraps the first `check_mailbox` call. Neo4j connection failure is non-fatal (warning only).

### Shared State (`loop.py: LoopState`)

`LoopState` is a mutable object shared between the loop and mailbox tools. It tracks `current_event` and `tool_call_count`. Exists as a separate object to avoid circular dependency between loop and tools.

## Code Conventions

See `AGENTS.md` for full style guide. Key points:
- `from __future__ import annotations` in every file
- Python 3.12+ union syntax (`str | None`)
- structlog for all logging (`structlog.get_logger("component")`)
- Full async pipeline — no sync I/O in the event loop
- Tools return error results instead of raising exceptions

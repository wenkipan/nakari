# AGENTS.md - Agentic Coding Guidelines for nakari

nakari is a Python agent with a persistent memory (Neo4j), a mailbox system for event handling, and a perpetual ReAct loop. Python 3.12+ with full async/await.

---

## Build, Lint, and Test Commands

```bash
# Setup
source .venv/bin/activate
pip install -e ".[dev]"

# Run the application
nakari

# Run all tests
pytest

# Run a single test file
pytest tests/test_memory.py

# Run a single test function
pytest tests/test_memory.py::test_connect

# Run tests matching a pattern
pytest -k "test_connect"

# Stop on first failure
pytest -x

# Run with coverage (if installed)
pytest --cov=src/nakari --cov-report=term-missing
```

---

## Code Style Guidelines

### General Principles

- Write clean, readable code with minimal abstraction unless necessary
- Prefer explicit over implicit
- Keep functions focused and small (< 50 lines when possible)
- Use async/await throughout (full async pipeline)

### Imports

Always use `from __future__ import annotations` at the top of every file. Organize imports in three sections:

1. Standard library (`asyncio`, `json`, `os`, `typing`, etc.)
2. Third-party packages (`structlog`, `openai`, `neo4j`, etc.)
3. Local modules (`from nakari.config import ...`)

```python
from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from openai import AsyncOpenAI

from nakari.config import Config
from nakari.models import Event
```

### Type Annotations

- Use Python 3.12+ union syntax: `str | None` instead of `Optional[str]`
- Use `dict[str, Any]` for generic dictionaries
- Always include return type annotations

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `LLMClient`, `MemoryStore`)
- **Functions/methods**: `snake_case` (e.g., `connect()`, `query()`)
- **Private attributes**: leading underscore `_driver`, `_config`
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Modules**: `snake_case` (e.g., `memory_tools.py`)
- **Enums**: `PascalCase` for enum and members (e.g., `EventType.USER_TEXT`)

### Dataclasses

Use `@dataclass` for data models. Prefer `frozen=True` for immutable config classes.

```python
@dataclass(frozen=True)
class Config:
    openai_api_key: str
    openai_model: str = "gpt-4o"

@dataclass
class Event:
    type: EventType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
```

### Enums

Use `Enum` with `str` as base for string enums:

```python
class EventType(str, Enum):
    USER_TEXT = "user_text"
    ASR_TRANSCRIPT = "asr_transcript"
```

### Logging

Use `structlog` for structured logging:

```python
import structlog
logger = structlog.get_logger("component_name")

logger.debug("action_performed", key="value")
logger.info("component_ready", uri=uri)
logger.error("operation_failed", error=str(e))
```

### Error Handling

- Use `assert` for internal invariants (preconditions that should never fail)
- Use try/except for recoverable errors
- Always log errors before returning/raising
- Return error results rather than raising when the caller should handle gracefully

```python
# For internal invariants
assert self._driver is not None, "MemoryStore not connected"

# For tool execution (return error result)
try:
    result = await tool.handler(**args)
    return ToolResult(tool_call_id="", output=result, is_error=False)
except Exception as e:
    logger.error("tool_execution_error", tool=name, error=str(e))
    return ToolResult(tool_call_id="", output=f"Error: {e}", is_error=True)
```

### Async/Await

- Use `async def` for all functions that perform I/O
- Always `await` async calls; never use `.result()` or `.wait()`

### Tool Definitions

Tools follow OpenAI function calling schema with `strict: True` and `additionalProperties: False`:

```python
registry.register(
    name="tool_name",
    description="Clear description of what the tool does.",
    parameters={
        "type": "object",
        "properties": {"param_name": {"type": "string", "description": "Description"}},
        "required": ["param_name"],
        "additionalProperties": False,
    },
    handler=async_handler_function,
)
```

### File Organization

```
src/nakari/
├── __init__.py       # Package exports
├── __main__.py       # Entry point (main())
├── cli.py            # CLI interface
├── config.py         # Configuration (Config dataclass)
├── context.py        # Context management
├── llm.py            # LLM client wrapper
├── loop.py           # ReAct loop
├── mailbox.py        # Event mailbox
├── memory.py         # Neo4j memory store
├── models.py         # Data models (Event, ToolResult, enums)
├── prompt.py         # System prompts
├── tool_registry.py # Tool registration and execution
└── tools/
    ├── __init__.py
    ├── context_tools.py
    ├── mailbox_tools.py
    ├── memory_tools.py
    └── reply_tool.py
```

---

## Environment Variables

Configure via `.env` file (see `.env.example`):

- `OPENAI_API_KEY` - OpenAI API key (required)
- `OPENAI_MODEL` - Model to use (default: `gpt-4o`)
- `NEO4J_URI` - Neo4j connection URI (default: `bolt://localhost:7687`)
- `NEO4J_USER` - Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD` - Neo4j password
- `CONTEXT_MAX_TOKENS` - Max tokens in context (default: 120000)
- `CONTEXT_TARGET_TOKENS` - Target for compression (default: 80000)
- `DEFAULT_MAX_TOOL_CALLS` - Max tool calls per event (default: 30)
- `EMBEDDING_MODEL` - Embedding model (default: `text-embedding-3-small`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

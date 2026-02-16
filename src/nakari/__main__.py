from __future__ import annotations

import asyncio

import structlog

from nakari.cli import CLI
from nakari.config import Config
from nakari.context import ContextManager
from nakari.journal import JournalStore
from nakari.llm import LLMClient
from nakari.loop import LoopState, ReactLoop
from nakari.mailbox import Mailbox
from nakari.memory import MemoryStore
from nakari.models import Event, EventType
from nakari.prompt import SYSTEM_PROMPT
from nakari.tool_registry import ToolRegistry
from nakari.tools.asr_tools import register_asr_tools
from nakari.tools.context_tools import register_context_tools
from nakari.tools.journal_tools import register_journal_tools
from nakari.tools.mailbox_tools import register_mailbox_tools
from nakari.tools.memory_tools import register_memory_tools
from nakari.tools.reply_tool import register_reply_tool
from nakari.tools.web_tools import register_web_tools
from nakari.tts import TTSPlayer, create_tts_backend


async def run() -> None:
    config = Config.from_env()

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
    )
    log = structlog.get_logger("main")

    # Core components
    mailbox = Mailbox()
    llm = LLMClient(config)
    memory = MemoryStore(config)
    journal = JournalStore()
    context = ContextManager(config)
    context.set_system_prompt(SYSTEM_PROMPT)
    loop_state = LoopState()
    registry = ToolRegistry()
    cli = CLI(mailbox, config)

    # Connect to Neo4j (optional — skip if not configured)
    try:
        await memory.connect()
    except Exception as e:
        log.warning("neo4j_unavailable", error=str(e))

    # Journal (SQLite conversation log)
    await journal.connect(config.journal_db_path)
    await journal.start_session()

    # TTS
    tts_backend = create_tts_backend(config)
    tts_player = TTSPlayer(tts_backend)

    # Register all tools
    register_mailbox_tools(registry, mailbox, loop_state, config)
    register_reply_tool(registry, cli.print_reply, tts_player)
    register_memory_tools(registry, memory, llm)
    register_context_tools(registry, context, llm)
    register_asr_tools(registry, config)
    register_journal_tools(registry, journal)
    if config.tavily_api_key:
        register_web_tools(registry, config)

    # ReAct loop
    react_loop = ReactLoop(llm, context, registry, loop_state, mailbox, journal)

    # Seed event to bootstrap the loop
    await mailbox.put(
        Event(
            type=EventType.SYSTEM,
            content="System started. You are now active. Call check_mailbox to begin.",
            max_tool_calls=5,
        )
    )

    log.info("nakari_starting")
    print("\033[36mnakari is awake. Type something to talk.\033[0m", flush=True)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(react_loop.run(), name="react_loop")
            tg.create_task(cli.input_loop(), name="cli_input")
    except* SystemExit:
        log.info("nakari_shutting_down")
    except* KeyboardInterrupt:
        log.info("nakari_interrupted")
    finally:
        await journal.close()
        await memory.close()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

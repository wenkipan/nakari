from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    openai_api_key: str
    openai_model: str
    openai_base_url: str | None
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    context_max_tokens: int
    context_target_tokens: int
    default_max_tool_calls: int
    embedding_model: str
    asr_backend: str
    asr_model: str
    asr_device: str
    audio_dir: str
    tts_backend: str
    tts_voice: str
    tts_speed: float
    tts_gptsov_url: str
    tts_gptsov_ref_audio: str
    tts_gptsov_ref_text: str
    tts_gptsov_ref_lang: str
    tts_player: str
    tavily_api_key: str
    journal_db_path: str
    log_level: str

    @classmethod
    def from_env(cls) -> Config:
        load_dotenv()
        return cls(
            openai_api_key=os.environ["OPENAI_API_KEY"],
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            openai_base_url=os.getenv("OPENAI_BASE_URL", None),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", ""),
            context_max_tokens=int(os.getenv("CONTEXT_MAX_TOKENS", "120000")),
            context_target_tokens=int(os.getenv("CONTEXT_TARGET_TOKENS", "80000")),
            default_max_tool_calls=int(os.getenv("DEFAULT_MAX_TOOL_CALLS", "30")),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            asr_backend=os.getenv("ASR_BACKEND", "whisper_api"),
            asr_model=os.getenv("ASR_MODEL", ""),
            asr_device=os.getenv("ASR_DEVICE", "auto"),
            audio_dir=os.getenv("AUDIO_DIR", "/tmp/nakari/audio"),
            tts_backend=os.getenv("TTS_BACKEND", "edge_tts"),
            tts_voice=os.getenv("TTS_VOICE", ""),
            tts_speed=float(os.getenv("TTS_SPEED", "1.0")),
            tts_gptsov_url=os.getenv("TTS_GPTSOV_URL", "http://localhost:9880"),
            tts_gptsov_ref_audio=os.getenv("TTS_GPTSOV_REF_AUDIO", ""),
            tts_gptsov_ref_text=os.getenv("TTS_GPTSOV_REF_TEXT", ""),
            tts_gptsov_ref_lang=os.getenv("TTS_GPTSOV_REF_LANG", "zh"),
            tts_player=os.getenv("TTS_PLAYER", "mpv"),
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            journal_db_path=os.getenv("JOURNAL_DB_PATH", "~/.nakari/journal.db"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

"""AI Office configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


_BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # AI — active provider
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_base_url: str = Field(default="", alias="OPENAI_BASE_URL")

    # Anthropic
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", alias="ANTHROPIC_MODEL")

    # Google Gemini
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # Ollama (local)
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.3", alias="OLLAMA_MODEL")

    # Groq
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # OpenRouter
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-4o", alias="OPENROUTER_MODEL")

    # Mistral
    mistral_api_key: str = Field(default="", alias="MISTRAL_API_KEY")
    mistral_model: str = Field(default="mistral-large-latest", alias="MISTRAL_MODEL")

    # Together AI
    together_api_key: str = Field(default="", alias="TOGETHER_API_KEY")
    together_model: str = Field(default="meta-llama/Llama-3.3-70B-Instruct-Turbo", alias="TOGETHER_MODEL")

    # DeepSeek
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    # Custom / Local (any OpenAI-compatible server)
    custom_base_url: str = Field(default="", alias="CUSTOM_BASE_URL")
    custom_model: str = Field(default="local-model", alias="CUSTOM_MODEL")
    custom_api_key: str = Field(default="", alias="CUSTOM_API_KEY")

    # LLM Tuning
    max_tokens_per_call: int = Field(default=4000, alias="MAX_TOKENS_PER_CALL")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    llm_rate_limit_delay: float = Field(default=0.5, alias="LLM_RATE_LIMIT_DELAY")
    memory_context_items: int = Field(default=30, alias="MEMORY_CONTEXT_ITEMS")

    # Agent Tuning
    tasks_per_cycle: int = Field(default=8, alias="TASKS_PER_CYCLE")
    task_timeout: int = Field(default=300, alias="TASK_TIMEOUT")
    task_delay: float = Field(default=2.0, alias="TASK_DELAY")
    cycle_delay: float = Field(default=45.0, alias="CYCLE_DELAY")
    agent_cycle_timeout: int = Field(default=600, alias="AGENT_CYCLE_TIMEOUT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Feature Flags
    enable_delegation: bool = Field(default=True, alias="ENABLE_DELEGATION")
    enable_cross_agent_context: bool = Field(default=True, alias="ENABLE_CROSS_AGENT_CONTEXT")
    enable_memory_cleanup: bool = Field(default=True, alias="ENABLE_MEMORY_CLEANUP")
    memory_max_entries: int = Field(default=1000, alias="MEMORY_MAX_ENTRIES")

    # Webhooks
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_events: str = Field(default="report,alert", alias="WEBHOOK_EVENTS")

    # Telegram
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    telegram_notify_cycles: bool = Field(default=False, alias="TELEGRAM_NOTIFY_CYCLES")
    telegram_notify_alerts: bool = Field(default=True, alias="TELEGRAM_NOTIFY_ALERTS")
    telegram_polling: bool = Field(default=False, alias="TELEGRAM_POLLING")
    telegram_polling_interval: int = Field(default=30, alias="TELEGRAM_POLLING_INTERVAL")

    # Email
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    email_from: str = Field(default="", alias="EMAIL_FROM")
    email_daily_report: bool = Field(default=True, alias="EMAIL_DAILY_REPORT")
    email_report_to: str = Field(default="", alias="EMAIL_REPORT_TO")
    email_bulk_delay: float = Field(default=1.0, alias="EMAIL_BULK_DELAY")

    # Web Browser
    web_search_results: int = Field(default=8, alias="WEB_SEARCH_RESULTS")
    web_page_cache_ttl: int = Field(default=3600, alias="WEB_PAGE_CACHE_TTL")
    web_request_timeout: float = Field(default=20.0, alias="WEB_REQUEST_TIMEOUT")
    web_max_page_chars: int = Field(default=8000, alias="WEB_MAX_PAGE_CHARS")

    # Product
    product_github_url: str = Field(
        default="https://github.com/yashab-cyber/hackbot",
        alias="PRODUCT_GITHUB_URL",
    )
    product_discord_url: str = Field(
        default="https://discord.gg/X2tgYHXYq",
        alias="PRODUCT_DISCORD_URL",
    )
    product_name: str = Field(default="HackBot", alias="PRODUCT_NAME")
    company_name: str = Field(default="HackBot Inc.", alias="COMPANY_NAME")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Persistence
    database_path: str = Field(default="data/aioffice.db", alias="DATABASE_PATH")
    state_dir: str = Field(default="data/state", alias="STATE_DIR")
    memory_dir: str = Field(default="data/memory", alias="MEMORY_DIR")
    log_dir: str = Field(default="logs", alias="LOG_DIR")

    # Schedule
    work_start_hour: int = Field(default=9, alias="WORK_START_HOUR")
    work_end_hour: int = Field(default=18, alias="WORK_END_HOUR")
    report_hour: int = Field(default=18, alias="REPORT_HOUR")
    timezone: str = Field(default="UTC", alias="TIMEZONE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True

    @property
    def base_dir(self) -> Path:
        return _BASE_DIR

    def resolve(self, rel: str) -> Path:
        p = _BASE_DIR / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()

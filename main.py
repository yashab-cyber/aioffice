"""AI Office — main entry point."""

import asyncio
import logging
import signal
import sys
import uvicorn
from pathlib import Path

from config import settings

# ── Logging setup ─────────────────────────────────────────
log_dir = Path(settings.log_dir)
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "office.log"),
    ],
)
logger = logging.getLogger("aioffice")


def main():
    logger.info("=" * 50)
    logger.info("🏢 AI OFFICE — Starting Up")
    logger.info(f"   Product: {settings.product_name}")
    logger.info(f"   GitHub:  {settings.product_github_url}")
    logger.info(f"   Discord: {settings.product_discord_url}")
    logger.info(f"   Server:  http://{settings.host}:{settings.port}")
    logger.info("=" * 50)

    if not settings.openai_api_key and settings.llm_provider == "openai":
        logger.warning("⚠️  OPENAI_API_KEY not set! Agents will run in demo mode.")
        logger.warning("   Set LLM_PROVIDER and its API key in .env")
        logger.warning("   Supported: openai, anthropic, gemini, ollama, groq, openrouter, mistral, together, deepseek")

    if not settings.telegram_bot_token:
        logger.warning("⚠️  TELEGRAM_BOT_TOKEN not set! Daily reports won't be sent.")

    uvicorn.run(
        "server:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()

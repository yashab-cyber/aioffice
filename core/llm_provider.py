"""Multi-provider LLM abstraction layer.

Supports: OpenAI, Anthropic, Google Gemini, Ollama, OpenRouter, Groq, Mistral, Together AI.
All providers expose a unified `complete(system, prompt) -> str` interface.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

logger = logging.getLogger("aioffice")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Base interface
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LLMProvider(ABC):
    """Unified interface every LLM backend must implement."""

    name: str

    @abstractmethod
    async def complete(
        self,
        system: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Return the assistant's text response."""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  OpenAI  (gpt-4o, gpt-4o-mini, o1, o3-mini, etc.)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        from openai import AsyncOpenAI
        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)
        self.model = model

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Anthropic  (claude-sonnet-4-20250514, claude-3.5-haiku, etc.)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        from anthropic import AsyncAnthropic
        self._client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        resp = await self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        # Extract text from content blocks
        return "".join(block.text for block in resp.content if hasattr(block, "text"))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Google Gemini  (gemini-2.0-flash, gemini-2.5-pro, etc.)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self._api_key = api_key
        self.model = model
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        url = f"{self._base_url}/models/{self.model}:generateContent?key={self._api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            logger.error(f"Gemini unexpected response: {data}")
            return ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Ollama  (local — llama3.3, qwen3, deepseek-r1, gemma3, etc.)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, model: str = "llama3.3", base_url: str = "http://localhost:11434"):
        self.model = model
        self._base_url = base_url.rstrip("/")

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("message", {}).get("content", "")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  OpenRouter  (routes to any model via openrouter.ai)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(self, api_key: str, model: str = "openai/gpt-4o"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = model

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Groq  (ultra-fast inference — llama-3.3-70b, mixtral, etc.)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = model

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Mistral AI  (mistral-large-latest, codestral, etc.)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MistralProvider(LLMProvider):
    name = "mistral"

    def __init__(self, api_key: str, model: str = "mistral-large-latest"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.mistral.ai/v1",
        )
        self.model = model

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Together AI  (Llama, Qwen, DeepSeek via together.ai)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TogetherProvider(LLMProvider):
    name = "together"

    def __init__(self, api_key: str, model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.together.xyz/v1",
        )
        self.model = model

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DeepSeek  (deepseek-chat, deepseek-reasoner)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
        )
        self.model = model

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Custom / Local  (any OpenAI-compatible server on a custom base URL)
#  Works with: LM Studio, text-generation-webui, LocalAI, vLLM, Kobold, etc.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CustomProvider(LLMProvider):
    name = "custom"

    def __init__(self, base_url: str, model: str, api_key: str = "no-key"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
        )
        self.model = model

    async def complete(self, system: str, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Factory — build the right provider from config
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
    "groq": GroqProvider,
    "mistral": MistralProvider,
    "together": TogetherProvider,
    "deepseek": DeepSeekProvider,
    "custom": CustomProvider,
}


def build_provider(settings) -> Optional[LLMProvider]:
    """Construct an LLM provider from the application settings."""
    provider_name = settings.llm_provider.lower()

    if provider_name not in _PROVIDERS:
        logger.error(
            f"Unknown LLM provider '{provider_name}'. "
            f"Available: {', '.join(_PROVIDERS.keys())}"
        )
        return None

    try:
        if provider_name == "openai":
            if not settings.openai_api_key:
                return None
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                base_url=settings.openai_base_url or None,
            )

        elif provider_name == "anthropic":
            if not settings.anthropic_api_key:
                return None
            return AnthropicProvider(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_model,
            )

        elif provider_name == "gemini":
            if not settings.gemini_api_key:
                return None
            return GeminiProvider(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
            )

        elif provider_name == "ollama":
            return OllamaProvider(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
            )

        elif provider_name == "openrouter":
            if not settings.openrouter_api_key:
                return None
            return OpenRouterProvider(
                api_key=settings.openrouter_api_key,
                model=settings.openrouter_model,
            )

        elif provider_name == "groq":
            if not settings.groq_api_key:
                return None
            return GroqProvider(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
            )

        elif provider_name == "mistral":
            if not settings.mistral_api_key:
                return None
            return MistralProvider(
                api_key=settings.mistral_api_key,
                model=settings.mistral_model,
            )

        elif provider_name == "together":
            if not settings.together_api_key:
                return None
            return TogetherProvider(
                api_key=settings.together_api_key,
                model=settings.together_model,
            )

        elif provider_name == "deepseek":
            if not settings.deepseek_api_key:
                return None
            return DeepSeekProvider(
                api_key=settings.deepseek_api_key,
                model=settings.deepseek_model,
            )

        elif provider_name == "custom":
            if not settings.custom_base_url:
                logger.error("Custom provider requires CUSTOM_BASE_URL to be set")
                return None
            return CustomProvider(
                base_url=settings.custom_base_url,
                model=settings.custom_model,
                api_key=settings.custom_api_key or "no-key",
            )

    except Exception as e:
        logger.error(f"Failed to initialize {provider_name} provider: {e}")
        return None

    return None


def list_providers() -> list[dict]:
    """Return metadata about all supported providers (for the GUI)."""
    return [
        {
            "id": "openai",
            "name": "OpenAI",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o3-mini", "o4-mini"],
            "needs_key": True,
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "models": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"],
            "needs_key": True,
        },
        {
            "id": "gemini",
            "name": "Google Gemini",
            "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-2.0-flash-lite"],
            "needs_key": True,
        },
        {
            "id": "ollama",
            "name": "Ollama (Local)",
            "models": ["llama3.3", "qwen3:8b", "deepseek-r1:8b", "gemma3:12b", "phi4", "mistral"],
            "needs_key": False,
        },
        {
            "id": "groq",
            "name": "Groq",
            "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
            "needs_key": True,
        },
        {
            "id": "openrouter",
            "name": "OpenRouter",
            "models": ["openai/gpt-4o", "anthropic/claude-sonnet-4-20250514", "google/gemini-2.5-flash", "meta-llama/llama-3.3-70b-instruct"],
            "needs_key": True,
        },
        {
            "id": "mistral",
            "name": "Mistral AI",
            "models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "codestral-latest"],
            "needs_key": True,
        },
        {
            "id": "together",
            "name": "Together AI",
            "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "Qwen/Qwen2.5-72B-Instruct-Turbo", "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"],
            "needs_key": True,
        },
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "models": ["deepseek-chat", "deepseek-reasoner"],
            "needs_key": True,
        },
        {
            "id": "custom",
            "name": "Custom / Local (OpenAI-compatible)",
            "models": ["any-model-name"],
            "needs_key": False,
            "needs_base_url": True,
        },
    ]

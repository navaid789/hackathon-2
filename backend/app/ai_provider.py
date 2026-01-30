import os
from pathlib import Path
from typing import Protocol, Any
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


class AIProvider(Protocol):
    def chat(self, messages: list[dict], tools: list[dict]) -> Any: ...


class OpenAIProvider:
    def __init__(self):
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def chat(self, messages: list[dict], tools: list[dict]) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self.client.chat.completions.create(**kwargs)


class GroqProvider:
    def __init__(self):
        from groq import Groq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def chat(self, messages: list[dict], tools: list[dict]) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self.client.chat.completions.create(**kwargs)


def get_provider(fallback: bool = True) -> AIProvider:
    import logging
    logger = logging.getLogger(__name__)
    provider_name = os.environ.get("AI_PROVIDER", "openai").lower()
    logger.info(f"AI provider requested: {provider_name}")
    logger.info(f"OPENAI_API_KEY set: {bool(os.environ.get('OPENAI_API_KEY'))}")
    logger.info(f"GROQ_API_KEY set: {bool(os.environ.get('GROQ_API_KEY'))}")
    try:
        if provider_name == "groq":
            return GroqProvider()
        return OpenAIProvider()
    except Exception as e:
        logger.warning(f"Primary provider ({provider_name}) failed: {e}")
        if fallback:
            try:
                if provider_name == "groq":
                    return OpenAIProvider()
                return GroqProvider()
            except Exception as e2:
                logger.warning(f"Fallback provider failed: {e2}")
        raise RuntimeError("No AI provider configured. Set OPENAI_API_KEY or GROQ_API_KEY.")

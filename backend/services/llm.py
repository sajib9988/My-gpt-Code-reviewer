from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str


class LLMProvider(Protocol):
    name: str

    async def complete(self, messages: list[LLMMessage], model: str) -> LLMResponse:
        ...

    async def stream(self, messages: list[LLMMessage], model: str) -> AsyncIterator[str]:
        ...


class OllamaProvider:
    name = "ollama"

    async def complete(self, messages: list[LLMMessage], model: str) -> LLMResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{get_settings().ollama_base_url}/api/chat",
                json={"model": model, "messages": [message.__dict__ for message in messages], "stream": False},
            )
            response.raise_for_status()
            payload = response.json()
        return LLMResponse(payload["message"]["content"], model, self.name)

    async def stream(self, messages: list[LLMMessage], model: str) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{get_settings().ollama_base_url}/api/chat",
                json={"model": model, "messages": [message.__dict__ for message in messages], "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line


class OpenRouterProvider:
    name = "openrouter"

    def _headers(self) -> dict[str, str]:
        settings = get_settings()
        return {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.frontend_url,
            "X-Title": settings.app_name,
        }

    async def complete(self, messages: list[LLMMessage], model: str) -> LLMResponse:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=self._headers(),
                json={"model": model, "messages": [message.__dict__ for message in messages], "stream": False},
            )
            response.raise_for_status()
            payload = response.json()
        return LLMResponse(payload["choices"][0]["message"]["content"], model, self.name)

    async def stream(self, messages: list[LLMMessage], model: str) -> AsyncIterator[str]:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{settings.openrouter_base_url}/chat/completions",
                headers=self._headers(),
                json={"model": model, "messages": [message.__dict__ for message in messages], "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        yield line[6:]


def provider_for(name: str) -> LLMProvider:
    providers: dict[str, LLMProvider] = {"ollama": OllamaProvider(), "openrouter": OpenRouterProvider()}
    try:
        return providers[name.lower()]
    except KeyError as error:
        raise ValueError(f"Unsupported LLM provider: {name}") from error
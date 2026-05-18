"""Model client interfaces."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class ModelClient(Protocol):
    name: str

    def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        ...


@dataclass
class OfflineModel:
    name: str = "offline"

    def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        return (
            "// OfflineModel placeholder. Replace with a real provider.\n"
            "module placeholder;\n"
            "endmodule\n"
        )


@dataclass
class OpenRouterModel:
    name: str
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    max_output_tokens: int = 8192

    def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        payload = {
            "model": self.name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": self.max_output_tokens,
        }
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://github.com/arnav/cvdp-ap"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "CVDP RTL Harness Study"),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=float(os.getenv("OPENROUTER_TIMEOUT_S", "120"))) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter request failed with HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"OpenRouter response did not contain chat content: {body}") from exc
        if not content:
            raise RuntimeError(f"OpenRouter returned empty content: {body}")
        return content


def make_model(name: str) -> ModelClient:
    if name == "offline":
        return OfflineModel()
    if name == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY must be set when model is 'openrouter'")
        model_name = os.getenv("OPENROUTER_MODEL")
        if not model_name:
            raise RuntimeError("OPENROUTER_MODEL must be set when model is 'openrouter'")
        return OpenRouterModel(
            name=model_name,
            api_key=api_key,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            max_output_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "8192")),
        )
    raise ValueError(f"Unknown model '{name}'. Add a provider in rtl_harness.models.")

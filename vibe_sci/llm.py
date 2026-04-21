"""Unified LLM client + request helpers.

Single interface for chat completions, regardless of provider. Uses the
OpenAI SDK (v1.x) against any OpenAI-compatible endpoint (OpenAI / Anthropic
/ DeepSeek / MiniMax / Moonshot / Gemini / …) when ``backend == "openai-compat"``,
and shells out to the local ``claude`` CLI when ``backend == "claude-cli"``.
No HTTP proxy, no provider-specific peak-hour logic — provider-neutral.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import subprocess
import time
from collections.abc import Sequence
from typing import Any

import openai

from .config import BackendConfig

log = logging.getLogger("vibe_sci.llm")

MAX_OUTPUT_TOKENS = 4096
DEFAULT_TEMP = 0.75
RETRY_SLEEP = (2, 4, 8, 16)  # exponential backoff
CLAUDE_CLI_TIMEOUT = 180     # seconds per claude -p call


class LLMError(RuntimeError):
    pass


# ── Concurrency ──────────────────────────────────────────────────────
#
# Provider-neutral concurrency ceilings. Chosen conservatively to avoid
# tripping rate limits on free/entry tiers. Users can override via
# ``--concurrency N`` on the CLI.
PROVIDER_CONCURRENCY: dict[str, int] = {
    "openai":     16,
    "anthropic":   8,
    "deepseek":    8,
    "minimax":     7,
    "moonshot":    4,
    "gemini":      8,
    "groq":        8,
    "together":    8,
    "xai":         8,
    "zhipu":       4,
    "claude-cli":  1,   # subprocess — serialise by default
}


def recommended_concurrency(cfg: BackendConfig) -> int:
    """Suggested asyncio.gather concurrency for the current backend."""
    return max(1, PROVIDER_CONCURRENCY.get(cfg.provider.lower(), 4))


def make_openai_client(cfg: BackendConfig) -> openai.OpenAI:
    return openai.OpenAI(api_key=cfg.api_key, base_url=cfg.openai_base)


def make_openai_async_client(cfg: BackendConfig) -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.openai_base)


def complete(
    cfg: BackendConfig,
    *,
    system: str,
    user: str,
    history: Sequence[dict] | None = None,
    model: str | None = None,
    temperature: float = DEFAULT_TEMP,
    max_tokens: int = MAX_OUTPUT_TOKENS,
    n: int = 1,
) -> tuple[str, list[dict]]:
    """Single-shot chat completion. Returns (text, updated_history).

    For n>1, returns the first choice (use `complete_batch` for ensembles).
    """
    model = model or cfg.model
    history = list(history or [])
    new_msgs = history + [{"role": "user", "content": user}]

    if cfg.backend == "claude-cli":
        return _claude_cli_complete(system, new_msgs, temperature, max_tokens)

    client = make_openai_client(cfg)
    last_err: Exception | None = None
    for attempt in range(len(RETRY_SLEEP) + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system}, *new_msgs],
                temperature=temperature,
                max_tokens=max_tokens,
                n=n,
            )
            text = resp.choices[0].message.content or ""
            new_msgs.append({"role": "assistant", "content": text})
            return text, new_msgs
        except (openai.RateLimitError, openai.APIConnectionError,
                openai.APITimeoutError, openai.InternalServerError) as e:
            last_err = e
            if attempt < len(RETRY_SLEEP):
                log.warning("LLM retry %d after %s", attempt + 1, e.__class__.__name__)
                time.sleep(RETRY_SLEEP[attempt])
            else:
                raise LLMError(f"LLM call failed after retries: {e}") from e
    raise LLMError(f"Unreachable: {last_err}")  # pragma: no cover


async def acomplete(
    cfg: BackendConfig,
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = DEFAULT_TEMP,
    max_tokens: int = MAX_OUTPUT_TOKENS,
) -> str:
    """Async single-shot completion. Used for parallel section generation.

    ``claude-cli`` backend has no native async shim — we run the subprocess
    in a thread so callers can still gather across sections.
    """
    model = model or cfg.model
    if cfg.backend == "claude-cli":
        return await asyncio.to_thread(
            lambda: complete(cfg, system=system, user=user, model=model,
                             temperature=temperature, max_tokens=max_tokens)[0]
        )
    last_err: Exception | None = None
    for attempt in range(len(RETRY_SLEEP) + 1):
        try:
            async with make_openai_async_client(cfg) as client:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}],
                    temperature=temperature, max_tokens=max_tokens, n=1,
                )
                return resp.choices[0].message.content or ""
        except (openai.RateLimitError, openai.APIConnectionError,
                openai.APITimeoutError, openai.InternalServerError) as e:
            last_err = e
            if attempt < len(RETRY_SLEEP):
                log.warning("async LLM retry %d after %s", attempt + 1, e.__class__.__name__)
                await asyncio.sleep(RETRY_SLEEP[attempt])
            else:
                raise LLMError(f"async LLM call failed after retries: {e}") from e
    raise LLMError(f"Unreachable: {last_err}")


def _claude_cli_complete(
    system: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
) -> tuple[str, list[dict]]:
    """Invoke the local ``claude`` CLI as a subprocess.

    vibe-sci's claude-cli backend flattens ``system`` + conversation into a
    single prompt; the claude CLI selects its own model (honours CLAUDE_MODEL
    env) and ignores ``temperature`` / ``max_tokens``. For tasks that need
    tighter control, switch to ``--backend openai-compat``.
    """
    parts = [f"[system]\n{system}"]
    for m in messages:
        parts.append(f"[{m['role']}]\n{m['content']}")
    prompt = "\n\n".join(parts)
    try:
        r = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "text"],
            capture_output=True, text=True, timeout=CLAUDE_CLI_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        raise LLMError(f"claude CLI invocation failed: {e}") from e
    if r.returncode != 0:
        raise LLMError(f"claude CLI exit {r.returncode}: {r.stderr[:300]}")
    text = r.stdout.strip()
    return text, messages + [{"role": "assistant", "content": text}]


def complete_batch(
    cfg: BackendConfig,
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = DEFAULT_TEMP,
    max_tokens: int = MAX_OUTPUT_TOKENS,
    n: int = 3,
) -> list[str]:
    """Return n sampled completions for ensemble voting / review."""
    model = model or cfg.model
    if cfg.backend == "claude-cli":
        # Subprocess: loop n times (no n-sampling via claude CLI).
        return [
            _claude_cli_complete(system,
                                 [{"role": "user", "content": user}],
                                 temperature, max_tokens)[0]
            for _ in range(n)
        ]

    client = make_openai_client(cfg)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=temperature, max_tokens=max_tokens, n=n,
    )
    return [c.message.content or "" for c in resp.choices]


# ── JSON extraction ───────────────────────────────────────────────────

_JSON_FENCED = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_BRACES = re.compile(r"(\{.*\}|\[.*\])", re.DOTALL)


def extract_json(text: str) -> Any:
    """Try to parse the first JSON object/array in `text`. Returns None on miss."""
    for pattern in (_JSON_FENCED, _JSON_BRACES):
        for match in pattern.finditer(text):
            chunk = match.group(1).strip()
            try:
                return json.loads(chunk)
            except json.JSONDecodeError:
                # strip control chars + retry
                cleaned = re.sub(r"[\x00-\x1F\x7F]", "", chunk)
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue
    return None

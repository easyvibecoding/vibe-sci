"""Provider auto-detection for vibe-sci.

vibe-sci is provider-neutral: it runs against any OpenAI-compatible endpoint
(pick whichever API keys the user has) or falls through to the local
``claude`` CLI as a subprocess. No Hermes runtime, no local proxy, no
``~/.hermes/config.yaml`` read — everything resolves from environment
variables and ``$PATH``.

Resolution order for ``backend="auto"``:
  1. First OpenAI-compat provider whose env var is set, in ``PROVIDER_MAP``
     iteration order (OpenAI → Anthropic → DeepSeek → MiniMax → …).
  2. ``claude`` CLI if present in ``$PATH``.
  3. ``RuntimeError`` with a helpful instruction.
"""
from __future__ import annotations

import dataclasses
import os
import shutil
from typing import Literal

Backend = Literal["auto", "claude-cli", "openai-compat"]

# provider name → (OpenAI-compat base URL, env var holding API key)
# Iteration order = auto-detection preference. OpenAI / Anthropic first
# because they have the broadest model catalogue; specialised / regional
# providers follow. Users override with --backend + --model.
PROVIDER_MAP: dict[str, tuple[str, str]] = {
    "openai":    ("https://api.openai.com/v1",           "OPENAI_API_KEY"),
    "anthropic": ("https://api.anthropic.com/v1",        "ANTHROPIC_API_KEY"),
    "deepseek":  ("https://api.deepseek.com/v1",         "DEEPSEEK_API_KEY"),
    "minimax":   ("https://api.minimax.io/v1",           "MINIMAX_API_KEY"),
    "moonshot":  ("https://api.moonshot.cn/v1",          "MOONSHOT_API_KEY"),
    "gemini":    ("https://generativelanguage.googleapis.com/v1beta/openai",
                  "GEMINI_API_KEY"),
    "groq":      ("https://api.groq.com/openai/v1",      "GROQ_API_KEY"),
    "together":  ("https://api.together.xyz/v1",         "TOGETHER_API_KEY"),
    "xai":       ("https://api.x.ai/v1",                 "XAI_API_KEY"),
    "zhipu":     ("https://open.bigmodel.cn/api/paas/v4", "ZHIPU_API_KEY"),
}

# Conservative default models per provider (as of 2026-04). Override with
# ``--model``. These should run on any account that has the base API key;
# if a user's plan doesn't include the default they'll get a clear 403/404
# from the upstream provider and can pass --model themselves.
DEFAULT_MODELS: dict[str, str] = {
    "openai":    "gpt-4.1",
    "anthropic": "claude-sonnet-4-6",
    "deepseek":  "deepseek-chat",
    "minimax":   "MiniMax-M2",
    "moonshot":  "moonshot-v1-32k",
    "gemini":    "gemini-2.0-flash",
    "groq":      "llama-3.3-70b-versatile",
    "together":  "meta-llama/Llama-3-70b-chat-hf",
    "xai":       "grok-beta",
    "zhipu":     "glm-4",
}

# Model label used when ``backend == "claude-cli"``. The ``claude`` CLI
# selects its own model based on login / CLAUDE_MODEL env, so this is only
# informational — surfaced in progress logs and returned metadata.
CLAUDE_CLI_DEFAULT_MODEL = "claude-sonnet-4-6"


@dataclasses.dataclass
class BackendConfig:
    backend: Backend
    model: str                              # resolved model
    provider: str                           # "claude-cli" or OpenAI-compat provider name
    openai_base: str | None = None       # None iff backend == "claude-cli"
    api_key: str | None = None           # None iff backend == "claude-cli"
    # ``claude_proxy_url`` is retained for call-site compatibility with
    # downstream modules ported from hermes-sci. It is always ``None`` in
    # vibe-sci — we no longer run the Anthropic-compat claude -p HTTP proxy;
    # the claude-cli backend invokes ``claude`` as a subprocess directly.
    claude_proxy_url: str | None = None


def _find_openai_provider() -> tuple[str, str, str] | None:
    """First provider with a usable API key in env → (name, base_url, api_key)."""
    for name, (base, key_var) in PROVIDER_MAP.items():
        val = os.environ.get(key_var, "").strip()
        if val and val != "***":
            return name, base, val
    return None


def _claude_cli_available() -> bool:
    return shutil.which("claude") is not None


def _no_route_error() -> RuntimeError:
    env_list = ", ".join(f"${kv[1]}" for kv in PROVIDER_MAP.values())
    return RuntimeError(
        "No LLM route available. Either set one of the provider API keys "
        f"({env_list}) or install the `claude` CLI "
        "(https://docs.claude.com/en/docs/claude-code)."
    )


def resolve_backend(
    backend: Backend = "auto",
    model_override: str | None = None,
    claude_proxy_url: str | None = None,  # accepted + ignored for compat
) -> BackendConfig:
    """Pick an LLM route and produce a concrete :class:`BackendConfig`."""
    if backend == "auto":
        found = _find_openai_provider()
        if found:
            name, base, key = found
            return BackendConfig(
                backend="openai-compat",
                model=model_override or DEFAULT_MODELS.get(name, ""),
                provider=name,
                openai_base=base,
                api_key=key,
            )
        if _claude_cli_available():
            return BackendConfig(
                backend="claude-cli",
                model=model_override or CLAUDE_CLI_DEFAULT_MODEL,
                provider="claude-cli",
            )
        raise _no_route_error()

    if backend == "openai-compat":
        found = _find_openai_provider()
        if not found:
            raise RuntimeError(
                "--backend openai-compat requires one of: "
                + ", ".join(f"${kv[1]}" for kv in PROVIDER_MAP.values())
            )
        name, base, key = found
        return BackendConfig(
            backend=backend,
            model=model_override or DEFAULT_MODELS.get(name, ""),
            provider=name,
            openai_base=base,
            api_key=key,
        )

    if backend == "claude-cli":
        if not _claude_cli_available():
            raise RuntimeError(
                "--backend claude-cli requires the `claude` CLI in PATH. "
                "Install via https://docs.claude.com/en/docs/claude-code"
            )
        return BackendConfig(
            backend=backend,
            model=model_override or CLAUDE_CLI_DEFAULT_MODEL,
            provider="claude-cli",
        )

    raise ValueError(f"Unknown backend: {backend}")


def apply_env(cfg: BackendConfig) -> None:
    """Export env so the OpenAI SDK picks up the right endpoint + key.

    No-op for ``claude-cli`` backend — that path uses subprocess, not SDKs.
    """
    if cfg.backend == "claude-cli":
        return
    if cfg.api_key:
        os.environ["OPENAI_API_KEY"] = cfg.api_key
    if cfg.openai_base:
        os.environ["OPENAI_API_BASE"] = cfg.openai_base
        os.environ["OPENAI_BASE_URL"] = cfg.openai_base


def probe_claude_proxy(url: str, timeout_s: float = 1.5) -> bool:
    """Deprecated — always returns ``False``.

    Kept so ``cli.py``'s ``--retry-backend=hybrid`` fallback path (ported
    from hermes-sci) degrades silently instead of erroring. vibe-sci has
    no HTTP proxy to probe; the claude-cli backend calls ``claude``
    directly.
    """
    return False

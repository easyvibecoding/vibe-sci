"""Unicode → LaTeX math-command conversion pass.

article.cls with the default inputenc cannot compile raw Greek or math
symbols that LLMs routinely emit in prose (``accuracy ≥ 95%``,
``ρ = 0.7``, ``x²``). This pass rewrites those characters into their
LaTeX equivalents with the right math-mode wrap:

  - A symbol in prose becomes ``$\\cmd$`` (inline math wrap)
  - A symbol already inside an existing ``$...$`` region becomes just
    ``\\cmd`` (the surrounding region already provides math mode)

Mapping data lives in ``vibe_sci/data/unicode_to_latex.yaml`` so adding
a symbol doesn't require a Python change.
"""
from __future__ import annotations

import pathlib
import re

import yaml

_DATA_PATH = pathlib.Path(__file__).parent.parent / "data" / "unicode_to_latex.yaml"

# Compiled once at import. Dict preserves YAML order so iteration
# ordering is stable across runs.
_MAPPING: dict[str, str] = {}


def _load() -> dict[str, str]:
    global _MAPPING
    if _MAPPING:
        return _MAPPING
    if not _DATA_PATH.exists():
        return {}
    raw = yaml.safe_load(_DATA_PATH.read_text(encoding="utf-8")) or {}
    # YAML file is a flat dict { "α": "\\alpha", ... }; coerce values to str.
    _MAPPING = {str(k): str(v) for k, v in raw.items() if k and v}
    return _MAPPING


# Split a string into alternating (prose, math) regions where math is
# ``$...$`` inline — greedy-but-single-line to avoid swallowing
# display math ``$$...$$`` or paragraph breaks.
_INLINE_MATH_SPLIT = re.compile(r"(\$[^$\n]*\$)")


def convert_unicode_math(s: str) -> str:
    """Replace Unicode math symbols with LaTeX commands.

    Prose regions get ``$\\cmd$`` wraps; content already inside ``$...$``
    gets bare ``\\cmd`` (no extra wrap, since surrounding ``$`` still
    provides math mode).
    """
    mapping = _load()
    if not mapping:
        return s

    parts = _INLINE_MATH_SPLIT.split(s)
    # parts[0::2] = prose (always present, possibly empty)
    # parts[1::2] = existing $...$ regions (including the $s themselves)
    for i, part in enumerate(parts):
        if not part:
            continue
        inside_math = i % 2 == 1  # odd index = $...$ region
        if inside_math:
            # Strip surrounding $ for symbol rewriting; re-wrap after
            inner = part[1:-1]
            for uc, cmd in mapping.items():
                if uc in inner:
                    inner = inner.replace(uc, cmd)
            parts[i] = f"${inner}$"
        else:
            for uc, cmd in mapping.items():
                if uc in part:
                    parts[i] = part = part.replace(uc, f"${cmd}$")
    return "".join(parts)

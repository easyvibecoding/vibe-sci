"""Coding agent — placeholder.

The design is: delegate coding-heavy steps to the ``claude`` CLI via
subprocess (the claude-cli backend in vibe_sci.config) or to the
claude-code SDK directly. Not implemented — the current pipeline always
skips the experiment stage.
"""
from __future__ import annotations


def run_coding_loop(*_args, **_kwargs):
    raise NotImplementedError(
        "vibe_sci.coder is not implemented — the current pipeline skips the "
        "experiment stage. Pass pre-computed results via --results-json or "
        "--results-md to writeup/pipeline instead."
    )

"""vibe-sci — provider-neutral autonomous research paper writer.

Public API:
    from vibe_sci import ideate, writeup, review, run_pipeline
    from vibe_sci.config import resolve_backend
    from vibe_sci.llm import make_client
"""
from __future__ import annotations

__version__ = "0.1.0"

from .ideation import ideate
from .orchestrator import run_pipeline
from .review import review
from .writeup import writeup

__all__ = ["ideate", "writeup", "review", "run_pipeline", "__version__"]

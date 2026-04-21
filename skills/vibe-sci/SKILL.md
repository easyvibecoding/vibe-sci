---
name: vibe-sci
description: Generate autonomous ML research paper drafts — ideation → LaTeX writeup → peer review → anti-hallucination numerical audit. Provider-neutral (works with the `claude` CLI, any OpenAI-compatible endpoint, or a rule-based fallback — no Hermes runtime required). Use when the user asks to "write a research paper", "generate a paper draft from this idea", "peer-review this paper", "ideate research topics", or "run an autonomous research writeup pipeline".
license: MIT
compatibility: Requires Python 3.12+ and uv. At least one LLM access route is needed — either the `claude` CLI in PATH, an OpenAI-compatible API key (OPENAI_API_KEY / MINIMAX_API_KEY / DEEPSEEK_API_KEY / MOONSHOT_API_KEY / GEMINI_API_KEY), or accept degraded rule-based output. Optional pdflatex for compiling `.tex` to PDF. Tested on macOS and Linux.
---

# vibe-sci

> **Phase 1 scaffold.** The canonical Python package and full procedural body will land in Phase 2 once the `hermes-sci` port is complete. Until then, refer to the upstream [hermes-sci SKILL.md](https://github.com/easyvibecoding/hermes-sci/blob/main/skills/hermes-sci/SKILL.md) for the operational shape — `vibe-sci` will match that flow minus the Hermes-backend-resolution steps.

## When to Use

The user asks to produce a research paper draft, peer-review an existing paper, or ideate research topics *without* requiring a specific LLM backend (no Hermes, no mandated API key). `vibe-sci` auto-detects available LLM routes and picks the best one on hand.

## Quick Reference

*Populated in Phase 2. Expected subcommands (inherited from hermes-sci):*

```bash
vibe-sci ideate    --topic "..." [--num-ideas N]
vibe-sci writeup   --idea IDX --ideas-json FILE [--results-md FILE]
vibe-sci review    --paper PATH
vibe-sci pipeline  --topic "..." [--num-ideas N] [--skip-experiment]
```

## Procedure

*Populated in Phase 2. Will follow the ideation → experiment (optional) → writeup → review → sanitize pipeline from hermes-sci, with the backend-resolution stage swapped for provider auto-detection.*

## Pitfalls

- **LLM-provider drift**: `vibe-sci` picks the highest-ranked available provider at run time. Hardcoding a prompt that only works on one provider will silently degrade when that provider isn't configured. Test each `writeup` section against at least two providers before shipping.
- **Anti-hallucination audit is a safety net, not a replacement for review**: the numerical audit catches invented metrics inside LaTeX, but cannot flag a wholly fabricated experimental setup. Always run `vibe-sci review` after `writeup`.
- **LaTeX fragility**: when pdflatex isn't available, `vibe-sci` emits `.tex` only and skips the compile step. Don't mistake the `.tex` artifact for a compiled PDF.

## Verification

1. `uv run vibe-sci --help` lists `ideate / writeup / review / pipeline` subcommands
2. `uv run vibe-sci ideate --topic "<any topic>" --num-ideas 3` emits `ideas.json` with 3 entries (falls back to rule-based placeholders if no LLM route is configured)
3. `uv run pytest tests/` passes

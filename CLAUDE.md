# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

## Status

**Phase 1 scaffold.** The Python package (`vibe_sci/`) lands in Phase 2 — a port of [`hermes-sci`](https://github.com/easyvibecoding/hermes-sci) with the Hermes-runtime coupling stripped out. Until then the CLI doesn't run; only the skill definition is live.

## Canonical skill location

`skills/vibe-sci/SKILL.md` is the single source of truth. Every host discovers it through a symlink:

- `.claude/skills/vibe-sci` → `../../skills/vibe-sci` (Claude Code, Copilot CLI, Warp)
- `.gemini/skills/vibe-sci` → same (Gemini CLI)
- `.agents/skills/vibe-sci` → same (OpenAI Codex + Warp + Cursor-via-AGENTS.md)
- `.opencode/skills/vibe-sci` → same (OpenCode)

Plugin-layer manifests at `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` reference the same canonical path — install via `npx skills add easyvibecoding/vibe-sci --skill vibe-sci` or through either plugin marketplace reaches the same file.

## When editing SKILL.md

1. Edit `skills/vibe-sci/SKILL.md` only. Every symlinked host sees the change immediately.
2. Keep the frontmatter to the four [agentskills.io](https://agentskills.io)-compliant fields only: `name`, `description`, `license`, `compatibility`. Non-standard fields (`title`, `version`, `trigger`, `dependencies`, `platforms`, `metadata`) go in `metadata:` or are dropped.
3. Bump the version in `.claude-plugin/plugin.json` + `.codex-plugin/plugin.json` together when the skill body changes materially.

## Phase 2 preview

Port target modules from `hermes-sci/skills/hermes-sci/package/hermes_sci/`:

- `orchestrator.py`, `ideation.py`, `writeup.py`, `review.py`, `coder.py`, `novelty.py`, `treesearch.py`, `verify.py` — business logic, port with minimal change
- `config.py` — **rewrite**: drop `Backend = Literal["minimax", "hybrid"]` and `~/.hermes/config.yaml` reads, replace with provider auto-detection (claude CLI → OpenAI-compat env var → rule-based fallback)
- `llm.py` — **rewrite**: keep the OpenAI-SDK-against-any-endpoint approach, drop MiniMax peak-hour throttle + hybrid claude-proxy, add `claude -p` subprocess path as an equal-citizen provider
- `sanitize/`, `prompts/`, `latex/`, `data/` — port as-is
- `hardware.py`, `progress.py`, `results.py` — port as-is

## Installing as a skill (validates the scaffold)

```bash
npx skills add easyvibecoding/vibe-sci --skill vibe-sci --list
```

Should report `1 skill` after push. Pre-push, `tests/test_skill_spec.py` catches frontmatter drift locally.

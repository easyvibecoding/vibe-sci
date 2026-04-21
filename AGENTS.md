# AGENTS.md

Repository conventions for every agent host (Claude Code, Cursor, OpenAI Codex, Gemini CLI, OpenCode, Warp).

## Canonical skill

`skills/vibe-sci/SKILL.md` is the source of truth. Each host picks it up through a symlink under `.claude/`, `.agents/`, `.gemini/`, or `.opencode/`, plus plugin-layer manifests at `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`.

Installable via:

```bash
npx skills add easyvibecoding/vibe-sci --skill vibe-sci
```

## Status

Phase 1 scaffold. The Python package port from [`hermes-sci`](https://github.com/easyvibecoding/hermes-sci) is pending — see `CLAUDE.md` for the Phase 2 module map.

## Editing rules

- Edit the canonical `skills/vibe-sci/SKILL.md`, never the symlinks.
- Keep the frontmatter to four [agentskills.io](https://agentskills.io)-compliant fields: `name`, `description`, `license`, `compatibility`.
- Bump `.claude-plugin/plugin.json` + `.codex-plugin/plugin.json` versions together on material skill-body changes.
- Run `uv run pytest tests/` before pushing — `tests/test_skill_spec.py` catches frontmatter + symlink-integrity drift.

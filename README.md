# vibe-sci

Provider-neutral autonomous ML research paper writer — **ideation → LaTeX writeup → peer review → anti-hallucination numerical audit**.

Spun out from [`hermes-sci`](https://github.com/easyvibecoding/hermes-sci) to remove the Hermes-runtime coupling (MiniMax peak-hour throttle, `~/.hermes/config.yaml` backend resolution) and conform to the open [agent skills](https://agentskills.io) standard. Works with any `claude -p` subprocess, an OpenAI-compatible endpoint, or a rule-based fallback — no single vendor required.

> **Status: scaffold only.** Core port from `hermes-sci` is tracked as Phase 2 — see [issue #1](https://github.com/easyvibecoding/vibe-sci/issues/1) once the repo is public. The SKILL.md body is a placeholder until the port lands.

## Install as a skill

```bash
npx skills add easyvibecoding/vibe-sci --skill vibe-sci
```

Or via plugin marketplace manifests (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`).

## Relationship to hermes-sci

| | `hermes-sci` | `vibe-sci` |
| --- | --- | --- |
| Backend | Hermes-resolved (MiniMax / hybrid) | Any `claude -p` subprocess, OpenAI-compat endpoint, or rule-based fallback |
| Config source | `~/.hermes/config.yaml` | Local `config.yaml` or env vars |
| Install path | `hermes skills tap add ...` | `npx skills add ...` (universal) |
| SKILL.md frontmatter | extended fields | [agentskills.io](https://agentskills.io)-compliant (4 fields) |

Both remain supported. Use `hermes-sci` inside a Hermes workflow; use `vibe-sci` anywhere else.

## License

MIT — see [LICENSE](LICENSE).

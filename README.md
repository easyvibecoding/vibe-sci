<p align="center">
  <img src="assets/logo.png" width="180" alt="vibe-sci logo — an academic paper being written by a quill whose ink trails off into a neural network"/>
</p>

<p align="center">
  <strong>English</strong> ·
  <a href="README.zh-TW.md">繁體中文</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a>
</p>

# vibe-sci

Provider-neutral autonomous ML research paper writer — **ideation → LaTeX writeup → peer review → anti-hallucination numerical audit**.

Spun out from [`hermes-sci`](https://github.com/easyvibecoding/hermes-sci) to remove the Hermes-runtime coupling (MiniMax peak-hour throttle, `~/.hermes/config.yaml` backend resolution) and conform to the open [agent skills](https://agentskills.io) standard. Works with any `claude -p` subprocess, an OpenAI-compatible endpoint, or a rule-based fallback — no single vendor required.

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

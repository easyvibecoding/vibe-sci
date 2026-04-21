<p align="center">
  <img src="assets/logo.png" width="180" alt="vibe-sci logo — an academic paper being written by a quill whose ink trails off into a neural network"/>
</p>

<p align="center">
  <strong>English</strong> ·
  <a href="README.zh-TW.md">繁體中文</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <a href="https://www.python.org/downloads/"><img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12%2B-blue"></a>
  <a href="https://github.com/easyvibecoding/vibe-sci/actions/workflows/tests.yml"><img alt="CI" src="https://github.com/easyvibecoding/vibe-sci/actions/workflows/tests.yml/badge.svg"></a>
  <a href="https://skills.sh/easyvibecoding/vibe-sci"><img alt="skills.sh" src="https://img.shields.io/badge/install-npx%20skills-black?logo=npm"></a>
  <a href="https://agentskills.io/specification"><img alt="agentskills.io compliant" src="https://img.shields.io/badge/agentskills.io-compliant-brightgreen"></a>
</p>

# vibe-sci

**An autonomous ML research paper writer** — give it a topic, get back a compilable LaTeX draft with ideation, peer review, and an anti-hallucination numerical audit. Runs against any `claude -p` subprocess or OpenAI-compatible endpoint; no single-vendor lock-in, no Hermes runtime required.

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

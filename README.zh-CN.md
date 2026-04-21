<p align="center">
  <img src="assets/logo.png" width="180" alt="vibe-sci logo — 羽毛笔在学术论文上书写,墨迹延伸为神经网络节点"/>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.zh-TW.md">繁體中文</a> ·
  <strong>简体中文</strong> ·
  <a href="README.ja.md">日本語</a>
</p>

# vibe-sci

提供者中立(Provider-neutral)的自动化 ML 研究论文写作工具 — **构思(ideation)→ LaTeX 撰写 → 同行评审 → 抗幻觉数值审计**。

由 [`hermes-sci`](https://github.com/easyvibecoding/hermes-sci) 剥离而来,去除 Hermes runtime 耦合(MiniMax 高峰时段节流、`~/.hermes/config.yaml` 后端解析),并遵循 [agent skills](https://agentskills.io) 开放标准。可搭配任何 `claude -p` subprocess、OpenAI 兼容端点、或 rule-based fallback — 不绑定单一供应商。

## 作为 skill 安装

```bash
npx skills add easyvibecoding/vibe-sci --skill vibe-sci
```

或通过 plugin marketplace manifests(`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`)。

## 与 hermes-sci 的关系

| | `hermes-sci` | `vibe-sci` |
| --- | --- | --- |
| 后端 | Hermes 解析(MiniMax / hybrid) | 任意 `claude -p` subprocess、OpenAI 兼容端点、或 rule-based fallback |
| 配置来源 | `~/.hermes/config.yaml` | 本地 `config.yaml` 或环境变量 |
| 安装路径 | `hermes skills tap add ...` | `npx skills add ...`(通用) |
| SKILL.md frontmatter | 扩展字段 | [agentskills.io](https://agentskills.io) 合规(4 个字段) |

两者同时支持。在 Hermes 工作流中使用 `hermes-sci`;其他环境使用 `vibe-sci`。

## 授权

MIT — 详见 [LICENSE](LICENSE)。

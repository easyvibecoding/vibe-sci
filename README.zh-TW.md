<p align="center">
  <img src="assets/logo.png" width="180" alt="vibe-sci logo — 羽毛筆在學術論文上書寫,墨跡延伸為神經網絡節點"/>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <strong>繁體中文</strong> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a>
</p>

# vibe-sci

提供者中立(Provider-neutral)的自動化 ML 研究論文寫作工具 — **構思(ideation)→ LaTeX 撰寫 → 同行審查 → 抗幻覺數值稽核**。

由 [`hermes-sci`](https://github.com/easyvibecoding/hermes-sci) 剝離而來,去除 Hermes runtime 耦合(MiniMax 尖峰時段節流、`~/.hermes/config.yaml` 後端解析),並遵循 [agent skills](https://agentskills.io) 開放標準。可搭配任何 `claude -p` subprocess、OpenAI 相容端點、或 rule-based fallback — 不綁定單一供應商。

## 安裝為 skill

```bash
npx skills add easyvibecoding/vibe-sci --skill vibe-sci
```

或透過 plugin marketplace manifests(`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`)。

## 與 hermes-sci 的關係

| | `hermes-sci` | `vibe-sci` |
| --- | --- | --- |
| 後端 | Hermes 解析(MiniMax / hybrid) | 任何 `claude -p` subprocess、OpenAI 相容端點、或 rule-based fallback |
| 設定來源 | `~/.hermes/config.yaml` | 本機 `config.yaml` 或環境變數 |
| 安裝路徑 | `hermes skills tap add ...` | `npx skills add ...`(通用) |
| SKILL.md frontmatter | 擴充欄位 | [agentskills.io](https://agentskills.io) 合規(4 個欄位) |

兩者皆持續支援。在 Hermes 工作流中使用 `hermes-sci`;其他環境用 `vibe-sci`。

## 授權

MIT — 詳見 [LICENSE](LICENSE)。

<p align="center">
  <img src="assets/logo.png" width="180" alt="vibe-sci ロゴ — 羽根ペンが学術論文を書き、そのインクの軌跡がニューラルネットワークのノードへと変わる"/>
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.zh-TW.md">繁體中文</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <strong>日本語</strong>
</p>

# vibe-sci

プロバイダ中立(Provider-neutral)な自律型 ML 研究論文ライター — **アイデア生成 → LaTeX 執筆 → ピアレビュー → 反ハルシネーション数値監査**。

[`hermes-sci`](https://github.com/easyvibecoding/hermes-sci) からスピンアウトし、Hermes ランタイム結合(MiniMax ピーク時間スロットリング、`~/.hermes/config.yaml` バックエンド解決)を取り除き、オープンな [agent skills](https://agentskills.io) 標準に準拠させました。`claude -p` サブプロセス、OpenAI 互換エンドポイント、またはルールベースのフォールバックと連携します — 単一ベンダーに依存しません。

## スキルとしてインストール

```bash
npx skills add easyvibecoding/vibe-sci --skill vibe-sci
```

またはプラグインマーケットプレイスのマニフェスト(`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`)経由。

## hermes-sci との関係

| | `hermes-sci` | `vibe-sci` |
| --- | --- | --- |
| バックエンド | Hermes 解決(MiniMax / hybrid) | 任意の `claude -p` サブプロセス、OpenAI 互換エンドポイント、またはルールベース |
| 設定ソース | `~/.hermes/config.yaml` | ローカル `config.yaml` または環境変数 |
| インストール方法 | `hermes skills tap add ...` | `npx skills add ...`(汎用) |
| SKILL.md frontmatter | 拡張フィールド | [agentskills.io](https://agentskills.io) 準拠(4 フィールド) |

両方とも引き続きサポートされます。Hermes ワークフロー内では `hermes-sci` を、それ以外では `vibe-sci` をご利用ください。

## ライセンス

MIT — [LICENSE](LICENSE) を参照。

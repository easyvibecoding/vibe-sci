---
name: vibe-sci
description: Generate autonomous ML research paper drafts — ideation → LaTeX writeup → peer review → anti-hallucination numerical audit. Provider-neutral (works with the `claude` CLI, any OpenAI-compatible endpoint, or a rule-based fallback — no Hermes runtime required). Use when the user asks to "write a research paper", "generate a paper draft from this idea", "peer-review this paper", "ideate research topics", or "run an autonomous research writeup pipeline".
license: MIT
compatibility: Requires Python 3.12+ and uv. At least one LLM route — either the `claude` CLI in PATH, or an OpenAI-compatible API key (OPENAI_API_KEY / ANTHROPIC_API_KEY / DEEPSEEK_API_KEY / MINIMAX_API_KEY / MOONSHOT_API_KEY / GEMINI_API_KEY / GROQ_API_KEY / TOGETHER_API_KEY / XAI_API_KEY / ZHIPU_API_KEY). Optional pdflatex for compiling `.tex` to PDF; optional pypdf / pymupdf4llm for reviewing PDFs. Tested on macOS and Linux (Python 3.12 / 3.13).
---

# vibe-sci

Provider-neutral autonomous ML research paper writer. Spun out from `hermes-sci` to remove the Hermes-runtime coupling — no local proxy, no `~/.hermes/config.yaml`, no vendor lock-in.

## When to Use

The user asks to:

- **"write a research paper"** / "generate a paper draft from this idea" → `vibe-sci writeup` or `vibe-sci pipeline`
- **"peer-review this paper"** / "review this .pdf" / "score my paper draft" → `vibe-sci review`
- **"ideate research topics around X"** → `vibe-sci ideate`
- **"run an autonomous research writeup pipeline"** → `vibe-sci pipeline`

…without requiring a specific LLM backend. vibe-sci auto-detects whichever provider env var is set, falling through to the `claude` CLI on PATH.

## Quick Reference

### Review a paper (fastest way to verify your install)

```bash
vibe-sci review --paper <path.md|path.pdf> --backend claude-cli --ensemble 1 \
  --output <review.json>
```

Emits `<review.json>` with `Summary`, `Strengths` / `Weaknesses` lists, the 7 NeurIPS sub-scores (Originality / Quality / Clarity / Significance / Soundness / Presentation / Contribution — each 1-4), `Overall` (1-10), `Confidence` (1-5), and `Decision` (`Accept` | `Reject`).

- `--ensemble 1` → ~25s on Apple Silicon via `claude` CLI (single-shot)
- `--ensemble 5` → NeurIPS-style median aggregation (5× serial cost on claude-cli; parallel on openai-compat)

### Ideate research topics

```bash
vibe-sci ideate --topic "efficient attention mechanisms" --num-ideas 5 \
  -o ideas.json
```

### Generate a paper from an idea (with numerical audit)

```bash
vibe-sci writeup --ideas-json ideas.json --idx 0 \
  --results-json experiment_results.json \
  -o out_dir/
```

### Full pipeline (ideate → writeup → review)

```bash
vibe-sci pipeline --topic "..." --num-ideas 3 -o out_dir/
```

## Procedure

1. **Pick a backend.** Default `--backend auto` resolves in this order:
   - First provider with an env var set (OpenAI → Anthropic → DeepSeek → MiniMax → Moonshot → Gemini → Groq → Together → xAI → Zhipu)
   - `claude` CLI if on PATH
   - `RuntimeError` with the full env-var list if neither.

2. **For review-only** you don't need ideation or writeup. Call `vibe-sci review --paper ...` on any existing `.pdf` (needs `pypdf` or `pymupdf4llm`) or plain-text `.md` / `.txt`.

3. **For writeup with anti-hallucination audit**, pass experiment results as `--results-json` (preferred — structured schema in `vibe_sci/data/results_schema.json`). Every numeric claim in the generated LaTeX is then cross-checked against that JSON; unverified numbers can be highlighted red in the PDF with `--annotate-unverified`.

4. **If `pdflatex` is missing**, `writeup` still emits a complete `.tex` (you can compile it elsewhere) but skips the PDF and the log-driven retry pass.

5. **For the fastest quality pass on a draft**, run `vibe-sci review --ensemble 3` against the `.tex` or a plain-text dump of your draft — the median-of-3 aggregation catches issues a single reviewer misses.

## Pitfalls

- **`claude-cli` backend is serial.** `complete_batch` loops `n` subprocesses, so `--ensemble 5` takes roughly 5× as long as `--ensemble 1`. Switch to `--backend openai-compat` when you need real parallelism.
- **`claude-cli` ignores `temperature` and `max_tokens`.** The `claude` CLI picks its own model (honours `CLAUDE_MODEL` env var) and decoding params. Use `--backend openai-compat` for tight decoding control.
- **Papers over ~60k characters are truncated** in review (`max_chars` parameter). Short papers get full fidelity; very long preprints lose late-section content. Split them or bump `max_chars` in the library API.
- **The `experiment` stage is skipped.** `vibe_sci.coder.run_coding_loop` is not implemented; always pass pre-computed results via `--results-json` / `--results-md`.
- **LaTeX citation filtering is aggressive.** The writeup pipeline drops `\cite{...}` keys not present in the bundled `references.bib`. Add your own bib entries before running, or post-edit the emitted `.tex`.

## Verification

1. `uv run vibe-sci --help` — lists `ideate / writeup / validate-results / review / pipeline` subcommands.

2. `uv run pytest tests/` — 9 scaffold guardrails pass (frontmatter compliance, host-symlink integrity, plugin manifest agreement).

3. **End-to-end smoke test** (requires `claude` CLI):

   ```bash
   mkdir -p /tmp/vibe-sci-smoke
   cat > /tmp/vibe-sci-smoke/paper.md <<'EOF'
   # Test Paper: Minimal Attention Variant
   ## Abstract
   We propose replacing softmax attention with sigmoid gating, yielding a 3.2%
   perplexity reduction on WikiText-103 at 124M parameters.
   ## Method
   Replace softmax(QK^T/√d) with σ((QK^T - b)/√d) for a learned per-head bias b.
   ## Results
   | Benchmark    | Baseline | Ours |
   |--------------|----------|------|
   | WikiText-103 | 15.8     | 15.3 |
   | enwik8 bpb   | 1.06     | 1.04 |
   ## Limitations
   Single seed, single model size, no comparison against other attention variants.
   EOF
   uv run vibe-sci review --paper /tmp/vibe-sci-smoke/paper.md \
     --backend claude-cli --ensemble 1 -o /tmp/vibe-sci-smoke/review.json
   ```

   **Expected:** `✅ review → /tmp/vibe-sci-smoke/review.json  overall=<N> decision=<Accept|Reject>` within ~30 seconds; the JSON contains non-null `Overall` (1-10) and a `Decision` field. A correctly-functioning reviewer will flag the intentionally weak empirical section (single seed, no CI, no attention-variant baselines) in `Weaknesses` — see `references/example_review.json` in this skill directory for a captured reference output.

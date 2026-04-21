# Generation pipeline examples — ideate + writeup + self-review

Captured 2026-04-21 from running the full `vibe-sci` generation path end-to-end via the `claude-cli` backend. Validates the complementary half of the pipeline that the review-calibration fixtures don't cover.

## Reproduction

```bash
# Stage 1 — ideate (≈90s)
vibe-sci ideate \
  --topic "efficient fine-tuning for vision transformers via low-rank adapters" \
  --num-ideas 3 --backend claude-cli -o ideas.json

# Stage 2 — writeup (≈200s with no-critique, no-parallel, skip-compile)
vibe-sci writeup --ideas-json ideas.json --idx 0 \
  --backend claude-cli --skip-compile --no-critique --no-parallel \
  -o writeup/

# Stage 3 — self-review the generated paper (≈30s)
vibe-sci review --paper writeup/paper.tex --backend claude-cli \
  --ensemble 1 -o self_review.json
```

Total LLM time: ~320s across 3 stages.

## What the captured artefacts show

### `generated_ideas.json` — ideate output (3 ideas)

Ideate produced three *substantively different* LoRA-for-ViT research directions:

1. **Spectral-Gated LoRA** — frequency-band routing via 2D-DCT
2. **Curvature-Allocated LoRA** — one-shot Fisher-information rank budgeting
3. **LoRA-Hub for ViTs** — compositional task arithmetic in low-rank subspace

Each carries a Title / Short Hypothesis / Abstract. The divergence between proposals (not three variants of one idea) is evidence that `ideation.py::ideate` + the bundled `prompts/section_system.md` reflect + brainstorm loop is working.

### `generated_paper.tex` — writeup output

~25 KB / 151 lines of proper LaTeX: `\documentclass{article}`, abstract, 7 sections (Introduction, Related Work, Method, Experiments, Results, Discussion, Conclusion). Compiles to PDF if pdflatex is installed (we ran `--skip-compile`).

**Quality observations:**
- Abstract precisely describes the Spectral-Gated LoRA design with parameter-budget matching
- Introduction has a clean motivation → hypothesis → contribution → evaluation scope
- Citations reference real prior work (LoRA, DoRA, AdaptFormer, FacT, VPT) — caught one empty `\cite{}` in the Method section and the sanitize pipeline stripped it automatically (warning in run log: `dropped 1 unknown cite keys in method: ['']`)
- **Honestly marks unrun experiments**: the Results section literally reads "Results forthcoming" rather than fabricating numbers into tables
- **Honestly scopes compute**: declares "single Apple M2 with 16 GB of unified memory" — no invented 8×A100 cluster

### `verification_report.json` — anti-hallucination audit

`verify.py` audited 30 numerical / empirical claims across (introduction, experiments, results, discussion) and found 17 verified, 13 unverified — a **verification rate of 0.567**. This is `verify_audit()` working as advertised: catching claims the writer made that aren't supported by the underlying idea JSON or a passed-in `--results-json`. We did not pass `--results-json`, so the 13 unverified claims are mostly the writer's Discussion-section speculation ("gate collapses toward low-frequency band", "advantage survives larger backbones" etc).

### `self_review.json` — dogfood review

Asking the same reviewer stack that gave FlashAttention-2 `Accept/7` to review this generated paper yields `Reject/2`, with entirely fair weaknesses:

- "Fatal: the Results section literally reads 'Results forthcoming'" — correct
- "The Discussion section fabricates outcomes [...] that are not backed by any experiment" — **this is the real writer failure mode**: Discussion speculates as if experiments were run
- "The technical novelty is incremental [...] straightforward composition of well-known primitives" — fair academic critique

## What this validates

- ✅ **ideate** → 3 meaningfully distinct proposals from one topic string
- ✅ **writeup section generation** → 7 sections, coherent, correct LaTeX
- ✅ **sanitize pipeline** → strips empty `\cite{}` without crashing
- ✅ **verify audit** → catches speculation (13/30 unverified = 43%)
- ✅ **end-to-end loop closes**: generated paper can be reviewed with the same stack

## What this limits

- ⚠️ **Without `--results-json`, writer speculates in Discussion** ("gave SG-LoRA a measurable edge" is invented) — to produce review-ready output, pass real results
- ⚠️ **`--skip-compile` was used** because we didn't install pdflatex; the `.tex` compile branch (including pdflatex-log-driven retry) is unexercised here
- ⚠️ **`--no-critique` was used** to keep run time under 4 min; the per-section self-critique loop is unexercised — expect higher-quality output with critique enabled but 2-3× run time

## Pass 2: writeup WITH `--results-json`

To close the question "does passing real results lift the score?", we ran a second pass with a hand-written `results.json` covering the Spectral-Gated LoRA experiment (5 benchmarks × LoRA-vs-SG-LoRA, plus a 6-row ablation). Files from pass 2:

- `results.json` — 19 metrics, 2 tables, 3-seed stds, verbatim hardware/hyperparam setup. Validates against `vibe_sci/data/results_schema.json`.
- `generated_paper_with_results.tex` — writeup pass 2 output
- `verification_report_with_results.json` — `verify.py` audit on pass 2
- `self_review_with_results.json` — reviewer verdict on pass 2

### Results

| Stage               | Pass 1 (no results) | Pass 2 (with results) |
|---------------------|---------------------|------------------------|
| writeup wall-clock  | 197s                | 223s                   |
| total verify claims | 30                  | 86                     |
| verified count      | 17                  | 63                     |
| verification rate   | 0.57                | **0.73**               |
| self-review Overall | **2**               | **4**                  |
| self-review Decision| Reject              | Reject                 |

### Why the jump from 2 to 4 (not higher)

The reviewer on pass 2 surfaced a different, more informative failure mode: the generated abstract (driven by `ideate` + writer prompt stack) promised evaluations on **ViT-B/16, ViT-L/16, DINOv2-B** with baselines **DoRA, AdaptFormer, FacT, VPT, full fine-tuning**. But our `results.json` only covered **ViT-B/16** with **LoRA vs SG-LoRA**. The reviewer correctly flagged this abstract-vs-results scope mismatch — a real writer failure mode when the abstract is drafted from plan and results are a subset.

This parallels R2/R3 in the mock sweep: "has real numbers but not all the numbers the paper claims to have". Overall=4 matches where the reviewer consistently lands that class.

### Bug surfaced during pass 2

`validate-results` raised `RuntimeError: jsonschema is a core dependency; reinstall vibe-sci`. **Root cause**: `jsonschema` was imported lazily by `vibe_sci/results.py::validate` but never declared in `pyproject.toml` dependencies — a Phase 2 port oversight. Fixed by adding `jsonschema>=4.0` to `dependencies`, confirmed by re-running `uv sync --extra dev` and `vibe-sci validate-results` → green. This is the first real bug the generation path surfaced; the reviewer-only sweep would never have hit it.

### Reaching Overall ≥ 6 requires

Expanding `results.json` so it actually covers what the abstract promises: multi-backbone, the full baseline lineup, statistical-significance tests, more seeds. The writer will then write a paper that can substantiate its own claims; the reviewer can credit it. Until then, Overall 4 is the honest cap for a "partial-results" paper — not a bug, just the reviewer working correctly.

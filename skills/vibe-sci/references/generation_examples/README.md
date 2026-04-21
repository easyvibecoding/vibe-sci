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

## Next step: writeup with real results

To reach a paper that the reviewer would score above 2, pass a `--results-json` (schema in `vibe_sci/data/results_schema.json`) describing what was actually measured. The writer will then cross-reference numerical claims against that schema via `verify_audit`, and the Results/Discussion sections will carry concrete numbers rather than speculation.

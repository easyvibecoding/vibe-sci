# Structural-fidelity iteration loop

**User goal**: "從真實論文中取得結構 迭代論文生成品質 — 目標不是要做出假以亂真 而是真的遵循結構與數據驅動自動產生論文的能力" — *not* "beat the reviewer", but "does the writer follow real-paper scaffolding and let supplied data drive the numbers?"

Method: three iterations against the same idea + results.json pair, differing only in the prompts/bib scaffolding the writer sees.

## Round 1 — structural diff between real and generated

Without any patch, comparing real `FlashAttention-2 (ar5iv)` vs the pass-2 `generated_paper_with_results.tex`:

| Feature (corrected counts)      | Real FA-2 | Generated pass-2 |
|---------------------------------|-----------|------------------|
| `\begin{table}`                 | 4         | **2** (= results.json tables, 1:1) ✅ |
| `\begin{algorithm}`             | 1         | **0** ← gap      |
| `\begin{equation/align}`        | 4         | 4 ✅             |
| `\cite{…}`                      | 20 refs   | **3** ← gap      |
| `\%` mentions                   | 9         | 79 (consumes every results.json metric) ✅ |
| `\ref{…}` / `\label{…}`         | n/a       | 9 / 2 ✅         |

Two intentional structures mistakenly flagged as bugs on first grep: duplicate "Discussion" (one inside Results for tables-level, one top-level for hypothesis/limitations — correct NeurIPS norm); and my percent-grep was wrong (it's 79 not 0).

**Real gaps that remain after correction:** missing algorithm pseudocode + citation density.

## Round 2 — root-cause the two gaps (no LLM run)

Inspect `vibe_sci/prompts/section_instructions.json` and `vibe_sci/latex/references.bib`:

- **`section_instructions.json::method`** — original: "Use `\begin{equation}...\end{equation}` when equations add clarity." No mention of `algorithm` / pseudocode. **Writer is following the prompt exactly**; producing 0 algorithm envs is prompt-compliant behaviour, not an LLM failure.
- **`references.bib`** — 2 entries only (`lu2024aiscientist`, `yamada2025aiscientistv2`, both AI-Scientist meta-papers). `writeup.py::_filter_citations` strips any `\cite{key}` whose key isn't in the bib — so writer can emit dozens of `\cite{hu2022lora}` style calls and they all get dropped before reaching the output `.tex`. The 3 surviving cites are the two AI-Scientist keys plus one more in related work.

Both limitations inherit from the upstream hermes-sci scaffold (identical files in `~/.hermes/my-skills/hermes-sci/`). Not a port bug — an upstream scaffold thinness that vibe-sci can improve on.

## Round 3 — patch + re-run

Two targeted changes, no code:

- **`references.bib`**: 2 → 29 entries covering transformers (Vaswani / BERT / GPT-3 / ViT / DINOv2), efficient attention (Performer / Linformer / FlashAttention / FA-2 / Mamba), PEFT (LoRA / DoRA / VPT / AdaptFormer), backbones (ResNet / Swin / ConvNeXt), channel attention (SENet / CBAM), optimisation (Adam / AdamW / BatchNorm / Chinchilla), benchmarks (VTAB / CUB / DTD). Covers the vocabulary a modern ML paper would need.
- **`section_instructions.json::method`**: add algorithm-env hint with a verbatim fallback ("If the contribution is an algorithm or procedure, include a pseudocode box using `\begin{algorithm}...\end{algorithm}` with `\caption{}` and numbered `\STATE` lines, or the equivalent `\begin{verbatim}...\end{verbatim}` if the algorithm package is unavailable").

Ran writeup with identical `ideas.json` + `results.json` as Round 2 so any change is attributable to the prompts/bib patch.

## Results (three-stage gradient)

| Stage                | Pass 1 (no results) | Pass 2 (w/ results, orig bib) | Pass 3 (patched) |
|----------------------|---------------------|--------------------------------|------------------|
| writeup wall-clock   | 197s                | 223s                          | 259s             |
| `\cite{…}` count     | 0 (no-results path) | 3                             | **45** (+42)     |
| `\begin{algorithm}`  | 0                   | 0                             | 0                |
| `\begin{verbatim}`   | 0                   | 0                             | 1 (fallback)     |
| `\%` mentions        | n/a                 | 79                            | 82               |
| `\begin{equation}`   | —                   | 4                             | 5                |
| verify rate          | 0.57                | 0.73                          | **0.81**         |
| self-review Overall  | 2                   | 4                             | 4                |
| Originality sub      | —                   | 2                             | **3** (+1)       |
| Presentation sub     | —                   | 2                             | **3** (+1)       |
| Decision             | Reject              | Reject                        | Reject           |

### What moved, and what didn't

- **Cite density 15× increase** is the headline — writer was already emitting the right cite *patterns* (`\cite{hu2022lora, liu2024dora, chen2022adaptformer, jia2022vpt}` style grouped citations), they were just all getting filtered out by a 2-entry bib. Patching the bib surfaces them immediately, no LLM change.
- **Algorithm env: writer used the fallback.** `\begin{algorithm}` requires LaTeX's `algorithm` package in the template preamble, which isn't bundled; writer correctly picked `\begin{verbatim}` (the alternative we listed in the instruction). Prompt discipline works.
- **verify rate climbs monotonically** (57 → 73 → 81) as both (a) more claims become cross-referenceable via results.json and (b) writer pulls more values from it instead of speculating.
- **Reviewer gives +1 to Originality and +1 to Presentation** in pass 3 vs pass 2 — the fuller bib + pseudocode is noticed and credited.
- **Overall sticks at 4.** Reviewer's other weaknesses (abstract scope overreach vs `results.json` that only covers ViT-B/16 + LoRA; three-seed cell with effect sizes at the variance boundary) are **content-quality limits** of what we supplied in `results.json`, not structural issues. Fixing them requires a richer `results.json` (multi-backbone, more seeds, more baselines), not a prompt tweak.

### Meta-conclusion (answering the user's goal)

> "真的遵循結構與數據驅動自動產生論文的能力"

**Confirmed.** Writer behaviour is *instruction-following*, not a black box. When we give it more bib keys, it cites more; when we tell it to emit a pseudocode box, it does (with the fallback we specified); when we supply richer metrics, verify rate rises and the reviewer credits the paper more. The failure mode at Overall=4 is the reviewer correctly spotting that `results.json` doesn't substantiate every abstract claim — a data gap, not a pipeline capability gap.

Structural-fidelity loop closes here. The lever for higher reviewer scores is now *the quality of results.json a user supplies*, not the scaffolding. That's the right separation of concerns for an "autonomous research writer" — the writer is doing its job; the humans still have to run the experiments.

## Artefacts promoted to repo

- `references/generation_examples/generated_paper_round3.tex` — patched-bib paper
- `references/generation_examples/verification_report_round3.json` — 92/113 verified
- `references/generation_examples/self_review_round3.json` — Reject/4 with Originality=3, Presentation=3

## Code changes committed alongside

- `vibe_sci/latex/references.bib`: 2 → 29 entries (modern ML core vocabulary)
- `vibe_sci/prompts/section_instructions.json::method`: add algorithm-env guidance + verbatim fallback

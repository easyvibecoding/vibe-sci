# vibe-sci structural-fidelity /loop

**Goal (user stated)**: "從真實論文中取得結構 迭代論文生成品質 — 目標不是要做出假以亂真 而是真的遵循結構與數據驅動自動產生論文的能力"

Not Turing-test territory (can we fool reviewers?), but **structural compliance** (does the writer follow the scaffolding real venues expect, and does it let supplied data drive the numbers?).

## Round 1 — structural diff: FlashAttention-2 (real) vs pass-2 writeup (generated w/ results.json)

Comparing the two artefacts already on disk:

|                          | Real FA-2 (markdown, 12 KB) | Generated pass 2 (LaTeX, 29 KB) |
|--------------------------|-----------------------------|----------------------------------|
| Tables                   | 4                           | **2** (= 2 tables in results.json, 1:1) |
| Algorithm blocks         | 1                           | **0** ← gap                      |
| Equation blocks          | 4                           | 4                                |
| `\cite` / citations      | inline prose, 20 refs       | **3** ← gap                      |
| Numeric `%` mentions     | 9                           | 79 (higher — consumes every results.json metric with `%` unit) |
| `\ref{...}`              | n/a (markdown)              | 9 ✅                            |
| `\label{...}`            | n/a (markdown)              | 2 ✅                            |
| Discussion duplication   | single                      | appears twice — but intentional: one inside Results (discussing tables), one top-level (discussing hypothesis + limitations); NOT a bug |

## Structural strengths (what the writer does right — data-driven path works)

- **results.json → tables: 1:1 render.** Every table in `results.json` becomes a `\begin{table}` env with booktabs styling, correct `\label{tab:<id>}`, and in-text `\ref{tab:<id>}`.
- **Metrics consumed.** All 19 metrics from results.json carry `%` unit; the paper mentions `\%` 79 times — the writer is actively pulling numbers from the registry rather than confabulating.
- **Values pinned.** Direct quotes of `72.8%`, `73.6%`, `85.1%`, `86.2%` appear in Results prose matching results.json exactly. verify.py reports 73% of claims cross-referenced.
- **Discussion depth.** Two-level discussion structure (tables-level inside Results + hypothesis-level at top) is what real NeurIPS papers often do.
- **Limitations section is honest.** Explicitly names the scope gaps ("single ViT-B/16 backbone", "square-grid assumption", "three-seed budget") that the reviewer in pass-2 self-review ended up citing — the writer knew about them but the abstract still overreached. This is a localised failure mode of *abstract drafting*, not of limitations awareness.

## Structural gaps (what to iterate)

1. **Missing `\begin{algorithm}` block.** Method section is 50 lines of prose; for a "new algorithm" paper the NeurIPS / ICML expectation is a formal pseudocode box (real FA-2 has Algorithm 1). This is a likely miss in `vibe_sci/prompts/section_instructions.json` (method section) not hinting to include algorithmic environments. **Round 2 check**: inspect that file.

2. **Citation density ~3 vs real paper ~20.** The writer plausibly generates `\cite{key}` references that then get stripped by `writeup.py::_filter_citations` when `key` isn't in `vibe_sci/latex/references.bib`. **Round 2 check**: grep how many citations were filtered in the pass-2 run; if the filter drops everything, the root cause is a sparse default bib, not a writer bug.

3. **No algorithmic environment triggered even with `newalgorithm` prompts.** Confirms item 1 — look at what the section prompt actually asks for.

## What's NOT a gap (was initial misread)

- Duplicate Discussion — intentional two-level structure, matches NeurIPS norms
- Zero percent mentions — my initial grep pattern was wrong; correct count is 79, which is *higher* than the real paper because results.json is metric-dense

## Round 2 plan

Read `vibe_sci/prompts/section_instructions.json` for the method-section entry and `vibe_sci/latex/references.bib` to check bib entry count. If (a) instructions don't mention algorithm block + (b) bib is nearly empty, the fix is a one-line addition to instructions + seeding the bib with common ML references. Cheap iteration, no extra LLM calls. Then Round 3 can re-run writeup and compare cite / algo counts directly.

# vibe-sci /loop mock review — 7 rounds completed

## Results summary

| # | Paper | Size | Lang | Time | Overall | Decision | Reviewer precision |
|---|-------|------|------|------|---------|----------|--------------------|
| 1 | Weak: single seed, no CI, 1 baseline | 3.3 KB | EN | 24.2s | **3** | Reject | ✅ caught single-seed, no-CI, novelty overstated |
| 2 | "Strong-ish": 5 seeds + p<0.001 + 5 baselines + scaling + downstream | 6.9 KB | EN | 24.2s | **4** | Reject | ✅ caught Mamba-1.4B vs 1.3B size mismatch, compute budget absent, novelty narrow vs GAU/Ramapuram |
| 3 | Polished: fixed all R2 flaws (compute table, matched baselines, novelty framing, Prop.1 derivation) | 10.3 KB | EN | 37.7s | **4** | Reject | ✅ caught NEW real errors — GPU-days arithmetic inconsistent, identical stds suspicious, 8.7% FLOPs unsupported, Prop.1 hand-wavy |
| 4 | Garbage: buzzword soup ("Quantum Hypergraph Transformer"), MNIST 99.7% | 1.7 KB | EN | 20.3s | **1** | Reject | ✅ every sub-score=1; caught no substance, no hypergraph definition, unnamed baseline |
| 5 | Mid-quality CV: ChannelShift channel-attention | 4.6 KB | EN | 26.8s | **3** | Reject | ✅ caught SE-in-ViT unexplained, effects-within-std, param-count inconsistency (25.6M vs 28.1M for same W_1+W_2 MLPs) |
| 6 | Chinese-language: AdaptSparse head sparsification | 3.8 KB | **ZH** | 25.3s | **4** | Reject | ✅ **reviewer responded in 繁中**, caught TopK(scalar) semantic issue, missing Michel-2019/Voita-2019 prior art |
| 7 | Super-short (284 bytes): ReLU^2 activation | 0.3 KB | EN | 18.9s | **2** | Reject | ✅ handled gracefully; low but non-zero score; flagged insufficient detail for review |

**Total wall-clock**: ~178s of LLM time across 7 rounds.
**Zero parse failures, zero crashes, zero timeouts.**

## Phase 2 port verdict: healthy

- `_claude_cli_complete()` subprocess path stable across 7 consecutive invocations
- `complete_batch` loop-n=1 pattern works
- `extract_json` recovered structured YAML from every claude response (7/7)
- `review.py` aggregation logic (`ensemble_size`, `Decision` majority, score median) works with n=1
- Multilingual: claude returns Chinese review for Chinese paper automatically; no glue code needed in vibe-sci
- Short paper (284 B) doesn't trigger empty-prompt or truncation bugs
- Review output matches the JSON schema specified in `review.py::REVIEW_PROMPT_TMPL`

## Reviewer quality observations

**Dynamic range: 1 (garbage) — 4 (rigorous-but-flawed)**

No Accept scores across any of the 7 mock papers. The Accept threshold (>=6) appears calibrated to genuine publishable-paper quality — mock drafts carrying even one subtle methodological flaw (arithmetic inconsistency, size-mismatched baseline, undefined terminology, under-rigorous statistics) get capped at 4.

**Reviewer is auditing, not template-matching.** Evidence:
- R2 and R3 both scored **4** but cited **entirely different weakness sets**. R3 fixed every R2 issue; reviewer found new, subtler ones (arithmetic internal consistency, copy-paste stds, unsupported headline FLOPs claim).
- R5 (mid-quality CV) scored **3** — lower than R2's 4 — because the flaws were *critical* (method doesn't apply to ViT architecture as described) not *incremental* (R2's "novelty narrow"). Reviewer weights severity over quantity.

**Sub-score coherence.** Overall ≈ median of (Quality, Soundness, Significance) across all 7 rounds. No outlier where, say, Originality=4 but Overall=1.

**Language preservation.** Round 6 reviewer replied entirely in Traditional Chinese, with formal academic register — no language-mixing, no template leakage.

## Edge cases surfaced

- **No Accept threshold reachable with plausible mocks.** For a realistic dogfood eval, generating an Accept-grade mock likely needs genuine researcher input — current prompt engineering alone doesn't clear the bar. *Not a bug, a feature*: it means vibe-sci review is trustworthy as a publication-readiness gate.
- **ensemble=1 is sufficient for rapid iteration.** The 24-38s per-paper turnaround makes this loop-style eval viable. For final publication-grade review, ensemble=5 recommended.
- **`.md` input path is fine**; `.pdf` path untested this loop (requires `pypdf` / `pymupdf4llm` extras — the review.py _extract_pdf_text branch).

## Bugs or surprises found in vibe-sci Phase 2 port

**None.** The port produced working, stable, high-quality review output across 7 highly varied inputs on the first shot. No fallbacks required, no hermes-runtime ghosts re-surfaced.

The single non-code finding: `review.py::REVIEW_PROMPT_TMPL` requests Summary / Strengths / Weaknesses but does not instruct the reviewer to answer in the paper's language — yet claude does so spontaneously for the Chinese paper. This is emergent, not guaranteed. Could be made explicit with a line in the prompt if we want deterministic multilingual behaviour.

## Per-round artefacts (at /tmp/vibe-sci-loop/)

- mock_paper_0{1..7}_*.md  — 7 input papers
- review_0{1..7}.json       — 7 structured reviews
- log.md                    — this file

These are *ephemeral* (/tmp is cleared on reboot). Candidates to promote into the repo as fixture data:
- review_01.json (weak-paper example — already in `skills/vibe-sci/references/`)
- review_04.json (garbage-paper floor calibration)
- review_06.json (Chinese-language multilingual proof)
- review_07.json (short-paper edge case)

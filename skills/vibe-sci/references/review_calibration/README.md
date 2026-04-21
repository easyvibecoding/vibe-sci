# Review calibration — reference paper / review pairs

Captured 2026-04-21 from an end-to-end `/loop` of `vibe-sci review --backend claude-cli --ensemble 1` against 7 mock ML papers of varying quality, topic, and language. Three pairs with the most pedagogical value are preserved here; the full 7-round sweep report is in [`../../evals/2026-04-21_loop_7round_review_calibration.md`](../../evals/2026-04-21_loop_7round_review_calibration.md).

Each pair shows what the reviewer produces for a specific paper archetype. Use them when:

- evaluating whether your draft is in the same quality bracket as one of these references
- writing unit tests that assert `review.py` integration still produces reasonable output shape after a code change
- debugging `_claude_cli_complete` / `extract_json` regressions — if your own reviews stop matching the shape of `review_*_*.json` here, something upstream has drifted

Paired with the original input paper so you can reproduce the exact call:

```bash
vibe-sci review --paper skills/vibe-sci/references/review_calibration/paper_<tag>.md \
  --backend claude-cli --ensemble 1 -o /tmp/your_review.json
```

## The three pairs

### 1. `paper_04_garbage.md` + `review_04_garbage.json` — **Overall = 1 (floor)**

Buzzword-soup paper: "Revolutionary Quantum-Neural Hypergraph Transformer", MNIST 99.7%, no method, no baseline name. Every sub-score = 1. Establishes that the reviewer can punish decorative language decoratively empty of technical content.

Use this as the low-end calibration anchor when you want to know what a 1/10 looks like from this reviewer.

### 2. `paper_06_chinese.md` + `review_06_chinese.json` — **Overall = 4, Traditional Chinese output**

繁中 paper on learned head-sparsification. Reviewer returned the `Summary`, `Strengths`, `Weaknesses` entirely in Traditional Chinese (no language-mixing), at formal academic register. Caught a real semantic issue in the method (`TopK` written over a scalar) and listed missing prior work (Michel et al. 2019, Voita et al. 2019).

Use this as proof that `review.py` handles non-English input without glue code — `REVIEW_PROMPT_TMPL` doesn't instruct the reviewer to match the paper's language, but claude does it spontaneously.

### 3. `paper_07_tiny.md` + `review_07_tiny.json` — **Overall = 2 (edge case)**

284-byte paper on ReLU² activation — just Abstract + one-line method + one number. Reviewer didn't crash, didn't produce "no valid reviews parsed", and gave a coherent low-but-non-zero score with an explanation that there's insufficient detail to assess.

Use this as the "minimum-length-that-still-reviews" bound for your own drafts.

## What's **not** captured here

- **No Accept-grade example.** Seven mock papers produced Decision = Reject across the board (Overall 1 → 4). A published NeurIPS paper would likely score ≥6; we don't ship one as a fixture because the mocks we could reasonably craft don't clear the bar.
- **No ensemble=5 example.** All three captured reviews are ensemble=1 (single-shot). For ensemble aggregation correctness testing, prefer `review_01.json` at the parent `references/` level or regenerate with `--ensemble 5`.
- **No PDF-input example.** The `review.py::_extract_pdf_text` branch (needs `pypdf` or `pymupdf4llm`) was not exercised this round.

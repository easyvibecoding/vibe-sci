# A Note on ReLU^2 Activation

## Abstract

We replace ReLU with ReLU squared (ReLU^2(x) = max(0, x)^2) in GPT-2 small.
Perplexity drops from 29.4 to 29.1 on WikiText-103.

## Method

Replace `F.relu(x)` with `F.relu(x) ** 2` in every MLP block.

## Result

29.1 vs 29.4 PPL, 1 seed.

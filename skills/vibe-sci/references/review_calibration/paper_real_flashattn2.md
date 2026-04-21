# FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning

**Tri Dao** (Department of Computer Science, Princeton University and Stanford University)

## Abstract

Scaling Transformers to longer sequence lengths has been challenging, as the attention layer's runtime and memory increase quadratically with sequence length. FlashAttention exploited GPU memory hierarchy for significant savings, but achieved only 25-40% of theoretical maximum FLOPs/s. This work proposes FlashAttention-2, addressing suboptimal work partitioning through: (1) reducing non-matmul FLOPs, (2) parallelizing attention computation across thread blocks to increase occupancy, and (3) optimizing warp-level work distribution to minimize shared memory communication. FlashAttention-2 achieves approximately 2× speedup over FlashAttention, reaching 50-73% of theoretical maximum FLOPs/s on A100 GPUs and achieving training speeds up to 225 TFLOPs/s per A100 GPU (72% model FLOPs utilization).

## 1 Introduction

Extending context length in Transformers remains challenging due to attention's quadratic complexity. Recent models demonstrate demand for longer contexts: GPT-4 (32k tokens), MosaicML's MPT (65k tokens), and Anthropic's Claude (100k tokens). While various approximate attention methods exist, large-scale training predominantly uses standard attention.

FlashAttention achieved 2-4× speedup and linear memory scaling through algorithmic reordering and classical techniques (tiling, recomputation). However, the forward pass reaches only 30-50% of maximum device throughput, while the backward pass achieves just 25-35% on A100 GPUs. In contrast, optimized GEMM operations reach 80-90% efficiency. Through profiling, suboptimal work partitioning between thread blocks and warps causes either low occupancy or unnecessary shared memory operations.

FlashAttention-2 addresses these inefficiencies through three main improvements:

1. Algorithm tweaks reducing non-matmul FLOPs (which execute 16× slower than matmul FLOPs on A100)
2. Parallelization along sequence length dimension in addition to batch and head dimensions
3. Work distribution between warps within thread blocks to minimize shared memory communication

Empirical validation shows FlashAttention-2 delivers approximately 2× speedup over FlashAttention, reaching up to 73% of theoretical maximum throughput in the forward pass and approaching GEMM efficiency. End-to-end GPT-style model training achieves 225 TFLOPs/s per A100 GPU.

## 2 Background

### 2.1 Hardware Characteristics

**GPU Performance Characteristics.** Modern GPUs contain specialized matrix multiply units (Tensor Cores on Nvidia GPUs for FP16/BF16). The memory hierarchy comprises high bandwidth memory (HBM) and on-chip SRAM. The A100 GPU features 40-80GB HBM with 1.5-2.0TB/s bandwidth and 192KB per-SM SRAM with approximately 19TB/s bandwidth across 108 streaming multiprocessors.

**Execution Model.** GPUs execute massive numbers of threads organized into thread blocks scheduled on streaming multiprocessors. Threads group into warps (32 threads each) enabling fast shuffle instructions and cooperative matrix operations. Warps communicate within thread blocks via shared memory. Each kernel loads inputs from HBM to registers and SRAM, computes, then writes outputs to HBM.

### 2.2 Standard Attention Implementation

Given input sequences $\mathbf{Q},\mathbf{K},\mathbf{V}\in\mathbb{R}^{N\times d}$ where $N$ is sequence length and $d$ is head dimension, compute attention output $\mathbf{O}\in\mathbb{R}^{N\times d}$:

$$\mathbf{S}=\mathbf{Q}\mathbf{K}^{\top}\in\mathbb{R}^{N\times N},\quad\mathbf{P}=\mathrm{softmax}(\mathbf{S})\in\mathbb{R}^{N\times N},\quad\mathbf{O}=\mathbf{P}\mathbf{V}\in\mathbb{R}^{N\times d}$$

Standard implementations materialize $\mathbf{S}$ and $\mathbf{P}$ matrices to HBM, requiring $O(N^2)$ memory. Since $N \gg d$ (typically $N$ is 1k–8k while $d$ is 64–128), this creates significant memory access overhead. The backward pass must save $\mathbf{P}\in\mathbb{R}^{N\times N}$ for gradient computation.

### 2.3 FlashAttention

FlashAttention reduces memory reads/writes while maintaining exact outputs through tiling: loading input blocks from HBM to SRAM, computing attention, and updating output without materializing $\mathbf{S}$ and $\mathbf{P}$ to HBM. Online softmax enables splitting attention into blocks with rescaling to obtain correct results.

#### 2.3.1 Forward Pass

For simplified exposition with attention matrix row $[\mathbf{S}^{(1)}\mathbf{S}^{(2)}]$ and values $[\mathbf{V}^{(1)}\mathbf{V}^{(2)}]^T$:

**Standard softmax:**
$$m = \max(\mathrm{rowmax}(\mathbf{S}^{(1)}), \mathrm{rowmax}(\mathbf{S}^{(2)}))$$
$$\ell = \mathrm{rowsum}(e^{\mathbf{S}^{(1)}-m}) + \mathrm{rowsum}(e^{\mathbf{S}^{(2)}-m})$$
$$\mathbf{O} = \mathrm{diag}(\ell)^{-1}[e^{\mathbf{S}^{(1)}-m}\mathbf{V}^{(1)} + e^{\mathbf{S}^{(2)}-m}\mathbf{V}^{(2)}]$$

**Online softmax** computes local softmax per block with rescaling — enables tiling without materializing intermediate matrices, achieving 2-4× speedup and 10-20× memory savings.

#### 2.3.2 Backward Pass

FlashAttention recomputes $\mathbf{S}$ and $\mathbf{P}$ when blocks load to SRAM, avoiding storage of $O(N^2)$ matrices. This delivers 10-20× memory savings and 2-4× wall-clock speedup.

## 3 FlashAttention-2: Algorithm, Parallelism, and Work Partitioning

### 3.1 Algorithm

Modern GPUs have specialized units making matmul 16× faster than non-matmul operations per FLOP. The A100's 312 TFLOPs/s FP16/BF16 matmul far exceeds 19.5 TFLOPs/s non-matmul FP32.

#### 3.1.1 Forward Pass — Two minor tweaks reduce non-matmul FLOPs:

1. **Delayed rescaling:** Instead of rescaling output by $\mathrm{diag}(\ell^{(2)})^{-1}$ after each block, maintain an "unscaled" output and only at the loop's end scale the final output.
2. **Logsumexp storage:** Rather than storing both max $m^{(j)}$ and exponential sum $\ell^{(j)}$, store only $L^{(j)} = m^{(j)} + \log(\ell^{(j)})$ for the backward pass.

**Algorithm 1: FlashAttention-2 Forward Pass**
Input: Matrices $\mathbf{Q},\mathbf{K},\mathbf{V}\in\mathbb{R}^{N\times d}$ in HBM, block sizes $B_c$, $B_r$.
Divide $\mathbf{Q}$ into $T_r = \lceil N/B_r \rceil$ blocks of size $B_r \times d$, and $\mathbf{K},\mathbf{V}$ into $T_c$ blocks. For each $i$, load $\mathbf{Q}_i$, loop over $j$ loading $\mathbf{K}_j, \mathbf{V}_j$ and accumulating $\mathbf{S}$, $\mathbf{P}$, $\mathbf{O}$ with online max/sum tracking. At loop end, compute $\mathbf{O}_i = \mathrm{diag}(\ell_i^{(T_c)})^{-1}\mathbf{O}_i^{(T_c)}$ and $L_i = m_i^{(T_c)} + \log(\ell_i^{(T_c)})$, write to HBM.

**Causal Masking:** Skip blocks where all column indices exceed row indices (approximately half for large sequences), yielding 1.7-1.8× speedup.

**Correctness, Runtime, Memory:** Algorithm 1 returns correct output $\mathbf{O} = \mathrm{softmax}(\mathbf{Q}\mathbf{K}^{\top})\mathbf{V}$ using $O(N^2d)$ FLOPs with $O(N)$ additional memory.

#### 3.1.2 Backward Pass

The backward pass uses only row-wise logsumexp $L$ instead of separate max and exponential sum. Algorithm 2 iterates outer over $T_c$ (K/V blocks) and inner over $T_r$ (Q blocks), computing $\mathbf{dK}, \mathbf{dV}, \mathbf{dQ}$ via atomic updates.

**Multi-Query and Grouped-Query Attention:** MQA and GQA variants share key/value heads across query heads. Backward pass sums gradients across implicitly duplicated heads.

### 3.2 Parallelism

FlashAttention-1 parallelizes over batch and number of heads (one thread block per head). With long sequences and small batch sizes, parallelization over sequence length improves GPU occupancy.

**Forward Pass:** The outer loop over sequence length is embarrassingly parallel, scheduled on different thread blocks without inter-block communication.

**Backward Pass:** The primary shared computation across column blocks occurs when updating $\mathbf{dQ}$. Atomic additions coordinate updates across thread blocks.

### 3.3 Work Partitioning Between Warps

Typically 4-8 warps per thread block.

**Forward Pass:** FlashAttention's "split-K" scheme splits $\mathbf{K}$ and $\mathbf{V}$ across 4 warps. FlashAttention-2 instead splits $\mathbf{Q}$ across 4 warps while keeping $\mathbf{K}$ and $\mathbf{V}$ shared. This eliminates inter-warp communication, reducing shared memory overhead.

**Backward Pass:** Similarly, avoiding "split-K" reduces shared memory operations.

**Tuning Block Sizes:** Block sizes typically $\{64,128\} \times \{64,128\}$ depending on head dimension and device shared memory.

## 4 Empirical Validation

### 4.1 Benchmarking Attention

FlashAttention-2 tested on A100 80GB SXM4 across various settings (±causal mask, head dimension 64 or 128). Results show approximately 2× speedup over FlashAttention, 1.3-1.5× faster than FlashAttention in Triton (forward), 2× faster (backward), and up to 10× faster than standard PyTorch attention. FlashAttention-2 reaches 230 TFLOPs/s (73% of theoretical maximum).

**Benchmark Settings:** Sequence length 512 to 16k tokens with total batch tokens fixed at 16k. Hidden dimension 2048, head dimension 64 or 128. Forward FLOPs = $4 \cdot \text{seqlen}^2 \cdot d \cdot \text{heads}$; backward FLOPs = 2.5× forward.

| Condition | Forward (no mask) d=64 | Forward (causal) d=64 | Backward (no mask) d=64 | Backward (causal) d=64 |
|-----------|----------------------|----------------------|------------------------|----------------------|
| PyTorch Baseline | ~80 TFLOPs/s | ~60 TFLOPs/s | ~40 TFLOPs/s | ~30 TFLOPs/s |
| FlashAttention | ~140 TFLOPs/s | ~120 TFLOPs/s | ~110 TFLOPs/s | ~90 TFLOPs/s |
| FA2 (Triton) | ~180 TFLOPs/s | ~160 TFLOPs/s | ~150 TFLOPs/s | ~130 TFLOPs/s |
| FA2 (CUTLASS) | ~200+ TFLOPs/s | ~180 TFLOPs/s | ~170 TFLOPs/s | ~150 TFLOPs/s |

H100 GPUs achieve up to 335 TFLOPs/s without using new instructions (TMA, 4th-gen Tensor Cores), with expected 1.5-2× additional speedup available.

### 4.2 End-to-End Performance

Training performance measured on 8× A100 80GB SXM GPUs for GPT-style models (1.3B and 2.7B parameters) on 2k and 8k sequence lengths.

| Model | Sequence Length | Without FlashAttention | FlashAttention | FlashAttention-2 |
|-------|-----------------|----------------------|----------------|------------------|
| GPT3-1.3B | 2k | 142 TFLOPs/s | 189 TFLOPs/s | 196 TFLOPs/s |
| GPT3-1.3B | 8k | 72 TFLOPs/s | 170 TFLOPs/s | 220 TFLOPs/s |
| GPT3-2.7B | 2k | 149 TFLOPs/s | 189 TFLOPs/s | 205 TFLOPs/s |
| GPT3-2.7B | 8k | 80 TFLOPs/s | 175 TFLOPs/s | 225 TFLOPs/s |

FlashAttention-2 yields 2.8× speedup over baseline without FlashAttention and 1.3× over FlashAttention, reaching 72% model FLOPs utilization.

## 5 Discussion and Future Directions

FlashAttention-2's 2× speedup enables training with 16k longer context at equivalent cost as 8k previously. Applications include understanding long books, reports, high-resolution images, video.

Near-term plans: collaboration on H100 / AMD GPUs, FP8, immediate H100 optimization using TMA and 4th-gen Tensor Cores. Combining low-level optimizations with high-level algorithmic changes (local, dilated, block-sparse attention) could enable even longer context.

## References

Ainslie et al. 2023 GQA. | Beltagy et al. 2020 Longformer. | Chen et al. 2021 Scatterbrain (NeurIPS). | Choromanski et al. 2020 Performers (ICLR). | Dao et al. 2022 FlashAttention (NeurIPS). | Jia and Van Sandt 2021 Ampere microbenchmarking. | Jia et al. 2018 Volta GPU. | Katharopoulos et al. 2020 Linear Transformers (ICML). | Kitaev et al. 2020 Reformer (ICML). | Lefaudeux et al. 2022 xformers. | Milakov and Gimelshein 2018 Online softmax. | OpenAI 2023 GPT-4. | Rabe and Staats 2021 Self-attention O(n^2) memory. | Roy et al. 2021 Routing Transformers. | Shazeer 2019 Multi-Query Attention. | Shoeybi et al. 2019 Megatron-LM. | Tillet et al. 2019 Triton (MAPL). | Vaswani et al. 2017 Attention Is All You Need (NeurIPS). | Wang et al. 2020 Linformer. | Zaheer et al. 2020 Big Bird (NeurIPS).

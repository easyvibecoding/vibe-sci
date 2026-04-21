# AdaptSparse:基於動態稀疏啟用的高效 Transformer 推理

## 摘要

我們提出 AdaptSparse,一種在推理階段根據 token 重要度動態選擇活躍 attention head 的稀疏化方法。透過在訓練時學習每層的 head 重要度 logits,並在推理時用一個輕量的 top-k 選擇器啟用子集,AdaptSparse 在 WMT14 英德翻譯上將 BLEU 從 27.3 ±0.2 提升至 27.6 ±0.2(3 個種子),同時將推理 FLOPs 減少 38 ±3%。在 GLUE 平均分數上,BERT-base 配備 AdaptSparse 後從 83.2 降至 82.8(-0.4),但推理時間縮短 42%。

## 1 引言

Transformer 的推理成本主要來自 self-attention 的 O(T²) 複雜度。靜態剪枝(如 LayerDrop、StructuredDropout)在訓練時移除部分 head,但對所有輸入使用相同的子集,無法針對輸入的難度自適應。

AdaptSparse 在訓練階段學習每個 (layer, head) 的重要度 logit `π_{l,h}`,並在推理時為每個 token 選擇 top-k head 子集。top-k 選擇透過 Gumbel-softmax 軟化以支持端到端訓練。

## 2 方法

設第 l 層有 H 個 attention head,輸入 token 表示 x_t。我們定義:

    π̂_{l,h}(x_t) = MLP_l(x_t)[h]    # 每個 token 的 head 重要度
    m_{l,h}(x_t) = TopK(π̂_{l,h}(x_t), k)  # 二元 mask (1 = 啟用)
    attn_output = Σ_{h ∈ active} head_h(x_t)

訓練時使用 Gumbel-softmax 近似 TopK 並允許梯度回傳。k 在訓練中從 H 降到目標值(線性 schedule,前 1 萬步降一次)。

## 3 實驗

### 3.1 設置

- 基線:標準 Transformer-base(6 層 × 8 head,512 維)
- 資料集:WMT14 En-De(翻譯)、GLUE(NLU)
- 硬體:4× A100-40GB,訓練 3 個 random seed
- 目標 k = 3(每層選 3/8 head)

### 3.2 翻譯結果(WMT14 En-De)

| 方法             | BLEU          | 推理 GFLOPs / 句 |
|------------------|---------------|------------------|
| Transformer-base | 27.3 ±0.2     | 4.2              |
| LayerDrop p=0.2  | 26.9 ±0.2     | 3.4              |
| StructuredDropout| 26.7 ±0.3     | 3.2              |
| **AdaptSparse**  | **27.6 ±0.2** | **2.6**          |

### 3.3 NLU 結果(GLUE 平均,BERT-base)

| 方法             | GLUE avg      | 推理時間 (ms/sample) |
|------------------|---------------|---------------------|
| BERT-base        | 83.2 ±0.1     | 12.5                |
| LayerDrop        | 82.4 ±0.2     | 9.3                 |
| **AdaptSparse**  | **82.8 ±0.1** | **7.2**             |

### 3.4 消融

| 變體                     | WMT14 BLEU |
|--------------------------|------------|
| 完整 AdaptSparse(k=3)   | 27.6       |
| k=2(更稀疏)             | 27.1       |
| k=5(較鬆)               | 27.4       |
| 固定 top-k(無 Gumbel)   | 26.8       |
| 無學習 logit(隨機選擇)  | 25.4       |

## 4 相關工作

LayerDrop(Fan et al. 2019)及 StructuredDropout 都是靜態剪枝的代表;它們不考慮輸入差異。MoE-based sparse models(如 Switch Transformer)做 expert-level 稀疏化,我們關注 head-level。Adaptive computation(PonderNet、Universal Transformer)與本方法正交。

## 5 限制

- 僅在 base-size 模型驗證(encoder-decoder 6 層)。scaling 到 large / XL 未測試。
- 3 個 seed 不足以做嚴謹的 significance test。
- k schedule 是人工設計;自動決定 k 值是自然的後續工作。
- 在 GLUE 上精度下降 0.4,雖然換取 42% 加速,但對 accuracy-critical 應用不宜。

## 6 結論

AdaptSparse 以學習到的 head-importance 與 Gumbel-Top-k 選擇器,在 WMT14 上同時提升翻譯品質並降低 38% 推理 FLOPs。方法簡單,可作為 drop-in 替換。

## 參考文獻

[1] Vaswani et al. Attention Is All You Need. NeurIPS 2017.
[2] Fan et al. Reducing Transformer Depth on Demand with Structured Dropout. ICLR 2020.
[3] Fedus et al. Switch Transformers. 2021.

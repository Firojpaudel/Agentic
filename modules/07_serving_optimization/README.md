# Module 07: Serving Economics and Prefix Caching

> "Agent traffic is multi-turn, prefix-heavy, and interleaved with tools. Serving choices dominate cost and latency."

---

## 1. Objectives
- Understand why agent workloads are radically different from standard chatbots (90%+ shared prompt prefixes across turns).
- Master RadixAttention prefix caching in SGLang and PagedAttention in vLLM.
- Calculate and optimize Token Economics: cost-per-step vs cost-per-task.

---

## 2. Key Repositories to Read Line-by-Line
- **sgl-project/sglang** (https://github.com/sgl-project/sglang): RadixAttention prefix caching and structured decoding.
- **vllm-project/vllm** (https://github.com/vllm-project/vllm): High-throughput serving with tool call parsers and prefix caching.
- **mlc-ai/xgrammar** (https://github.com/mlc-ai/xgrammar): Grammar-constrained decoding for guaranteeing valid JSON at inference time.

---

## 3. Hands-On Exercises
1. Run an open model locally on SGLang or vLLM with prefix caching enabled.
2. Send a 10-turn agent trajectory and measure the cache hit rate on prompt tokens. Compare latency with and without prefix caching.

---

## 4. Acceptance Criteria
- You can explain how prefix caching avoids recomputing the KV-cache on long agent trajectories.

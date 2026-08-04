---
name: llm-inference
description: "LLM inference and serving: vLLM (production throughput, OpenAI API) and llama.cpp (local GGUF, edge deployment). Choose, configure, deploy."
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [vllm, torch, transformers, llama-cpp-python>=0.2.0]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [vLLM, llama.cpp, GGUF, Inference Serving, PagedAttention, Continuous Batching, High Throughput, Production, OpenAI API, Quantization, Tensor Parallelism, CPU Inference, Apple Silicon, Edge Deployment, AMD GPUs, Intel GPUs, NVIDIA, URL-first]
    absorbed_from: [serving-llms-vllm, llama-cpp]
---

# LLM Inference & Serving

Unified skill for deploying LLMs: **vLLM** for production GPU serving and **llama.cpp** for local/edge GGUF inference.

---

## Choosing: vLLM vs llama.cpp

| Criteria | vLLM | llama.cpp |
|---|---|---|
| **Best for** | Production APIs, multi-user, high throughput | Local inference, edge, CPU/Apple Silicon |
| **Hardware** | NVIDIA/AMD GPUs (multi-GPU support) | CPU, Apple Metal, CUDA, ROCm, Intel |
| **Throughput** | 24x over naive serving (PagedAttention + continuous batching) | Optimized for single-user / small batch |
| **Model format** | HuggingFace Transformers (safetensors) | GGUF (quantized) |
| **Quantization** | AWQ, GPTQ, FP8 | Q2–Q8, IQ, K-quants, imatrix |
| **API** | OpenAI-compatible server (`/v1/...`) | OpenAI-compatible server (`/v1/...`) |
| **Deployment** | Docker, Kubernetes, cloud | Binary, Homebrew, Docker |
| **When to use** | 100+ req/sec, chatbots, APIs | Dev testing, offline, constrained hardware |

**Quick rule**: GPU server with users → vLLM. Laptop / edge / offline → llama.cpp.

---

## vLLM: High-Throughput Serving

Use when deploying production LLM APIs, optimizing inference latency/throughput, or serving models with limited GPU memory. Supports OpenAI-compatible endpoints, quantization (GPTQ/AWQ/FP8), and tensor parallelism.

### Quick start

**Installation**:
```bash
pip install vllm
```

**Basic offline inference**:
```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3-8B-Instruct")
sampling = SamplingParams(temperature=0.7, max_tokens=256)

outputs = llm.generate(["Explain quantum computing"], sampling)
print(outputs[0].outputs[0].text)
```

**OpenAI-compatible server**:
```bash
vllm serve meta-llama/Llama-3-8B-Instruct

# Query with OpenAI SDK
python -c "
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8000/v1', api_key='EMPTY')
print(client.chat.completions.create(
    model='meta-llama/Llama-3-8B-Instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}]
).choices[0].message.content)
"
```

### Production API deployment

```bash
# For 7B-13B models on single GPU
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192 \
  --port 8000

# For 30B-70B models with tensor parallelism
vllm serve meta-llama/Llama-2-70b-hf \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9 \
  --quantization awq \
  --port 8000

# Production with caching and metrics
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching \
  --enable-metrics \
  --metrics-port 9090 \
  --port 8000 \
  --host 0.0.0.0
```

Docker deployment:
```bash
docker run --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching
```

### Monitoring

Prometheus metrics on port 9090:
```bash
curl http://localhost:9090/metrics | grep vllm
```

Key metrics: `vllm:time_to_first_token_seconds`, `vllm:num_requests_running`, `vllm:gpu_cache_usage_perc`.

### Quantized model serving

- **AWQ**: Best for 70B models, minimal accuracy loss
- **GPTQ**: Wide model support, good compression
- **FP8**: Fastest on H100 GPUs

```bash
vllm serve TheBloke/Llama-2-70B-AWQ \
  --quantization awq \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95
```

### Offline batch inference

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3-8B-Instruct", tensor_parallel_size=2, gpu_memory_utilization=0.9, max_model_len=4096)
sampling = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=512, stop=["</s>", "\n\n"])

outputs = llm.generate(prompts, sampling)  # vLLM handles batching internally
```

### vLLM common issues

- **OOM**: Reduce `--gpu-memory-utilization` to 0.7, reduce `--max-model-len`, or use quantization
- **Slow TTFT**: Enable `--enable-prefix-caching` or `--enable-chunked-prefill`
- **Model not found**: Add `--trust-remote-code`
- **Low throughput**: Increase `--max-num-seqs 512`, check GPU utilization >80%
- **Slow inference**: Use power-of-2 `--tensor-parallel-size`, enable `--speculative-model`

### vLLM hardware requirements

- **7B-13B**: 1x A10 (24GB) or A100 (40GB)
- **30B-40B**: 2x A100 (40GB) with tensor parallelism
- **70B+**: 4x A100 (40GB) or 2x A100 (80GB), use AWQ/GPTQ

### vLLM references

- **[vllm-server-deployment.md](references/vllm-server-deployment.md)** — Docker, Kubernetes, load balancing
- **[vllm-optimization.md](references/vllm-optimization.md)** — PagedAttention tuning, continuous batching, benchmarks
- **[vllm-quantization.md](references/vllm-quantization.md)** — AWQ/GPTQ/FP8 setup, accuracy comparisons
- **[vllm-troubleshooting.md](references/vllm-troubleshooting.md)** — Error messages, debugging, performance diagnostics

---

## llama.cpp: Local GGUF Inference

Use for local GGUF inference, quant selection, or Hugging Face repo discovery for llama.cpp.

### When to use

- Run local models on CPU, Apple Silicon, CUDA, ROCm, or Intel GPUs
- Find the right GGUF for a specific Hugging Face repo
- Build a `llama-server` or `llama-cli` command from the Hub
- Search the Hub for models that already support llama.cpp

### Install llama.cpp

```bash
# macOS / Linux
brew install llama.cpp

# Windows
winget install llama.cpp

# From source
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp && cmake -B build && cmake --build build --config Release
```

### Model Discovery workflow

Prefer URL workflows before asking for `hf`, Python, or custom scripts.

1. Search candidate repos: `https://huggingface.co/models?apps=llama.cpp&sort=trending`
2. Open with local-app view: `https://huggingface.co/<repo>?local-app=llama.cpp`
3. Treat the local-app snippet as source of truth for commands and recommended quants
4. Extract `Hardware compatibility` section from the local-app page
5. Confirm with tree API: `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`
6. Reconstruct command if snippet unavailable: `llama-server -hf <repo>:<QUANT>` or `llama-server --hf-repo <repo> --hf-file <filename.gguf>`

### Quick start

```bash
# Direct from Hub
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0

# Exact GGUF file
llama-server \
    --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf \
    --hf-file Phi-3-mini-4k-instruct-q4.gguf \
    -c 4096

# OpenAI-compatible check
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Write a limerick"}]}'
```

### Python bindings (llama-cpp-python)

```bash
pip install llama-cpp-python
# CUDA: CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
# Metal: CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

```python
from llama_cpp import Llama

llm = Llama(model_path="./model-q4_k_m.gguf", n_ctx=4096, n_gpu_layers=35, n_threads=8)
out = llm("What is machine learning?", max_tokens=256, temperature=0.7)
print(out["choices"][0]["text"])

# Chat
llm = Llama(model_path="./model-q4_k_m.gguf", n_ctx=4096, n_gpu_layers=35, chat_format="llama-3")
resp = llm.create_chat_completion(
    messages=[{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "What is Python?"}],
    max_tokens=256,
)

# From Hub
llm = Llama.from_pretrained(repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF", filename="*Q4_K_M.gguf", n_gpu_layers=35)

# Embeddings
llm = Llama(model_path="./model-q4_k_m.gguf", embedding=True, n_gpu_layers=35)
vec = llm.embed("Test sentence.")
```

### Choosing a quant

- Start with `Q4_K_M` for general chat
- Prefer `Q5_K_M` or `Q6_K` for code/technical work if memory allows
- Use `Q3_K_M`, `IQ` variants only for very tight RAM budgets
- For multimodal: mention `mmproj-*.gguf` separately (projector ≠ main model)
- Do not normalize repo-native labels (e.g., `UD-Q4_K_M` stays as-is)

### Search patterns

```text
https://huggingface.co/models?apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&sort=trending
https://huggingface.co/<repo>?local-app=llama.cpp
https://huggingface.co/api/models/<repo>/tree/main?recursive=true
```

### llama.cpp references

- **[llamacpp-hub-discovery.md](references/llamacpp-hub-discovery.md)** — URL-only HF workflows, search patterns, GGUF extraction, command reconstruction
- **[llamacpp-advanced-usage.md](references/llamacpp-advanced-usage.md)** — Speculative decoding, batched inference, grammar-constrained generation, LoRA, multi-GPU, custom builds, benchmark scripts
- **[llamacpp-quantization.md](references/llamacpp-quantization.md)** — Quant quality tradeoffs, Q4/Q5/Q6/IQ guidance, model size scaling, imatrix
- **[llamacpp-server.md](references/llamacpp-server.md)** — Direct-from-Hub server launch, OpenAI API endpoints, Docker, NGINX load balancing, monitoring
- **[llamacpp-optimization.md](references/llamacpp-optimization.md)** — CPU threading, BLAS, GPU offload heuristics, batch tuning, benchmarks
- **[llamacpp-troubleshooting.md](references/llamacpp-troubleshooting.md)** — Install/convert/quantize/inference/server issues, Apple Silicon, debugging

---

## Resources

- **vLLM docs**: https://docs.vllm.ai
- **vLLM GitHub**: https://github.com/vllm-project/vllm
- **vLLM paper**: "Efficient Memory Management for Large Language Model Serving with PagedAttention" (SOSP 2023)
- **llama.cpp GitHub**: https://github.com/ggml-org/llama.cpp
- **HF GGUF docs**: https://huggingface.co/docs/hub/gguf-llamacpp
- **HF Local Apps**: https://huggingface.co/docs/hub/main/local-apps

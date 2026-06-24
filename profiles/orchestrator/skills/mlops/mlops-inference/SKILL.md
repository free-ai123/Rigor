---
name: mlops-inference
description: "Local model inference: llama.cpp GGUF inference + HF Hub discovery, and OBLITERATUS LLM refusal removal (diff-in-means)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [llama.cpp, GGUF, local-inference, obliteratus, abliteration, model-surgery, huggingface]
    category: mlops
---

# MLOps Inference Suite

Two tools for working with LLMs locally: **llama.cpp** for GGUF inference and model discovery, and **OBLITERATUS** for refusal/guardrail removal via mechanistic interpretability.

---

## Mode A: llama.cpp GGUF Inference

**Trigger:** "run local model", "GGUF", "llama-server", "find GGUF on HuggingFace", "quantization", "local LLM"

### URL-First Model Discovery (preferred)
1. Search: `https://huggingface.co/models?apps=llama.cpp&sort=trending&search=<term>`
2. Open repo with local-app view: `https://huggingface.co/<repo>?local-app=llama.cpp`
3. Copy exact `llama-server`/`llama-cli` command from local-app snippet
4. Confirm GGUF files exist via tree API: `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`
5. Reconstruct command: `llama-server -hf <repo>:<QUANT>` or `--hf-repo <repo> --hf-file <filename.gguf>`

### Quick Start
```bash
brew install llama.cpp                    # macOS/Linux
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0  # Direct from Hub
llama-server -hf <repo>:<QUANT>           # OpenAI-compatible server
curl http://localhost:8080/v1/chat/completions ...         # Test
```

### Python Bindings
```python
from llama_cpp import Llama
llm = Llama(model_path="./model-q4_k_m.gguf", n_ctx=4096, n_gpu_layers=35)
# Or from Hub: Llama.from_pretrained(repo_id="<repo>", filename="*Q4_K_M.gguf")
```

### Choosing a Quant
- General chat: start with `Q4_K_M`
- Code/technical: prefer `Q5_K_M` or `Q6_K`
- Tight RAM: `Q3_K_M` or `IQ` variants
- Don't normalize repo-native labels (if HF says `UD-Q4_K_M`, report `UD-Q4_K_M`)

### VRAM Guide (4-bit quant)
| VRAM | Max Model | Examples |
|------|-----------|----------|
| CPU only | ~1B | GPT-2, SmolLM |
| 4-8 GB | ~4B | Phi-3 mini, Llama 3.2 3B |
| 8-16 GB | ~9B | Llama 3.1 8B, Mistral 7B |
| 24 GB | ~32B | Qwen3-32B |

---

## Mode B: OBLITERATUS (Refusal Removal)

**Trigger:** "uncensor", "abliterate", "remove guardrails", "refusal removal", "OBLITERATUS"

**License warning:** OBLITERATUS is AGPL-3.0. NEVER import as Python library. Always invoke via CLI or subprocess.

### Method Selection
| Situation | Method |
|-----------|--------|
| Default / most models | `advanced` (multi-direction SVD, norm-preserving) |
| Quick test | `basic` (single direction, fast) |
| MoE models | `nuclear` (expert-granular) |
| Reasoning models (R1 distills) | `surgical` (CoT-aware) |
| Stubborn refusals persist | `aggressive` (whitened SVD + head surgery) |
| Reversible changes | Use steering vectors (Python API) |

### Standard Usage
```bash
obliteratus obliterate <model_name> --method advanced --quantization 4bit --output-dir ./out
obliteratus models --tier medium    # Browse by compute tier
obliteratus recommend <model_name>  # Telemetry-driven recommendation
obliteratus recommend <model_name> --insights  # Global rankings
```

### Verification Metrics
| Metric | Good | Warning |
|--------|------|---------|
| Refusal rate | < 5% | > 10% |
| Perplexity change | < 10% increase | > 15% (coherence damage) |
| KL divergence | < 0.1 | > 0.5 |

### Pitfalls
- Models < 1B respond poorly to abliteration (fragmented refusal directions)
- `aggressive` can make things worse on small models
- Always check perplexity — if it spikes > 15%, reduce aggressiveness
- MoE models need `nuclear` method
- Reasoning models need `surgical` to preserve chain-of-thought
- Large models (70B+): always use `--large-model` flag
- Quantized models can't be re-quantized — abliterate full-precision, then quantize output
- Don't use `informed` as default (experimental, slower than `advanced`)
- Spectial certification RED is common even when practical refusal rate is 0%

---

## Mode C: HuggingFace Hub CLI (`hf`)

**Trigger:** "huggingface", "hf CLI", "download model", "upload to Hub", "search models", "datasets"

The `hf` command (replaces deprecated `huggingface-cli`):
```bash
curl -LsSf https://hf.co/cli/install.sh | bash -s
hf download REPO_ID              # Download files
hf upload REPO_ID                # Upload files/folders
hf upload-large-folder REPO_ID   # Resumable large uploads
hf models list / info            # Model discovery
hf datasets list / info / sql    # Datasets + DuckDB SQL
hf papers list                   # Daily papers
hf auth login/logout             # Manage tokens
hf repos create/delete/move      # Repo management
hf endpoints deploy/pause        # Inference endpoints
hf jobs uv                       # Run Python on HF compute
```
- `--format json` for machine-readable output; `-q` for IDs only
- **Integration with llama.cpp:** `hf download <repo>` to get GGUFs, then point llama.cpp at them

---

## Mode D: vLLM (High-Throughput Serving)

**Trigger:** "serve LLM", "vLLM", "OpenAI API server", "high-throughput inference", "quantized serving"

vLLM for production LLM serving with PagedAttention:
```bash
pip install vllm
vllm serve <model> --host 0.0.0.0 --port 8000
# OpenAI-compatible endpoint at http://localhost:8000/v1
curl http://localhost:8000/v1/chat/completions -d '{"model":"<model>","messages":[{"role":"user","content":"Hello"}]}'
```

Supports GGUF quantization (AWQ, GPTQ, FP8), tensor parallelism (`--tensor-parallel-size N`), and continuous batching. Compatible with most HuggingFace models.
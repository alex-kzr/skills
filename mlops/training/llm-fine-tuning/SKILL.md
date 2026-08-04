---
name: llm-fine-tuning
description: "LLM fine-tuning: Unsloth (fast LoRA), Axolotl (YAML configs), TRL (SFT/DPO/GRPO/RLHF). Choose framework, configure, train, evaluate."
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [unsloth, axolotl, trl, torch, transformers, datasets, peft, accelerate, deepspeed]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Fine-Tuning, LoRA, QLoRA, SFT, DPO, PPO, GRPO, RLHF, Unsloth, Axolotl, TRL, YAML, HuggingFace, DeepSpeed, Memory-Efficient, Preference Alignment, Multimodal]
    absorbed_from: [unsloth, axolotl, fine-tuning-with-trl]

---

# LLM Fine-Tuning

Umbrella skill covering three major LLM fine-tuning frameworks: **Unsloth** (fast LoRA/QLoRA), **Axolotl** (YAML-driven configs), and **TRL** (SFT/DPO/GRPO/RLHF). Choose the right framework, configure training, run it, and evaluate results.

---

## Choosing a Framework

| Criteria | Unsloth | Axolotl | TRL |
|---|---|---|---|
| **Goal** | Fastest LoRA/QLoRA SFT | Full-featured YAML fine-tuning | RLHF / preference alignment |
| **Config style** | Python script | YAML config file | Python script / CLI |
| **Training types** | SFT (LoRA/QLoRA) | SFT, DPO, KTO, ORPO, GRPO | SFT, DPO, PPO, GRPO, Reward Model |
| **Speed** | 2-5x faster than standard | Standard (DeepSpeed/FSDP) | Standard |
| **Multimodal** | Limited | Yes | No |
| **Ease of use** | Very easy (few lines) | Easy (YAML) | Moderate (more code) |
| **Best for** | Quick LoRA experiments | Production multi-GPU training | RLHF pipelines, research |

**Decision flow:**

1. **Need preference alignment (DPO/PPO/GRPO)?** → TRL (most methods, active research) or Axolotl (YAML convenience)
2. **Need the fastest LoRA SFT?** → Unsloth
3. **Want YAML configs + multi-GPU?** → Axolotl
4. **Building full RLHF pipeline (SFT → Reward Model → PPO)?** → TRL
5. **Need multimodal fine-tuning?** → Axolotl

---

## Unsloth: Fast LoRA/QLoRA

2-5x faster LoRA/QLoRA fine-tuning with significantly less VRAM. Best for quick SFT experiments on Llama, Mistral, Gemma, Qwen models.

### When to use
- Quick LoRA/QLoRA experiments
- Limited VRAM budget
- Single-GPU SFT on consumer hardware
- Supported architectures: Llama, Mistral, Gemma, Qwen

### Dependencies
```
pip install unsloth torch transformers trl datasets peft
```

### Quick start
```python
from unsloth import FastLanguageModel
from trl import SFTTrainer

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=16,
    lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    processing_class=tokenizer,
)
trainer.train()
```

### Reference Files
- `references/unsloth/` — Unsloth documentation (llms-txt.md, llms.md, index.md, llms-full.md)

### Resources
- Docs: https://docs.unsloth.ai/
- GitHub: https://github.com/unslothai/unsloth

---

## Axolotl: YAML Fine-Tuning

YAML-driven fine-tuning supporting 100+ models, LoRA/QLoRA, DPO/KTO/ORPO/GRPO, multimodal, and multi-GPU (DeepSpeed/FSDP).

### When to use
- Production training with YAML configs
- Multi-GPU (DeepSpeed/FSDP) setups
- DPO/KTO/ORPO/GRPO alignment
- Multimodal fine-tuning
- Need dataset format flexibility

### Dependencies
```
pip install axolotl torch transformers datasets peft accelerate deepspeed
```

### Quick start (YAML config)
```yaml
base_model: meta-llama/Meta-Llama-3-8B
model_type: LlamaForCausalLM
tokenizer_type: AutoTokenizer

load_in_4bit: true
lora_r: 16
lora_alpha: 16
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj

datasets:
  - path: tatsu-lab/alpaca
    type: alpaca

output_dir: ./models/llama3-lora
sequence_len: 2048
micro_batch_size: 2
gradient_accumulation_steps: 4
num_epochs: 1
learning_rate: 2e-5
```

Train with:
```bash
accelerate launch -m axolotl.cli train config.yml
```

### Key patterns

**FSDP configuration:**
```yaml
fsdp_version: 2
fsdp_config:
  offload_params: true
  state_dict_type: FULL_STATE_DICT
  auto_wrap_policy: TRANSFORMER_BASED_WRAP
  transformer_layer_cls_to_wrap: LlamaDecoderLayer
  reshard_after_forward: true
```

**Compressed saving** (~40% smaller, vLLM-compatible):
```yaml
save_compressed: true
```

### Reference Files
- `references/axolotl/` — API docs, dataset formats, other docs

### Resources
- Docs: https://docs.axolotl.ai/
- GitHub: https://github.com/OpenAccess-AI-Collective/axolotl

---

## TRL: RLHF/DPO/GRPO Training

HuggingFace TRL — post-training methods for aligning LMs with human preferences: SFT, DPO, PPO, GRPO, Reward Modeling.

### When to use
- Preference alignment (DPO, PPO, GRPO)
- Full RLHF pipeline (SFT → Reward Model → PPO)
- Reward model training
- Research / custom training loops
- Need fine-grained control over training

### Dependencies

`trl`, `transformers`, `datasets`, `peft`, and `torch` are provided by the
shared agents ML runtime: `agents/runtime/python/ml/.venv` (see
`runtime/README.md`). `accelerate` and `deepspeed` are training-environment
specific and are not part of the shared runtime — install them in your
training environment as needed.

This skill requires the optional ML runtime:

`agents/runtime/python/ml/.venv`

### Quick start — SFT
```python
from trl import SFTTrainer, SFTConfig

trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",
    train_dataset=dataset,
)
trainer.train()
```

### Quick start — DPO
```python
from trl import DPOTrainer, DPOConfig

config = DPOConfig(output_dir="model-dpo", beta=0.1)
trainer = DPOTrainer(
    model=model,
    args=config,
    train_dataset=preference_dataset,
    processing_class=tokenizer
)
trainer.train()
```

### Quick start — GRPO
```python
from trl import GRPOTrainer, GRPOConfig

def reward_function(completions, **kwargs):
    return [len(c.split()) for c in completions]

config = GRPOConfig(
    output_dir="model-grpo",
    num_generations=4,
    max_new_tokens=128,
)
trainer = GRPOTrainer(
    model="Qwen/Qwen2-0.5B-Instruct",
    reward_funcs=reward_function,
    args=config,
    train_dataset=dataset,
)
trainer.train()
```

### CLI commands
```bash
# DPO
trl dpo --model_name_or_path Qwen/Qwen2.5-0.5B-Instruct \
    --dataset_name argilla/Capybara-Preferences \
    --output_dir model-dpo --beta 0.1

# GRPO
trl grpo --model_name_or_path Qwen/Qwen2-0.5B-Instruct \
    --dataset_name trl-lib/tldr \
    --output_dir model-grpo --num_generations 4
```

### Full RLHF pipeline
```
1. SFT → instruction-tune base model
2. Train Reward Model on preference data
3. PPO → optimize policy using reward model
4. Evaluate aligned model
```

### Common issues
- **OOM during DPO**: Reduce `per_device_train_batch_size`, `max_length`; enable `gradient_checkpointing`
- **Poor DPO alignment**: Tune `beta` (higher = more conservative, default 0.1)
- **PPO instability**: Increase `kl_coef`, reduce `cliprange`
- **GRPO**: Loss increasing is normal early on; see `references/trl/grpo-training.md` for expert guidance

### Hardware requirements
| Method | 7B model VRAM (LoRA) |
|---|---|
| SFT | ~16 GB |
| DPO | ~24 GB |
| PPO | ~40 GB |
| GRPO | ~24 GB |

### Reference Files
- `references/trl/` — SFT guide, DPO variants, GRPO deep dive, reward modeling, online RL
- `templates/trl/` — Production GRPO training script

### Resources
- Docs: https://huggingface.co/docs/trl/
- GitHub: https://github.com/huggingface/trl

---

## General Tips

1. **Always use LoRA/QLoRA** unless you have a specific reason for full fine-tuning
2. **Gradient checkpointing** saves VRAM at the cost of speed
3. **BF16** mixed precision on A100/H100; FP16 on older GPUs
4. **Monitor loss curves** — DPO/GRPO loss patterns differ from SFT
5. **Start small** — test on a subset before full training runs
6. **Save checkpoints** — use `save_strategy="epoch"` or `"steps"`

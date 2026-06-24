---
name: mlops-research-eval
description: "ML system building: DSPy (declarative LM programming, prompt optimization, RAG) and Weights & Biases (experiment tracking, sweeps, model registry)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [DSPy, wandb, experiment-tracking, prompt-optimization, RAG, hyperparameter-tuning, MLOps]
    category: mlops
---

# MLOps Research & Evaluation Suite

Two tools for building and optimizing ML/AI systems: **DSPy** for declarative LM programming and automatic prompt optimization, and **Weights & Biases** for experiment tracking, hyperparameter sweeps, and model registry.

---

## Mode A: DSPy (Declarative LM Programming)

**Trigger:** "build AI pipeline", "optimize prompts", "DSPy", "RAG system", "declarative LM", "prompt engineering"

### Core Pattern
```python
import dspy
lm = dspy.Claude(model="claude-sonnet-4-5-20250929")
dspy.settings.configure(lm=lm)

# Signature (input → output)
class QA(dspy.Signature):
    """Answer questions with short factual answers."""
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")

# Module
qa = dspy.Predict(QA)  # or dspy.ChainOfThought(QA) for reasoning
response = qa(question="What is the capital of France?")
```

### Modules
| Module | Use For |
|--------|---------|
| `dspy.Predict` | Basic input→output |
| `dspy.ChainOfThought` | Auto-reasoning steps before answer |
| `dspy.ReAct` | Agent-like reasoning with tools |
| `dspy.ProgramOfThought` | Generate + execute code for reasoning |

### Optimizers
| Optimizer | When |
|-----------|------|
| `BootstrapFewShot` | Learn from examples (fast, simple) |
| `MIPRO` | Iteratively improve prompts (best quality) |
| `BootstrapFinetune` | Create datasets for model fine-tuning |

### Multi-Stage Pipeline Pattern
```python
class MultiHopQA(dspy.Module):
    def __init__(self):
        self.retrieve = dspy.Retrieve(k=3)
        self.generate_query = dspy.ChainOfThought("question -> search_query")
        self.generate_answer = dspy.ChainOfThought("context, question -> answer")
    def forward(self, question):
        query = self.generate_query(question=question).search_query
        context = "\n".join(self.retrieve(query).passages)
        return self.generate_answer(context=context, question=question)
```

### Best Practices
- Start simple (Predict) → add reasoning (ChainOfThought) → optimize when you have data
- Use descriptive signatures with `desc` fields
- Optimize with representative, diverse training data
- Save/load optimized models: `optimized_qa.save("model.json")`

---

## Mode B: Weights & Biases (Experiment Tracking)

**Trigger:** "track ML experiments", "wandb", "experiment logging", "hyperparameter sweep", "model registry", "W&B"

### Basic Tracking
```python
import wandb
run = wandb.init(project="my-project", config={"lr": 0.001, "epochs": 10})
for epoch in range(run.config.epochs):
    wandb.log({"epoch": epoch, "train/loss": train_loss, "val/accuracy": val_acc})
wandb.finish()
```

### Hyperparameter Sweeps
```python
sweep_config = {
    'method': 'bayes',  # or 'grid', 'random'
    'metric': {'name': 'val/accuracy', 'goal': 'maximize'},
    'parameters': {
        'learning_rate': {'distribution': 'log_uniform', 'min': 1e-5, 'max': 1e-1},
        'batch_size': {'values': [16, 32, 64, 128]},
    }
}
sweep_id = wandb.sweep(sweep_config, project="my-project")
wandb.agent(sweep_id, function=train, count=50)  # 50 trials
```

### Artifacts & Model Registry
```python
artifact = wandb.Artifact('model', type='model')
artifact.add_file('model.pth')
wandb.log_artifact(artifact, aliases=['best', 'production'])
```

### Integrations
- **HuggingFace**: `TrainingArguments(report_to="wandb")`
- **PyTorch Lightning**: `Trainer(logger=WandbLogger(project="demo", log_model=True))`
- **Keras**: `model.fit(..., callbacks=[WandbCallback()])`

### Best Practices
- Organize with tags, groups, and descriptive run names
- Log system metrics (GPU util, memory) alongside training metrics
- Use offline mode (`WANDB_MODE=offline`) for unstable connections
- Save predictions as `wandb.Table` for analysis

---

## Mode C: LLM Evaluation (lm-eval-harness)

**Trigger:** "benchmark LLM", "evaluate model", "MMLU", "GSM8K", "lm-eval"

lm-eval-harness for academic LLM benchmarking:
```bash
pip install lm-eval
lm-eval --model hf --model_args pretrained=<model> --tasks mmlu,gsm8k --batch_size auto
```

Common task suites: MMLU (knowledge), GSM8K (math), HellaSwag (commonsense), ARC (reasoning), TruthfulQA (truthfulness), Winogrande (coreference).

Use `--tasks <task1>,<task2>` for multi-task evaluation. `--batch_size auto` for optimal throughput. Results output as JSON with per-task scores.
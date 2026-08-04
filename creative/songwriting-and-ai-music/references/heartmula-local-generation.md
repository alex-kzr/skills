# HeartMuLa — Local AI Music Generation

HeartMuLa is a Suno-like local model for generating songs from lyrics + tags. Use when Suno API is unavailable or you need offline/local generation.

## When to Use

- Local/offline music generation (no Suno API access)
- Custom model fine-tuning experiments
- Privacy-sensitive content generation

## Hardware Requirements

- GPU with ≥8GB VRAM (16GB+ recommended)
- CUDA 11.8+ (NVIDIA) or ROCm (AMD)
- 16GB+ system RAM

## Installation

```bash
# Clone and install
git clone https://github.com/heartmula/heartmula.git
cd heartmula
pip install -r requirements.txt

# Download model weights
python download_models.py
```

## GPU / CUDA

Verify CUDA is available:
```python
import torch
print(torch.cuda.is_available())  # Should return True
print(torch.cuda.get_device_name(0))
```

If CUDA is not detected:
- Ensure NVIDIA drivers are installed (`nvidia-smi` should work)
- Reinstall PyTorch with CUDA support: `pip install torch --index-url https://download.pytorch.org/whl/cu118`

## Usage

```bash
# Generate from lyrics + tags
python generate.py \
  --lyrics "lyrics.txt" \
  --tags "pop, upbeat, female vocals" \
  --output output.wav

# Interactive mode
python generate.py --interactive
```

## Pitfalls

1. **OOM errors** — reduce batch size or use `--half-precision`
2. **Slow generation on CPU** — HeartMuLa requires GPU for reasonable speed
3. **Model weight download fails** — check network/proxy, try manual download from releases page
4. **Audio quality** — experiment with temperature and top_k parameters

## Links

- GitHub: https://github.com/heartmula/heartmula
- Model weights: see releases page
- Discussion: see GitHub discussions

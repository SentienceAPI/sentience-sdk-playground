# Command Reference - Local LLM

All commands should be run from the `local_llm` directory:

```bash
cd playground/local_llm
```

---

## 🚀 Quick Start (Recommended)

### Option 1: Interactive Script (Checks everything)
```bash
./run_demo.sh
```

### Option 2: Direct Run (No checks)
```bash
./run.sh
```

### Option 3: Python Direct
```bash
python demos/google_search.py
```

---

## 🧹 Before Running: Clean Up Disk Space

### Check what's taking space
```bash
python check_cache_sizes.py
```

### Quick cleanup (one command, frees ~4-5 GB)
```bash
npm cache clean --force && pip cache purge && brew cleanup -s && rm -rf ~/.cargo/registry && rm -rf ~/.gradle/caches
```

### Interactive cleanup (step-by-step)
```bash
bash cleanup_mac_cache.sh
```

---

## 📦 Installation

### Install dependencies
```bash
pip install -r requirements.txt
```

### Verify setup
```bash
python test_setup.py
```

Expected output: `✅ All tests passed!`

---

## 🤖 Running Demos

### Google search demo (default: Qwen 2.5 3B)
```bash
python demos/google_search.py
```

### Compare multiple models
```bash
python compare_models.py
```

---

## 🔧 Model Management

### Check if model is cached
```bash
ls -lh ~/.cache/huggingface/hub/
```

### Download model manually (optional)
```bash
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = 'Qwen/Qwen2.5-3B-Instruct'
print(f'Downloading {model_name}...')
AutoTokenizer.from_pretrained(model_name)
AutoModelForCausalLM.from_pretrained(model_name)
print('✅ Download complete!')
"
```

### Clear model cache (if you need space)
```bash
rm -rf ~/.cache/huggingface/
```

**Warning**: Will need to re-download models!

---

## 🐛 Troubleshooting

### Check Python version (need 3.8+)
```bash
python --version
```

### Check available disk space
```bash
df -h .
```

### Check GPU availability
```bash
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

### Check installed packages
```bash
pip list | grep -E "transformers|torch|sentience"
```

### Re-install dependencies
```bash
pip install --upgrade -r requirements.txt
```

---

## 📊 View Results

### List all demo runs
```bash
ls -ltr google_search_*/screenshots/
```

### View latest screenshots
```bash
open $(ls -td google_search_*/screenshots/*/ | head -1)
```

### View token summary
```bash
cat $(ls -t google_search_*/screenshots/*/token_summary_data.json | head -1) | python -m json.tool
```

---

## 🎨 Customization

### Use different model (edit demos/google_search.py)

**Smaller model (Gemma 2B, ~5 GB)**:
```python
llm_config = {
    "type": "local",
    "model_name": "google/gemma-2-2b-it",
    "device": "auto"
}
```

**Larger model (Qwen 7B, ~15 GB)**:
```python
llm_config = {
    "type": "local",
    "model_name": "Qwen/Qwen2.5-7B-Instruct",
    "device": "auto"
}
```

**Use 4-bit quantization (saves 75% VRAM)**:
```python
llm_config = {
    "type": "local",
    "model_name": "Qwen/Qwen2.5-3B-Instruct",
    "device": "auto",
    "load_in_4bit": True  # ← Add this!
}
```

**Use CPU instead of GPU**:
```python
llm_config = {
    "type": "local",
    "model_name": "Qwen/Qwen2.5-3B-Instruct",
    "device": "cpu"  # ← Change to cpu
}
```

**Use cloud LLM for comparison**:
```python
llm_config = {
    "type": "cloud",
    "model": "gpt-4-turbo-preview"
    # Make sure OPENAI_API_KEY is set in .env
}
```

---

## 📝 Documentation

### Read quick start
```bash
cat QUICK_START.md
```

### Read full README
```bash
cat README.md
```

### Read implementation summary
```bash
cat IMPLEMENTATION_SUMMARY.md
```

### Read design doc
```bash
cat ../../docs/LOCAL_LLM_INTEGRATION.md
```

---

## 🔍 Useful One-Liners

### Find large files (>100MB)
```bash
find ~ -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -20
```

### Find largest directories in home
```bash
du -sh ~/* | sort -hr | head -20
```

### Check total cache size
```bash
du -sh ~/.cache/
```

### Check Python cache
```bash
find . -type d -name "__pycache__" -exec du -sh {} \; | head -10
```

### Remove Python cache in current project
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
```

---

## 🎯 Common Workflows

### First-time setup
```bash
# 1. Clean up space
python check_cache_sizes.py
npm cache clean --force && pip cache purge && brew cleanup -s

# 2. Install
pip install -r requirements.txt

# 3. Verify
python test_setup.py

# 4. Run
./run_demo.sh
```

### Daily usage
```bash
# Just run it!
./run.sh
```

### Compare different models
```bash
# Edit compare_models.py to select models
python compare_models.py
```

### Troubleshooting
```bash
# 1. Check setup
python test_setup.py

# 2. Check space
python check_cache_sizes.py

# 3. Reinstall if needed
pip install --upgrade -r requirements.txt

# 4. Try with CPU
# Edit demos/google_search.py: device="cpu"
python demos/google_search.py
```

---

## 💡 Pro Tips

1. **First run is slow** - Model downloads only once
2. **Use GPU if available** - 8x faster than CPU
3. **Use 4-bit quantization** if limited VRAM
4. **Clean cache regularly** to save space
5. **Check cache before downloading** new models

---

**Quick Start**: `./run_demo.sh` 🚀

from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

# Paths
BASE_MODEL = "microsoft/Phi-3-mini-4k-instruct"
ADAPTER_PATH = "./soprano_adapter"
OUTPUT_DIR = "./merged_model"

# Detect available device
if torch.cuda.is_available():
    device = "cuda"
    print(f"✓ Using GPU: {torch.cuda.get_device_name(0)}")
    use_device_map = "auto"
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    device = "mps"
    print("✓ Using Apple Silicon GPU (MPS)")
    # MPS doesn't work well with device_map="auto", load to CPU first then move
    use_device_map = None
else:
    device = "cpu"
    print("⚠ Using CPU (this will be slower - consider using GPU if available)")
    use_device_map = None

print("\n--- Loading base model ---")
# For MPS, load to CPU first to avoid offloading issues, then move to MPS
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16 if device != "cpu" else torch.float32,
    trust_remote_code=True,
    device_map=use_device_map,
    low_cpu_mem_usage=False  # Disable low memory mode to avoid offloading
)

# Move to device manually for MPS/CPU
if use_device_map is None:
    base_model = base_model.to(device)

print("\n--- Loading LoRA adapter ---")
try:
    # Load adapter without device_map to avoid structure issues
    model = PeftModel.from_pretrained(
        base_model, 
        ADAPTER_PATH,
        device_map=None  # Don't use device_map for adapter loading
    )
    
    # Move to device manually
    if use_device_map is None:
        model = model.to(device)
    
    print("✓ Adapter loaded successfully")
except Exception as e:
    print(f"\n❌ Error loading adapter: {e}")
    print("\nTroubleshooting:")
    print("1. Verify adapter was trained on Phi-3-mini-4k-instruct (not Phi-2)")
    print("2. Check that soprano_adapter/adapter_model.safetensors exists")
    print("3. Verify adapter_config.json target_modules match Phi-3 architecture")
    print("4. Try loading on CPU instead: set device='cpu' in the script")
    raise

print("\n--- Merging weights... ---")
model = model.merge_and_unload()

print("\n--- Saving full model ---")
model.save_pretrained(OUTPUT_DIR)

print("\n--- Saving tokenizer... ---")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
tokenizer.save_pretrained(OUTPUT_DIR)

print("\n" + "="*60)
print("✓ Done! Model merged and saved to:", OUTPUT_DIR)
print("="*60)
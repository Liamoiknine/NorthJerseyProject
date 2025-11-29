from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

# Paths
BASE_MODEL = "microsoft/phi-2"
ADAPTER_PATH = "./soprano_adapter"
OUTPUT_DIR = "./merged_model"

print("--- Loading base model ---")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    trust_remote_code=True
)

print("--- Loading LoRA adapter ---")
# Force loading to CPU explicitly to avoid MPS/CUDA complexity during merge
model = PeftModel.from_pretrained(
    base_model, 
    ADAPTER_PATH,
    device_map="cpu" 
)

print("--- Merging weights... ---")
model = model.merge_and_unload()

print("--- Saving full model ---")
model.save_pretrained(OUTPUT_DIR)

print("--- Saving tokenizer... ---")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
tokenizer.save_pretrained(OUTPUT_DIR)

print("Done! Model merged and saved.")
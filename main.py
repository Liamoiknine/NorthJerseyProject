from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from torch.quantization import quantize_dynamic
import torch
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to allow frontend to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for images, CSS, etc.
static_dir = Path(__file__).parent / "static"
# Check if static dir exists before mounting to prevent crash loop if missing
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

BASE_MODEL = "microsoft/phi-2"
# Use absolute path to adapter directory
ADAPTER_PATH = str(Path(__file__).parent / "soprano_adapter")

# Global variables for model and tokenizer
model = None
tokenizer = None

@app.on_event("startup")
async def load_model():
    """Load the model and tokenizer on startup"""
    global model, tokenizer
    
    logger.info("=" * 60)
    logger.info("Starting model loading process...")
    logger.info("=" * 60)
    
    torch.set_num_threads(4)
    logger.info("Set torch threads to 4 for CPU optimization")
    
    # Load tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token
    logger.info("✓ Tokenizer loaded")

    # Load base model
    logger.info("Loading base model...")
    # Load model without device_map first to avoid structure issues with PEFT
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        dtype=torch.float32, # Use float32 for CPU stability before quantization
        low_cpu_mem_usage=True
    )
    logger.info("✓ Base model loaded")

    # Load LoRA adapter (must be done before device_map)
    logger.info("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(model, ADAPTER_PATH)
    logger.info("✓ LoRA adapter loaded")
    
    logger.info("Merging LoRA weights into base model...")
    model = model.merge_and_unload()
    logger.info("✓ Weights merged")

    logger.info("Applying Dynamic Quantization (int8)...")
    model = quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )
    logger.info("✓ Model quantized to int8")
    
    model.eval()
    logger.info("✓ Model ready for inference")
    
    logger.info("=" * 60)
    logger.info("Model loading complete! API is ready to accept requests.")
    logger.info("=" * 60)

class Query(BaseModel):
    prompt: str

def generate_response(prompt):
    text = (
        f"Instruction: {prompt}\n"
        f"Write 1–3 complete sentences.\n"
        f"Response:\n"
    )

    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=150,
            do_sample=True,
            temperature=1.1,
            top_p=0.95,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id
        )

    out = tokenizer.decode(output
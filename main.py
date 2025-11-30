from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse # <--- ADDED StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import logging
from pathlib import Path
from prometheus_fastapi_instrumentator import Instrumentator
import os
from contextlib import asynccontextmanager
from typing import List, Optional, Tuple
import tiktoken
import json # <--- ADDED json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Llama instance
llm = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP LOGIC
    global llm
    logger.info("=" * 60)
    logger.info("Initializing Llama.cpp Engine...")
    logger.info("=" * 60)
    
    try:
        threads = os.cpu_count() or 2
        
        # Load the GGUF model directly
        llm = Llama(
            model_path="./tony.gguf",
            n_ctx=4096,
            n_threads=threads,
            verbose=False
        )
        logger.info(f"✓ Model loaded successfully with {threads} threads!")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise e
    
    yield
    
    llm = None
    logger.info("Shutting down model...")

# --- APP INITIALIZATION ---
app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrumentation for Prometheus
Instrumentator().instrument(app).expose(app)

# Static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Token counting setup
try:
    tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception as e:
    logger.warning(f"Failed to load tiktoken: {e}. Token counting may be inaccurate.")
    tokenizer = None

# Constants for token management
MAX_CONTEXT = 4096
SYSTEM_PROMPT_TOKENS = 150 
CURRENT_INPUT_TOKENS = 512
RESPONSE_BUFFER_TOKENS = 512
SAFETY_MARGIN_TOKENS = 100
HISTORY_TOKENS_AVAILABLE = MAX_CONTEXT - SYSTEM_PROMPT_TOKENS - CURRENT_INPUT_TOKENS - RESPONSE_BUFFER_TOKENS - SAFETY_MARGIN_TOKENS

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class Query(BaseModel):
    prompt: str
    history: Optional[List[Message]] = []

@app.get("/")
def read_root():
    return {"message": "Ay-oh! The GGUF API is runnin'. Whaddaya want?"}

@app.get("/health")
def health_check():
    if llm is None:
        return {"status": "loading", "message": "Model is still loading..."}, 503
    return {"status": "ready", "message": "Model is loaded and ready"}

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken with cl100k_base encoding."""
    if tokenizer is None:
        return len(text) // 4
    return len(tokenizer.encode(text))

def format_message_for_prompt(role: str, content: str) -> str:
    """Format a message for the Phi-3 prompt template."""
    if role == "user":
        return f"<|user|>\n{content}<|end|>\n"
    else:  # assistant
        return f"<|assistant|>\n{content}<|end|>\n"

def build_conversation_prompt(system_prompt: str, history: List[Message], current_input: str) -> Tuple[str, int]:
    """
    Build full conversation prompt with FIFO history management.
    """
    # Start with system prompt
    system_formatted = f"<s><|user|>\n{system_prompt}\n\n"
    system_tokens = count_tokens(system_formatted)
    
    # Format current input
    current_formatted = format_message_for_prompt("user", current_input)
    current_tokens = count_tokens(current_formatted)
    
    used_tokens = system_tokens + current_tokens
    available_for_history = MAX_CONTEXT - used_tokens - RESPONSE_BUFFER_TOKENS - SAFETY_MARGIN_TOKENS
    
    history_text = ""
    history_tokens = 0
    
    i = 0
    while i < len(history):
        if i + 1 < len(history) and history[i].role == "user" and history[i + 1].role == "assistant":
            user_msg = history[i]
            assistant_msg = history[i + 1]
            
            user_formatted = format_message_for_prompt("user", user_msg.content)
            assistant_formatted = format_message_for_prompt("assistant", assistant_msg.content)
            
            pair_text = user_formatted + assistant_formatted
            pair_tokens = count_tokens(pair_text)
            
            if history_tokens + pair_tokens > available_for_history:
                break 
            
            history_text += pair_text
            history_tokens += pair_tokens
            i += 2
        else:
            msg = history[i]
            msg_formatted = format_message_for_prompt(msg.role, msg.content)
            msg_tokens = count_tokens(msg_formatted)
            
            if history_tokens + msg_tokens > available_for_history:
                break
            
            history_text += msg_formatted
            history_tokens += msg_tokens
            i += 1
    
    assistant_start = "<|assistant|>\n"
    full_prompt = system_formatted + history_text + current_formatted + assistant_start
    total_tokens = count_tokens(full_prompt)
    
    logger.debug(f"Prompt tokens: system={system_tokens}, history={history_tokens}, current={current_tokens}, total={total_tokens}")
    
    return full_prompt, total_tokens

@app.post("/generate")
async def generate(query: Query):
    if llm is None:
        return {"error": "Model is still loading."}, 503
    
    # System prompt
    system_prompt = "Respond like Tony Soprano would. He is slightly agitated and on-edge. Be somewhat vulger in your response."
    
    # Build full conversation prompt with history
    formatted_prompt, prompt_tokens = build_conversation_prompt(
        system_prompt,
        query.history or [],
        query.prompt
    )
    
    if prompt_tokens > MAX_CONTEXT - RESPONSE_BUFFER_TOKENS:
        logger.warning(f"Prompt tokens ({prompt_tokens}) approaching context limit. Response may be truncated.")
    
    # --- STREAMING LOGIC ---
    def token_generator():
        stream = llm(
            formatted_prompt,
            max_tokens=512, 
            stop=["<|end|>", "<|user|>", "User:", "\nUser", "Instruct:"],
            echo=False,
            stream=True # <--- Enable Streaming
        )
        
        for output in stream:
            # Extract the token text
            token = output["choices"][0]["text"]
            
            # Yield in SSE format (data: <json>\n\n)
            # This allows the frontend to parse it easily
            yield f"data: {json.dumps({'token': token})}\n\n"
            
        # Optional: Send a [DONE] message if your frontend expects it
        yield "data: [DONE]\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=300,
        limit_concurrency=5
    )
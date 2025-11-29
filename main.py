from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import logging
from pathlib import Path
from prometheus_fastapi_instrumentator import Instrumentator
import os
from contextlib import asynccontextmanager

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
            n_ctx=2048,
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
# Now 'lifespan' is defined, so we can pass it in
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

class Query(BaseModel):
    prompt: str

@app.get("/")
def read_root():
    return {"message": "Ay-oh! The GGUF API is runnin'. Whaddaya want?"}

@app.get("/health")
def health_check():
    if llm is None:
        return {"status": "loading", "message": "Model is still loading..."}, 503
    return {"status": "ready", "message": "Model is loaded and ready"}

@app.post("/generate")
def generate(query: Query):
    if llm is None:
        return {"error": "Model is still loading."}, 503
    
    # Prompt formatting
    formatted_prompt = f"Instruct: Respond like Tony Soprano would. He is slightly agitated and on-edge. Be somewhat vulger in your response.\nUser: {query.prompt}\nOutput:"
    
    # Inference
    output = llm(
        formatted_prompt,
        max_tokens=128, 
        stop=["User:", "\nUser", "Instruct:"],
        echo=False
    )
    
    response_text = output["choices"][0]["text"].strip()
    return {"response": response_text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=300,
        limit_concurrency=5
    )
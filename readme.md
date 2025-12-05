# North Jersey Project

A conversational AI chatbot that simulates Tony Soprano, built with a fine-tuned language model and streaming web interface.

## Architecture

- **Backend**: FastAPI server using llama.cpp with GGUF model format
- **Frontend**: Next.js application with TypeScript and Tailwind CSS
- **Model**: Fine-tuned Phi-3 model with custom adapter weights

## Requirements

- Python 3.9+
- Node.js 18+
- `tony.gguf` model file (place in project root)

## Setup

### Backend

```bash
pip install -r requirements.txt
pip install llama-cpp-python
python main.py
```

Server runs on `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_ENDPOINT` environment variable to your backend URL.

## Features

- Streaming responses via Server-Sent Events (SSE)
- Multi-turn conversation with context management
- Token-based input limits and history truncation
- Prometheus metrics instrumentation

## Deployment

Docker and Kubernetes configurations are included. The Dockerfile builds a containerized version of the backend service.

## Model Training

Training data and scripts are located in `data/` and `training/`. The model combines base Phi-3 weights with a custom LoRA adapter trained on character-specific dialogue.

## Docker Hub
https://hub.docker.com/r/mdallolmo1/soprano-bot

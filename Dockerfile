FROM python:3.9-slim

WORKDIR /app

# 1. Install system dependencies for compiling llama-cpp (gcc, g++, cmake)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Install llama-cpp-python (Compiling from source)
# We set CMAKE_ARGS to ensure it optimizes for standard CPUs (AVX/AVX2)
# instead of specific hardware that might not match the build node.
RUN CMAKE_ARGS="-DGGML_BLAS=OFF" pip install llama-cpp-python

# 4. Copy app code and model
COPY tony.gguf .
COPY main.py .

CMD ["python", "main.py"]
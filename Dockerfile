#use a lightweight Python base image
FROM python:3.11-slim

#set working directory inside the container
WORKDIR /app

#install system tools needed for some ML libraries
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

#copy the requirements file first (better for Docker caching)
COPY requirements.txt .

#insastall Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

#cpoyy the rest of your application code
COPY main.py .

#copy the lora-weights folder
COPY lora-weights ./lora-weights

#expose the port the app runs on
ENV PORT=8000
EXPOSE 8000

#the command to start the server when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

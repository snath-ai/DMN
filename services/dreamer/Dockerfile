FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root context
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy logic
COPY src/ ./src/
COPY services/dreamer/dreamer_worker.py ./services/dreamer/

# Environment setup
ENV PYTHONPATH=/app/src
ENV OLLAMA_HOST=host.docker.internal
ENV PYTHONUNBUFFERED=1

# Entrypoint
CMD ["python", "services/dreamer/dreamer_worker.py"]

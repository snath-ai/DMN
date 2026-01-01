FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (e.g. for build tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root context
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# We assume source code is mounted at runtime to /app/src
# But we copy it for the build image just in case
COPY src/ ./src/

# Environment setup
ENV PYTHONPATH=/app/src
ENV OLLAMA_HOST=host.docker.internal

# Expose Streamlit port
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entrypoint
CMD ["streamlit", "run", "src/lar/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Dockerfile for RAG Service

FROM python:3.10-slim

# Set working directory
WORKDIR /app/rag_service

# Install system dependencies (for llama-cpp-python)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY rag_service/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy RAG service code
COPY rag_service/ .

# Copy shared data and models directories
# These should exist in the repository
COPY data/ /app/data/
COPY models/ /app/models/

# Copy config that points to shared folders
COPY rag_service/config_paths_rag.py .

# Create startup script
RUN echo '#!/bin/bash\n\
if [ ! -f /app/data/faiss_civil.index ]; then\n\
    echo "Warning: FAISS index not found"\n\
fi\n\
uvicorn rag_app:app --host 0.0.0.0 --port 8001' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["uvicorn", "rag_app:app", "--host", "0.0.0.0", "--port", "8001"]

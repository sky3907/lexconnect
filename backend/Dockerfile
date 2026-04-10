# Dockerfile for Backend Service

FROM python:3.10-slim

# Set working directory
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy config file from root
COPY config_paths.py /app/
COPY suppress_warnings.py /app/

# Create startup script with health check for RAG service
RUN echo '#!/bin/bash\n\
echo "Waiting for RAG service to be ready..."\n\
until curl -f http://${RAG_SERVICE_URL:-http://localhost:8001}/health; do\n\
    echo "RAG service not ready, waiting..."\n\
    sleep 5\n\
done\n\
echo "RAG service is ready!"\n\
uvicorn app:app --host 0.0.0.0 --port 8000' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

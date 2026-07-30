# ---------------------------------------------------------------
# loader/Dockerfile
# GraphChatEngine – Loader Service
# Base: python:3.11-slim  (Milestone 04 – Kafka Consumer)
# ---------------------------------------------------------------

FROM python:3.11-slim

# Metadata labels
LABEL maintainer="GraphChatEngine Team"
LABEL service="loader"
LABEL milestone="04-kafka-consumer"

# Set working directory inside the container
WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Set PYTHONPATH so absolute imports work
ENV PYTHONPATH=/app

# No port to expose — loader is an internal worker, not an HTTP server

# Run the consumer process
CMD ["python", "consumer.py"]

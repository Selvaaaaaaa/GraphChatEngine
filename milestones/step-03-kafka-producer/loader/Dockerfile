# ---------------------------------------------------------------
# loader/Dockerfile
# GraphChatEngine – Loader Service
# Base: python:3.11-slim  (Milestone 01)
# ---------------------------------------------------------------

FROM python:3.11-slim

# Metadata labels
LABEL maintainer="GraphChatEngine Team"
LABEL service="loader"
LABEL milestone="01-project-foundation"

# Set working directory inside the container
WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# No port to expose — loader is an internal worker, not a server

# Run the loader process
CMD ["python", "loader.py"]

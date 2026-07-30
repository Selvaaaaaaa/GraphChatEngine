# ---------------------------------------------------------------
# api/Dockerfile
# GraphChatEngine – API Service
# Base: python:3.11-slim  (Milestone 01)
# ---------------------------------------------------------------

FROM python:3.11-slim

# Metadata labels
LABEL maintainer="GraphChatEngine Team"
LABEL service="api"
LABEL milestone="01-project-foundation"

# Set working directory inside the container
WORKDIR /app

# Install Python dependencies first (layer caching: only re-run on
# requirements.txt changes, not on source code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the port Uvicorn will listen on
EXPOSE 8000

# Run the FastAPI application with Uvicorn
# --host 0.0.0.0  → listen on all interfaces (required inside Docker)
# --reload        → disabled in production; enable during dev if needed
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

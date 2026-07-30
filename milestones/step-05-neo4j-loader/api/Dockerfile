# ---------------------------------------------------------------
# api/Dockerfile
# GraphChatEngine – API Service
# Base: python:3.11-slim  (Milestone 01.5 – Project Hardening)
#
# WHY python:3.11-slim?
#   Minimal attack surface, no unnecessary OS packages.
#   wget and curl are NOT included in this image.
#   Therefore, the health check uses Python's built-in `urllib`
#   (always available) instead of wget — zero extra dependencies.
# ---------------------------------------------------------------

FROM python:3.11-slim

# Metadata labels
LABEL maintainer="GraphChatEngine Team"
LABEL service="api"
LABEL milestone="01.5-project-hardening"

# Set working directory inside the container
WORKDIR /app

# Install Python dependencies first (layer caching: only re-run on
# requirements.txt changes, not on source code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire api/ package source under /app/api/
# so that `from api.xxx import ...` resolves correctly
COPY . ./api/

# Add /app to PYTHONPATH so Python finds the `api` package
ENV PYTHONPATH=/app

# Expose the port Uvicorn will listen on
EXPOSE 8000

# Health check using Python's built-in urllib.
# WHY this approach:
#   - python:3.11-slim does NOT include wget or curl
#   - Python is always present in this image
#   - urllib is part of the standard library — no extra install needed
#   - This is the zero-dependency, most portable health check option
HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the FastAPI application with Uvicorn
# --host 0.0.0.0  → listen on all interfaces (required inside Docker)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

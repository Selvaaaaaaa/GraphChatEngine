"""
api/__init__.py
---------------
GraphChatEngine – API Package

Makes the `api/` directory a Python package so that absolute imports
like `from api.services.ingest_service import ...` resolve correctly
both inside Docker (PYTHONPATH=/app) and in local development.
"""

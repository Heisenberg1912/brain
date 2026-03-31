"""Vercel serverless entry point — re-exports the FastAPI ASGI app."""
import sys
import os

# Ensure the project root is on sys.path so `api.*` and `brain.*` are importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app  # noqa: F401, E402 — Vercel picks up the `app` export

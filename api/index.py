"""Vercel serverless entry-point.

Vercel looks for an ASGI/WSGI app in api/index.py.
We simply re-export the FastAPI app created in app.main.
"""
from app.main import app  # noqa: F401

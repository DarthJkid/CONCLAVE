"""CONCLAVE FastAPI orchestrator application."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="CONCLAVE",
    description="Calibrated Orchestrated Network of Criterion-level LLM Agents for Variant Evaluation",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "CONCLAVE API is running. See /docs for the API specification."}

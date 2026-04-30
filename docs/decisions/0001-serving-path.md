# ADR 0001: Serving Path — FastAPI over Flask/Django

**Status:** Accepted
**Date:** 2024-01-01

## Context
We need an HTTP serving layer for CONCLAVE that supports async I/O (required for parallel LLM calls), automatic OpenAPI schema generation, and Pydantic-native request/response validation.

## Decision
Use **FastAPI** as the serving framework.

## Consequences
- Async endpoints align naturally with `asyncio`-based LLM client calls.
- Pydantic v2 models in `conclave.schemas` are used directly as request/response types.
- Auto-generated `/docs` endpoint aids rapid prototyping.
- FastAPI's limited built-in auth requires external middleware for production deployments.

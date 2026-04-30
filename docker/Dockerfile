FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Copy source
COPY src/ src/
COPY conf/ conf/
COPY app/ app/

# Install the package
RUN uv pip install --no-deps -e .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "conclave.orchestrator.app:app", "--host", "0.0.0.0", "--port", "8000"]

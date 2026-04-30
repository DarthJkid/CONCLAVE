.PHONY: install test lint format type-check clean docs

install:
	uv sync --all-extras

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit -v

test-integration:
	uv run pytest tests/integration -v

test-property:
	uv run pytest tests/property -v

test-determinism:
	uv run pytest tests/determinism -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

type-check:
	uv run mypy src/

pre-commit:
	uv run pre-commit run --all-files

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

docs:
	echo "Documentation lives in docs/"

serve:
	uv run uvicorn conclave.orchestrator.app:app --reload

ui:
	uv run streamlit run app/streamlit_app.py

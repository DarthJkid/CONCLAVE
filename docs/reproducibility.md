# Reproducibility Guide

## Reproducing CONCLAVE Results

### Prerequisites
- Python 3.11 (see `.python-version`)
- `uv` package manager

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DarthJkid/CONCLAVE
   cd CONCLAVE
   ```

2. **Install dependencies:**
   ```bash
   uv sync --all-extras
   ```

3. **Set environment variables:**
   ```bash
   cp .env.example .env  # then fill in API keys
   ```

4. **Run determinism tests:**
   ```bash
   make test-determinism
   ```

5. **Reproduce evaluation metrics:**
   ```bash
   # TODO: add evaluation script
   ```

## Version Pinning
- Python version: `.python-version`
- Dependency versions: `uv.lock`
- Model snapshots: `conf/models/default.yaml`
- Data versions: `conf/data/default.yaml`

## DVC Data Tracking
Large data files are tracked with DVC. To pull data:
```bash
dvc pull
```

# Nebius Assignment

A FastAPI service that accepts a GitHub repository URL and returns an LLM-generated summary.

## Requirements

- Python 3.11
- [uv](https://docs.astral.sh/uv/)

## Setup

1. Install dependencies:

   ```bash
   make install
   ```

2. Copy the example env file and fill in your API key:

   ```bash
   cp .env.example .env
   ```

   Then set `NEBIUS_API_KEY` in `.env`.

## Running the API

```bash
make run_api
```

## Running Tests

```bash
make test
```

The API will be available at `http://localhost:8000`.

## API Docs

| URL                           | Description              |
| ----------------------------- | ------------------------ |
| `http://localhost:8000/docs`  | Swagger UI (interactive) |
| `http://localhost:8000/redoc` | ReDoc                    |

## Endpoints

### `POST /summarize`

Accepts a GitHub repository URL and returns an LLM-generated summary.

#### Request

```json
{
  "url": "https://github.com/owner/repo"
}
```

#### Response

```json
{
  "summary": "...",
  "technologies": ["..."],
  "structure": "..."
}
```

## What did we fetch?

### Tier 1 — Always fetch (high signal, low size)

README.md — author-written description, the single best signal
Repo metadata — description, language, topics, stars (free from GitHub API)
Package manifests — pyproject.toml, package.json, Cargo.toml, go.mod, requirements.txt — tells you language, dependencies, purpose

### Tier 2 — Fetch selectively (medium signal, variable size)

Directory tree — full structure in one API call, no content needed, gives the LLM shape of the project
Top-level source files — main.py, app.py, index.ts, cmd/ etc.
Key config files — Dockerfile, docker-compose.yml, .github/workflows/ (CI tells you a lot)


### Tier 3 — Skip entirely

Lock files (uv.lock, package-lock.json, yarn.lock)
Binary files (images, compiled artifacts, fonts)
Dependency directories (node_modules/, .venv/, __pycache__/)
Generated/build output (dist/, build/, *.min.js)
Large data files (*.csv, *.parquet, large *.json)
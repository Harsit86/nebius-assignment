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

2. Copy the example env file and fill in your API keys:

   ```bash
   cp .env.example .env
   ```

   Then set `NEBIUS_API_KEY` in `.env`.

3. (Recommended) Add a GitHub personal access token to `.env`:

   ```env
   GITHUB_TOKEN=ghp_your_token_here
   ```

   **Why:** The GitHub API allows only 60 unauthenticated requests per hour. This service
   makes several API calls per repository (metadata, README, file tree, root-level files),
   so you will hit the limit quickly. A token raises the limit to 5,000 requests per hour.

   **How to generate one:**
   1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
   2. Click **Generate new token (classic)**
   3. Give it a name (e.g. `nebius-assignment`)
   4. No scopes are needed — public repository data is accessible without any permissions
   5. Click **Generate token** and copy the value into `.env`

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

## Model

The service uses `openai/gpt-oss-20b` via the Nebius AI API. It was chosen because:

- **Lightweight** — 20B parameters keeps inference fast and cost low
- **High context window** — handles large repositories with long READMEs and many files without truncation
- **Strong reasoning** — sufficient capability for structured summarisation tasks
- **OpenAI-compatible API** — works with the standard OpenAI SDK, no custom integration needed

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
Dependency directories (node_modules/, .venv/, \_\_pycache\_\_/)
Generated/build output (dist/, build/, *.min.js)
Large data files (*.csv, *.parquet, large *.json)
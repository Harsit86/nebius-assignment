# Nebius Assignment

A FastAPI service that accepts a GitHub repository URL and returns an LLM-generated summary.

## Setup

1. Install [uv](https://docs.astral.sh/uv/) (Python package manager):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:

   ```bash
   make install
   ```

3. Copy the example env file and set your API key:

   ```bash
   cp .env.example .env
   ```

   Then set `NEBIUS_API_KEY` in `.env`.

4. (Recommended) Add a GitHub personal access token to `.env`:

   ```env
   GITHUB_TOKEN=ghp_your_token_here
   ```

   The GitHub API allows only 60 unauthenticated requests per hour. This service makes
   several API calls per repository, so you will hit the limit quickly. A token raises
   it to 5,000 requests per hour.

   To generate one: go to [github.com/settings/tokens](https://github.com/settings/tokens),
   click **Generate new token (classic)**, give it a name, and select no scopes (public
   repository data requires none). Copy the value into `.env`.

## Running the API

```bash
make run_api
```

The API will be available at `http://localhost:8000`.

## Running Tests

```bash
make test
```

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
  "github_url": "https://github.com/owner/repo"
}
```

#### Response (success)

```json
{
  "summary": "...",
  "technologies": ["..."],
  "structure": "..."
}
```

#### Response (error)

```json
{
  "status": "error",
  "message": "Description of what went wrong"
}
```

## Which model you chose and why

I am using `openai/gpt-oss-20b` because it has support for large context window which is essential for repositories with long READMEs and many files,
strong reasoning capability and instruction-following for structured JSON output.
Furthermore, compute and inference costs are low due to its 20B parameter size.

## Approach to handling repository contents

My goal  wasto maximise signal sent to the LLM while minimising API calls and token usage.

**What I fetched:**

- **Repo metadata** (name, description, language, topics, stars) — free from the GitHub
  API, zero extra requests, high signal.
- **README** - the author's own description of the project; the single best signal.
- **Full file tree** - fetched in one API call with the recursive tree endpoint. Gives
  the LLM the shape of the project without downloading any file content.
- **All root-level files** - config and manifest files (`pyproject.toml`, `package.json`,
  `Dockerfile`, etc.) live at the root and reveal language, dependencies, and
  infrastructure. Fetching everything at the root is language-agnostic and avoids
  hardcoding specific filenames.

**What I skip:**

Any file larger than 100 KB is excluded, using the size metadata returned by the GitHub
tree API (no extra requests needed). This single rule efficiently filters out lock files,
generated bundles, large data files, and binary assets. This excludes all content that adds tokens
but no analytical value. Subdirectory source files are also skipped; the tree listing
already tells the LLM how the code is organised without the cost of fetching every file.

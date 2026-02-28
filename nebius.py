import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from github import RepoContents

load_dotenv()

NEBIUS_MODEL = "openai/gpt-oss-20b"
API_KEY = os.environ.get("NEBIUS_API_KEY")
if not API_KEY:
    raise ValueError("NEBIUS_API_KEY is not set in environment variables")

_client = AsyncOpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ.get("NEBIUS_API_KEY"),
)

_SYSTEM_PROMPT = (
    "You are a software project analyst. Analyse the GitHub repository data "
    "provided and return a JSON object with exactly these three fields:\n\n"
    '- "summary": 1-3 sentences describing what the project does and its purpose.\n'
    '- "technologies": an array of technology, framework, and library names used '
    '(e.g. ["Python", "FastAPI", "PostgreSQL"]).\n'
    '- "structure": 1-4 sentences describing the project layout. '
    "Reference key directories using backtick-formatted paths "
    '(e.g. `src/`, `tests/`, `docs/`) and note the architecture pattern or entry point.\n\n'
    "Return only valid JSON. No markdown, no code blocks, no explanation."
)


def _build_user_message(contents: RepoContents) -> str:
    parts: list[str] = []

    meta = contents.metadata
    parts.append(f"Repository: {meta.name}")
    if meta.description:
        parts.append(f"Description: {meta.description}")
    if meta.language:
        parts.append(f"Language: {meta.language}")
    if meta.topics:
        parts.append(f"Topics: {', '.join(meta.topics)}")
    parts.append(f"Stars: {meta.stars}")

    if contents.readme:
        parts.append("\n## README")
        parts.append(contents.readme)

    if contents.manifests:
        parts.append("\n## Root-level configuration files")
        for filename, content in contents.manifests.items():
            parts.append(f"\n### {filename}")
            parts.append(content)

    if contents.tree:
        parts.append("\n## File tree")
        parts.append("\n".join(contents.tree))

    return "\n".join(parts)


async def summarize_repo(contents: RepoContents) -> dict:
    user_message = _build_user_message(contents)

    response = await _client.chat.completions.create(
        model=NEBIUS_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [{"type": "text", "text": user_message}],
            },
        ],
    )

    return json.loads(response.choices[0].message.content)

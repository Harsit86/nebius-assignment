from urllib.parse import urlparse

import httpx
from fastapi import HTTPException


GITHUB_API_BASE = "https://api.github.com"


class RepoMetadata:
    def __init__(self, name: str, description: str | None, language: str | None, topics: list[str]):
        self.name = name
        self.description = description
        self.language = language
        self.topics = topics


def parse_github_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.netloc != "github.com":
        raise HTTPException(status_code=400, detail="URL must be a github.com repository")

    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="URL must point to a repository: github.com/owner/repo")

    return parts[0], parts[1]


async def fetch_repo_metadata(url: str) -> RepoMetadata:
    owner, repo = parse_github_url(url)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
            headers={"Accept": "application/vnd.github+json"},
        )

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Repository {owner}/{repo} not found")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch repository from GitHub")

    data = response.json()
    return RepoMetadata(
        name=data["full_name"],
        description=data.get("description"),
        language=data.get("language"),
        topics=data.get("topics", []),
    )

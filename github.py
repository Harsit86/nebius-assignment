import base64
import os
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

GITHUB_API_BASE = "https://api.github.com"
_HEADERS = {"Accept": "application/vnd.github+json"}
if _token := os.environ.get("GITHUB_TOKEN"):
    _HEADERS["Authorization"] = f"Bearer {_token}"

_MAX_FILE_SIZE = 100 * 1024  # 100KB


class RepoMetadata:
    def __init__(
        self,
        name: str,
        description: str | None,
        language: str | None,
        topics: list[str],
        stars: int = 0,
    ):
        self.name = name
        self.description = description
        self.language = language
        self.topics = topics
        self.stars = stars


class RepoContents:
    def __init__(
        self,
        metadata: RepoMetadata,
        readme: str | None,
        manifests: dict[str, str],
        tree: list[str],
    ):
        self.metadata = metadata
        self.readme = readme
        self.manifests = manifests
        self.tree = tree


def parse_github_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.netloc != "github.com":
        raise HTTPException(
            status_code=400,
            detail="URL must be a github.com repository",
        )

    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if len(parts) < 2:
        raise HTTPException(
            status_code=400,
            detail="URL must point to a repository: github.com/owner/repo",
        )

    return parts[0], parts[1]


async def _fetch_file_content(
    owner: str, repo: str, path: str, client: httpx.AsyncClient
) -> str | None:
    response = await client.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
        headers=_HEADERS,
    )
    if response.status_code != 200:
        return None
    data = response.json()
    if data.get("encoding") != "base64":
        return None
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


async def _fetch_file_tree(
    owner: str, repo: str, client: httpx.AsyncClient
) -> list[str]:
    response = await client.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1",
        headers=_HEADERS,
    )
    if response.status_code != 200:
        return []
    data = response.json()
    return [
        item["path"]
        for item in data.get("tree", [])
        if item["type"] == "blob" and item.get("size", 0) <= _MAX_FILE_SIZE
    ]


async def fetch_repo_metadata(url: str) -> RepoMetadata:
    owner, repo = parse_github_url(url)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
            headers=_HEADERS,
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404, detail=f"Repository {owner}/{repo} not found"
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API error: {response.status_code}",
        )

    data = response.json()
    return RepoMetadata(
        name=data["full_name"],
        description=data.get("description"),
        language=data.get("language"),
        topics=data.get("topics", []),
        stars=data.get("stargazers_count", 0),
    )


async def fetch_repo_contents(url: str) -> RepoContents:
    owner, repo = parse_github_url(url)

    async with httpx.AsyncClient() as client:
        meta_response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
            headers=_HEADERS,
        )
        if meta_response.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"Repository {owner}/{repo} not found"
            )
        if meta_response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"GitHub API error: {meta_response.status_code}",
            )

        meta_data = meta_response.json()
        metadata = RepoMetadata(
            name=meta_data["full_name"],
            description=meta_data.get("description"),
            language=meta_data.get("language"),
            topics=meta_data.get("topics", []),
            stars=meta_data.get("stargazers_count", 0),
        )

        readme = await _fetch_file_content(owner, repo, "README.md", client)
        tree = await _fetch_file_tree(owner, repo, client)
        root_files = [path for path in tree if "/" not in path]
        manifests: dict[str, str] = {}
        for path in root_files:
            content = await _fetch_file_content(owner, repo, path, client)
            if content is not None:
                manifests[path] = content

    return RepoContents(
        metadata=metadata,
        readme=readme,
        manifests=manifests,
        tree=tree,
    )

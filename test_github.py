from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from github import fetch_repo_contents, fetch_repo_metadata, parse_github_url


def test_parse_github_url_valid():
    owner, repo = parse_github_url("https://github.com/owner/repo")
    assert owner == "owner"
    assert repo == "repo"


def test_parse_github_url_valid_git_suffix():
    owner, repo = parse_github_url("https://github.com/owner/repo.git")
    assert owner == "owner"
    assert repo == "repo"


def test_parse_github_url_invalid_domain():
    with pytest.raises(HTTPException) as exc_info:
        parse_github_url("https://gitlab.com/owner/repo")
    assert exc_info.value.status_code == 400


def test_parse_github_url_missing_repo():
    with pytest.raises(HTTPException) as exc_info:
        parse_github_url("https://github.com/owner")
    assert exc_info.value.status_code == 400


def test_parse_github_url_empty_path():
    with pytest.raises(HTTPException) as exc_info:
        parse_github_url("https://github.com/")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_fetch_repo_metadata_valid():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "full_name": "owner/repo",
        "description": "A test repo",
        "language": "Python",
        "topics": ["fastapi", "python"],
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    mock_async_client = AsyncMock(
        __aenter__=AsyncMock(return_value=mock_client),
        __aexit__=AsyncMock(),
    )
    with patch("github.httpx.AsyncClient", return_value=mock_async_client):
        metadata = await fetch_repo_metadata("https://github.com/owner/repo")

    assert metadata.name == "owner/repo"
    assert metadata.description == "A test repo"
    assert metadata.language == "Python"
    assert metadata.topics == ["fastapi", "python"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_repo_metadata_psf_requests():
    metadata = await fetch_repo_metadata("https://github.com/psf/requests")

    assert metadata.name == "psf/requests"
    assert metadata.description == "A simple, yet elegant, HTTP library."
    assert metadata.language == "Python"
    assert metadata.topics == [
        "client",
        "cookies",
        "forhumans",
        "http",
        "humans",
        "python",
        "python-requests",
        "requests",
    ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_repo_contents_psf_requests():
    contents = await fetch_repo_contents("https://github.com/psf/requests")

    assert contents.metadata.name == "psf/requests"
    assert contents.readme is not None
    assert len(contents.tree) > 0
    assert "README.md" in contents.tree
    assert len(contents.manifests) > 0
    assert contents.manifests.get("README.md") is not None
    assert contents.manifests["README.md"].split()[1] == "Requests"

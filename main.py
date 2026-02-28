from fastapi import FastAPI
from pydantic import BaseModel

from github import fetch_repo_metadata

app = FastAPI(
    title="Nebius Assignment",
    description="Accepts a GitHub repository URL and returns an LLM-generated summary.",
    version="0.1.0",
)


class SummarizeRequest(BaseModel):
    url: str


class SummarizeResponse(BaseModel):
    summary: str
    technologies: list[str]
    structure: str


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    _metadata = await fetch_repo_metadata(request.url)
    return SummarizeResponse(summary="", technologies=[], structure="")

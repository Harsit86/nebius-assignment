from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from github import fetch_repo_contents
from nebius import summarize_repo

load_dotenv()

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
    contents = await fetch_repo_contents(request.url)
    result = await summarize_repo(contents)
    return SummarizeResponse(**result)

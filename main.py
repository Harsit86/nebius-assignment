from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from github import fetch_repo_contents
from nebius import summarize_repo

load_dotenv()

app = FastAPI(
    title="Nebius Assignment",
    description="Accepts a GitHub repository URL and returns an LLM-generated summary.",
    version="0.1.0",
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(exc)},
    )


class SummarizeRequest(BaseModel):
    github_url: str


class SummarizeResponse(BaseModel):
    summary: str
    technologies: list[str]
    structure: str


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    contents = await fetch_repo_contents(request.github_url)
    result = await summarize_repo(contents)
    return SummarizeResponse(**result)

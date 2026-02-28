install:
	uv sync

test:
	uv run pytest -m ""

run_api:
	uv run uvicorn main:app --reload

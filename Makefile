install:
	uv sync
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest -m ""

run_api:
	uv run uvicorn main:app --reload

run:
	uv run python -m migration.main

lint:
	uv run mypy .

install:
	uv sync

format:
	uv run black .
	uv run isort .

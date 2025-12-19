lint:
	uv run mypy .

install:
	uv sync

format:
	uv run black .
	uv run isort .

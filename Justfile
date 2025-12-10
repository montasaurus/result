install:
	uv sync

build:
	uv build

test:
	uv run pytest

test-ci:
	uv run --frozen pytest

pyright:
	uv run pyright

mypy:
	uv run mypy

ruff:
	uv run ruff check .

[parallel]
check: pyright ruff mypy

fix:
	uv run ruff check . --fix
	uv run ruff format


[confirm("Are you sure you want to delete all runtime data in var?")]
clean:
	git clean var -X --force

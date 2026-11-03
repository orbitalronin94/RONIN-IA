.PHONY: install test lint check info readiness

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check ronin tests scripts

check: lint test

info:
	ronin info --profile tiny

readiness:
	ronin readiness --profile tiny

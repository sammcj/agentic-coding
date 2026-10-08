.PHONY: help run lint format typecheck test check

REPO ?= .
PY := PYTHONPATH=scripts:tests python3

help:
	@echo "make run REPO=path   serve the dashboard for an OpenSpec repo"
	@echo "make test            run the tests"
	@echo "make lint            ruff lint + format check, JS syntax check"
	@echo "make typecheck       ty type check"
	@echo "make check           lint, typecheck and test"

run:
	scripts/serve.py $(REPO)

test:
	$(PY) -m unittest discover -s tests -t tests

lint:
	uvx ruff check scripts tests
	uvx ruff format --check scripts tests
	@for f in assets/web/*.js assets/web/views/*.js; do node --check "$$f" || exit 1; done

format:
	uvx ruff format scripts tests
	uvx ruff check --fix scripts tests

typecheck:
	uvx ty check --extra-search-path scripts --extra-search-path tests scripts tests

check: lint typecheck test

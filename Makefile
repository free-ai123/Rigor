PYTHON ?= python3
VENV_PYTHON := .venv/bin/python
ifneq ("$(wildcard $(VENV_PYTHON))","")
PYTHON := $(VENV_PYTHON)
endif

.PHONY: bootstrap install install-dev test app-test lint format check ci scan

bootstrap:
	bash scripts/bootstrap.sh --skip-hermes

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev,security]"

test:
	$(PYTHON) -m pytest

app-test:
	@if [ -f serverguard/requirements.txt ]; then \
		$(PYTHON) -m pip install -r serverguard/requirements.txt; \
		$(PYTHON) -m pytest tests/test_serverguard --no-cov; \
	else \
		echo "No generated app test suite found."; \
	fi

lint:
	$(PYTHON) -m ruff check src tests

format:
	$(PYTHON) -m ruff format src tests

check:
	$(PYTHON) -m ruff check src tests
	$(PYTHON) -m ruff format --check src tests
	$(PYTHON) -m pytest

scan:
	$(PYTHON) -m rigor.cli scan --dir . --language all

ci: check

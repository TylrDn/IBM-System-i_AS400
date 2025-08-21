VENV?=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: dev legacy-run test lint package install run sync setup clean-staging coverage

dev:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	$(PIP) install pytest flake8 ruff pyinstaller pytest-cov coverage

legacy-run: dev
	$(PYTHON) payroll.py

install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

run: install
	$(PYTHON) -m src.runner --file tests/smoke_local.csv --dry-run

sync: install
	$(PYTHON) -m src.runner --file tests/smoke_local.csv --sync --dry-run

setup: sync

clean-staging: install
	$(PYTHON) -m src.runner --teardown --dry-run --file tests/smoke_local.csv

test: dev
	$(PYTHON) -m pytest

lint: dev
	$(VENV)/bin/ruff .
	$(VENV)/bin/flake8 .

package: dev
	$(VENV)/bin/pyinstaller pyinstaller.spec

coverage: dev
	$(PYTHON) -m pytest --cov=. --cov-report=xml:coverage.xml
	bash <(curl -Ls https://coverage.codacy.com/get.sh) report -r coverage.xml

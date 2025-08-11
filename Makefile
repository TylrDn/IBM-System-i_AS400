VENV?=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: dev run test lint package

dev:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	$(PIP) install pytest flake8 ruff pyinstaller

run: dev
	$(PYTHON) payroll.py

test: dev
	$(PYTHON) -m pytest

lint: dev
	$(VENV)/bin/ruff .
	$(VENV)/bin/flake8 .

package: dev
	$(VENV)/bin/pyinstaller pyinstaller.spec

# macOS ships no `python`, only `python3`; some Linux images are the other way
# round. Resolve it once here rather than making every user discover it.
PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)

.PHONY: help install demo quick audit doctor test lint ingest run clean

help:
	@echo "make install   install the package and dev dependencies"
	@echo "make demo      synthetic world -> pipeline -> data/build/report.html"
	@echo "make quick     the same, smaller and without the leakage study"
	@echo "make doctor    check that a real ingest would work, before starting one"
	@echo "make audit     run the leakage checks; non-zero exit on any failure"
	@echo "make test      run the test suite"
	@echo "make ingest    pull real EDGAR filings and prices (needs network)"
	@echo "make run       run the pipeline over whatever make ingest produced"
	@echo
	@echo "using PYTHON=$(PYTHON)"

check-python:
	@test -n "$(PYTHON)" || { \
	  echo "No python3 found on PATH."; \
	  echo "  macOS:  brew install python   (or install the Xcode command line tools)"; \
	  echo "  Ubuntu: sudo apt install python3 python3-venv"; \
	  exit 1; }

install: check-python
	$(PYTHON) -m pip install -e ".[dev]"

demo: check-python
	$(PYTHON) -m filing_triage.cli demo --issuers 300

quick: check-python
	$(PYTHON) -m filing_triage.cli demo --issuers 80 --quick

doctor: check-python
	$(PYTHON) -m filing_triage.cli doctor

audit: check-python
	$(PYTHON) -m filing_triage.cli audit

test: check-python
	$(PYTHON) -m pytest

lint: check-python
	$(PYTHON) -m ruff check src tests scripts

ingest: check-python
	@test -n "$$EDGAR_USER_AGENT" || { \
	  echo 'EDGAR_USER_AGENT is not set. The SEC requires an identifying'; \
	  echo 'User-Agent with a real name and email:'; \
	  echo; \
	  echo '  export EDGAR_USER_AGENT="Your Name you@example.com"'; \
	  exit 1; }
	$(PYTHON) -m filing_triage.cli ingest

run: check-python
	$(PYTHON) -m filing_triage.cli run

clean:
	rm -rf data/build .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -exec rm -rf {} +

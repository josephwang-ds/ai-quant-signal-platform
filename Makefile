# Resolve the interpreter once, rather than making every user discover it.
#
# The project's own virtualenv comes first. It sits in the source tree, it is the
# one the dependencies are installed into, and forgetting to activate a shell is
# not a reason for the build to fail with a version error about a system Python
# nobody meant to use. After that: python3 (macOS ships no bare `python`), then
# python (some Linux images are the other way round). PYTHON=... overrides all of it.
PYTHON ?= $(shell   test -x .venv/bin/python && echo .venv/bin/python ||   command -v python3 2>/dev/null ||   command -v python 2>/dev/null)

.PHONY: help install demo quick audit doctor test lint ingest run clean

help:
	@echo "make install   install the package and dev dependencies"
	@echo "make demo      synthetic world -> pipeline -> data/build/report.html"
	@echo "make quick     the same, smaller and without the leakage study"
	@echo "make universe  resolve the demo ticker list to CIKs (needs network)"
	@echo "make doctor    check that a real ingest would work, before starting one"
	@echo "make audit     run the leakage checks; non-zero exit on any failure"
	@echo "make test      run the test suite"
	@echo "make ingest    pull real EDGAR filings and prices (needs network)"
	@echo "make run       run the pipeline over whatever make ingest produced"
	@echo "make site      publish the latest report to web/ for the static site"
	@echo
	@echo "using PYTHON=$(PYTHON)"

check-python:
	@test -n "$(PYTHON)" || { \
	  echo "No python3 found on PATH."; \
	  echo "  macOS:  brew install python@3.12"; \
	  echo "  Ubuntu: sudo apt install python3 python3-venv"; \
	  exit 1; }
	@$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || { \
	  echo "Python 3.11+ required; $(PYTHON) is $$($(PYTHON) -V 2>&1)."; \
	  echo; \
	  echo "macOS ships 3.9 with the Xcode command line tools, and a venv built"; \
	  echo "from it inherits both the old interpreter and a pip too old to install"; \
	  echo "this project at all. Build the venv from a newer interpreter:"; \
	  echo; \
	  echo "  brew install python@3.12"; \
	  echo "  rm -rf .venv && python3.12 -m venv .venv"; \
	  echo "  source .venv/bin/activate"; \
	  echo "  make install"; \
	  exit 1; }

install: check-python
	@# pip older than 21.3 cannot do an editable install of a project that has
	@# only a pyproject.toml (PEP 660), and fails claiming setup.py is missing --
	@# which sends you looking for the wrong problem entirely. Upgrade first.
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
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

universe: check-python
	@test -n "$$EDGAR_USER_AGENT" || { \
	  echo 'export EDGAR_USER_AGENT="Your Name you@example.com"'; exit 1; }
	$(PYTHON) scripts/build_demo_universe.py --out data/build/universe.csv

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

site: check-python
	@test -f data/build/report.html || { \
	  echo "data/build/report.html not found -- run 'make demo' or 'make run' first"; \
	  exit 1; }
	@cp data/build/report.html web/report.html
	@echo "web/report.html updated from the latest run."
	@echo "Commit it to publish: the site is served statically, with no build step,"
	@echo "so what is in git is what goes live."

clean:
	rm -rf data/build .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -exec rm -rf {} +

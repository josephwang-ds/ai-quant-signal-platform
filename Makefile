.PHONY: help install demo quick audit test lint ingest run clean

help:
	@echo "make install   install the package and dev dependencies"
	@echo "make demo      synthetic world -> pipeline -> data/build/report.html"
	@echo "make quick     the same, smaller and without the leakage study"
	@echo "make audit     run the leakage checks; non-zero exit on any failure"
	@echo "make test      run the test suite"
	@echo "make ingest    pull real EDGAR filings and prices (needs network)"
	@echo "make run       run the pipeline over whatever make ingest produced"

install:
	pip install -e ".[dev]"

demo:
	python -m filing_triage.cli demo --issuers 300

quick:
	python -m filing_triage.cli demo --issuers 80 --quick

audit:
	python -m filing_triage.cli audit

test:
	python -m pytest

lint:
	ruff check src tests

ingest:
	@test -n "$$EDGAR_USER_AGENT" || (echo "set EDGAR_USER_AGENT=\"Your Name you@example.com\"" && exit 1)
	python -m filing_triage.cli ingest

run:
	python -m filing_triage.cli run

clean:
	rm -rf data/build .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -exec rm -rf {} +

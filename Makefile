# Makefile
# Common development tasks

.PHONY: help install test lint run clean

help:
	@echo "Available commands:"
	@echo "  make install   - Install dependencies"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linters"
	@echo "  make run       - Run the crawler"
	@echo "  make clean     - Clean temporary files"

install:
	pip install -r requirements/dev.txt

test:
	pytest tests/ -v --cov=src

lint:
	black src/ tests/
	flake8 src/ tests/
	mypy src/

run:
	python scripts/run.py -q energy infrastructure telecom

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
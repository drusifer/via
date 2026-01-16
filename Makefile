# Makefile for the VIA project

.PHONY: all venv install test clean

# Variables
PYTHON := python3
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python

# Default target runs install and test
all: install test

# Create the virtual environment if it doesn't exist
$(VENV_DIR):
	$(PYTHON) -m venv $(VENV_DIR)

venv: $(VENV_DIR)

# Install dependencies into the virtual environment
install: venv
	$(VENV_PYTHON) -m pip install --upgrade pip && $(VENV_PYTHON) -m pip install -e .

# Run tests using the virtual environment's pytest
test: install
	$(VENV_PYTHON) -m pytest tests/

# Clean up the project directory
clean:
	rm -rf .via/
	rm -rf $(VENV_DIR)
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -rf .pytest_cache .coverage htmlcov
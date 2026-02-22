SHELL := /bin/bash

UV ?= uv
UV_CACHE_DIR ?= /tmp/uv-cache
PYTHON_VERSION ?= 3.11
VENV_PYTHON := .venv/bin/python
UV_RUN := UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) run --no-sync --python $(VENV_PYTHON)
DEV_TOOLS := pytest ruff

.PHONY: install start test smoke lint check-venv

install:
	UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) venv --python $(PYTHON_VERSION) .venv
	UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) pip install --python $(VENV_PYTHON) -e .
	UV_CACHE_DIR=$(UV_CACHE_DIR) $(UV) pip install --python $(VENV_PYTHON) $(DEV_TOOLS)

check-venv:
	@test -x $(VENV_PYTHON) || (echo "Missing .venv. Run 'make install' first."; exit 1)

start: check-venv
	$(UV_RUN) -m server

test: check-venv
	$(UV_RUN) pytest -q

smoke: check-venv
	@test -n "$(GOOGLE_EMAIL)" || (echo "GOOGLE_EMAIL is required"; exit 1)
	@test -n "$(GOOGLE_MASTER_TOKEN)" || (echo "GOOGLE_MASTER_TOKEN is required"; exit 1)
	$(UV_RUN) scripts/smoke_test.py

lint: check-venv
	$(UV_RUN) ruff check .

# Makefile for the VIA project

.DEFAULT_GOAL := help

.PHONY: dist release install-hooks security-scan-secrets security-scan-python security-scan-npm security-scan all venv install install-dev test coverage test-coverage test-js test-e2e test-all clean lint-fast lint lint-slow duplicates security dead-code fix install-system via-watch via-mcp-serve via deploy-forgejo help

# Variables
PYTHON := python3
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_ACTIVATE := $(VENV_DIR)/bin/activate
VENV_STAMP := $(VENV_DIR)/venv.stamp

REQUIREMENTS := pyproject.toml
INSTALL_STAMP := $(VENV_DIR)/installed.stamp
INSTALL_DEV_STAMP := $(VENV_DIR)/installed-dev.stamp

# Default target runs install and test
all: install test

# Create the virtual environment if it doesn't exist
$(VENV_STAMP):
	$(PYTHON) -m venv $(VENV_DIR)
	touch $(VENV_STAMP)

venv: $(VENV_STAMP)

# Install dependencies into the virtual environment
$(INSTALL_STAMP): $(VENV_STAMP) $(REQUIREMENTS)
	$(VENV_PYTHON) -m pip install --upgrade pip && $(VENV_PYTHON) -m pip install -e .
	touch $(INSTALL_STAMP)

install: $(INSTALL_STAMP)

# Install dev dependencies. This target is self-contained and includes base dependencies.
# It no longer depends on the 'install' target's stamp file to avoid redundant installations.
$(INSTALL_DEV_STAMP): $(VENV_STAMP) $(REQUIREMENTS)
	. ${VENV_ACTIVATE} && pip install -e ".[dev]"
	touch $(INSTALL_DEV_STAMP)

install-dev: $(INSTALL_DEV_STAMP)

via: install-dev ## Run via command in the virtual environment (usage: make via ARGS="...")
	$(VENV_DIR)/bin/via $(ARGS)

# Run tests using the virtual environment's python
test: install-dev
	rm -f .coverage .coverage.*
	. ${VENV_ACTIVATE} && pytest $(or $(FILE),tests/) $(ARGS)

# Run tests with terminal coverage plus LCOV export
coverage: install-dev
	rm -f .coverage .coverage.*
	mkdir -p coverage
	. ${VENV_ACTIVATE} && pytest $(or $(FILE),tests/) \
		--cov=via \
		--cov-report=term-missing \
		--cov-report=lcov:coverage/lcov.info \
		$(ARGS)

# Capture per-test coverage + run metadata (status/duration/last-run), then
# import into the via index as `covered-by` (per-test) and `test_runs`.
# Subprocess tests (e.g. tests/subprocess/) are also attributed per-test via
# coverage.py's `patch = ["subprocess"]` and conftest.py context propagation.
test-coverage: install-dev
	rm -f .coverage .coverage.*
	. ${VENV_ACTIVATE} && python -m via index .
	. ${VENV_ACTIVATE} && pytest --cov=via --cov-branch --cov-context=test -v tests/
	. ${VENV_ACTIVATE} && python -m via coverage import-contexts .coverage
	. ${VENV_ACTIVATE} && python -m via coverage report -o coverage/via-test-quality-report.html

# Run JavaScript unit tests
test-js:
	npm test

# Run Playwright E2E tests (requires via installed; screenshots saved to tests/e2e/screenshots/)
test-e2e:
	npx playwright test

# Run all tests: Python + JavaScript + E2E
test-all: test test-js test-e2e

# Clean up the project directory
clean:
	rm -rf .via/
	rm -rf $(VENV_DIR)
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -rf .pytest_cache .coverage htmlcov coverage

# =============================================================================
# Static Analysis Tools
# =============================================================================

# FAST: Ruff hygiene only - unused imports/vars, dead code (~1 sec)
lint-fast: install-dev
	@echo "=== RUFF: Hygiene (unused imports/vars, dead code) ==="
	. ${VENV_ACTIVATE} && ruff check via/ --select F401,F841,ERA

# MEDIUM: Ruff hygiene + Bandit security (~5 sec)
lint: install-dev fix
	@echo "=== RUFF: Hygiene (unused imports/vars, dead code) ==="
	-. ${VENV_ACTIVATE} && ruff check via/ --select F401,F841,ERA
	@echo ""
	@echo "=== BANDIT: Security Analysis ==="
	. ${VENV_ACTIVATE} && bandit -r via/ -c pyproject.toml

# SLOW: Full analysis - Ruff complexity + hygiene + Pylint (duplicates) + Bandit (~30 sec)
lint-slow: install-dev duplicates security vulture
	@echo "=== RUFF: Complexity, Dead Code, Unused Imports ==="
	-. ${VENV_ACTIVATE} && ruff check via/
	@echo ""
	@echo "=== PYLINT: Duplicate Code & Design Rules ==="
	-. ${VENV_ACTIVATE} && pylint via/ --disable=all --enable=duplicate-code
	@echo ""
	@echo "=== BANDIT: Security Analysis ==="
	-. ${VENV_ACTIVATE} && bandit -r via/ -c pyproject.toml

# Individual tools (for targeted runs)
duplicates: install-dev
	. ${VENV_ACTIVATE} && pylint via/ --disable=all --enable=duplicate-code

security: install-dev
	. ${VENV_ACTIVATE} && bandit -r via/ -c pyproject.toml

dead-code: install-dev ## Run Vulture dead code detection against via/
	. ${VENV_ACTIVATE} && vulture via/ --min-confidence 80

fix: install-dev
	@echo "=== RUFF: fix ==="
	. ${VENV_ACTIVATE} && ruff check --fix via/

# Run Via watch mode with the web UI enabled. Override DIR/PORT as needed:
# make via-watch DIR=. PORT=7891
via-watch: install-dev
	. ${VENV_ACTIVATE} && via index -w $(or $(DIR),.) --port $(or $(PORT),7891)

# Run the Via MCP stdio server. This also starts watch mode and serves the web UI.
# Override DIR/PORT as needed: make via-mcp-serve DIR=. PORT=7891
via-mcp-serve: install-dev
	. ${VENV_ACTIVATE} && via mcp serve $(or $(DIR),.) --port $(or $(PORT),7891)

# Install via as a package available globally via pipx
install-system: ## Install via globally using pipx (makes 'via' command available system-wide)
	pipx install --editable . --force

# Build sdist + wheel and validate metadata (artifacts land in dist/)
dist: install-dev ## Build sdist and wheel into dist/ and validate with twine
	rm -rf dist
	. ${VENV_ACTIVATE} && python -m build && twine check dist/*

# ── Publish to public PyPI via GitHub trusted publishing (drew.gs.works) ───────
# Creating a GitHub Release triggers .github/workflows/publish.yml, which builds
# and publishes `via-index` to PyPI (OIDC; no token). Needs `gh` authenticated
# with permission to create releases. Version comes from via/__init__.py.
VERSION := $(shell sed -n 's/^__version__ = "\(.*\)"/\1/p' via/__init__.py)

release: dist ## Tag v<version>, push, and create the GitHub Release that publishes via-index to PyPI
	@test -n "$(VERSION)" || { echo "cannot read version from via/__init__.py"; exit 1; }
	@test "$$(git rev-parse --abbrev-ref HEAD)" = main || { echo "release must run from main"; exit 1; }
	@git diff --quiet HEAD -- pyproject.toml via || { echo "uncommitted changes in package files"; exit 1; }
	@git fetch -q origin main && test "$$(git rev-parse HEAD)" = "$$(git rev-parse origin/main)" || { echo "HEAD must match origin/main (push first)"; exit 1; }
	@git rev-parse -q --verify refs/tags/v$(VERSION) >/dev/null || git tag -a v$(VERSION) -m "via-index $(VERSION)"
	git push origin v$(VERSION)
	@gh release view v$(VERSION) >/dev/null 2>&1 && { echo "release v$(VERSION) already exists"; exit 1; } || true
	gh release create v$(VERSION) --generate-notes --title "via-index $(VERSION)"

# ── Secret scanning hooks (Tank / Switch standard) ─────────────────────────────
install-hooks: ## Enable .githooks/pre-commit (gitleaks on staged changes) via core.hooksPath
	@command -v gitleaks >/dev/null || { echo "gitleaks is not installed: https://github.com/gitleaks/gitleaks#installing"; exit 1; }
	git config core.hooksPath .githooks
	@echo "git hooks enabled: .githooks/pre-commit (gitleaks)"

security-scan-secrets: ## Scan git history for committed secrets (gitleaks, git-aware)
	@command -v gitleaks >/dev/null || { echo "gitleaks is not installed: https://github.com/gitleaks/gitleaks#installing"; exit 1; }
	gitleaks detect --source . --no-banner

security-scan-python: install-dev ## Audit installed Python dependencies with pip-audit
	@test -x $(VENV_DIR)/bin/pip-audit || { echo "pip-audit is not installed in $(VENV_DIR): run 'make install-dev' (requires pip-audit>=2.7.0 in pyproject.toml)"; exit 1; }
	. ${VENV_ACTIVATE} && pip-audit

security-scan-npm: ## Audit JS dev dependencies (high and above) against package-lock.json
	@command -v npm >/dev/null || { echo "npm is not installed: install Node.js/npm (https://nodejs.org/)"; exit 1; }
	npm audit --audit-level=high

security-scan: security-scan-secrets security-scan-python security-scan-npm ## Run all build-time security scans (secrets, Python deps, npm deps)

# ── Publish to the pi-patch Forgejo registry (forge.pi-patch.lan) ──────────────
# Credentials: make -C $(PI_PATCH)/cluster forgejo-token
PI_PATCH        ?= $(HOME)/Projects/pi-patch
FORGEJO_PUBLISH := $(PI_PATCH)/cluster/scripts/forgejo-publish.sh
FORGEJO_VERSION ?= $(shell git describe --tags --always --dirty)

deploy-forgejo: dist ## Build the via-index wheel/sdist and publish to pi-patch Forgejo PyPI
	$(FORGEJO_PUBLISH) pypi dist

help: ## Show available make targets
	@grep -E '^[a-zA-Z_][a-zA-Z0-9_-]*:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  %-20s %s\n", $$1, $$2}'
